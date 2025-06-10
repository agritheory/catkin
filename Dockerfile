# Multi-stage build for Python application + Caddy

# --------------------------------------------------------------------------------

# 1. Build stage for Python dependencies
FROM python:3.12-slim AS dependencies

RUN pip install --no-cache-dir poetry poetry-plugin-export

WORKDIR /app

# Copy only dependency files first to leverage Docker layer caching
COPY pyproject.toml poetry.lock ./

# Generate requirements.txt for a more efficient pip install
RUN poetry export --without-hashes --format=requirements.txt > requirements.txt

# --------------------------------------------------------------------------------

# 2. Build stage for the Python application
FROM python:3.12-slim AS auth

WORKDIR /app

# Install system dependencies and Python requirements
COPY --from=dependencies /app/requirements.txt .
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y --auto-remove build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy app code
COPY catkin ./catkin

# Create a marker file to identify site-packages directory
RUN python -c "import site; open('/usr/local/lib/python3.12/site-packages/SITE_PACKAGES_DIR', 'w').close()"

# --------------------------------------------------------------------------------

# 3. Final stage using Caddy as the base
FROM caddy:2-alpine AS proxy

# Set environment variables for configuration
ENV CATKIN_PORT=5000 \
    CADDY_CONFIG_PATH=/etc/caddy/Caddyfile \
    PYTHONPATH=/app \
    DEFAULT_REDIRECT="/"

# Create directory structure for Caddy
# These directories will be available for mounting volumes
RUN mkdir -p /data /config /var/log/caddy

# Add a default Caddyfile that can be overridden by volume mounts
COPY caddy/configs/Caddyfile /etc/caddy/Caddyfile.default

# Copy Python application from the build stage
COPY --from=auth /app /app

# Install Python and set up a virtual environment for dependencies
RUN apk add --no-cache python3 py3-pip libpq tini netcat-openbsd && \
    python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir uvicorn asyncpg jinja2 cryptography databases pyjwt environs quart quart-cors strawberry-graphql httpx

# Update environment to use the virtual environment
ENV PATH="/app/venv/bin:$PATH" \
    VIRTUAL_ENV="/app/venv"

# Set work directory
WORKDIR /app

# Expose ports for Caddy and the Python app
EXPOSE 80 443 $CATKIN_PORT

# Create a healthcheck for the combined container
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost/health || exit 1

# Add wait-for-it script to check database connectivity
COPY <<EOF /wait-for-it.sh
#!/bin/sh
# Simple wait-for-it script to wait for a host:port to be available
HOST=\${1}
PORT=\${2}
TIMEOUT=\${3:-30}
QUIET=\${4:-0}

if [ \$# -lt 2 ]; then
  echo "Usage: \$0 host port [timeout] [quiet]"
  exit 1
fi

start_time=\$(date +%s)
end_time=\$((start_time + TIMEOUT))

if [ \$QUIET -ne 1 ]; then
  echo "Waiting for \$HOST:\$PORT for up to \$TIMEOUT seconds..."
fi

while [ \$(date +%s) -lt \$end_time ]; do
  nc -z \$HOST \$PORT > /dev/null 2>&1
  result=\$?
  if [ \$result -eq 0 ]; then
    if [ \$QUIET -ne 1 ]; then
      echo "Connection to \$HOST:\$PORT succeeded!"
    fi
    exit 0
  fi
  sleep 1
done

if [ \$QUIET -ne 1 ]; then
  echo "Timeout: Could not connect to \$HOST:\$PORT within \$TIMEOUT seconds"
fi
exit 1
EOF

RUN chmod +x /wait-for-it.sh

# Create an entrypoint script with environment variable support
COPY <<EOF /entrypoint.sh
#!/bin/sh
# Check if DATABASE_URL is provided
if [ -z "\${DATABASE_URL}" ]; then
    echo "ERROR: No DATABASE_URL environment variable set."
    echo "Please provide a valid PostgreSQL connection URL using the DATABASE_URL environment variable."
    echo "Example: DATABASE_URL=postgresql://user:password@host:port/database"
    exit 1
fi

# Check if the URL is PostgreSQL
if [[ ! "\$DATABASE_URL" == postgresql* ]]; then
    echo "ERROR: Only PostgreSQL databases are supported."
    echo "DATABASE_URL must start with postgresql://"
    exit 1
fi

# Parse the database host and port from DATABASE_URL and wait for it
DB_HOST=\$(echo \$DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
DB_PORT=\$(echo \$DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

# If host and port were extracted successfully, wait for the database
if [ ! -z "\$DB_HOST" ] && [ ! -z "\$DB_PORT" ]; then
    echo "Waiting for PostgreSQL database at \$DB_HOST:\$DB_PORT..."
    /wait-for-it.sh \$DB_HOST \$DB_PORT 60
    if [ \$? -ne 0 ]; then
        echo "ERROR: Database at \$DB_HOST:\$DB_PORT is not available."
        exit 1
    fi
fi

# Check JWT_SECRET
if [ -z "\${JWT_SECRET}" ]; then
    echo "WARNING: No JWT_SECRET environment variable set. Using insecure default value!"
    echo "WARNING: This is fine for development but must be changed in production!"
    export JWT_SECRET="default-jwt-secret-change-in-production"
fi

# Check if a user-provided Caddyfile exists, otherwise use the default
if [ ! -f \${CADDY_CONFIG_PATH} ]; then
    echo "No user-provided Caddyfile found at \${CADDY_CONFIG_PATH}, using default configuration"
    cp /etc/caddy/Caddyfile.default \${CADDY_CONFIG_PATH}
else
    echo "Using user-provided Caddyfile at \${CADDY_CONFIG_PATH}"
fi

# Handle signals properly
cleanup() {
    echo "Received shutdown signal, stopping services..."
    if [ ! -z "\$PYTHON_PID" ]; then
        kill -TERM \$PYTHON_PID
    fi
    if [ ! -z "\$CADDY_PID" ]; then
        kill -TERM \$CADDY_PID
    fi
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

# Start the Python application in the background
echo "Starting Python application on port \${CATKIN_PORT}..."
cd /app && python -m uvicorn catkin.src.app:app --host 0.0.0.0 --port \${CATKIN_PORT} \${CATKIN_UVICORN_OPTS:-} &
PYTHON_PID=\$!

# Start Caddy in the background
echo "Starting Caddy server..."
caddy run --config \${CADDY_CONFIG_PATH} &
CADDY_PID=\$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit \$?
EOF

RUN chmod +x /entrypoint.sh

# Use tini as init system to properly handle signals and child processes
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]

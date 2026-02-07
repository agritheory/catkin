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

# Add wait-for-it and entrypoint scripts
COPY container/wait-for-it.sh /wait-for-it.sh
COPY container/entrypoint.sh /entrypoint.sh
RUN chmod +x /wait-for-it.sh /entrypoint.sh

# Use tini as init system to properly handle signals and child processes
ENTRYPOINT ["/sbin/tini", "--", "/entrypoint.sh"]

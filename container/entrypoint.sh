#!/bin/sh
# Check if DATABASE_URL is provided
if [ -z "${DATABASE_URL}" ]; then
    echo "ERROR: No DATABASE_URL environment variable set."
    echo "Please provide a valid PostgreSQL connection URL using the DATABASE_URL environment variable."
    echo "Example: DATABASE_URL=postgresql://user:password@host:port/database"
    exit 1
fi

# Check if the URL is PostgreSQL
case "$DATABASE_URL" in
    postgresql*) ;;
    *)
        echo "ERROR: Only PostgreSQL databases are supported."
        echo "DATABASE_URL must start with postgresql://"
        exit 1
        ;;
esac

# Parse the database host and port from DATABASE_URL and wait for it
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')

# If host and port were extracted successfully, wait for the database
if [ ! -z "$DB_HOST" ] && [ ! -z "$DB_PORT" ]; then
    echo "Waiting for PostgreSQL database at $DB_HOST:$DB_PORT..."
    /wait-for-it.sh $DB_HOST $DB_PORT 60
    if [ $? -ne 0 ]; then
        echo "ERROR: Database at $DB_HOST:$DB_PORT is not available."
        exit 1
    fi
fi

# Check JWT_SECRET
if [ -z "${JWT_SECRET}" ]; then
    echo "WARNING: No JWT_SECRET environment variable set. Using insecure default value!"
    echo "WARNING: This is fine for development but must be changed in production!"
    export JWT_SECRET="default-jwt-secret-change-in-production"
fi

# Check if a user-provided Caddyfile exists, otherwise use the default
if [ ! -f ${CADDY_CONFIG_PATH} ]; then
    echo "No user-provided Caddyfile found at ${CADDY_CONFIG_PATH}, using default configuration"
    cp /etc/caddy/Caddyfile.default ${CADDY_CONFIG_PATH}
else
    echo "Using user-provided Caddyfile at ${CADDY_CONFIG_PATH}"
fi

# Handle signals properly
cleanup() {
    echo "Received shutdown signal, stopping services..."
    if [ ! -z "$PYTHON_PID" ]; then
        kill -TERM $PYTHON_PID
    fi
    if [ ! -z "$CADDY_PID" ]; then
        kill -TERM $CADDY_PID
    fi
    exit 0
}

# Set up signal handlers
trap cleanup INT TERM

# Start the Python application in the background
echo "Starting Python application on port ${CATKIN_PORT}..."
cd /app && python -m uvicorn catkin.src.app:app --host 0.0.0.0 --port ${CATKIN_PORT} ${CATKIN_UVICORN_OPTS:-} &
PYTHON_PID=$!

# Start Caddy in the background
echo "Starting Caddy server..."
caddy run --config ${CADDY_CONFIG_PATH} &
CADDY_PID=$!

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?

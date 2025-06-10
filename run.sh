#!/bin/bash
# run.sh - Helper script to run the catkin container with proper configuration

# Default values
IMAGE_NAME="catkin-auth"
CONTAINER_NAME="catkin-auth"
DATABASE_HOST="localhost"
DATABASE_PORT="5432"
DATABASE_USER="postgres"
DATABASE_PASSWORD="postgres"
DATABASE_NAME="catkin_auth"
JWT_SECRET=$(openssl rand -hex 32) # Generate a random secret
CATKIN_PORT=5000
HOST_PORT=8080

# Help message
show_help() {
    echo "Usage: $0 [options]"
    echo
    echo "Options:"
    echo "  -h, --help                Show this help message"
    echo "  -i, --image NAME          Docker image name (default: $IMAGE_NAME)"
    echo "  -c, --container NAME      Container name (default: $CONTAINER_NAME)"
    echo "  -d, --db-host HOST        Database hostname (default: $DATABASE_HOST)"
    echo "  -p, --db-port PORT        Database port (default: $DATABASE_PORT)"
    echo "  -u, --db-user USER        Database username (default: $DATABASE_USER)"
    echo "  -w, --db-password PASS    Database password (default: $DATABASE_PASSWORD)"
    echo "  -n, --db-name NAME        Database name (default: $DATABASE_NAME)"
    echo "  -s, --jwt-secret SECRET   JWT secret (default: randomly generated)"
    echo "  -P, --port PORT           Host port to map to container port 80 (default: $HOST_PORT)"
    echo
    echo "Example:"
    echo "  $0 --db-host postgres-server --db-port 5432 --port 8080"
    echo
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -h|--help)
            show_help
            exit 0
            ;;
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -c|--container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -d|--db-host)
            DATABASE_HOST="$2"
            shift 2
            ;;
        -p|--db-port)
            DATABASE_PORT="$2"
            shift 2
            ;;
        -u|--db-user)
            DATABASE_USER="$2"
            shift 2
            ;;
        -w|--db-password)
            DATABASE_PASSWORD="$2"
            shift 2
            ;;
        -n|--db-name)
            DATABASE_NAME="$2"
            shift 2
            ;;
        -s|--jwt-secret)
            JWT_SECRET="$2"
            shift 2
            ;;
        -P|--port)
            HOST_PORT="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Construct DATABASE_URL
DATABASE_URL="postgresql://${DATABASE_USER}:${DATABASE_PASSWORD}@${DATABASE_HOST}:${DATABASE_PORT}/${DATABASE_NAME}"

# Build the container if needed
if ! docker images | grep -q "$IMAGE_NAME"; then
    echo "Building Docker image: $IMAGE_NAME"
    docker build -t "$IMAGE_NAME" .
fi

# Check if container is already running
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Container $CONTAINER_NAME is already running. Stopping it..."
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# Run the container
echo "Starting container with DATABASE_URL=$DATABASE_URL"
docker run -d \
    --name "$CONTAINER_NAME" \
    -p "${HOST_PORT}:80" \
    -p "${CATKIN_PORT}:5000" \
    -e "DATABASE_URL=${DATABASE_URL}" \
    -e "JWT_SECRET=${JWT_SECRET}" \
    -e "FERNET_KEY=${JWT_SECRET}" \
    "$IMAGE_NAME"

echo
echo "Container started!"
echo "Access the application at: http://localhost:${HOST_PORT}"
echo "Direct access to the API: http://localhost:${CATKIN_PORT}"
echo
echo "JWT_SECRET: ${JWT_SECRET}"
echo
echo "To view logs: docker logs $CONTAINER_NAME"
echo "To stop the container: docker stop $CONTAINER_NAME"

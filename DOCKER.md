# Catkin + Caddy Docker Image

This Docker image combines a Python-based authentication service (Catkin) with Caddy as a reverse proxy and security layer. It's designed to be used as a component within other applications while being highly configurable through environment variables and volume mounts.

## Features

- **Pre-configured Caddy Server**: Acts as a reverse proxy with built-in HTTPS
- **Authentication Service**: Python-based auth system using Quart and JWT
- **Configurable**: Easily customizable through environment variables and volume mounts
- **Performance Optimized**: Multi-stage build with minimal dependencies
- **Production Ready**: Includes proper signal handling and health checks

## Pre-built Images

Images are automatically built and published to GitHub Container Registry:

```bash
# Latest stable version
docker pull ghcr.io/agritheory/catkin:latest

# Development version
docker pull ghcr.io/agritheory/catkin:main

# Specific version
docker pull ghcr.io/agritheory/catkin:v1.0.0
```

## Quick Start

### Using GHCR Image

```bash
docker run -p 80:80 -p 443:443 \
  -e DATABASE_URL="postgresql://user:pass@your-db-host:5432/catkin_auth" \
  -e JWT_SECRET="your-secure-jwt-secret" \
  -v ./your-caddyfile:/etc/caddy/Caddyfile \
  -v catkin_data:/data \
  ghcr.io/agritheory/catkin:latest
```

### Private Registry Access

For private repositories, authenticate with GHCR:

```bash
# Using GitHub token
echo $GITHUB_TOKEN | docker login ghcr.io -u your-username --password-stdin

# Using GitHub CLI
gh auth token | docker login ghcr.io -u your-username --password-stdin
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string (required) | None |
| `JWT_SECRET` | Secret key for JWT token generation | `your-secret-key-change-in-production` |
| `FERNET_KEY` | Key for password encryption | None |
| `DEFAULT_REDIRECT` | Default redirect after login | `/` |
| `CATKIN_PORT` | Port for the Catkin service | `5000` |
| `CADDY_CONFIG_PATH` | Path to the Caddyfile | `/etc/caddy/Caddyfile` |
| `CATKIN_UVICORN_OPTS` | Additional options for Uvicorn | None |

## Volume Mounts

| Path | Purpose |
|------|---------|
| `/etc/caddy/Caddyfile` | Caddy configuration file |
| `/data` | Caddy data (certificates, etc.) |
| `/config` | Caddy configuration storage |
| `/var/log/caddy` | Caddy logs |

## Custom Caddyfile

You can provide your own Caddyfile by mounting it to the container:

```bash
docker run -v ./my-caddyfile:/etc/caddy/Caddyfile:ro ...
```

If no custom Caddyfile is provided, the container will use the default configuration.

## Health Check

The container includes a built-in health check that verifies the service is running properly. You can monitor the container's health using:

```bash
docker inspect --format='{{.State.Health.Status}}' container_id
```

## Using in Docker Compose

Example integration with other services:

```yaml
services:
  auth:
    image: catkin:latest
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/catkin_auth
      - JWT_SECRET=your-secure-jwt-secret
    volumes:
      - ./caddy/configs/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy_data:/data
    depends_on:
      - db
    ports:
      - "80:80"
      - "443:443"

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: catkin_auth
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  caddy_data:
  postgres_data:
```

## Using the Helper Script

For easier startup, you can use the included `run.sh` script:

```bash
./run.sh --db-host your-postgres-server --db-port 5432
```

This script automatically:
1. Builds the image if needed
2. Generates a secure JWT secret
3. Sets up proper environment variables
4. Runs the container with appropriate settings

Run `./run.sh --help` to see all available options.

## Troubleshooting

### Database Connection Issues

If you encounter database connection errors:

1. **Hostname Resolution**: When running standalone (not with docker-compose), use the actual database hostname instead of "db". In the error `Name does not resolve`, the container is trying to connect to a host called "db" that doesn't exist.

2. **Connection Timing**: The container includes a wait script to wait for the database to be available. You can set the timeout with the `-t` option in `run.sh`.

3. **Network Issues**: Ensure the database is accessible from the container network.

## Advanced Configuration

### Performance Tuning

For high-traffic deployments, consider adjusting Uvicorn settings:

```bash
docker run -e CATKIN_UVICORN_OPTS="--workers 4 --loop uvloop" ...
```

## Building the Image

### Local Build
```bash
docker build -t catkin:latest .
```

### Multi-platform Build
```bash
docker buildx build --platform linux/amd64,linux/arm64 -t catkin:latest .
```

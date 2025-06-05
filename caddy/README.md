# Caddy JWT Authentication System

This folder contains all files related to the Caddy JWT authentication system that secures normally unsecured services using JWT tokens from the catkin authentication service.

## Folder Structure

```
caddy/
├── README.md                    # This file - overview of the Caddy system
├── configs/                     # Caddy configuration files
│   ├── Caddyfile               # Development configuration (HTTP, ports 8000/8001)
│   └── Caddyfile.production    # Production configuration (HTTPS, security headers)
├── docs/                       # Documentation and architecture
│   ├── CADDY_JWT_SETUP.md      # Complete setup and configuration guide
│   └── ARCHITECTURE_DIAGRAMS.md # System architecture and flow diagrams
├── scripts/                    # Deployment and testing scripts
│   ├── docker-compose.caddy.yml # Docker compose setup for complete system
│   └── test-caddy-auth.sh      # Automated test script for validation
└── demo-apps/                  # Example protected applications
    ├── example-app1/           # Demo web application
    └── example-app2/           # Demo admin panel
```

## Quick Start

### Development Environment (Current Setup)

1. **Start the complete system:**
   ```bash
   # From project root (/home/rohan/agritheory/catkin/)
   cd caddy/configs
   caddy run --config Caddyfile
   ```

2. **Access the system:**
   - **Main gateway**: http://localhost:8000
   - **Auth service**: http://localhost:8000/auth/login
   - **Protected app 1**: http://localhost:8000/app1/ (proxies to :8080)
   - **Protected app 2**: http://localhost:8000/app2/ (proxies to :9000)
   - **Health check**: http://localhost:8000/health

### Production Deployment

1. **Deploy with Docker Compose:**
   ```bash
   cd caddy/scripts
   docker-compose -f docker-compose.caddy.yml up -d
   ```

2. **Production endpoints:**
   - Services only accessible through Caddy gateway (ports 80/443)
   - Internal services: auth:5000, app1:80, app2:80

### Testing

```bash
cd caddy/scripts
./test-caddy-auth.sh
```

**Note**: Commands should be run from the project root directory (`/home/rohan/agritheory/catkin/`) using the relative paths shown above.

## Key Features

- **Single Sign-On**: One login protects multiple services
- **JWT Authentication**: Secure token-based authentication with HTTP-only cookies
- **Zero Configuration**: Protect existing applications without code changes
- **Development & Production Ready**: Separate configurations for different environments

## Port Configuration Reference

### Development Environment
| Service | Port | Access | Purpose |
|---------|------|--------|---------|
| Caddy Gateway | 8000, 8001 | External | Main entry point |
| Auth Service | 5000 | External (direct) | catkin authentication |
| Protected App 1 | 8080 | External (direct) | Demo application |
| Protected App 2 | 9000 | External (direct) | Admin panel |
| Database | 5434 | External | PostgreSQL |

### Production Environment (Docker)
| Service | Port | Access | Purpose |
|---------|------|--------|---------|
| Caddy Gateway | 80, 443 | External | HTTPS entry point |
| auth | 5000 | Internal only | Authentication service |
| app1 | 80 | Internal only | Protected application |
| app2 | 80 | Internal only | Admin panel |
| db | 5432 | Internal only | PostgreSQL |
- **Header Injection**: User context automatically passed to backend services
- **Auto-HTTPS**: Automatic TLS certificates in production
- **Security Headers**: Built-in security headers (HSTS, CSP, etc.)
- **Error Handling**: Automatic redirects to login on authentication failure

## Configuration

- **Development**: Uses HTTP on ports 8000/8001 for easy local testing
- **Production**: HTTPS with Let's Encrypt certificates and security headers
- **Authentication**: Forward auth to catkin service on port 5000
- **Protected Services**: Any service can be protected by adding forward_auth directive

## Documentation

See `docs/CADDY_JWT_SETUP.md` for complete setup instructions and `docs/ARCHITECTURE_DIAGRAMS.md` for system architecture diagrams.

## Testing

The `scripts/test-caddy-auth.sh` script provides comprehensive testing of:
- Unauthenticated access blocking
- Login flow
- JWT token validation
- Protected resource access
- Security headers
- Health checks

## Integration

To protect a new service, add to your Caddyfile:

```caddyfile
handle /your-service/* {
    forward_auth localhost:5000 {
        uri /auth/verify
        copy_headers X-User-Email X-User-ID X-Auth-Method
    }
    uri strip_prefix /your-service
    reverse_proxy localhost:YOUR_SERVICE_PORT
}
```

The service will receive authenticated requests with user context in headers.

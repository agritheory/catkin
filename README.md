# Catkin - Simple Auth Server

A lightweight authentication server built with Quart that provides both local and OAuth-based authentication with JWT tokens. Designed to work as a forward authentication service for reverse proxies like Caddy.

## Features

- **Local Authentication**: Username/password login with encrypted password storage
- **OAuth Integration**: Support for multiple OAuth providers (Frappe, Google, GitHub)
- **JWT Tokens**: Secure token-based authentication with configurable expiration
- **Forward Auth**: Compatible with Caddy's `forward_auth` directive
- **Database Backend**: PostgreSQL with asyncpg for high performance
- **Encrypted Storage**: Passwords and OAuth secrets encrypted using Fernet
- **Docker Ready**: Includes Docker and docker-compose configuration

## Architecture

- **Backend**: Quart (async Python web framework)
- **Database**: PostgreSQL 16
- **Authentication**: JWT tokens with HTTP-only cookies
- **Encryption**: Fernet symmetric encryption for sensitive data
- **Deployment**: Docker with docker-compose
- **Reverse Proxy**: Caddy with forward authentication

## Quick Start

### Using Docker Compose with GHCR Images (Recommended)

1. **Clone and setup environment**:
   ```bash
   cd catkin
   touch .env  # Create your environment file
   ```

2. **Configure environment variables** in `.env`:
   ```bash
   # Required
   FERNET_KEY=your-fernet-key-here
   JWT_SECRET=your-jwt-secret-here

   # Default admin user
   ADMIN_EMAIL=admin@agritheory.com
   ADMIN_PASSWORD=password123

   # OAuth providers (optional)
   FRAPPE_BASE_URL=https://your-frappe-site.com
   FRAPPE_CLIENT_ID=your-client-id
   FRAPPE_CLIENT_SECRET=your-client-secret

   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret

   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   ```

3. **Start the services**:
   ```bash
   # For development with local builds Using pre-built images from
   # GitHub Container Registry
   docker compose up -d
   ```

4. **Access the application**:
   - Auth server: http://localhost:5000
   - Login page: http://localhost:8000/auth/login
   - Protected applications through Caddy:
     - Protected App 1: http://localhost:8000/app1/
     - Protected App 2: http://localhost:8000/app2/
     - Admin: http://localhost:8000/admin/
   - Assets: http://localhost:8000/static/

### Using Docker Run with GHCR

```bash
# Pull and run the latest image from GHCR
docker run -p 80:80 -p 443:443 \
  -e DATABASE_URL="postgresql://user:pass@host:5432/catkin_auth" \
  -e JWT_SECRET="your-secure-secret" \
  ghcr.io/agritheory/catkin:latest
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/catkin_auth` |
| `JWT_SECRET` | Secret key for JWT token signing | `your-secret-key-change-in-production` |
| `FERNET_KEY` | Key for encrypting passwords/secrets | Required for encryption |
| `DEFAULT_REDIRECT` | Default redirect after login | `/` |
| `ADMIN_EMAIL` | Default admin user email | `admin@agritheory.com` |
| `ADMIN_PASSWORD` | Default admin user password | `password123` |

### OAuth Provider Configuration

OAuth providers are automatically configured if their client credentials are provided via environment variables. Supported providers:

- **Frappe**: `FRAPPE_BASE_URL`, `FRAPPE_CLIENT_ID`, `FRAPPE_CLIENT_SECRET`
- **Google**: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- **GitHub**: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`

## API Endpoints

### Authentication
- `GET /auth/login` - Login page
- `POST /auth/login` - Handle login form submission
- `GET /auth/verify` - Forward auth verification endpoint
- `GET /auth/oauth/<provider>` - Initiate OAuth flow
- `GET /auth/oauth/<provider>/callback` - OAuth callback handler

### Response Headers (for forward auth)
- `X-User-Email` - Authenticated user's email
- `X-User-ID` - User's database ID
- `X-Auth-Method` - Authentication method used

## Caddy Integration

This project includes a Caddy JWT-authentication system that demonstrates how to secure normally unsecured services using the catkin authentication service. The integration provides:

- **Single Sign-On**: One login protects multiple services
- **JWT Forward Auth**: Automatic authentication for all proxied services
- **User Context**: Backend services receive user information via headers
- **Production Ready**: HTTPS, security headers, and auto-certificate management
- **Zero Code Changes**: Protect existing applications without modification
- **Working Demo Apps**: Two fully functional protected applications

### Quick Access

```bash
# Access the system (already running and configured)
open http://localhost:8000/           # Redirects to login
open http://localhost:8000/app1/      # Protected application 1
open http://localhost:8000/app2/      # Protected application 2
open http://localhost:8000/health     # Health check (no auth)
```

### Production Setup

Configure Caddy to use catkin for forward authentication:

```caddyfile
your-app.com {
    forward_auth localhost:5000 {
        uri /auth/verify
        copy_headers X-User-Email X-User-ID
    }

    reverse_proxy localhost:8080  # Your protected application
}
```

## Security Notes

- Always use HTTPS in production
- Generate secure `FERNET_KEY` and `JWT_SECRET` values
- Regularly rotate encryption keys
- Set secure cookie flags in production
- Use strong passwords for the admin account

## Docker Images

### GitHub Container Registry

Pre-built images are available at:
- `ghcr.io/agritheory/catkin:latest` - Latest stable version
- `ghcr.io/agritheory/catkin:main` - Latest development version
- `ghcr.io/agritheory/catkin:v1.0.0` - Tagged releases

### Authentication

To pull private images from GHCR:

```bash
# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Or using GitHub CLI
gh auth token | docker login ghcr.io -u USERNAME --password-stdin
```

### Available Tags

- `latest` - Latest stable release
- `main` - Latest commit on main branch
- `v*.*.*` - Semantic version tags
- `pr-*` - Pull request builds

## License

MIT License - see LICENSE file for details.

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

## Quick Start

### Using Docker Compose

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
   docker compose up -d
   ```

4. **Access the application**:
   - Auth server: http://localhost:5000
   - Login page: http://localhost:5000/auth/login

### Manual Installation

1. **Install dependencies**:
   ```bash
   pip install poetry
   poetry install
   ```

2. **Setup database**:
   ```bash
   # Start PostgreSQL and create database 'catkin_auth'
   poetry run python -c "from catkin.src.database import initialize_db; import asyncio; asyncio.run(initialize_db())"
   ```

3. **Run the server**:
   ```bash
   poetry run serve  # Development with reload
   # or
   poetry run start  # Production
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

## Usage with Caddy

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

## Development

### Project Structure
```
catkin/
├── src/
│   ├── app.py              # Main application
│   ├── database.py         # Database operations
│   └── oauth_provider.py   # OAuth provider management
├── templates/
│   └── login.html          # Login page template
├── static/                 # Static assets
├── docker-compose.yml      # Docker composition
├── Dockerfile             # Container definition
└── pyproject.toml         # Python project config
```

### Available Commands
```bash
poetry run serve    # Development server with reload
poetry run start    # Production server
```

## Security Notes

- Always use HTTPS in production
- Generate secure `FERNET_KEY` and `JWT_SECRET` values
- Regularly rotate encryption keys
- Set secure cookie flags in production
- Use strong passwords for the admin account

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

### Caddy System Structure

```
caddy/                               ✅ FULLY ORGANIZED
├── configs/                        # Production-ready configurations
├── docs/                          # Complete documentation + architecture diagrams
├── scripts/                       # Docker compose and comprehensive tests
├── demo-apps/                     # Working example applications
└── IMPLEMENTATION_COMPLETE.md     # Full completion summary
```

**📚 Complete Documentation**: [`caddy/docs/SETUP.md`](./caddy/docs/SETUP.md)
**🏗️ Architecture Diagrams**: [`caddy/docs/ARCHITECTURE.md`](./caddy/docs/ARCHITECTURE.md)

## License

MIT License - see LICENSE file for details.

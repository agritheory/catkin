# Caddy JWT Authentication Setup Documentation

## Status

This document explains how to configure Caddy to secure normally unsecured services using JWT tokens from the catkin authentication service.

## Overview

The configuration uses Caddy's `forward_auth` directive to authenticate requests by forwarding them to catkin's `/auth/verify` endpoint. If authentication succeeds, the request is proxied to the target service with user information headers.

## Key Components

### 1. Authentication Endpoint
- **URL**: `/auth/verify`
- **Method**: GET
- **Purpose**: Validates JWT tokens from cookies
- **Returns**:
  - 200 OK with user headers if valid
  - 401 Unauthorized if invalid/missing token

### 2. JWT Token Flow
1. User logs in via `/auth/login`
2. Catkin issues JWT token as HTTP-only cookie
3. Subsequent requests include the cookie
4. Caddy forwards to `/auth/verify` for validation
5. If valid, request proceeds to target service

## Configuration Examples

### Development Configuration (localhost with direct ports)

```caddyfile
# Development setup - services accessible on localhost ports
http://localhost:8000 {
    # Authentication service
    handle /auth/* {
        reverse_proxy localhost:5000
    }

    # Protected service 1 (development port)
    handle /app1/* {
        forward_auth localhost:5000 {
            uri /auth/verify
            copy_headers X-User-Email X-User-ID X-Auth-Method
        }
        uri strip_prefix /app1
        reverse_proxy localhost:8080  # Direct port access
    }

    # Protected service 2 (development port)
    handle /app2/* {
        forward_auth localhost:5000 {
            uri /auth/verify
            copy_headers X-User-Email X-User-ID X-Auth-Method
        }
        uri strip_prefix /app2
        reverse_proxy localhost:9000  # Direct port access
    }
}
```

### Production Configuration (Docker containers)

```caddyfile
# Production setup - services only accessible through Caddy
your-domain.com {
    # Authentication service (container name)
    handle /auth/* {
        reverse_proxy auth:5000
    }

    # Protected service 1 (container internal port)
    handle /app1/* {
        forward_auth auth:5000 {
            uri /auth/verify
            copy_headers X-User-Email X-User-ID X-Auth-Method
        }
        uri strip_prefix /app1
        reverse_proxy app1:80  # Container internal port
    }

    # Protected service 2 (container internal port)
    handle /app2/* {
        forward_auth auth:5000 {
            uri /auth/verify
            copy_headers X-User-Email X-User-ID X-Auth-Method
        }
        uri strip_prefix /app2
        reverse_proxy app2:80  # Container internal port
    }
}
```

### Subdomain-Based Protection

```caddyfile
auth.your-domain.com {
    reverse_proxy localhost:5000
}

app.your-domain.com {
    forward_auth auth.your-domain.com {
        uri /auth/verify
        copy_headers X-User-Email X-User-ID X-Auth-Method
    }
    reverse_proxy localhost:8080
}
```

## Headers Passed to Backend Services

When authentication succeeds, these headers are forwarded:

- `X-User-Email`: User's email/username
- `X-User-ID`: Numeric user ID
- `X-Auth-Method`: Always "jwt"

## Error Handling

Authentication failures (401 responses) are automatically redirected to the login page:

```caddyfile
handle_errors {
    @auth_required expression {http.error.status_code} == 401
    redir @auth_required /auth/login?redirect={uri}
}
```

## Environment Variables

Ensure these are set in your catkin application:

```bash
JWT_SECRET=your-secret-key-change-in-production
FERNET_KEY=your-fernet-key-for-encryption
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/catkin_auth
DEFAULT_REDIRECT=/
```

## Security Considerations

1. **HTTPS**: Use HTTPS in production and set `secure=True` for cookies
2. **JWT Secret**: Use a strong, unique JWT secret
3. **Token Expiry**: Tokens expire after 24 hours by default
4. **Cookie Security**: Cookies are HTTP-only and SameSite=Lax

## Testing the Setup

### Development Environment (Current Setup)

In development, protected services are exposed on specific ports for testing:

1. Start your services:
   ```bash
   # Start catkin auth service (port 5000)
   docker-compose up -d

   # Protected services are already running on:
   # - App 1: http://localhost:8080
   # - App 2: http://localhost:9000

   # Start Caddy with development configuration
   cd caddy/configs
   caddy run --config Caddyfile
   ```

2. Test authentication flow:
   ```bash
   # Test health endpoint (no auth required)
   curl -i http://localhost:8000/health

   # Test protected app (should return 401)
   curl -i http://localhost:8000/app1/

   # Test login page accessibility
   curl -i http://localhost:8000/auth/login

   # Access via browser for full authentication flow
   open http://localhost:8000/app1/
   ```

### Production Environment (Docker Compose)

In production, services are only accessible through Caddy:

1. Deploy with Docker Compose:
   ```bash
   cd caddy/scripts
   docker-compose -f docker-compose.caddy.yml up -d
   ```

2. Services configuration:
   - **Auth service**: `auth:5000` (internal)
   - **Protected App 1**: `app1:80` (internal only)
   - **Protected App 2**: `app2:80` (internal only)
   - **Caddy Gateway**: `localhost:80` and `localhost:443` (external)

### Port Reference Guide

| Service | Development | Production (Docker) | Purpose |
|---------|-------------|-------------------|---------|
| Caddy Gateway | :8000, :8001 | :80, :443 | Main entry point |
| Auth Service | :5000 | auth:5000 | Authentication |
| Protected App 1 | :8080 | app1:80 | Demo application |
| Protected App 2 | :9000 | app2:80 | Admin panel |
| Database | :5434 | db:5432 | PostgreSQL |

## Advanced Configuration

### Custom Authentication Logic

You can customize the verification endpoint in catkin to add additional checks:

```python
@app.route("/auth/verify", methods=["GET"])
async def verify() -> ResponseTypes:
    token = request.cookies.get("auth_token")

    if token:
        payload = verify_jwt_token(token)
        if payload:
            # Add custom authorization logic here
            # e.g., check user roles, permissions, etc.

            response = await make_response("", 200)
            response.headers["X-User-Email"] = payload["username"]
            response.headers["X-User-ID"] = str(payload["user_id"])
            response.headers["X-Auth-Method"] = "jwt"
            # Add custom headers
            response.headers["X-User-Role"] = "admin"  # example
            return response

    return await make_response("", 401)
```

### Multiple Authentication Methods

You can extend the system to support API keys alongside JWT:

```python
@app.route("/auth/verify", methods=["GET"])
async def verify() -> ResponseTypes:
    # Check JWT token first
    token = request.cookies.get("auth_token")
    if token:
        payload = verify_jwt_token(token)
        if payload:
            return create_auth_response(payload, "jwt")

    # Check API key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        user = await verify_api_key(api_key)
        if user:
            return create_auth_response(user, "api_key")

    return await make_response("", 401)
```

## Troubleshooting

### Common Issues

1. **401 Errors**: Check that JWT_SECRET matches between services
2. **Cookie Issues**: Ensure domain and path settings are correct
3. **CORS Problems**: Add appropriate CORS headers if needed
4. **Network Issues**: Verify service connectivity between Caddy and catkin

### Debug Logging

Enable debug logging in Caddy:

```caddyfile
{
    debug
}

your-domain.com {
    log {
        output file /var/log/caddy/debug.log
        level DEBUG
    }
    # ... rest of configuration
}
```

### Health Checks

Add health check endpoints to verify service status:

```python
@app.route("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

## Integration with Different Services

The configuration can protect various types of services:

- **Web Applications**: React, Vue, Angular apps
- **APIs**: REST APIs, GraphQL endpoints
- **Dashboards**: Grafana, Kibana, custom dashboards
- **Admin Panels**: Database admin tools, monitoring interfaces
- **File Servers**: Static file serving with authentication

Simply change the `reverse_proxy` target to point to your service.

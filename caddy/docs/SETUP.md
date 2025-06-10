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

### Complete Development Configuration Example

```caddyfile
# Development configuration for localhost (non-privileged ports)
:80 {
	# Static files for auth service (CSS, images, etc.)
	handle /static/* {
		reverse_proxy auth:5000
	}

	# Authentication service - catkin app (all other auth routes)
	handle /auth/* {
		reverse_proxy auth:5000
	}

	# Example protected apps with new path structure
	handle /app/* {
		# Forward authentication to catkin's verify endpoint
		forward_auth auth:5000 {
			uri /auth/verify
			copy_headers X-User-Email X-User-ID X-Auth-Method
		}

		# Strip the /app prefix before forwarding to the app
		uri strip_prefix /app

		# If authentication succeeds, proxy to app
		reverse_proxy app:80 {
			header_up Host {upstream_hostport}
			header_up X-Real-IP {remote_host}
		}
	}

	# Public content (no authentication required)
	handle /public/* {
		reverse_proxy app:80
	}

	# Root path - redirect to login page
	handle_path / {
		redir /auth/login 302
	}

	# Catch-all for other paths - redirect to login
	handle {
		redir /auth/login?redirect={uri} 302
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
   docker compose up -d

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
   docker compose up -d
   ```

2. Services configuration:
   - **Auth service**: `auth:5000` (internal)
   - **Protected App 1**: `app1:80` (internal only)
   - **Protected App 2**: `app2:80` (internal only)
   - **Caddy Gateway**: `localhost:80` and `localhost:443` (external)

## Docker Volume Configuration

The Docker setup includes persistent volumes for both the PostgreSQL database and Caddy's data:

```yaml
volumes:
  postgres_data:  # Database persistence
  caddy-data:     # Caddy certificates and cache persistence
  caddy-config:   # Caddy runtime configuration persistence
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

## Integration with Different Services

The configuration can protect various types of services:

- **Web Applications**: React, Vue, Angular apps
- **APIs**: REST APIs, GraphQL endpoints
- **Dashboards**: Grafana, Kibana, custom dashboards
- **Admin Panels**: Database admin tools, monitoring interfaces
- **File Servers**: Static file serving with authentication

Simply change the `reverse_proxy` target to point to your service.

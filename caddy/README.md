# Caddy JWT Authentication System

This folder contains all files related to the Caddy JWT authentication system that secures normally unsecured services using JWT tokens from the catkin authentication service.

## Key Features

- **Single Sign-On**: One login protects multiple services
- **JWT Authentication**: Secure token-based authentication with HTTP-only cookies
- **Zero Configuration**: Protect existing applications without code changes
- **Development & Production Ready**: Separate configurations for different environments

## Folder Structure

```
caddy/
├── README.md                   # This file - overview of the Caddy system
├── configs/                    # Caddy configuration files
│   ├── Caddyfile               # Development configuration (HTTP, ports 8000)
│   └── Caddyfile.production    # Production configuration (HTTPS, security headers)
├── docs/                       # Documentation and architecture
│   ├── ARCHITECTURE.md         # System architecture and flow diagrams
│   ├── QUICKSTART.md          # Quick start guide for Caddy setup
│   ├── SETUP.md                # Complete setup and configuration guide
│   └── TESTING.md                 # Guide to testing the JWT authentication system
└── demo-apps/                  # Example protected applications
    ├── example-app1/           # Demo web application
    └── example-app2/           # Demo admin panel
```

## Port Configuration Reference

### Development Environment
| Service | Port | Access | Purpose |
|---------|------|--------|---------|
| Caddy Gateway | 8000 | External | Main entry point |
| Auth Service | 5000 | External (direct) | catkin authentication |
| Database | 5434 | External | PostgreSQL |
| Protected Apps | Internal | Via Caddy | Demo applications |

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

- **Development**: Uses HTTP on ports 8000 for easy local testing
- **Production**: HTTPS with Let's Encrypt certificates and security headers
- **Authentication**: Forward auth to catkin service on port 5000
- **Protected Services**: Any service can be protected by adding `forward_auth` directive

## Documentation

- **[`ARCHITECTURE`](./docs/ARCHITECTURE.md)**: System architecture and diagrams
- **[`QUICKSTART`](./docs/QUICKSTART.md)**: Quick-start guide for the Caddy setup
- **[`SETUP`](./docs/SETUP.md)**: Detailed guide for the Caddy setup
- **[`TESTING`](./docs/TESTING.md)**: Guide to testing the JWT authentication system after setup

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

## Next Steps

1. **Customize Services**: Replace example apps with your actual services
2. **Add HTTPS**: Configure SSL certificates for production
3. **Role-Based Access**: Extend auth verification for role checks
4. **Monitoring**: Add health checks and monitoring
5. **Scaling**: Configure load balancing for multiple instances

## Production Checklist

- [ ] Use HTTPS with valid certificates
- [ ] Set strong JWT_SECRET and FERNET_KEY
- [ ] Configure security headers
- [ ] Set up proper logging and monitoring
- [ ] Test failover scenarios
- [ ] Configure backup authentication methods
- [ ] Set appropriate cookie security flags
- [ ] Implement rate limiting
- [ ] Configure CORS policies for APIs
- [ ] Set up log rotation

## Support

For issues or questions:
1. Check the detailed documentation in [`SETUP.md`](./docs/SETUP.md)
2. Review Caddy documentation: https://caddyserver.com/docs/
3. Check catkin auth service logs

# Quick Start Guide: Caddy JWT Authentication

This guide will get you up and running with Caddy protecting services using JWT tokens from catkin.

## Prerequisites

- Docker and Docker Compose installed
- Caddy 2.x installed
- Your catkin authentication service running

## Step 1: Start the Authentication Service

```bash
# Start catkin auth service and database
docker compose up -d

# Wait for services to be healthy
docker compose ps
```

## Step 2: Create Test User (Optional)

```bash
# Connect to your database and create a test user
# Replace with your actual database connection method

# Example SQL to create test user:
# INSERT INTO "user" (username, password_hash, disabled, owner, modified_by)
# VALUES ('test@example.com', 'encrypted_password', false, 'admin', 'system');
```

## Step 3: Start Caddy with JWT Configuration

```bash
# Using the basic development Caddyfile
caddy run --config caddy/configs/Caddyfile

# Or for production:
# caddy run --config caddy/configs/Caddyfile.production
```

## Step 4: Start Your Protected Services

```bash
# Example: Start a simple nginx server for testing
docker run -d --name protected-app1 -p 8080:80 -v $(pwd)/caddy/demo-apps/example-app1:/usr/share/nginx/html:ro nginx:alpine

# Start another protected service
docker run -d --name protected-app2 -p 9000:80 -v $(pwd)/caddy/demo-apps/example-app2:/usr/share/nginx/html:ro nginx:alpine
```

## Step 5: Test the Setup

```bash
# Run the automated test script
./test-caddy-auth.sh

# Or test manually:
# 1. Open browser to http://localhost:8000/secure-app/
# 2. Should redirect to http://localhost:8000/auth/login
# 3. Login with your credentials or OAuth
# 4. Should be redirected back to protected resource

# Alternative test URLs:
# - http://localhost:8001/app/ (different Caddy instance)
# - http://localhost:8000/admin/ (admin-specific path)
```

## Directory Structure After Setup

```
catkin/
├── caddy/                      # Caddy JWT authentication system
│   ├── README.md               # Caddy system overview
│   ├── configs/                # Caddy configuration files
│   │   ├── Caddyfile           # Basic development configuration
│   │   └── Caddyfile.production # Production-ready configuration
│   ├── docs/                   # Documentation
│   │   ├── SETUP.md  # Detailed setup guide
│   │   └── ARCHITECTURE.md # System architecture
│   ├── scripts/                # Deployment and testing
│   │   └── test-caddy-auth.sh  # Automated test script
│   └── demo-apps/              # Example protected services
│       ├── example-app1/       # Demo web application
│       └── example-app2/       # Demo admin panel
└── catkin/                     # Your existing auth service
    ├── src/
    ├── static/
    └── templates/
```

## Configuration Highlights

### Key Caddy Directives

```caddyfile
# Protected service configuration
handle /secure-app/* {
    forward_auth localhost:5000 {
        uri /auth/verify
        copy_headers X-User-Email X-User-ID X-Auth-Method
    }
    reverse_proxy localhost:8080
}
```

### Key Headers Passed to Services

- `X-User-Email`: User's email/username
- `X-User-ID`: Numeric user ID
- `X-Auth-Method`: Authentication method ("jwt")

## Troubleshooting

### Common Issues

1. **401 Errors**: Check JWT_SECRET consistency
2. **Connection Refused**: Verify all services are running
3. **Redirect Loops**: Check cookie domain/path settings

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
1. Check the detailed documentation in `SETUP.md`
2. Run the test script: `./test-caddy-auth.sh`
3. Review Caddy documentation: https://caddyserver.com/docs/
4. Check catkin auth service logs

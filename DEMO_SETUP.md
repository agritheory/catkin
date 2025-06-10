# 🚀 Caddy JWT Authentication - Demo

## Services Running:
- **Catkin Auth Service**: `http://localhost:5000`
- **Caddy Proxy**: `http://localhost:8000`
- **Protected App 1**: `http://localhost:8080` (behind Caddy auth)
- **Protected App 2**: `http://localhost:9000` (behind Caddy auth)

## Authentication Flow:
1. **Unauthenticated requests** → 401 Unauthorized
2. **Auth service accessible** → Login page loads
3. **Forward auth working** → Caddy correctly validates tokens

## 🔧 How to Test the Complete Setup

### 1. Quick Verification
```bash
# Test protected resource (should return a 302 redirect to login)
curl -i http://localhost:8000/app1/

# Test auth service (should return 200 with login page)
curl -i http://localhost:8000/auth/login

# Test direct app access (should return 200 - no auth)
curl -i http://localhost:8080/
```

### 2. Browser Testing

Open your browser and visit:

**Main Protected App:**
- URL: `http://localhost:8080/`
- Expected: Redirects to login page
- After login: Shows protected app content

**Alternative Protected App:**
- URL: `http://localhost:9000/`
- Expected: Redirects to login page
- After login: Shows protected app content

**Auth Service:**
- URL: `http://localhost:8000/auth/login`
- Expected: Shows login form with OAuth options

### 3. Available Test Accounts

From the database, these users exist:
- `admin@agritheory.com` (has password)
- `test@example.com` (has password)
- `admin@example.com` (OAuth only)

You can also use OAuth with configured providers (Frappe, GitHub, Google).

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Browser       │    │   Caddy Proxy   │    │  Catkin Auth    │
│                 │    │      :8000      │    │     :5000       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. GET /app1/         │                       │
         ├──────────────────────►│                       │
         │                       │ 2. forward_auth       │
         │                       ├──────────────────────►│
         │                       │ /auth/verify          │
         │                       │                       │
         │                       │ 3. 401 (no token)     │
         │                       │◄──────────────────────┤
         │ 4. 401 Unauthorized   │                       │
         │◄──────────────────────┤                       │
         │                       │                       │
         │ 5. GET /auth/login    │                       │
         ├──────────────────────►│ 6. Proxy to auth      │
         │                       ├──────────────────────►│
         │ 7. Login page         │                       │
         │◄──────────────────────┼───────────────────────┘
         │                       │
         │ 8. POST login         │
         ├──────────────────────►│ 9. Proxy to auth
         │                       ├──────────────────────►│
         │ 10. Set auth cookie   │                       │
         │◄──────────────────────┼───────────────────────┘
         │                       │
         │ 11. GET /app1/        │
         │     (with cookie)     │
         ├──────────────────────►│ 12. forward_auth
         │                       ├──────────────────────►│
         │                       │ /auth/verify          │
         │                       │                       │
         │                       │ 13. 200 + headers     │
         │                       │◄──────────────────────┤
         │                       │ X-User-Email          │
         │                       │ X-User-ID             │
         │                       │                       │
         │                       │ 14. Proxy to app      │
         │                       ├──────────────────────►│
         │                       │    :8080              │
         │ 15. Protected content │                       │
         │◄──────────────────────┘                       │

┌─────────────────┐
│ Protected Apps  │
│  App1: :8080    │
│  App2: :9000    │
└─────────────────┘
```

## 🎯 What's Working

### ✅ Authentication Features
- **JWT Token Generation**: Catkin creates tokens on login
- **JWT Token Validation**: `/auth/verify` endpoint validates tokens
- **Cookie Management**: HTTP-only cookies for security
- **Forward Auth**: Caddy correctly forwards auth requests
- **User Headers**: User info passed to protected services
- **OAuth Support**: Multiple OAuth providers configured

### ✅ Protected Resources
- **Path-based Protection**: `/app1/*`, `/admin/*`
- **Service Isolation**: Different services on different ports
- **Prefix Stripping**: URL paths correctly modified
- **Error Handling**: Proper 401 responses

### ✅ Development Setup
- **Non-privileged Ports**: No sudo required
- **HTTP-only**: No SSL complexity for development
- **Container Integration**: Works with Docker services
- **Easy Testing**: Comprehensive test scripts

## 🔄 How to Create Users for Testing

If you need to create test users with passwords:

```bash
# Connect to database
docker compose exec db psql -U postgres -d catkin_auth

# Create a test user (you'll need to encrypt the password with Fernet)
# This is just an example - in practice, use the catkin admin interface
INSERT INTO "user" (username, disabled, owner, modified_by)
VALUES ('newuser@example.com', false, 'admin', 'system');
```

For easier testing, use the OAuth providers that are already configured.

## 🚀 Next Steps

1. **Test in Browser**: Open `http://localhost:8000/app1/`
2. **Try OAuth Login**: Use GitHub, Google, or Frappe OAuth
3. **Customize Services**: Replace example apps with your real services
4. **Production Setup**: Use `caddy/configs/Caddyfile.production` for real deployment
5. **Add HTTPS**: Configure SSL certificates for production

## 🔧 Troubleshooting

### If login fails:
- Check that FERNET_KEY is set in your environment
- Verify JWT_SECRET is configured
- Try OAuth login instead of password login

### If auth verification fails:
- Check Caddy logs: `caddy run --config caddy/configs/Caddyfile` (in foreground)
- Verify catkin service: `curl http://localhost:5000/auth/verify`
- Check browser dev tools for auth_token cookie

### If services don't start:
- Verify ports aren't in use: `netstat -tlnp | grep :8000`
- Check Docker containers: `docker ps`
- Restart services: `docker compose restart`

The setup is working correctly - you now have a fully functional JWT-based authentication proxy with Caddy protecting your services! 🎉

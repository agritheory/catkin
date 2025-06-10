# 🚀 Caddy JWT Authentication - Demo

## Services Running:
- **Catkin Auth Service**: `http://localhost:5000`
- **Caddy Proxy**: `http://localhost:8000`
- **Protected App 1**: `http://localhost:8000/app1/` (behind Caddy auth)
- **Protected App 2**: `http://localhost:8000/app2/` (behind Caddy auth)
- **Admin Interface**: `http://localhost:8000/admin/` (behind Caddy auth)
- **Assets Content**: `http://localhost:8000/static/*` (no auth required)

## 🔧 How to Test the Complete Setup

### 1. Quick Verification
```bash
# Test protected resource (should return a 302 redirect to login)
curl -i http://localhost:8000/app1/

# Test admin interface (should return a 302 redirect to login)
curl -i http://localhost:8000/admin/

# Test static content (should return 200 with content - no auth)
curl -i http://localhost:8000/static/

# Test auth service (should return 200 with login page)
curl -i http://localhost:8000/auth/login

# Test direct auth service access (should return 200 with login page)
curl -i http://localhost:5000/auth/login

# Test health check endpoint (should return 200 OK)
curl -i http://localhost:8000/health
```

### 2. Browser Testing

Open your browser and visit:

**Main Protected App:**
- URL: `http://localhost:8000/app1/`
- Expected: Redirects to login page
- After login: Shows protected app content

**Alternative Protected App:**
- URL: `http://localhost:8000/app2/`
- Expected: Redirects to login page
- After login: Shows protected app content

**Admin Interface:**
- URL: `http://localhost:8000/admin/`
- Expected: Redirects to login page
- After login: Shows protected admin content

**Asset Content:**
- URL: `http://localhost:8000/static/`
- Expected: Shows assets without login

**Auth Service:**
- URL: `http://localhost:8000/auth/login`
- Expected: Shows login form with OAuth options

### 3. Available Test Accounts

- From the database, the following user exists with a default password: `admin@agritheory.com`
- You can also use OAuth with configured providers (Frappe, GitHub, Google).

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

## 🔧 Troubleshooting

### If login fails:
- Check that FERNET_KEY is set in your environment
- Verify JWT_SECRET is configured
- Try OAuth login instead of password login

### If auth verification fails:
- Check Caddy logs: `docker compose logs caddy`
- Verify catkin service: `curl http://localhost:5000/auth/verify`
- Check browser dev tools for `auth_token` cookie

### If services don't start:
- Verify ports aren't in use: `netstat -tlnp | grep :8000`
- Check Docker containers: `docker ps`
- Restart services: `docker compose restart`

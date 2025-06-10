# Quick Start Guide

This guide will get you up and running with Caddy protecting services using JWT tokens from catkin.

## Prerequisites

- Docker and Docker Compose installed
- Git for cloning the repository

## Step 1: Clone and Configure the Repository

```bash
# Clone the repository
git clone https://github.com/agritheory/catkin.git
cd catkin

# Create and configure .env file
touch .env
# Add required environment variables to .env:
# FERNET_KEY=your-fernet-key-here
# JWT_SECRET=your-jwt-secret-here
# ADMIN_EMAIL=admin@example.com
# ADMIN_PASSWORD=your-password-here
```

## Step 2: Start All Services

```bash
# Start all services (auth, apps, caddy, database)
docker compose up -d

# Check service status
docker compose ps
```

## Step 3: Access Services

Open your browser and visit:

- Auth login page: http://localhost:8000/auth/login
- Protected app 1: http://localhost:8000/app1/
- Protected app 2: http://localhost:8000/app2/
- Health check: http://localhost:8000/health

## Step 4: Login with User

1. Visit http://localhost:8000/auth/login
2. Enter credentials:
   - Email: `admin@agritheory.com` (or your configured `ADMIN_EMAIL`)
   - Password: `password123` (or your configured `ADMIN_PASSWORD`)
3. After login, you'll be able to access protected services

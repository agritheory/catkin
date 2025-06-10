#!/bin/bash

# Test script for Caddy JWT authentication setup
# This script tests various scenarios to ensure the authentication is working correctly

set -e

# Configuration
AUTH_URL="http://localhost:5000"
PROXY_URL="http://localhost:8000"  # Caddy proxy
TEST_USER="admin@agritheory.com"
TEST_PASSWORD="password123"

echo "🧪 Testing Caddy JWT Authentication Setup"
echo "=========================================="

# Function to make HTTP requests and capture cookies
make_request() {
    local url="$1"
    local method="${2:-GET}"
    local data="${3:-}"
    local cookie_jar="${4:-/tmp/test_cookies.txt}"

    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        curl -s -i -X "$method" -d "$data" -c "$cookie_jar" -b "$cookie_jar" "$url"
    else
        curl -s -i -c "$cookie_jar" -b "$cookie_jar" "$url"
    fi
}

# Test 1: Access protected resource without authentication
echo "🔒 Test 1: Accessing protected resource without auth (should redirect to login)"
response=$(curl -s -i "$PROXY_URL/secure-app/")
if echo "$response" | grep -q "302\|401\|/auth/login"; then
    echo "✅ PASS: Correctly redirected/blocked unauthenticated request"
else
    echo "❌ FAIL: Should have redirected to login"
    echo "$response"
fi
echo

# Test 2: Direct access to auth service
echo "🔑 Test 2: Direct access to auth service"
response=$(curl -s -i "$AUTH_URL/auth/login")
if echo "$response" | grep -q "200 OK"; then
    echo "✅ PASS: Auth service is accessible"
else
    echo "❌ FAIL: Auth service not accessible"
    echo "$response"
fi
echo

# Test 3: Authentication verification endpoint
echo "🔍 Test 3: Auth verification endpoint without token"
response=$(curl -s -i "$AUTH_URL/auth/verify")
if echo "$response" | grep -q "401"; then
    echo "✅ PASS: Verification correctly returns 401 without token"
else
    echo "❌ FAIL: Should return 401 without token"
    echo "$response"
fi
echo

# Test 4: Login process (requires test user to exist)
echo "👤 Test 4: Login process"
cookie_jar="/tmp/test_cookies.txt"
rm -f "$cookie_jar"

# First get the login page to establish session
make_request "$AUTH_URL/auth/login" "GET" "" "$cookie_jar" > /dev/null

# Attempt login
login_data="username=$TEST_USER&password=$TEST_PASSWORD&redirect=/secure-app/"
login_response=$(make_request "$AUTH_URL/auth/login" "POST" "$login_data" "$cookie_jar")

if echo "$login_response" | grep -q "302\|Set-Cookie.*auth_token"; then
    echo "✅ PASS: Login appears successful (got redirect or auth cookie)"

    # Test 5: Access protected resource with valid token
    echo "🔓 Test 5: Accessing protected resource with valid token"
    protected_response=$(make_request "$PROXY_URL/secure-app/" "GET" "" "$cookie_jar")

    if echo "$protected_response" | grep -q "200 OK\|Protected Application"; then
        echo "✅ PASS: Successfully accessed protected resource"
    else
        echo "❌ FAIL: Could not access protected resource with valid token"
        echo "$protected_response"
    fi
else
    echo "⚠️  SKIP: Login failed (test user may not exist)"
    echo "   Create test user with: $TEST_USER / $TEST_PASSWORD"
fi
echo

# Test 6: Verify JWT token validation
echo "🎫 Test 6: JWT token validation"
if [ -f "$cookie_jar" ]; then
    verify_response=$(make_request "$AUTH_URL/auth/verify" "GET" "" "$cookie_jar")

    if echo "$verify_response" | grep -q "200 OK"; then
        echo "✅ PASS: JWT token validation working"

        # Check if expected headers are present
        if echo "$verify_response" | grep -q "X-User-Email\|X-User-ID"; then
            echo "✅ PASS: User headers are being set correctly"
        else
            echo "⚠️  WARNING: User headers may not be set correctly"
        fi
    else
        echo "❌ FAIL: JWT token validation not working"
        echo "$verify_response"
    fi
else
    echo "⚠️  SKIP: No cookie jar available"
fi
echo

# Test 7: Test expired/invalid token
echo "🕐 Test 7: Invalid token handling"
echo "auth_token=invalid.jwt.token" > /tmp/invalid_cookies.txt
invalid_response=$(make_request "$AUTH_URL/auth/verify" "GET" "" "/tmp/invalid_cookies.txt")

if echo "$invalid_response" | grep -q "401"; then
    echo "✅ PASS: Invalid tokens correctly rejected"
else
    echo "❌ FAIL: Invalid tokens should be rejected"
    echo "$invalid_response"
fi
echo

# Test 8: Test Caddy health
echo "🏥 Test 8: Caddy service health"
caddy_response=$(curl -s -i "$PROXY_URL/health" 2>/dev/null || echo "Connection failed")

if echo "$caddy_response" | grep -q "200 OK\|healthy"; then
    echo "✅ PASS: Caddy is healthy"
else
    echo "❌ FAIL: Caddy health check failed"
    echo "$caddy_response"
fi
echo

# Test 9: HTTPS redirect (if applicable)
echo "🔐 Test 9: Security headers check"
security_response=$(curl -s -i "$PROXY_URL/" 2>/dev/null || echo "Connection failed")

if echo "$security_response" | grep -q "X-Frame-Options\|X-Content-Type-Options"; then
    echo "✅ PASS: Security headers are present"
else
    echo "⚠️  INFO: Security headers not detected (may be in production config only)"
fi
echo

# Cleanup
rm -f /tmp/test_cookies.txt /tmp/invalid_cookies.txt

echo "🎯 Test Summary"
echo "==============="
echo "Tests completed. Check for any ❌ FAIL messages above."
echo
echo "💡 Next Steps:"
echo "1. If login tests failed, create a test user in your database"
echo "2. Verify all services are running (catkin auth, caddy, protected services)"
echo "3. Check Caddy and application logs for any errors"
echo "4. Ensure JWT_SECRET is consistent across services"
echo
echo "📝 Manual Tests:"
echo "1. Open browser to: $PROXY_URL/secure-app/"
echo "2. Should redirect to: $AUTH_URL/auth/login"
echo "3. After login, should access protected resource"
echo "4. Check browser dev tools for auth_token cookie"

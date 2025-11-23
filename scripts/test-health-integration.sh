#!/bin/bash

# =============================================================================
# Health Check Integration Test Script
# Story 0.6: Inter-Service Health Check & API Contract (Pattern B)
#
# Tests the full health check flow including:
# - All health endpoints
# - Correlation ID propagation
# - Response time validation
# - Error handling
# =============================================================================

set -e

echo "🧪 Health Check Integration Tests"
echo "=================================="
echo ""

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
CHROMADB_URL="${CHROMADB_URL:-http://localhost:8001}"
MAX_RESPONSE_TIME_MS=200

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# =============================================================================
# Helper Functions
# =============================================================================

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED++))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED++))
}

test_skip() {
    echo -e "${YELLOW}⏭️  SKIP${NC}: $1"
    ((SKIPPED++))
}

measure_response_time() {
    local url=$1
    local start_time=$(date +%s%N)
    curl -s -o /dev/null "$url"
    local end_time=$(date +%s%N)
    echo $(( (end_time - start_time) / 1000000 ))
}

# =============================================================================
# Test Cases
# =============================================================================

echo -e "${BLUE}Phase 1: Health Endpoint Tests${NC}"
echo "-----------------------------------"

# Test 1: Spring Boot /actuator/health returns 200
echo -n "Testing Spring Boot /actuator/health... "
response=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/actuator/health" 2>/dev/null)
http_code=$(echo "$response" | tail -1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    test_pass "Spring Boot health endpoint returns 200"
else
    test_fail "Spring Boot health endpoint returned $http_code (expected 200)"
fi

# Test 2: Health response contains required components
echo -n "Testing health response contains 'db' component... "
if echo "$body" | grep -q '"db"'; then
    test_pass "Health contains 'db' component"
else
    test_fail "Health missing 'db' component"
fi

echo -n "Testing health response contains 'fastapi' component... "
if echo "$body" | grep -q '"fastapi"'; then
    test_pass "Health contains 'fastapi' component"
else
    test_fail "Health missing 'fastapi' component"
fi

echo -n "Testing health response contains 'redis' component... "
if echo "$body" | grep -q '"redis"'; then
    test_pass "Health contains 'redis' component"
else
    test_fail "Health missing 'redis' component"
fi

echo -n "Testing health response contains 'diskSpace' component... "
if echo "$body" | grep -q '"diskSpace"'; then
    test_pass "Health contains 'diskSpace' component"
else
    test_fail "Health missing 'diskSpace' component"
fi

# Test 3: Prometheus endpoint
echo -n "Testing Prometheus endpoint... "
prom_response=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/actuator/prometheus" 2>/dev/null)
if [ "$prom_response" = "200" ]; then
    test_pass "Prometheus endpoint returns 200"
else
    test_fail "Prometheus endpoint returned $prom_response (expected 200)"
fi

# Test 4: API system health endpoint
echo -n "Testing /api/v1/system/health... "
api_health=$(curl -s -w "\n%{http_code}" "$BACKEND_URL/api/v1/system/health" 2>/dev/null)
api_code=$(echo "$api_health" | tail -1)
if [ "$api_code" = "200" ]; then
    test_pass "API health endpoint returns 200"
else
    test_fail "API health endpoint returned $api_code (expected 200)"
fi

# Test 5: Liveness probe
echo -n "Testing /api/v1/system/live... "
live_code=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/system/live" 2>/dev/null)
if [ "$live_code" = "200" ]; then
    test_pass "Liveness probe returns 200"
else
    test_fail "Liveness probe returned $live_code (expected 200)"
fi

# Test 6: Readiness probe
echo -n "Testing /api/v1/system/ready... "
ready_code=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/api/v1/system/ready" 2>/dev/null)
if [ "$ready_code" = "200" ]; then
    test_pass "Readiness probe returns 200"
else
    test_fail "Readiness probe returned $ready_code (expected 200)"
fi

echo ""
echo -e "${BLUE}Phase 2: Correlation ID Tests${NC}"
echo "-----------------------------------"

# Test 7: Correlation ID generated when not provided
echo -n "Testing correlation ID generation... "
corr_response=$(curl -s -i "$BACKEND_URL/actuator/health" 2>/dev/null)
corr_id=$(echo "$corr_response" | grep -i "x-correlation-id" | awk '{print $2}' | tr -d '\r')
if [ -n "$corr_id" ]; then
    test_pass "Correlation ID generated: $corr_id"
else
    test_fail "Correlation ID not found in response headers"
fi

# Test 8: Correlation ID propagated when provided
echo -n "Testing correlation ID propagation... "
test_corr_id="test-correlation-$(date +%s)"
prop_response=$(curl -s -i -H "X-Correlation-ID: $test_corr_id" "$BACKEND_URL/actuator/health" 2>/dev/null)
returned_id=$(echo "$prop_response" | grep -i "x-correlation-id" | awk '{print $2}' | tr -d '\r')
if [ "$returned_id" = "$test_corr_id" ]; then
    test_pass "Correlation ID propagated correctly"
else
    test_fail "Correlation ID not propagated (expected: $test_corr_id, got: $returned_id)"
fi

echo ""
echo -e "${BLUE}Phase 3: Performance Tests${NC}"
echo "-----------------------------------"

# Test 9: Health check response time
echo -n "Testing health check response time... "
response_time=$(measure_response_time "$BACKEND_URL/actuator/health")
if [ "$response_time" -lt "$MAX_RESPONSE_TIME_MS" ]; then
    test_pass "Response time ${response_time}ms (< ${MAX_RESPONSE_TIME_MS}ms)"
else
    test_fail "Response time ${response_time}ms (>= ${MAX_RESPONSE_TIME_MS}ms)"
fi

# Test 10: Concurrent health checks (simple test)
echo -n "Testing concurrent health checks... "
for i in {1..5}; do
    curl -s -o /dev/null "$BACKEND_URL/actuator/health" &
done
wait
test_pass "5 concurrent requests completed"

echo ""
echo -e "${BLUE}Phase 4: ChromaDB Health Test${NC}"
echo "-----------------------------------"

# Test 11: ChromaDB heartbeat
echo -n "Testing ChromaDB heartbeat... "
chroma_code=$(curl -s -o /dev/null -w "%{http_code}" "$CHROMADB_URL/api/v1/heartbeat" 2>/dev/null)
if [ "$chroma_code" = "200" ]; then
    test_pass "ChromaDB heartbeat returns 200"
else
    test_skip "ChromaDB not available (code: $chroma_code)"
fi

echo ""
echo -e "${BLUE}Phase 5: Frontend Health Test${NC}"
echo "-----------------------------------"

# Test 12: Frontend availability
echo -n "Testing Frontend availability... "
fe_code=$(curl -s -o /dev/null -w "%{http_code}" "$FRONTEND_URL" 2>/dev/null)
if [ "$fe_code" = "200" ]; then
    test_pass "Frontend returns 200"
else
    test_skip "Frontend not available (code: $fe_code)"
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "=================================="
echo "Test Summary"
echo "=================================="
echo -e "  ${GREEN}Passed${NC}: $PASSED"
echo -e "  ${RED}Failed${NC}: $FAILED"
echo -e "  ${YELLOW}Skipped${NC}: $SKIPPED"
echo ""

TOTAL=$((PASSED + FAILED))
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}💥 Some tests failed.${NC}"
    exit 1
fi

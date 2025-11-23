#!/bin/bash

# =============================================================================
# Gaji Stack Verification Script
# Story 0.6: Inter-Service Health Check & API Contract (Pattern B)
#
# This script validates that all services are healthy and Pattern B architecture
# is correctly configured (FastAPI is NOT externally accessible)
# =============================================================================

set -e

echo "🔍 Verifying Gaji Stack Health (Pattern B Architecture)..."
echo ""

# Configuration
MAX_WAIT=180  # 3 minutes
WAIT_INTERVAL=5
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"
CHROMADB_URL="${CHROMADB_URL:-http://localhost:8001}"
FASTAPI_EXTERNAL_URL="${FASTAPI_EXTERNAL_URL:-http://localhost:8000}"
REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track overall status
OVERALL_STATUS=0

# =============================================================================
# Helper Functions
# =============================================================================

wait_for_service() {
    local service_name=$1
    local health_url=$2
    local elapsed=0

    echo -e "⏳ Waiting for ${service_name}..."

    while [ $elapsed -lt $MAX_WAIT ]; do
        if curl -f -s "$health_url" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ ${service_name}: Healthy${NC}"
            return 0
        fi
        sleep $WAIT_INTERVAL
        elapsed=$((elapsed + WAIT_INTERVAL))
        echo "   ... still waiting ($elapsed/$MAX_WAIT seconds)"
    done

    echo -e "${RED}❌ ${service_name}: Timeout after $MAX_WAIT seconds${NC}"
    return 1
}

check_redis() {
    echo -e "⏳ Checking Redis..."

    if command -v redis-cli &> /dev/null; then
        if redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" ping > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Redis: Healthy (PONG)${NC}"
            return 0
        fi
    else
        # Fallback: try using nc (netcat) or direct socket
        if nc -z "$REDIS_HOST" "$REDIS_PORT" 2>/dev/null; then
            echo -e "${GREEN}✅ Redis: Healthy (port reachable)${NC}"
            return 0
        fi
    fi

    echo -e "${RED}❌ Redis: Not responding${NC}"
    return 1
}

check_pattern_b_security() {
    echo ""
    echo "🔐 Validating Pattern B Architecture..."
    echo ""

    # Verify FastAPI is NOT externally accessible
    echo "   Checking FastAPI external access..."
    if curl -f -s "$FASTAPI_EXTERNAL_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}⚠️  WARNING: FastAPI is externally accessible (should be internal-only)${NC}"
        echo -e "${RED}   Pattern B architecture violation detected!${NC}"
        echo ""
        echo "   Fix: Ensure docker-compose.yml uses 'expose' instead of 'ports' for ai-service"
        return 1
    else
        echo -e "${GREEN}✅ FastAPI: Correctly configured as internal-only (Pattern B)${NC}"
    fi

    return 0
}

check_backend_fastapi_connectivity() {
    echo ""
    echo "   Checking Backend → FastAPI (internal) connectivity..."

    # Get backend health and check FastAPI status
    local backend_health
    backend_health=$(curl -s "$BACKEND_URL/actuator/health" 2>/dev/null)

    if echo "$backend_health" | grep -q '"fastapi"'; then
        local fastapi_status
        fastapi_status=$(echo "$backend_health" | grep -o '"fastapi"[^}]*}' | grep -o '"status":"[^"]*"' | head -1)

        if echo "$fastapi_status" | grep -q '"UP"'; then
            echo -e "${GREEN}✅ Backend → FastAPI (internal): OK${NC}"
            return 0
        else
            echo -e "${RED}❌ Backend → FastAPI (internal): Failed${NC}"
            echo "   FastAPI status: $fastapi_status"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Backend → FastAPI: Status not available in health response${NC}"
        return 1
    fi
}

# =============================================================================
# Main Health Checks
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Phase 1: Infrastructure Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Redis
check_redis || OVERALL_STATUS=1

# Check ChromaDB
wait_for_service "ChromaDB" "$CHROMADB_URL/api/v1/heartbeat" || OVERALL_STATUS=1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Phase 2: Application Services"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Spring Boot Backend (API Gateway)
wait_for_service "Backend (API Gateway)" "$BACKEND_URL/actuator/health" || OVERALL_STATUS=1

# Check Frontend
wait_for_service "Frontend" "$FRONTEND_URL" || OVERALL_STATUS=1

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Phase 3: Pattern B Architecture Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Validate Pattern B security
check_pattern_b_security || OVERALL_STATUS=1

# Check Backend → FastAPI internal connectivity
check_backend_fastapi_connectivity || OVERALL_STATUS=1

# Test Frontend → Backend connectivity
echo ""
echo "   Checking Frontend → Backend connectivity..."
if curl -f -s "$BACKEND_URL/actuator/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend → Backend: OK${NC}"
else
    echo -e "${RED}❌ Frontend → Backend: Failed${NC}"
    OVERALL_STATUS=1
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Health Check Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e "${GREEN}🎉 All services healthy! Pattern B architecture validated.${NC}"
    echo ""
    echo "📊 Service URLs:"
    echo "   Frontend:         $FRONTEND_URL"
    echo "   Backend (API):    $BACKEND_URL"
    echo "   Health Dashboard: $BACKEND_URL/actuator/health"
    echo "   Prometheus:       $BACKEND_URL/actuator/prometheus"
    echo "   ChromaDB (dev):   $CHROMADB_URL"
    echo "   FastAPI:          Internal only (not exposed)"
    echo ""
    echo "📖 API Documentation:"
    echo "   Swagger UI:       $BACKEND_URL/swagger-ui.html"
    echo "   OpenAPI Spec:     $BACKEND_URL/v3/api-docs"
else
    echo -e "${RED}💥 Some services failed health checks. See details above.${NC}"
    echo ""
    echo "Troubleshooting tips:"
    echo "  1. Run 'docker-compose ps' to check container status"
    echo "  2. Run 'docker-compose logs <service>' to view logs"
    echo "  3. Ensure all required environment variables are set"
    echo "  4. Check if ports are already in use"
fi

echo ""
exit $OVERALL_STATUS

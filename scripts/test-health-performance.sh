#!/bin/bash

# =============================================================================
# Health Check Performance Test Script
# Story 0.6: Inter-Service Health Check & API Contract (Pattern B)
#
# Tests performance requirements:
# - Health check response time < 200ms (P95)
# - Concurrent request handling
# - Load testing with sustained traffic
# =============================================================================

set -e

echo "⚡ Health Check Performance Tests"
echo "=================================="
echo ""

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8080}"
NUM_REQUESTS="${NUM_REQUESTS:-100}"
CONCURRENCY="${CONCURRENCY:-10}"
MAX_RESPONSE_TIME_MS=200
P95_THRESHOLD_MS=200

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Results storage
RESULTS_DIR="/tmp/health-perf-tests"
mkdir -p "$RESULTS_DIR"

# =============================================================================
# Helper Functions
# =============================================================================

check_dependencies() {
    echo -e "${BLUE}Checking dependencies...${NC}"

    # Check for curl
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}curl is required but not installed.${NC}"
        exit 1
    fi

    # Check for bc (calculator)
    if ! command -v bc &> /dev/null; then
        echo -e "${YELLOW}bc not found, using awk for calculations${NC}"
    fi

    echo -e "${GREEN}✅ Dependencies OK${NC}"
    echo ""
}

# Measure single request response time in milliseconds
measure_request() {
    local url=$1
    local start_time=$(python3 -c 'import time; print(int(time.time() * 1000))')
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    local end_time=$(python3 -c 'import time; print(int(time.time() * 1000))')
    local duration=$((end_time - start_time))
    echo "$duration $http_code"
}

# Calculate statistics from a file of numbers
calculate_stats() {
    local file=$1
    local count=$(wc -l < "$file")

    if [ "$count" -eq 0 ]; then
        echo "0 0 0 0"
        return
    fi

    # Sort the file for percentile calculation
    sort -n "$file" > "${file}.sorted"

    # Calculate min, max, avg
    local min=$(head -1 "${file}.sorted")
    local max=$(tail -1 "${file}.sorted")
    local sum=$(awk '{sum+=$1} END {print sum}' "$file")
    local avg=$((sum / count))

    # Calculate P95 (95th percentile)
    local p95_index=$(echo "scale=0; ($count * 95 / 100)" | bc 2>/dev/null || echo $((count * 95 / 100)))
    [ "$p95_index" -lt 1 ] && p95_index=1
    local p95=$(sed -n "${p95_index}p" "${file}.sorted")

    echo "$min $max $avg $p95"
}

# =============================================================================
# Test Cases
# =============================================================================

test_single_endpoint_performance() {
    local endpoint=$1
    local name=$2
    local results_file="${RESULTS_DIR}/${name}_times.txt"

    echo -e "${BLUE}Testing $name ($NUM_REQUESTS requests)...${NC}"
    > "$results_file"

    local success=0
    local failed=0

    for i in $(seq 1 $NUM_REQUESTS); do
        result=$(measure_request "$endpoint")
        time_ms=$(echo "$result" | awk '{print $1}')
        http_code=$(echo "$result" | awk '{print $2}')

        if [ "$http_code" = "200" ]; then
            echo "$time_ms" >> "$results_file"
            ((success++))
        else
            ((failed++))
        fi

        # Progress indicator
        if [ $((i % 20)) -eq 0 ]; then
            echo -n "."
        fi
    done
    echo ""

    # Calculate statistics
    if [ "$success" -gt 0 ]; then
        stats=$(calculate_stats "$results_file")
        min=$(echo "$stats" | awk '{print $1}')
        max=$(echo "$stats" | awk '{print $2}')
        avg=$(echo "$stats" | awk '{print $3}')
        p95=$(echo "$stats" | awk '{print $4}')

        echo "   Requests:  $success successful, $failed failed"
        echo "   Min:       ${min}ms"
        echo "   Max:       ${max}ms"
        echo "   Avg:       ${avg}ms"
        echo "   P95:       ${p95}ms"

        if [ "$p95" -lt "$P95_THRESHOLD_MS" ]; then
            echo -e "   ${GREEN}✅ PASS: P95 (${p95}ms) < ${P95_THRESHOLD_MS}ms${NC}"
            return 0
        else
            echo -e "   ${RED}❌ FAIL: P95 (${p95}ms) >= ${P95_THRESHOLD_MS}ms${NC}"
            return 1
        fi
    else
        echo -e "   ${RED}❌ FAIL: All requests failed${NC}"
        return 1
    fi
}

test_concurrent_load() {
    local endpoint=$1
    local name=$2
    local results_file="${RESULTS_DIR}/${name}_concurrent.txt"

    echo -e "${BLUE}Testing $name with $CONCURRENCY concurrent connections...${NC}"
    > "$results_file"

    # Run concurrent requests
    for i in $(seq 1 $CONCURRENCY); do
        (
            for j in $(seq 1 $((NUM_REQUESTS / CONCURRENCY))); do
                result=$(measure_request "$endpoint")
                time_ms=$(echo "$result" | awk '{print $1}')
                http_code=$(echo "$result" | awk '{print $2}')
                if [ "$http_code" = "200" ]; then
                    echo "$time_ms" >> "$results_file"
                fi
            done
        ) &
    done

    # Wait for all background jobs
    wait

    # Calculate statistics
    local count=$(wc -l < "$results_file")
    if [ "$count" -gt 0 ]; then
        stats=$(calculate_stats "$results_file")
        min=$(echo "$stats" | awk '{print $1}')
        max=$(echo "$stats" | awk '{print $2}')
        avg=$(echo "$stats" | awk '{print $3}')
        p95=$(echo "$stats" | awk '{print $4}')

        echo "   Completed:  $count requests"
        echo "   Min:        ${min}ms"
        echo "   Max:        ${max}ms"
        echo "   Avg:        ${avg}ms"
        echo "   P95:        ${p95}ms"

        # Under load, allow slightly higher threshold (1.5x)
        local load_threshold=$((P95_THRESHOLD_MS * 3 / 2))
        if [ "$p95" -lt "$load_threshold" ]; then
            echo -e "   ${GREEN}✅ PASS: P95 under load (${p95}ms) < ${load_threshold}ms${NC}"
            return 0
        else
            echo -e "   ${RED}❌ FAIL: P95 under load (${p95}ms) >= ${load_threshold}ms${NC}"
            return 1
        fi
    else
        echo -e "   ${RED}❌ FAIL: No successful requests${NC}"
        return 1
    fi
}

test_sustained_traffic() {
    local endpoint=$1
    local duration_seconds=10
    local results_file="${RESULTS_DIR}/sustained_traffic.txt"

    echo -e "${BLUE}Testing sustained traffic for ${duration_seconds} seconds...${NC}"
    > "$results_file"

    local end_time=$(($(date +%s) + duration_seconds))
    local request_count=0
    local error_count=0

    while [ $(date +%s) -lt $end_time ]; do
        result=$(measure_request "$endpoint")
        time_ms=$(echo "$result" | awk '{print $1}')
        http_code=$(echo "$result" | awk '{print $2}')

        if [ "$http_code" = "200" ]; then
            echo "$time_ms" >> "$results_file"
            ((request_count++))
        else
            ((error_count++))
        fi
    done

    local rps=$((request_count / duration_seconds))
    local error_rate=0
    if [ $((request_count + error_count)) -gt 0 ]; then
        error_rate=$((error_count * 100 / (request_count + error_count)))
    fi

    echo "   Duration:     ${duration_seconds}s"
    echo "   Requests:     $request_count"
    echo "   Errors:       $error_count"
    echo "   Rate:         ~${rps} req/s"
    echo "   Error Rate:   ${error_rate}%"

    if [ "$error_rate" -lt 1 ]; then
        echo -e "   ${GREEN}✅ PASS: Error rate < 1%${NC}"
        return 0
    else
        echo -e "   ${RED}❌ FAIL: Error rate >= 1%${NC}"
        return 1
    fi
}

# =============================================================================
# Main Test Execution
# =============================================================================

check_dependencies

echo "Configuration:"
echo "  Backend URL:    $BACKEND_URL"
echo "  Requests:       $NUM_REQUESTS"
echo "  Concurrency:    $CONCURRENCY"
echo "  P95 Threshold:  ${P95_THRESHOLD_MS}ms"
echo ""

# Check if backend is available
echo -e "${BLUE}Checking backend availability...${NC}"
if ! curl -s -f "$BACKEND_URL/actuator/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ Backend not available at $BACKEND_URL${NC}"
    echo "Please start the stack with: docker-compose up -d"
    exit 1
fi
echo -e "${GREEN}✅ Backend is available${NC}"
echo ""

# Track results
PASSED=0
FAILED=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test 1: Actuator Health Endpoint"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if test_single_endpoint_performance "$BACKEND_URL/actuator/health" "actuator_health"; then
    ((PASSED++))
else
    ((FAILED++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test 2: API System Health Endpoint"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if test_single_endpoint_performance "$BACKEND_URL/api/v1/system/health" "api_health"; then
    ((PASSED++))
else
    ((FAILED++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test 3: Liveness Probe"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if test_single_endpoint_performance "$BACKEND_URL/api/v1/system/live" "liveness"; then
    ((PASSED++))
else
    ((FAILED++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test 4: Concurrent Load Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if test_concurrent_load "$BACKEND_URL/actuator/health" "concurrent_health"; then
    ((PASSED++))
else
    ((FAILED++))
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Test 5: Sustained Traffic Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if test_sustained_traffic "$BACKEND_URL/actuator/health"; then
    ((PASSED++))
else
    ((FAILED++))
fi
echo ""

# =============================================================================
# Summary
# =============================================================================

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Performance Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "  ${GREEN}Passed${NC}: $PASSED"
echo -e "  ${RED}Failed${NC}: $FAILED"
echo ""

# Cleanup
rm -rf "$RESULTS_DIR"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All performance tests passed!${NC}"
    echo ""
    echo "Performance Requirements Met:"
    echo "  ✅ Health check response time < 200ms (P95)"
    echo "  ✅ Handles concurrent requests"
    echo "  ✅ Sustains traffic with < 1% error rate"
    exit 0
else
    echo -e "${RED}💥 Some performance tests failed.${NC}"
    echo ""
    echo "Potential issues:"
    echo "  - Database connection pool exhaustion"
    echo "  - FastAPI service overloaded"
    echo "  - Network latency"
    echo "  - Insufficient resources"
    exit 1
fi

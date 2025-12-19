#!/bin/bash

# CSA AIaaS Platform - Quick Curl Testing Script
# Sprint 1: The Neuro-Skeleton

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║            CSA AIaaS Platform - Quick API Testing                        ║"
echo "║                    Sprint 1: The Neuro-Skeleton                          ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_test() {
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════"
    echo -e "${BLUE}TEST: $1${NC}"
    echo "════════════════════════════════════════════════════════════════════════════"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if server is running
print_test "Health Check"
HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$HEALTH_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    print_success "Server is healthy"
    echo "$RESPONSE_BODY" | jq '.' 2>/dev/null || echo "$RESPONSE_BODY"
else
    print_error "Server health check failed (HTTP $HTTP_CODE)"
    echo "$RESPONSE_BODY"
    echo ""
    echo "Make sure the server is running:"
    echo "  cd backend"
    echo "  python main.py"
    exit 1
fi

# Test 1: Missing Critical Data
print_test "Test 1: Missing Critical Data (Foundation Design)"
print_info "Testing ambiguity detection with incomplete data..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_data": {
      "task_type": "foundation_design",
      "soil_type": "clayey"
    }
  }')

echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"

if echo "$RESPONSE" | jq -e '.ambiguity_flag == true' > /dev/null 2>&1; then
    print_success "Correctly identified ambiguity"
    QUESTION=$(echo "$RESPONSE" | jq -r '.clarification_question')
    echo "Question asked: $QUESTION"
else
    print_error "Failed to identify ambiguity"
fi

# Test 2: Complete Data
print_test "Test 2: Complete Data (No Ambiguity Expected)"
print_info "Testing with complete data set..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_data": {
      "task_type": "foundation_design",
      "foundation_type": "isolated_footing",
      "soil_type": "medium dense sand",
      "safe_bearing_capacity": 200,
      "column_dimensions": "400x400",
      "load_dead": 600,
      "load_live": 400,
      "foundation_depth": 1.5,
      "concrete_grade": "M25",
      "steel_grade": "Fe500",
      "code": "IS 456:2000"
    }
  }')

echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"

if echo "$RESPONSE" | jq -e '.ambiguity_flag == false' > /dev/null 2>&1; then
    print_success "Correctly identified complete data (no ambiguity)"
else
    print_error "Incorrectly flagged complete data as ambiguous"
fi

# Test 3: Conflicting Requirements
print_test "Test 3: Conflicting Requirements"
print_info "Testing conflict detection (steel beam with RCC code)..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_data": {
      "task_type": "beam_design",
      "material": "steel",
      "design_code": "IS 456",
      "span": 6000,
      "load": 50
    }
  }')

echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"

if echo "$RESPONSE" | jq -e '.ambiguity_flag == true' > /dev/null 2>&1; then
    print_success "Correctly identified conflict"
    QUESTION=$(echo "$RESPONSE" | jq -r '.clarification_question')
    echo "Question asked: $QUESTION"
else
    print_error "Failed to identify conflict"
fi

# Test 4: Partial Data
print_test "Test 4: Partial Data (Structural Analysis)"
print_info "Testing with some but not all required data..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_data": {
      "task_type": "structural_analysis",
      "structure_type": "frame",
      "material": "RCC",
      "number_of_stories": 3
    }
  }')

echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"

if echo "$RESPONSE" | jq -e '.ambiguity_flag == true' > /dev/null 2>&1; then
    print_success "Correctly identified missing data"
    QUESTION=$(echo "$RESPONSE" | jq -r '.clarification_question')
    echo "Question asked: $QUESTION"
else
    print_error "Failed to identify missing data"
fi

# Test 5: Vague Request
print_test "Test 5: Vague Requirements"
print_info "Testing with very vague request..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_data": {
      "task_type": "design_building",
      "building_type": "residential",
      "location": "somewhere in India"
    }
  }')

echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"

if echo "$RESPONSE" | jq -e '.ambiguity_flag == true' > /dev/null 2>&1; then
    print_success "Correctly identified vague requirements"
    QUESTION=$(echo "$RESPONSE" | jq -r '.clarification_question')
    echo "Question asked: $QUESTION"
else
    print_error "Failed to identify vague requirements"
fi

# Summary
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo -e "${BLUE}TEST SUMMARY${NC}"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
print_info "All tests completed!"
echo ""
echo "For detailed testing with LLM-based evaluation, run:"
echo "  python test_performance.py"
echo ""

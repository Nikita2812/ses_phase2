# Testing Guide - CSA AIaaS Platform

## Available Testing Tools

You have **3 ways** to test the API:

1. **Quick Curl Tests** - Fast bash script using curl
2. **Python Performance Tests** - Comprehensive testing with LLM-based evaluation
3. **Manual Unit Tests** - Individual component testing

---

## 1. Quick Curl Tests (Fastest)

### What It Does:
- Tests 5 different scenarios using curl
- Checks if server is running
- Validates ambiguity detection
- Color-coded output (pass/fail)

### How to Run:

```bash
cd backend

# Make sure server is running in another terminal
python main.py

# In a new terminal, run the tests
./test_curl.sh
```

### Expected Output:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            CSA AIaaS Platform - Quick API Testing                        ║
║                    Sprint 1: The Neuro-Skeleton                          ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

════════════════════════════════════════════════════════════════════════════
TEST: Health Check
════════════════════════════════════════════════════════════════════════════
✓ Server is healthy

... (more tests) ...
```

### What It Tests:
- ✅ Server health
- ✅ Missing data detection
- ✅ Complete data handling
- ✅ Conflict detection
- ✅ Partial data handling
- ✅ Vague requirements detection

---

## 2. Python Performance Tests (Most Comprehensive)

### What It Does:
- Runs 6 comprehensive test cases
- Uses **LLM to judge response quality**
- Measures response time
- Generates detailed report with scores
- Saves results to JSON file

### How to Run:

```bash
cd backend

# Make sure server is running in another terminal
python main.py

# In a new terminal, run the performance tests
python test_performance.py
```

### Expected Output:

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║            CSA AIaaS Platform - Performance Testing Tool                 ║
║                    Sprint 1: The Neuro-Skeleton                          ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

This script will:
1. Test API health and connectivity
2. Run multiple test cases with different scenarios
3. Use LLM to judge response quality
4. Generate performance report

================================================================================
TEST: Health Check Endpoint
================================================================================
Status Code: 200
Response Time: 0.123s
Response: {...}

================================================================================
TEST CASE: Missing Critical Data
================================================================================
Description: Foundation design with only soil type - missing load, dimensions, SBC

Input Data:
{
  "task_type": "foundation_design",
  "soil_type": "clayey"
}

Sending request...

✓ Response received in 2.456s
Ambiguity Flag: True
Status: clarification_needed
Question: What is the load on the foundation? Please provide dead load and live load.

🤖 Judging response quality with LLM...

📊 SCORES:
  Correctness:      9/10
  Clarity:          10/10
  Relevance:        9/10
  Completeness:     8/10
  Professionalism:  10/10
  OVERALL:          9.2/10

  Verdict: PASS

  Reasoning: The system correctly identified missing critical data...

... (more tests) ...

================================================================================
PERFORMANCE TEST REPORT
================================================================================
Test Date: 2025-12-19 14:30:00
Total Tests: 6
Successful Requests: 6/6
Quality Passed: 5/6

Performance Metrics:
  Average Response Time: 2.134s
  Average Quality Score: 8.7/10

Detailed Scores:
  ✓ Missing Critical Data: 9.2/10 (2.45s)
  ✓ Conflicting Requirements: 9.0/10 (2.12s)
  ✓ Complete Data - No Ambiguity: 8.5/10 (1.98s)
  ✓ Partial Data - Structural Analysis: 8.8/10 (2.34s)
  ✗ Ambiguous Specifications: 6.5/10 (2.01s)
  ✓ BOQ Generation Request: 9.1/10 (2.15s)

================================================================================

📄 Detailed report saved to: test_report_20251219_143000.json

✅ Testing complete!
```

### What It Tests:

| Test Case | Description | Expected Behavior |
|-----------|-------------|-------------------|
| **Missing Critical Data** | Foundation with only soil type | Detect missing load, dimensions, SBC |
| **Conflicting Requirements** | Steel beam with RCC code | Identify conflict in material/code |
| **Complete Data** | All parameters provided | No ambiguity flagged |
| **Partial Data** | Some but not all data | Detect missing parameters |
| **Ambiguous Specifications** | Vague requirements | Request specific details |
| **BOQ Generation** | Minimal information | Identify missing drawings/specs |

### LLM Evaluation Criteria:

Each response is judged on 5 criteria (0-10):
1. **Correctness** - Did it identify ambiguity correctly?
2. **Clarity** - Is the question clear and specific?
3. **Relevance** - Are issues actually relevant?
4. **Completeness** - Did it catch all major issues?
5. **Professionalism** - Is the tone appropriate?

### Report File:

The script generates a JSON report with:
```json
{
  "timestamp": "2025-12-19T14:30:00",
  "base_url": "http://localhost:8000",
  "total_tests": 6,
  "results": [
    {
      "name": "Missing Critical Data",
      "success": true,
      "response_time": 2.456,
      "response": {...},
      "judgment": {
        "correctness": 9,
        "clarity": 10,
        "relevance": 9,
        "completeness": 8,
        "professionalism": 10,
        "overall": 9.2,
        "reasoning": "...",
        "verdict": "PASS"
      }
    },
    ...
  ]
}
```

---

## 3. Manual Unit Tests

### Ambiguity Detection Tests

```bash
python tests/test_ambiguity_detection.py
```

**What it tests:**
- Test 1: Missing data detection
- Test 2: Complete data handling
- Test 3: Conflicting requirements

### Graph Routing Tests

```bash
python tests/test_graph_routing.py
```

**What it tests:**
- Test 1: Routing with ambiguous input
- Test 2: Routing with complete input
- Test 3: Routing with partial data

---

## Comparison: Which Test to Use?

| Feature | Quick Curl | Python Performance | Unit Tests |
|---------|------------|-------------------|------------|
| **Speed** | ⚡ Fastest (30s) | 🐢 Slower (2-3 min) | ⚡ Fast (30s) |
| **Setup** | None | None | None |
| **API Testing** | ✅ Yes | ✅ Yes | ❌ No |
| **LLM Evaluation** | ❌ No | ✅ Yes | ❌ No |
| **Detailed Scores** | ❌ No | ✅ Yes | ❌ No |
| **Report File** | ❌ No | ✅ Yes (JSON) | ❌ No |
| **Component Testing** | ❌ No | ❌ No | ✅ Yes |
| **When to Use** | Quick check | Full evaluation | Development |

---

## Test Scenarios Explained

### 1. Missing Critical Data
**Input**: Only soil type provided
**Expected**: Should ask for load, dimensions, SBC
**Why Important**: Core safety feature - never guess missing data

### 2. Conflicting Requirements
**Input**: Steel beam with IS 456 code (RCC code)
**Expected**: Identify material/code mismatch
**Why Important**: Prevents dangerous design errors

### 3. Complete Data
**Input**: All required parameters provided
**Expected**: No ambiguity flag, proceed to execution
**Why Important**: Validates system doesn't over-flag

### 4. Partial Data
**Input**: Some parameters but not all
**Expected**: Identify specific missing items
**Why Important**: Precision in identifying gaps

### 5. Ambiguous Specifications
**Input**: Vague, non-specific requirements
**Expected**: Request concrete details
**Why Important**: Ensures actionable specifications

### 6. BOQ Generation
**Input**: Request without drawings/specifications
**Expected**: Ask for necessary documents
**Why Important**: Domain-specific validation

---

## Troubleshooting

### Error: "Connection refused"
**Problem**: Server is not running
**Solution**:
```bash
# Start the server
cd backend
python main.py
```

### Error: "OPENROUTER_API_KEY not found"
**Problem**: Environment not configured
**Solution**:
```bash
# Check your .env file
cat .env | grep OPENROUTER_API_KEY

# Add if missing
echo "OPENROUTER_API_KEY=sk-or-v1-your-key" >> .env
```

### Error: "jq: command not found" (curl tests)
**Problem**: jq not installed
**Solution**:
```bash
# On Ubuntu/Debian
sudo apt install jq

# On Fedora
sudo dnf install jq

# On macOS
brew install jq
```

### Error: "ModuleNotFoundError: No module named 'requests'"
**Problem**: Missing Python dependencies
**Solution**:
```bash
pip install -r requirements.txt
```

---

## Performance Benchmarks

### Expected Response Times:

| Metric | Target | Acceptable | Poor |
|--------|--------|------------|------|
| Health Check | <100ms | <500ms | >1s |
| Simple Query | <2s | <5s | >10s |
| Complex Query | <3s | <8s | >15s |

### Expected Quality Scores:

| Scenario | Target | Acceptable | Poor |
|----------|--------|------------|------|
| Missing Data | 9-10 | 7-8 | <7 |
| Complete Data | 8-10 | 6-7 | <6 |
| Conflicts | 8-10 | 6-7 | <6 |

---

## Continuous Testing

### During Development:

1. **After code changes**:
   ```bash
   ./test_curl.sh  # Quick validation
   ```

2. **Before committing**:
   ```bash
   python test_performance.py  # Full evaluation
   ```

3. **Component-level**:
   ```bash
   python tests/test_ambiguity_detection.py
   python tests/test_graph_routing.py
   ```

### Before Production:

1. Run all tests multiple times
2. Check average scores are >8/10
3. Verify response times are acceptable
4. Review LLM reasoning for edge cases

---

## Adding New Tests

### To Quick Curl Tests:

Edit `test_curl.sh`, add a new test block:

```bash
print_test "Test X: Your Test Name"
print_info "Description..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_data": {
      "your": "data"
    }
  }')

echo "$RESPONSE" | jq '.'
```

### To Python Performance Tests:

Edit `test_performance.py`, add to `test_cases` list:

```python
{
    "name": "Your Test Name",
    "description": "What this tests",
    "input_data": {
        "your": "data"
    },
    "expected_behavior": "What should happen"
}
```

---

## Summary

✅ **Quick Testing**: Use `./test_curl.sh`
✅ **Comprehensive Testing**: Use `python test_performance.py`
✅ **Component Testing**: Use `python tests/test_*.py`

All tests work together to ensure:
- API is functional
- Responses are accurate
- Performance is acceptable
- Quality meets standards

---

**Last Updated**: December 19, 2025
**Version**: Sprint 1

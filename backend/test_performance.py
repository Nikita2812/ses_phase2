#!/usr/bin/env python3
"""
CSA AIaaS Platform - Performance & Quality Testing Script
Sprint 1: The Neuro-Skeleton

This script tests the API endpoints and uses an LLM to evaluate the quality
of the ambiguity detection responses.

Usage:
    python test_performance.py

Requirements:
    - Server must be running on localhost:8000
    - OPENROUTER_API_KEY must be set in .env
"""

import requests
import json
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class APIPerformanceTester:
    """
    Tests API performance and uses LLM to judge response quality.
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []

        # Initialize LLM for judging responses
        openrouter_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_key:
            raise ValueError("OPENROUTER_API_KEY not found in .env")

        self.judge_llm = ChatOpenAI(
            model=os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free"),
            api_key=openrouter_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://csa-aiaas-platform.local",
                "X-Title": "CSA AIaaS Platform - Testing"
            }
        )

    def test_health_endpoint(self) -> Tuple[bool, float]:
        """Test the /health endpoint."""
        print("\n" + "="*80)
        print("TEST: Health Check Endpoint")
        print("="*80)

        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=5)
            elapsed = time.time() - start_time

            print(f"Status Code: {response.status_code}")
            print(f"Response Time: {elapsed:.3f}s")
            print(f"Response: {response.json()}")

            success = response.status_code == 200
            return success, elapsed
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False, 0.0

    def send_request(self, test_case: Dict) -> Tuple[Optional[Dict], float]:
        """Send a request to the API and measure response time."""
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.base_url}/api/v1/execute",
                json=test_case,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            elapsed = time.time() - start_time

            if response.status_code == 200:
                return response.json(), elapsed
            else:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return None, elapsed
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return None, 0.0

    def judge_response(self, test_case: Dict, response: Dict) -> Dict:
        """Use LLM to judge the quality of the API response."""

        judge_prompt = f"""You are an expert evaluator of AI system responses. Evaluate the following API response for an engineering ambiguity detection system.

INPUT DATA:
{json.dumps(test_case['input_data'], indent=2)}

EXPECTED BEHAVIOR:
{test_case.get('expected_behavior', 'Detect missing or ambiguous information')}

API RESPONSE:
{json.dumps(response, indent=2)}

Evaluate the response on these criteria:

1. **Correctness (0-10)**: Did it correctly identify ambiguity or completeness?
2. **Clarity (0-10)**: Is the clarification question clear and specific?
3. **Relevance (0-10)**: Are the identified issues actually relevant?
4. **Completeness (0-10)**: Did it catch all major ambiguities?
5. **Professionalism (0-10)**: Is the tone appropriate for engineering?

Respond ONLY with valid JSON in this format:
{{
  "correctness": <score>,
  "clarity": <score>,
  "relevance": <score>,
  "completeness": <score>,
  "professionalism": <score>,
  "overall": <average score>,
  "reasoning": "Brief explanation of the scores",
  "verdict": "PASS" or "FAIL"
}}
"""

        try:
            messages = [HumanMessage(content=judge_prompt)]
            llm_response = self.judge_llm.invoke(messages)
            response_text = llm_response.content.strip()

            # Handle markdown code blocks
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                json_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("```"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or not line.strip().startswith("```"):
                        json_lines.append(line)
                response_text = "\n".join(json_lines)

            judgment = json.loads(response_text)
            return judgment
        except Exception as e:
            print(f"⚠ LLM Judgment Error: {e}")
            return {
                "correctness": 5,
                "clarity": 5,
                "relevance": 5,
                "completeness": 5,
                "professionalism": 5,
                "overall": 5.0,
                "reasoning": f"Error during judgment: {str(e)}",
                "verdict": "ERROR"
            }

    def run_test_case(self, test_case: Dict) -> Dict:
        """Run a single test case and evaluate it."""
        print("\n" + "="*80)
        print(f"TEST CASE: {test_case['name']}")
        print("="*80)
        print(f"Description: {test_case['description']}")
        print(f"\nInput Data:")
        print(json.dumps(test_case['input_data'], indent=2))

        # Send request
        print(f"\nSending request...")
        response, elapsed = self.send_request({
            "user_id": "performance_test",
            "input_data": test_case['input_data']
        })

        if response is None:
            print("❌ Request Failed")
            return {
                "name": test_case['name'],
                "success": False,
                "response_time": elapsed,
                "error": "Request failed"
            }

        print(f"\n✓ Response received in {elapsed:.3f}s")
        print(f"Ambiguity Flag: {response.get('ambiguity_flag')}")
        print(f"Status: {response.get('status')}")
        if response.get('clarification_question'):
            print(f"Question: {response.get('clarification_question')}")

        # Judge response quality
        print(f"\n🤖 Judging response quality with LLM...")
        judgment = self.judge_response(test_case, response)

        print(f"\n📊 SCORES:")
        print(f"  Correctness:      {judgment['correctness']}/10")
        print(f"  Clarity:          {judgment['clarity']}/10")
        print(f"  Relevance:        {judgment['relevance']}/10")
        print(f"  Completeness:     {judgment['completeness']}/10")
        print(f"  Professionalism:  {judgment['professionalism']}/10")
        print(f"  OVERALL:          {judgment['overall']:.1f}/10")
        print(f"\n  Verdict: {judgment['verdict']}")
        print(f"\n  Reasoning: {judgment['reasoning']}")

        return {
            "name": test_case['name'],
            "success": True,
            "response_time": elapsed,
            "response": response,
            "judgment": judgment
        }

    def generate_report(self):
        """Generate a comprehensive test report."""
        print("\n" + "="*80)
        print("PERFORMANCE TEST REPORT")
        print("="*80)
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total Tests: {len(self.results)}")

        successful_tests = [r for r in self.results if r.get('success')]
        passed_tests = [r for r in successful_tests if r.get('judgment', {}).get('verdict') == 'PASS']

        print(f"Successful Requests: {len(successful_tests)}/{len(self.results)}")
        print(f"Quality Passed: {len(passed_tests)}/{len(successful_tests)}")

        if successful_tests:
            avg_response_time = sum(r['response_time'] for r in successful_tests) / len(successful_tests)
            avg_score = sum(r['judgment']['overall'] for r in successful_tests) / len(successful_tests)

            print(f"\nPerformance Metrics:")
            print(f"  Average Response Time: {avg_response_time:.3f}s")
            print(f"  Average Quality Score: {avg_score:.1f}/10")

            print(f"\nDetailed Scores:")
            for result in successful_tests:
                judgment = result['judgment']
                status = "✓" if judgment['verdict'] == 'PASS' else "✗"
                print(f"  {status} {result['name']}: {judgment['overall']:.1f}/10 ({result['response_time']:.2f}s)")

        print("\n" + "="*80)


def main():
    """Main test execution."""

    # Test cases covering different scenarios
    test_cases = [
        {
            "name": "Missing Critical Data",
            "description": "Foundation design with only soil type - missing load, dimensions, SBC",
            "input_data": {
                "task_type": "foundation_design",
                "soil_type": "clayey"
            },
            "expected_behavior": "Should identify missing: load, dimensions, safe bearing capacity"
        },
        {
            "name": "Conflicting Requirements",
            "description": "Steel beam with RCC design code (conflict)",
            "input_data": {
                "task_type": "beam_design",
                "material": "steel",
                "design_code": "IS 456",  # IS 456 is for RCC, not steel
                "span": 6000,
                "load": 50
            },
            "expected_behavior": "Should identify conflict: Steel beam with RCC code"
        },
        {
            "name": "Complete Data - No Ambiguity",
            "description": "Foundation design with all required parameters",
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
            },
            "expected_behavior": "Should NOT flag as ambiguous - all data present"
        },
        {
            "name": "Partial Data - Structural Analysis",
            "description": "Structural analysis with some missing parameters",
            "input_data": {
                "task_type": "structural_analysis",
                "structure_type": "frame",
                "material": "RCC",
                "number_of_stories": 3
                # Missing: dimensions, loads, seismic zone, soil conditions
            },
            "expected_behavior": "Should identify missing: dimensions, loads, seismic parameters"
        },
        {
            "name": "Ambiguous Specifications",
            "description": "Vague requirements without specifics",
            "input_data": {
                "task_type": "design_building",
                "building_type": "residential",
                "location": "somewhere in India"
                # Very vague, missing everything specific
            },
            "expected_behavior": "Should identify lack of specific requirements"
        },
        {
            "name": "BOQ Generation Request",
            "description": "Bill of Quantities request with minimal info",
            "input_data": {
                "task_type": "generate_boq",
                "project_type": "industrial_warehouse"
                # Missing: drawings, specifications, scope
            },
            "expected_behavior": "Should identify missing: drawings reference, specifications, scope"
        }
    ]

    print("""
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
    """)

    # Initialize tester
    tester = APIPerformanceTester()

    # Test health endpoint first
    health_ok, health_time = tester.test_health_endpoint()
    if not health_ok:
        print("\n❌ Server health check failed. Is the server running on localhost:8000?")
        print("   Start the server with: python main.py")
        return

    print("\n✓ Server is healthy and ready for testing")

    # Run all test cases
    print(f"\n{'='*80}")
    print(f"Running {len(test_cases)} test cases...")
    print(f"{'='*80}")

    for test_case in test_cases:
        result = tester.run_test_case(test_case)
        tester.results.append(result)
        time.sleep(1)  # Small delay between tests

    # Generate report
    tester.generate_report()

    # Save detailed results to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "base_url": tester.base_url,
            "total_tests": len(tester.results),
            "results": tester.results
        }, f, indent=2)

    print(f"\n📄 Detailed report saved to: {report_file}")
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()

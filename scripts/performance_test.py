#!/usr/bin/env python3
"""
Performance Testing Script
Comprehensive performance testing for the DRASS system
"""

import asyncio
import aiohttp
import time
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import statistics
from dataclasses import dataclass
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Test result data structure"""
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    response_size_bytes: int = 0


@dataclass
class TestScenario:
    """Test scenario configuration"""
    name: str
    endpoint: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, Any]] = None
    expected_status: int = 200
    weight: float = 1.0  # Weight for load distribution


class PerformanceTester:
    """Performance testing class"""
    
    def __init__(self, base_url: str = "http://localhost:8888"):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self.results: List[TestResult] = []
        
        # Test scenarios
        self.scenarios = [
            TestScenario(
                name="health_check",
                endpoint="/health",
                method="GET",
                expected_status=200
            ),
            TestScenario(
                name="api_health",
                endpoint="/api/v1/health",
                method="GET",
                expected_status=200
            ),
            TestScenario(
                name="login",
                endpoint="/api/v1/auth/login",
                method="POST",
                data={
                    "email": "test@example.com",
                    "password": "testpassword123"
                },
                expected_status=200
            ),
            TestScenario(
                name="document_list",
                endpoint="/api/v1/documents/",
                method="GET",
                headers={"Authorization": "Bearer test_token"},
                expected_status=200
            ),
            TestScenario(
                name="audit_logs",
                endpoint="/api/v1/audit-enhanced/logs",
                method="GET",
                headers={"Authorization": "Bearer test_token"},
                expected_status=200
            ),
            TestScenario(
                name="compliance_demo",
                endpoint="/api/v1/compliance-demo/analyze",
                method="POST",
                headers={"Authorization": "Bearer test_token"},
                data={
                    "data": {
                        "name": "John Doe",
                        "email": "john@example.com",
                        "phone": "123-456-7890"
                    },
                    "compliance_rules": ["GDPR", "SOC2"]
                },
                expected_status=200
            ),
            TestScenario(
                name="performance_analysis",
                endpoint="/api/v1/performance/analysis",
                method="GET",
                headers={"Authorization": "Bearer test_token"},
                expected_status=200
            )
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def run_single_test(self, scenario: TestScenario) -> TestResult:
        """Run a single test scenario"""
        url = f"{self.base_url}{scenario.endpoint}"
        start_time = time.time()
        
        try:
            if scenario.method == "GET":
                async with self.session.get(url, headers=scenario.headers) as response:
                    response_text = await response.text()
                    response_time = (time.time() - start_time) * 1000
                    
                    return TestResult(
                        endpoint=scenario.endpoint,
                        method=scenario.method,
                        status_code=response.status,
                        response_time_ms=response_time,
                        success=response.status == scenario.expected_status,
                        response_size_bytes=len(response_text.encode('utf-8'))
                    )
            
            elif scenario.method == "POST":
                json_data = json.dumps(scenario.data) if scenario.data else None
                async with self.session.post(
                    url, 
                    headers=scenario.headers,
                    data=json_data,
                    content_type='application/json'
                ) as response:
                    response_text = await response.text()
                    response_time = (time.time() - start_time) * 1000
                    
                    return TestResult(
                        endpoint=scenario.endpoint,
                        method=scenario.method,
                        status_code=response.status,
                        response_time_ms=response_time,
                        success=response.status == scenario.expected_status,
                        response_size_bytes=len(response_text.encode('utf-8'))
                    )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return TestResult(
                endpoint=scenario.endpoint,
                method=scenario.method,
                status_code=0,
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
    
    async def run_load_test(
        self, 
        duration_seconds: int = 60,
        concurrent_users: int = 10,
        scenario_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Run load test with multiple concurrent users"""
        logger.info(f"Starting load test: {duration_seconds}s, {concurrent_users} users")
        
        # Prepare scenarios with weights
        weighted_scenarios = []
        for scenario in self.scenarios:
            weight = scenario_weights.get(scenario.name, scenario.weight) if scenario_weights else scenario.weight
            weighted_scenarios.extend([scenario] * int(weight * 10))  # Scale weights
        
        if not weighted_scenarios:
            weighted_scenarios = self.scenarios
        
        # Run load test
        start_time = time.time()
        tasks = []
        
        async def user_simulation():
            """Simulate a single user"""
            user_results = []
            while time.time() - start_time < duration_seconds:
                # Select random scenario
                scenario = weighted_scenarios[hash(str(time.time())) % len(weighted_scenarios)]
                
                # Run test
                result = await self.run_single_test(scenario)
                user_results.append(result)
                
                # Small delay between requests
                await asyncio.sleep(0.1)
            
            return user_results
        
        # Start concurrent users
        for _ in range(concurrent_users):
            tasks.append(user_simulation())
        
        # Wait for all users to complete
        all_results = await asyncio.gather(*tasks)
        
        # Flatten results
        self.results = []
        for user_results in all_results:
            self.results.extend(user_results)
        
        # Calculate statistics
        return self._calculate_statistics(duration_seconds, concurrent_users)
    
    async def run_stress_test(
        self,
        max_concurrent_users: int = 100,
        step_size: int = 10,
        step_duration: int = 30
    ) -> Dict[str, Any]:
        """Run stress test with increasing load"""
        logger.info(f"Starting stress test: up to {max_concurrent_users} users")
        
        stress_results = []
        
        for concurrent_users in range(step_size, max_concurrent_users + 1, step_size):
            logger.info(f"Testing with {concurrent_users} concurrent users")
            
            # Run load test for this step
            step_results = await self.run_load_test(
                duration_seconds=step_duration,
                concurrent_users=concurrent_users
            )
            
            step_results["concurrent_users"] = concurrent_users
            stress_results.append(step_results)
            
            # Check if system is still responsive
            if step_results["success_rate_percent"] < 95:
                logger.warning(f"Success rate dropped below 95% at {concurrent_users} users")
                break
            
            if step_results["average_response_time_ms"] > 5000:
                logger.warning(f"Response time exceeded 5s at {concurrent_users} users")
                break
        
        return {
            "stress_test_results": stress_results,
            "max_sustainable_users": stress_results[-1]["concurrent_users"] if stress_results else 0,
            "bottleneck_detected": len(stress_results) < (max_concurrent_users // step_size)
        }
    
    def _calculate_statistics(self, duration_seconds: int, concurrent_users: int) -> Dict[str, Any]:
        """Calculate test statistics"""
        if not self.results:
            return {"error": "No test results available"}
        
        # Basic statistics
        total_requests = len(self.results)
        successful_requests = sum(1 for r in self.results if r.success)
        failed_requests = total_requests - successful_requests
        
        # Response time statistics
        response_times = [r.response_time_ms for r in self.results if r.success]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = p99_response_time = 0
            min_response_time = max_response_time = 0
        
        # Throughput
        requests_per_second = total_requests / duration_seconds if duration_seconds > 0 else 0
        
        # Success rate
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Endpoint breakdown
        endpoint_stats = {}
        for result in self.results:
            endpoint = result.endpoint
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "response_times": []
                }
            
            endpoint_stats[endpoint]["total_requests"] += 1
            if result.success:
                endpoint_stats[endpoint]["successful_requests"] += 1
                endpoint_stats[endpoint]["response_times"].append(result.response_time_ms)
        
        # Calculate endpoint averages
        for endpoint, stats in endpoint_stats.items():
            if stats["response_times"]:
                stats["average_response_time_ms"] = statistics.mean(stats["response_times"])
                stats["success_rate_percent"] = (stats["successful_requests"] / stats["total_requests"]) * 100
            else:
                stats["average_response_time_ms"] = 0
                stats["success_rate_percent"] = 0
        
        return {
            "test_summary": {
                "duration_seconds": duration_seconds,
                "concurrent_users": concurrent_users,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "success_rate_percent": round(success_rate, 2),
                "requests_per_second": round(requests_per_second, 2)
            },
            "response_times": {
                "average_ms": round(avg_response_time, 2),
                "median_ms": round(median_response_time, 2),
                "p95_ms": round(p95_response_time, 2),
                "p99_ms": round(p99_response_time, 2),
                "min_ms": round(min_response_time, 2),
                "max_ms": round(max_response_time, 2)
            },
            "endpoint_breakdown": endpoint_stats,
            "test_timestamp": datetime.now().isoformat()
        }
    
    def save_results(self, results: Dict[str, Any], filename: Optional[str] = None) -> str:
        """Save test results to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"performance_test_results_{timestamp}.json"
        
        filepath = Path(filename)
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Test results saved to {filepath}")
        return str(filepath)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DRASS Performance Testing Script")
    parser.add_argument("--base-url", "-u", 
                       default="http://localhost:8888",
                       help="Base URL for the API")
    parser.add_argument("--test-type", "-t",
                       choices=["load", "stress", "single"],
                       default="load",
                       help="Type of test to run")
    parser.add_argument("--duration", "-d",
                       type=int, default=60,
                       help="Test duration in seconds (for load test)")
    parser.add_argument("--concurrent-users", "-c",
                       type=int, default=10,
                       help="Number of concurrent users")
    parser.add_argument("--max-users", "-m",
                       type=int, default=100,
                       help="Maximum concurrent users (for stress test)")
    parser.add_argument("--step-size", "-s",
                       type=int, default=10,
                       help="Step size for stress test")
    parser.add_argument("--step-duration", "-sd",
                       type=int, default=30,
                       help="Duration per step in stress test")
    parser.add_argument("--output", "-o",
                       help="Output file for results")
    parser.add_argument("--verbose", "-v",
                       action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run performance test
    async with PerformanceTester(args.base_url) as tester:
        if args.test_type == "single":
            # Run single test for each scenario
            results = []
            for scenario in tester.scenarios:
                logger.info(f"Testing {scenario.name}: {scenario.endpoint}")
                result = await tester.run_single_test(scenario)
                results.append(result)
                logger.info(f"Result: {result.status_code} - {result.response_time_ms:.2f}ms")
            
            test_results = {
                "test_type": "single",
                "results": [
                    {
                        "endpoint": r.endpoint,
                        "method": r.method,
                        "status_code": r.status_code,
                        "response_time_ms": r.response_time_ms,
                        "success": r.success,
                        "error_message": r.error_message
                    }
                    for r in results
                ]
            }
        
        elif args.test_type == "load":
            test_results = await tester.run_load_test(
                duration_seconds=args.duration,
                concurrent_users=args.concurrent_users
            )
            test_results["test_type"] = "load"
        
        elif args.test_type == "stress":
            test_results = await tester.run_stress_test(
                max_concurrent_users=args.max_users,
                step_size=args.step_size,
                step_duration=args.step_duration
            )
            test_results["test_type"] = "stress"
        
        # Save results
        output_file = tester.save_results(test_results, args.output)
        
        # Print summary
        if args.test_type == "single":
            print(f"\nSingle Test Results:")
            for result in test_results["results"]:
                status = "✓" if result["success"] else "✗"
                print(f"  {status} {result['endpoint']}: {result['response_time_ms']:.2f}ms")
        
        elif args.test_type == "load":
            summary = test_results["test_summary"]
            print(f"\nLoad Test Results:")
            print(f"  Duration: {summary['duration_seconds']}s")
            print(f"  Concurrent Users: {summary['concurrent_users']}")
            print(f"  Total Requests: {summary['total_requests']}")
            print(f"  Success Rate: {summary['success_rate_percent']:.1f}%")
            print(f"  Requests/sec: {summary['requests_per_second']:.1f}")
            print(f"  Avg Response Time: {test_results['response_times']['average_ms']:.2f}ms")
        
        elif args.test_type == "stress":
            print(f"\nStress Test Results:")
            print(f"  Max Sustainable Users: {test_results['max_sustainable_users']}")
            print(f"  Bottleneck Detected: {test_results['bottleneck_detected']}")
        
        print(f"\nDetailed results saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())

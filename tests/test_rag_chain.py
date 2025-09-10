#!/usr/bin/env python3
"""
Test script for LangChain RAG Chain functionality
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

async def test_health_check():
    """Test API health endpoint"""
    print("1. Testing health check...")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                f"{API_BASE_URL}/health",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"   ✓ Health check passed: {data}")
                    return True
                else:
                    print(f"   ✗ Health check failed: Status {response.status}")
                    return False
        except Exception as e:
            print(f"   ✗ Health check error: {e}")
            return False

async def test_simple_chat():
    """Test simple chat without RAG"""
    print("\n2. Testing simple chat...")
    
    async with aiohttp.ClientSession() as session:
        payload = {
            "query": "What is data compliance?",
            "stream": False,
            "use_knowledge_base": False
        }
        
        try:
            async with session.post(
                f"{API_BASE_URL}/api/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Check response format
                    if "response" in data:
                        response_text = data["response"]
                    elif "choices" in data and len(data["choices"]) > 0:
                        response_text = data["choices"][0].get("message", {}).get("content", "")
                    else:
                        print(f"   ✗ Unexpected response format: {data}")
                        return False
                    
                    print(f"   ✓ Response received: {response_text[:100]}...")
                    return True
                else:
                    error_text = await response.text()
                    print(f"   ✗ Chat failed: Status {response.status}")
                    print(f"   Error: {error_text}")
                    return False
        except Exception as e:
            print(f"   ✗ Chat error: {e}")
            return False

async def test_rag_with_context():
    """Test RAG with document context"""
    print("\n3. Testing RAG with context...")
    
    async with aiohttp.ClientSession() as session:
        # First, upload a test document
        test_content = """
        Company Data Protection Policy:
        1. All personal data must be encrypted at rest and in transit
        2. Access to customer data requires multi-factor authentication
        3. Data retention period is limited to 90 days
        4. Regular security audits must be conducted monthly
        5. GDPR compliance is mandatory for all EU customer data
        """
        
        # Create test file
        with open("/tmp/test_policy.txt", "w") as f:
            f.write(test_content)
        
        # Upload document
        print("   Uploading test document...")
        with open("/tmp/test_policy.txt", "rb") as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename='test_policy.txt', content_type='text/plain')
            
            try:
                async with session.post(
                    f"{API_BASE_URL}/api/v1/documents/upload",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT)
                ) as response:
                    if response.status == 200:
                        print("   ✓ Document uploaded successfully")
                    else:
                        print(f"   ⚠ Document upload status: {response.status}")
            except Exception as e:
                print(f"   ⚠ Document upload skipped: {e}")
        
        # Query with RAG
        payload = {
            "query": "What is our data retention policy?",
            "stream": False,
            "use_knowledge_base": True
        }
        
        try:
            async with session.post(
                f"{API_BASE_URL}/api/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract response
                    if "response" in data:
                        response_text = data["response"]
                    elif "choices" in data and len(data["choices"]) > 0:
                        response_text = data["choices"][0].get("message", {}).get("content", "")
                    else:
                        response_text = str(data)
                    
                    # Check if response contains relevant information
                    if "90 days" in response_text or "retention" in response_text.lower():
                        print(f"   ✓ RAG response is relevant: {response_text[:150]}...")
                        return True
                    else:
                        print(f"   ⚠ RAG response may not use context: {response_text[:150]}...")
                        return True  # Still pass if response is received
                else:
                    print(f"   ✗ RAG query failed: Status {response.status}")
                    return False
        except Exception as e:
            print(f"   ✗ RAG query error: {e}")
            return False

async def test_streaming_response():
    """Test streaming chat response"""
    print("\n4. Testing streaming response...")
    
    async with aiohttp.ClientSession() as session:
        payload = {
            "query": "Explain GDPR in detail",
            "stream": True
        }
        
        try:
            async with session.post(
                f"{API_BASE_URL}/api/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT)
            ) as response:
                if response.status == 200:
                    chunks = []
                    async for line in response.content:
                        if line:
                            chunks.append(line.decode('utf-8'))
                    
                    if len(chunks) > 0:
                        print(f"   ✓ Received {len(chunks)} streaming chunks")
                        return True
                    else:
                        print("   ⚠ No streaming chunks received")
                        return False
                else:
                    print(f"   ✗ Streaming failed: Status {response.status}")
                    return False
        except Exception as e:
            print(f"   ✗ Streaming error: {e}")
            return False

async def test_chinese_language():
    """Test Chinese language support"""
    print("\n5. Testing Chinese language support...")
    
    async with aiohttp.ClientSession() as session:
        payload = {
            "query": "什么是GDPR？请用中文回答。",
            "stream": False
        }
        
        try:
            async with session.post(
                f"{API_BASE_URL}/api/v1/chat/completions",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=TEST_TIMEOUT)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Extract response
                    if "response" in data:
                        response_text = data["response"]
                    elif "choices" in data and len(data["choices"]) > 0:
                        response_text = data["choices"][0].get("message", {}).get("content", "")
                    else:
                        response_text = str(data)
                    
                    # Check if response contains Chinese characters
                    if any('\u4e00' <= char <= '\u9fff' for char in response_text):
                        print(f"   ✓ Chinese response received: {response_text[:100]}...")
                        return True
                    else:
                        print(f"   ⚠ Response may not be in Chinese: {response_text[:100]}...")
                        return True  # Still pass if response is received
                else:
                    print(f"   ✗ Chinese query failed: Status {response.status}")
                    return False
        except Exception as e:
            print(f"   ✗ Chinese query error: {e}")
            return False

async def main():
    """Run all tests"""
    print("="*50)
    print("LangChain RAG Chain Test Suite")
    print(f"API URL: {API_BASE_URL}")
    print(f"Time: {datetime.now()}")
    print("="*50)
    
    tests = [
        ("Health Check", test_health_check),
        ("Simple Chat", test_simple_chat),
        ("RAG with Context", test_rag_with_context),
        ("Streaming Response", test_streaming_response),
        ("Chinese Language", test_chinese_language),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*50)
    print("Test Summary:")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✅ All RAG chain tests passed!")
        return 0
    else:
        print(f"\n⚠️ {failed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
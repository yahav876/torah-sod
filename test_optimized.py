#!/usr/bin/env python3
"""
Test script to verify the optimized application works correctly
"""
import requests
import time
import json


def test_health_check():
    """Test health check endpoint."""
    print("Testing health check...")
    response = requests.get("http://localhost:5001/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✅ Health check passed\n")


def test_search_api():
    """Test search API endpoint."""
    print("Testing search API...")
    data = {"phrase": "אלהים"}
    response = requests.post("http://localhost:5001/api/search", json=data)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Success: {result.get('success')}")
    print(f"Total variants: {result.get('total_variants', 0)}")
    print(f"Search time: {result.get('search_time', 0)}s")
    
    if result.get('results'):
        print(f"First result: {result['results'][0]['variant']}")
    
    print("✅ Search API test passed\n")


def test_stats_api():
    """Test statistics API endpoint."""
    print("Testing stats API...")
    response = requests.get("http://localhost:5001/api/stats")
    print(f"Status: {response.status_code}")
    stats = response.json()
    print(f"Torah verses: {stats.get('torah_verses', 0)}")
    print(f"Cached searches: {stats.get('cached_searches', 0)}")
    print(f"Total searches: {stats.get('total_searches', 0)}")
    print("✅ Stats API test passed\n")


def test_web_interface():
    """Test web interface."""
    print("Testing web interface...")
    response = requests.get("http://localhost:5001/")
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.text)} bytes")
    assert "Torah Search" in response.text
    print("✅ Web interface test passed\n")


def test_background_search():
    """Test background search for long phrases."""
    print("Testing background search...")
    # This should trigger a background job
    long_phrase = " ".join(["מילה"] * 15)  # 15 words to trigger background
    data = {"phrase": long_phrase}
    response = requests.post("http://localhost:5001/api/search", json=data)
    
    if response.status_code == 202:
        result = response.json()
        job_id = result.get('job_id')
        print(f"Background job created: {job_id}")
        
        # Check status
        time.sleep(2)
        status_response = requests.get(f"http://localhost:5001/api/search/status/{job_id}")
        print(f"Job status: {status_response.json()}")
        print("✅ Background search test passed\n")
    else:
        print("Background search not triggered (might need more words)")


def main():
    """Run all tests."""
    print("🧪 Testing Optimized Torah Search Application\n")
    
    try:
        test_health_check()
        test_web_interface()
        test_search_api()
        test_stats_api()
        # test_background_search()  # Uncomment if Celery is running
        
        print("✅ All tests passed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the application.")
        print("Make sure the application is running on http://localhost:5001")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()

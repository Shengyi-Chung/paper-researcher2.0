#!/usr/bin/env python3
"""测试 arXiv API 连通性"""

import requests
import time

def test_arxiv_api():
    """测试 arXiv API"""
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": "ti:neural",
        "max_results": 1,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    
    print("Testing arXiv API...")
    print(f"URL: {url}")
    print(f"Params: {params}")
    print("-" * 50)
    
    start_time = time.time()
    
    try:
        response = requests.get(url, params=params, timeout=30)
        elapsed = time.time() - start_time
        
        print(f"\n✓ Status Code: {response.status_code}")
        print(f"✓ Response Time: {elapsed:.2f}s")
        print(f"✓ Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            # Check if we got valid XML
            content = response.text[:500]
            print(f"\n✓ Success! Sample response:\n{content}...")
            return {"status": "success", "code": response.status_code, "time": elapsed}
        else:
            print(f"\n✗ Error: {response.text[:200]}")
            return {"status": "error", "code": response.status_code}
            
    except requests.exceptions.Timeout:
        print("\n✗ Timeout: API 请求超时 (30s)")
        return {"status": "timeout"}
    except requests.exceptions.ConnectionError as e:
        print(f"\n✗ Connection Error: {e}")
        return {"status": "connection_error"}
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    result = test_arxiv_api()
    print("\n" + "=" * 50)
    print(f"Test Result: {result['status'].upper()}")

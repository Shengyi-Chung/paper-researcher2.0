"""
Quick test for paper-search skill
"""

import sys
sys.path.insert(0, __file__.rsplit('/', 1)[0] if '/' in __file__ else '.')

from paper_search import search_papers, save_results

# Test search
print("Testing paper-search skill...")
print("=" * 60)

result = search_papers("transformer attention", max_results=10)

if result["papers"]:
    # Save to default location
    save_results(result, "data")
    
    print("\n" + "=" * 60)
    print("TEST PASSED")
    print("=" * 60)
    print(f"\nFirst paper example:")
    p = result["papers"][0]
    print(f"Title: {p['title']}")
    print(f"Authors: {p['authors']}")
    print(f"Abstract: {p['abstract'][:150]}...")
else:
    print("\nTEST FAILED - No papers found")

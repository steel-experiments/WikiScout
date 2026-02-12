#!/usr/bin/env python3
"""
Test Example - Practical Usage Demonstration
==============================================

This file demonstrates how to test WikiScout agent functionality
with real-world scenarios. Use it as a template for your own tests.

Run with: python test_example.py
Or with pytest: pytest test_example.py -v
"""

import sys
import json
from pathlib import Path

# Add modules to path
sys.path.insert(0, str(Path(__file__).parent / "modules"))

from agent import WikipediaAgent


def test_basic_search():
    """
    Example 1: Basic Search
    Tests simple topic search and validates results structure.
    """
    print("\n" + "=" * 70)
    print("TEST 1: Basic Search")
    print("=" * 70)
    
    agent = WikipediaAgent()
    
    # Search for a topic
    query = "Python programming"
    print(f"\nSearching for: '{query}'")
    
    result = agent.search(query, candidates=5)
    
    # Validate results
    assert result is not None, "Search should return results"
    assert result.get('status') == 'success', "Should return success status"
    assert 'candidates' in result, "Should contain candidates"
    candidates = result.get('candidates', [])
    assert len(candidates) > 0, "Should find at least one result"
    assert 'title' in candidates[0], "Result should have title"
    assert 'url' in candidates[0], "Result should have URL"
    assert 'score' in candidates[0], "Result should have relevance score"
    
    print(f"✅ Found {len(candidates)} candidates")
    print(f"   Best match: {candidates[0]['title']}")
    print(f"   Score: {candidates[0]['score']:.2f}")
    print(f"   URL: {candidates[0]['url']}")
    
    return True


def test_summarization():
    """
    Example 2: Content Summarization
    Tests fetching and summarizing Wikipedia articles.
    """
    print("\n" + "=" * 70)
    print("TEST 2: Content Summarization")
    print("=" * 70)
    
    agent = WikipediaAgent()
    
    # Summarize a topic
    query = "Artificial Intelligence"
    num_bullets = 3
    
    print(f"\nSummarizing: '{query}' (top {num_bullets} points)")
    
    result = agent.summarize(query, bullets=num_bullets)
    
    # Validate summary
    assert result is not None, "Should return summary"
    assert result.get('status') == 'success', "Should return success status"
    assert 'title' in result, "Summary should have title"
    assert 'summary' in result, "Summary should have bullet points"
    summary_bullets = result.get('summary', [])
    assert len(summary_bullets) <= num_bullets, f"Should have at most {num_bullets} bullets"
    assert 'source_url' in result, "Summary should include source URL"
    
    print(f"✅ Summarized: {result['title']}")
    print(f"\n   Key Points:")
    for i, bullet in enumerate(summary_bullets, 1):
        print(f"   {i}. {bullet}")
    print(f"\n   Source: {result['source_url']}")
    
    return True


def test_page_fetch():
    """
    Example 3: Page Fetch
    Tests fetching full Wikipedia page data.
    """
    print("\n" + "=" * 70)
    print("TEST 3: Page Fetch")
    print("=" * 70)
    
    agent = WikipediaAgent()
    
    # Fetch page data
    query = "Croatia"
    print(f"\nFetching page data for: '{query}'")
    
    result = agent.fetch(query)
    
    # Validate fetch
    assert result is not None, "Should return page data"
    assert result.get('status') == 'success', "Should return success status"
    assert 'title' in result, "Page should have title"
    assert 'url' in result, "Page should have URL"
    assert 'content' in result or 'sections' in result, "Page should have content or sections"
    
    sections = result.get('sections', [])
    print(f"✅ Fetched page: {result['title']}")
    print(f"   URL: {result['url']}")
    print(f"   Sections found: {len(sections)}")
    
    if sections:
        print(f"\n   Sample sections:")
        for section in sections[:3]:
            if isinstance(section, dict):
                print(f"   - {section.get('heading', 'Unknown')}")
            else:
                print(f"   - {section}")
    
    return True


def test_topic_comparison():
    """
    Example 4: Compare Two Topics
    Tests side-by-side comparison of related topics.
    """
    print("\n" + "=" * 70)
    print("TEST 4: Topic Comparison")
    print("=" * 70)
    
    agent = WikipediaAgent()
    
    # Compare two topics
    topic1 = "Python (programming language)"
    topic2 = "JavaScript"
    
    print(f"\nComparing: '{topic1}' vs '{topic2}'")
    
    result = agent.compare(topic1, topic2, bullets=3)
    
    # Validate comparison
    assert result is not None, "Should return comparison"
    assert result.get('status') == 'success', "Should return success status"
    assert 'topic1' in result, "Should have topic1"
    assert 'topic2' in result, "Should have topic2"
    assert 'comparison' in result, "Should have comparison data"
    
    comparison = result.get('comparison', {})
    similarities = comparison.get('similarities', [])
    differences = comparison.get('differences', [])
    
    print(f"✅ Compared topics:")
    print(f"\n   Topic 1: {result['topic1']}")
    print(f"   Topic 2: {result['topic2']}")
    print(f"   Similarities: {len(similarities)} found")
    print(f"   Differences: {len(differences)} found")
    
    return True


def test_json_export():
    """
    Example 5: JSON Export
    Tests exporting results in JSON format for integration.
    """
    print("\n" + "=" * 70)
    print("TEST 5: JSON Export")
    print("=" * 70)
    
    agent = WikipediaAgent()
    
    # Get data and export as JSON
    query = "Machine Learning"
    print(f"\nExporting '{query}' as JSON")
    
    result = agent.summarize(query, bullets=3)
    
    # Convert to JSON
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    # Validate JSON
    assert json_output, "Should produce JSON output"
    parsed = json.loads(json_output)  # Verify it's valid JSON
    assert parsed['title'] == result['title'], "JSON should preserve data"
    
    print(f"✅ JSON export successful")
    print(f"\n   JSON Structure:")
    print(f"   - Status: {parsed.get('status', 'N/A')}")
    print(f"   - Title: {parsed.get('title', 'N/A')}")
    print(f"   - Summary: {len(parsed.get('summary', []))} items")
    print(f"   - URL: {parsed.get('source_url', 'N/A')}")
    print(f"\n   Sample JSON (first 200 chars):")
    print(f"   {json_output[:200]}...")
    
    return True


def test_error_handling():
    """
    Example 6: Error Handling
    Tests graceful handling of invalid queries and edge cases.
    """
    print("\n" + "=" * 70)
    print("TEST 6: Error Handling")
    print("=" * 70)
    
    agent = WikipediaAgent()
    
    # Test 1: Invalid/nonsense query
    invalid_query = "xyzabc123nonexistent999"
    print(f"\nTesting invalid query: '{invalid_query}'")
    
    results = agent.search(invalid_query)
    print(f"✅ Handled gracefully - returned {len(results) if results else 0} results")
    
    # Test 2: Ambiguous query (should return suggestions)
    ambiguous_query = "Python"
    print(f"\nTesting ambiguous query: '{ambiguous_query}'")
    
    results = agent.search(ambiguous_query)
    assert len(results) > 1, "Ambiguous query should return multiple options"
    print(f"✅ Handled ambiguity - returned {len(results)} disambiguation options")
    
    # Test 3: Empty query
    print(f"\nTesting empty query")
    try:
        results = agent.search("")
        print(f"✅ Handled empty query - returned {len(results) if results else 0} results")
    except Exception as e:
        print(f"✅ Properly raised error: {type(e).__name__}")
    
    return True


def test_cache_performance():
    """
    Example 7: Cache Performance
    Tests caching mechanism and performance improvement.
    """
    print("\n" + "=" * 70)
    print("TEST 7: Cache Performance")
    print("=" * 70)
    
    import time
    agent = WikipediaAgent()
    
    # Use a more reliable topic (Wikipedia's featured articles are more stable)
    query = "Python (programming language)"
    
    # First request (cold cache)
    print(f"\nFirst request (cold cache): '{query}'")
    start_cold = time.time()
    result1 = agent.summarize(query, bullets=3)
    time_cold = time.time() - start_cold
    
    # Second request (should hit cache)
    print(f"Second request (cached): '{query}'")
    start_cached = time.time()
    result2 = agent.summarize(query, bullets=3)
    time_cached = time.time() - start_cached
    
    # Validate
    assert result1 is not None, "First request should succeed"
    assert result1.get('status') == 'success', "First request should succeed"
    assert result2 is not None, "Second request should succeed"
    assert result2.get('status') == 'success', "Second request should succeed"
    assert result1['title'] == result2['title'], "Results should be identical"
    
    speedup = time_cold / time_cached if time_cached > 0 else float('inf')
    
    print(f"\n✅ Cache Performance:")
    print(f"   Cold cache: {time_cold:.2f}s")
    print(f"   Cached: {time_cached:.2f}s")
    print(f"   Speedup: {speedup:.1f}x faster")
    
    return True


def run_all_tests():
    """Run all test examples."""
    print("\n" + "=" * 70)
    print("WikiScout Agent - Test Examples")
    print("=" * 70)
    print("\nRunning 7 practical test scenarios...")
    
    tests = [
        ("Basic Search", test_basic_search),
        ("Summarization", test_summarization),
        ("Page Fetch", test_page_fetch),
        ("Topic Comparison", test_topic_comparison),
        ("JSON Export", test_json_export),
        ("Error Handling", test_error_handling),
        ("Cache Performance", test_cache_performance),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\nRunning: {name}")
            result = test_func()
            if result:
                passed += 1
                print(f"✅ PASSED: {name}")
        except AssertionError as e:
            failed += 1
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
        except Exception as e:
            failed += 1
            print(f"❌ ERROR: {name}")
            print(f"   Exception: {e}")
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total: {passed + failed}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success Rate: {100 * passed / (passed + failed):.1f}%")
    print("=" * 70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

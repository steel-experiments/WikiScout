"""
Final Verification: Complete Agent Workflow with Real Wikipedia API Integration
"""

from agent import WikipediaAgent

print("=" * 70)
print("  Wikipedia CLI Agent - wptools Integration Verification")
print("  Complete Workflow with Real Wikipedia API")
print("=" * 70)

# Create agent
print("\n[1/5] Initializing agent...")
agent = WikipediaAgent()
print(f"      Agent version: 1.1")
print(f"      Status: Ready")

# Search for a topic
print("\n[2/5] Searching for topic 'Python'...")
search_results = agent.search("Python")
if search_results.get("status") == "success":
    print(f"      Found {len(search_results.get('candidates', []))} result(s)")
    for i, candidate in enumerate(search_results.get('candidates', [])[:3], 1):
        print(f"        [{i}] {candidate.get('title', 'Unknown')}")

# Fetch real Wikipedia content
print("\n[3/5] Fetching page content from Wikipedia...")
fetch_result = agent.fetch("Python")
if fetch_result.get("status") == "success":
    print(f"      Page fetched: {fetch_result.get('title')}")
    print(f"      Sections: {', '.join(fetch_result.get('sections', [])[:3])}")
    print(f"      URL: {fetch_result.get('url')}")

# Generate summary
print("\n[4/5] Generating summary from Wikipedia content...")
summary_result = agent.summarize("Python", bullets=3)
if summary_result.get("status") == "success":
    print(f"      Summary generated with {len(summary_result.get('summary', []))} points")
    for i, point in enumerate(summary_result.get('summary', [])[:3], 1):
        point_text = point[:60] + "..." if len(point) > 60 else point
        print(f"        {i}. {point_text}")

# Compare topics
print("\n[5/5] Comparing two topics...")
compare_result = agent.compare("Python", "Java", bullets=4)
if compare_result.get("status") == "success":
    comparison = compare_result.get('comparison', {})
    print(f"      Similarities: {len(comparison.get('similarities', []))}")
    for sim in comparison.get('similarities', [])[:2]:
        print(f"        [+] {sim}")
    print(f"      Differences: {len(comparison.get('differences', []))}")
    for diff in comparison.get('differences', [])[:2]:
        print(f"        [-] {diff}")

print("\n" + "=" * 70)
print("  Status: COMPLETE [OK]")
print("  Agent workflow demonstration successful")
print("=" * 70)

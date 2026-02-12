# Wikipedia Research Agent - Practical Examples

Real-world usage scenarios and code examples.

## Example 1: Quick Topic Research

**Scenario:** Student researching photosynthesis for a biology assignment.

```bash
# Search for the page
python agent.py search -q "photosynthesis"

# Output:
# ✓ Search: photosynthesis
#   [1] Photosynthesis (main article) | Score: 1.0
#   [2] Photosynthetic membrane | Score: 0.42
#   [3] Photosynthesis and chemosynthesis | Score: 0.28

# Get a 5-point summary
python agent.py summarize -q "Photosynthesis" --bullets 5

# Output:
# ✓ Summary: Photosynthesis
#   Source: https://en.wikipedia.org/wiki/Photosynthesis
#
#   1) Plants convert light energy into chemical energy
#   2) Light reactions occur in thylakoid membranes of chloroplasts
#   3) Calvin cycle fixes CO₂ in the stroma to produce glucose
#   4) Rate affected by light intensity, CO₂ concentration, temperature
#   5) Essential for oxygen production and food chains
```

## Example 2: Extracting Structured Data

**Scenario:** Data analyst needs population statistics for 10 countries.

```bash
# Extract infobox for multiple countries
countries=("France" "Japan" "Brazil" "India" "Nigeria")

for country in "${countries[@]}"; do
  python agent.py infobox -q "$country" --format json | \
    jq '.infobox.fields | {Country: input_filename, Capital, Population, Area}'
done

# Output (JSON):
# {
#   "Country": "France",
#   "Capital": "Paris",
#   "Population": "67,970,000",
#   "Area": "643,801 km²"
# }
# ...
```

## Example 3: Topic Comparison

**Scenario:** Developer comparing Python vs JavaScript for a blog post.

```bash
# Get detailed comparison
python agent.py compare "Python (programming language)" "JavaScript" --bullets 7

# Output:
# ✓ Comparison: Python vs JavaScript
#
# SIMILARITIES:
#   • Both are high-level interpreted languages
#   • Support object-oriented and functional programming
#   • Have dynamic typing
#   • Popular for education and rapid development
#
# DIFFERENCES:
#   • Python: Server-side focus; JavaScript: Browser-native
#   • Python: Whitespace-sensitive syntax; JavaScript: Brace-delimited
#   • Python: Single-threaded; JavaScript: Event-driven async
#   • Python: Data science focus; JavaScript: Web focus
```

## Example 4: JSON Export for Automation

**Scenario:** CI/CD pipeline needs machine-readable research data.

```bash
# Get JSON output
python agent.py search -q "machine learning" --format json > /tmp/ml_search.json

# Use in Python script
python - << 'EOF'
import json
import subprocess

result = subprocess.run(
    ["python", "agent.py", "search", "-q", "neural networks", "--format", "json"],
    capture_output=True, text=True
)

data = json.loads(result.stdout)
print(f"Found {len(data['candidates'])} candidates")
for candidate in data['candidates']:
    print(f"  • {candidate['title']} (score: {candidate['score']})")
EOF

# Output:
# Found 5 candidates
#   • Artificial neural network (score: 1.0)
#   • Convolutional neural network (score: 0.92)
#   • Neural network (disambiguation) (score: 0.85)
#   ...
```

## Example 5: PowerShell Integration

**Scenario:** Windows user building a knowledge base system.

```powershell
# Search and process in PowerShell
$topics = @("Quantum computing", "Blockchain", "Climate change")

foreach ($topic in $topics) {
    Write-Host "Researching: $topic"
    
    $result = python agent.py summarize -q $topic --bullets 3 --format json | ConvertFrom-Json
    
    $output = @{
        Title = $result.title
        Summary = $result.bullets | Select-Object -ExpandProperty text
        URL = $result.source_url
        Timestamp = $result.timestamp
    }
    
    $output | ConvertTo-Json | Out-File "research_$($topic -replace ' ', '_').json"
}

Write-Host "Research complete!"
```

## Example 6: Batch Processing

**Scenario:** Researcher needs summaries for 100 Wikipedia articles.

```bash
#!/bin/bash
# Batch summarize from a list

topics_file="topics.txt"  # One topic per line
output_file="summaries.md"

while IFS= read -r topic; do
    echo "Processing: $topic"
    
    # Get summary in JSON
    result=$(python agent.py summarize -q "$topic" --bullets 5 --format json)
    
    # Extract title and bullets
    title=$(echo "$result" | jq -r '.title')
    bullets=$(echo "$result" | jq -r '.summary[]' | sed 's/^/  - /')
    
    # Append to output
    {
        echo "## $title"
        echo "$bullets"
        echo ""
    } >> "$output_file"
    
done < "$topics_file"

echo "Output saved to $output_file"
```

## Example 7: Disambiguation Handling

**Scenario:** Handling ambiguous queries gracefully.

```bash
# Query with ambiguous term
python agent.py search -q "Mercury" --limit 5

# Output:
# ? Multiple matches found for "Mercury":
#   [1] Mercury (element) - Chemical element, atomic number 80
#   [2] Mercury (planet) - Smallest planet in solar system  
#   [3] Mercury (mythology) - Roman god of commerce
#   [4] Mercury (automobile) - Defunct American car brand
#   [5] Mercury (Freddie) - Queen lead singer

# User selects option [2]
python agent.py summarize -q "Mercury (planet)" --bullets 4

# Output:
# ✓ Summary: Mercury (planet)
#   Source: https://en.wikipedia.org/wiki/Mercury_(planet)
#
#   1) Smallest planet in solar system
#   2) Closest to sun with extreme temperature variations
#   3) No atmosphere; surface heavily cratered
#   4) Named after Roman messenger god
```

## Example 8: Error Handling

**Scenario:** Handling various error conditions.

```bash
# Typo in query
python agent.py search -q "Photosynthezis"

# Output:
# ✗ Page not found: "Photosynthezis"
#   Did you mean: Photosynthesis? [y/n]
#   Or try: Photosynthesis (process), Photosynthetic organisms

# Non-existent page
python agent.py summarize -q "XyZzzyNotARealPage123"

# Output:
# ✗ Cannot summarize: Page not found
#   Suggestions: Check spelling or try a more specific query

# Network timeout (auto-retried)
python agent.py summarize -q "Large topic" --timeout 60

# Output:
# ℹ Fetching page (no cache)... attempt 1/3
# ⚠ Steel API timeout, falling back to wptools...
# ✓ Page retrieved via wptools (8s)
```

## Example 9: Cache Management

**Scenario:** Understanding and managing the cache.

```bash
# Check agent status (includes cache info)
python agent.py status

# Output:
# Wikipedia Research Agent Status
#
# Configuration:
#   Language: en
#   Cache TTL: 3600 seconds
#   Timeout: 30 seconds
#
# Cache Statistics:
#   Total cached pages: 12
#   Cache size: 2.3 MB
#   Cache hit rate: 87%
#   Performance improvement: 50x (cache vs cold fetch)
#
# Recent searches:
#   ✓ Photosynthesis (cached 2h ago)
#   ✓ Python (programming) (cached 5m ago)
#   ✗ NonExistentPage (failed 10m ago)

# To clear cache
rm -rf cache/  # Remove all cached pages
python agent.py status  # Cache rebuilt as needed
```

## Example 10: Glossary Extraction

**Scenario:** Extract key terminology for domain understanding.

```bash
# Get glossary from a technical article
python agent.py summarize -q "Machine learning" --bullets 10 --format json | \
  jq '.glossary | map(.term) | .[0:10]'

# Output:
# [
#   "machine learning",
#   "artificial intelligence",
#   "algorithm",
#   "neural network",
#   "training data",
#   "classification",
#   "supervised learning",
#   "unsupervised learning",
#   "model",
#   "optimization"
# ]
```

## Example 11: Academic Citation Generation

**Scenario:** Generate proper citations for Wikipedia sources.

```bash
# Get article metadata for citation
python agent.py search -q "Climate change" --format json | \
  jq '.candidates[0] | {title, url, accessed: now | todate}'

# Store for citation management
python agent.py summarize -q "Climate change" --bullets 5 --format json | \
  jq '{
    title: .title,
    url: .source_url,
    accessed_date: now | todate,
    reference_count: (.bullets | length)
  }' > citation_data.json
```

## Example 12: Real-Time Research Workflow

**Scenario:** Interactive research session combining multiple queries.

```bash
#!/bin/bash
# Multi-step research workflow

main_topic="Renewable energy"

echo "=== Researching: $main_topic ==="

# 1. Get overview
echo -e "\n## Overview ##"
python agent.py summarize -q "$main_topic" --bullets 3

# 2. Find related topics
echo -e "\n## Related Topics ##"
python agent.py search -q "$main_topic" --limit 3 | \
  grep "^\s*\[" | sed 's/\[.\] /  • /'

# 3. Compare specific types
echo -e "\n## Solar vs Wind ##"
python agent.py compare "Solar energy" "Wind power" --bullets 4

# 4. Extract key statistics
echo -e "\n## Key Statistics ##"
python agent.py infobox -q "Solar energy" --format json | \
  jq '.infobox.fields | to_entries[] | "\(.key): \(.value)"'

echo -e "\n=== Research complete ===" 
```

## Example 13: Integration with External Tools

**Scenario:** Feeding Wikipedia data into other applications.

```python
#!/usr/bin/env python3
import subprocess
import json
from pathlib import Path

class WikipediaResearcher:
    def search(self, query: str) -> dict:
        """Search Wikipedia and return JSON."""
        result = subprocess.run(
            ["python", "agent.py", "search", "-q", query, "--format", "json"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)
    
    def summarize(self, topic: str, bullets: int = 5) -> dict:
        """Get summary as dictionary."""
        result = subprocess.run(
            ["python", "agent.py", "summarize", "-q", topic, 
             "--bullets", str(bullets), "--format", "json"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)

# Usage
researcher = WikipediaResearcher()

# Search
results = researcher.search("Artificial intelligence")
print(f"Found {len(results['candidates'])} results")

# Summarize
summary = researcher.summarize("Artificial intelligence", bullets=5)
print(f"\n{summary['title']}:")
for bullet in summary['summary']:
    print(f"  • {bullet}")
```

## Example 14: Performance Monitoring

**Scenario:** Monitoring response times for optimization.

```bash
#!/bin/bash
# Benchmark different operations

echo "Performance Benchmarks"
echo "====================="

# Test cold cache (first run)
echo -e "\nCold cache (first fetch):"
time python agent.py summarize -q "Physics" > /dev/null

# Test warm cache (second run)
echo -e "\nWarm cache:"
time python agent.py summarize -q "Physics" > /dev/null

# Test parallel vs sequential
echo -e "\nComparison (parallel):"
time python agent.py compare "Classical mechanics" "Quantum mechanics" > /dev/null

# Test JSON parsing overhead
echo -e "\nJSON output:"
time python agent.py search -q "Chemistry" --format json > /dev/null
```

---

## Tips & Best Practices

### Performance Tips
1. **Use caching:** Run same query twice to see 50x improvement
2. **Cache warming:** Pre-fetch frequently-used topics during off-peak
3. **Batch queries:** Process multiple topics in parallel scripts
4. **JSON mode:** Use `--format json` for faster parsing

### Reliability Tips
1. **Fallback handling:** Agent automatically retries on timeout
2. **Error checking:** Always check exit codes in scripts
3. **Disambiguation:** Use search first for ambiguous terms
4. **Rate limiting:** Keep queries under 100/hour for stability

### Integration Tips
1. **Use JSON:** Easiest for automation and data pipelines
2. **Subprocess:** Call via Python subprocess for direct integration  
3. **Error handling:** Wrap calls in try-except for robustness
4. **Logging:** Capture both stdout (results) and stderr (logs)

---

**Last Updated:** February 12, 2026
**For more help:** See SKILL.md for command reference and MODULE_REFERENCE.md for technical details.

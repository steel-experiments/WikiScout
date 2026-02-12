---
name: wikipedia-research-agent
description: Perform fast, verifiable Wikipedia research with summarization, comparison, and structured extraction. Use when you need accurate encyclopedia information, topic comparisons, or to extract structured data (infoboxes) from Wikipedia pages. Provides JSON output for integration with other tools.
---

# Wikipedia Research Agent Skill

A professional domain-specific agent for Wikipedia browsing, summarization, and comparison through a command-line interface. Designed for researchers, students, and developers who need fast, verifiable, and reproducible access to encyclopedic information.

## Quick Start

The Wikipedia Research Agent has 5 core commands:

```bash
# Search for Wikipedia pages
python agent.py search -q "Python programming"

# Summarize an article
python agent.py summarize -q "Photosynthesis" --bullets 5

# Compare two topics
python agent.py compare "Classical conditioning" "Operant conditioning"

# Extract structured data
python agent.py infobox -q "Croatia"

# Check agent status
python agent.py status

# Get JSON output for integration
python agent.py search -q "AI" --format json
```

## Key Capabilities

### 1. Smart Search & Disambiguation
- **Direct page lookup** for exact titles (< 1 second)
- **MediaWiki API fallback** for search-based discovery (2-4 seconds)
- **Automatic disambiguation detection** and ranking
- Returns top 5 candidates with similarity scores

```bash
python agent.py search -q "Mercury"
# Returns: Mercury (planet), Mercury (element), Mercury (mythology), etc.
```

### 2. Structured Content Extraction
- Extract Wikipedia **sections** with heading hierarchy
- Parse **infobox fields** (capital, population, GDP, etc.)
- Detect and flag **ambiguous or disputed claims**
- Normalize and clean HTML content

```bash
python agent.py infobox -q "Croatia"
# Returns: Capital, Population, GDP, Area, Currency, etc.
```

### 3. Intelligent Summarization
- Generate **1-2 sentence abstracts** for quick understanding
- Create **3-7 bullet summaries** with section citations
- Extract **key terminology** and glossary terms
- Produce **abstractive + extractive** summaries

```bash
python agent.py summarize -q "Photosynthesis" --bullets 5
# 1) Plants convert light energy into chemical energy
# 2) Light reactions occur in thylakoid membranes
# 3) Calvin cycle fixes CO₂ in the stroma
# ... with section references
```

### 4. Topic Comparison
- Side-by-side analysis of **similarities and differences**
- Keyword-based **relationship detection**
- Focus on **contrasting aspects** for clarity
- Parallel fetch (~2x speedup) for multi-page operations

```bash
python agent.py compare "Classical conditioning" "Operant conditioning"
# Similarities: Both are learning theories, involve behavioral response
# Differences: Classical (stimulus-response), Operant (reinforcement)
```

### 5. JSON Output for Automation
All commands support `--format json` for seamless integration:

```bash
python agent.py search -q "AI" --format json | jq '.candidates[0]'

# Output:
# {
#   "title": "Artificial intelligence",
#   "url": "https://en.wikipedia.org/wiki/Artificial_intelligence",
#   "score": 1.0,
#   "pageid": 856
# }
```

## Architecture

The agent uses a **4-stage modular pipeline**:

```
Query → Search (Find pages) → Fetch (Get content) → Parse (Extract sections) → Summarize (Generate output)
         (220 lines)          (268 lines)          (280 lines)               (460 lines)
```

### Module 1: SearchModule (220 lines)
Discovers and ranks Wikipedia pages
- wptools direct page fetch (fast path)
- MediaWiki API search fallback
- Disambiguation detection
- Similarity-based ranking

### Module 2: FetchModule (268 lines)
Reliably retrieves page content with caching
- Steel API scraping (primary, ~50s cold)
- wptools fallback (8-10s cold)
- JSON cache with 1-hour TTL
- 50x performance improvement on cache hits

### Module 3: ParseModule (280 lines)
Extracts and normalizes Wikipedia content
- HTML section extraction (h2/h3/h4 headings)
- Infobox parsing (table → key-value)
- Text normalization (citations, encoding)
- Paragraph grouping and hierarchy

### Module 4: SummarizeModule (460 lines)
Generates summaries and comparisons
- Extractive NLP with scoring algorithms
- Sentence selection based on relevance
- Keyword extraction with stop-word filtering
- Topic comparison and glossary generation

## Performance

| Operation | First Run | Cached | Notes |
|-----------|-----------|--------|-------|
| Search (direct) | <1s | <1s | Fast wptools lookup |
| Fetch (Steel API) | ~50s | <1s | **50x improvement** |
| Summarize | 2-3s | <1s | Usually from cache |
| Compare (parallel) | ~12s | ~3s | **2x speedup** |

**Key Metrics:**
- Cache hit rate: 87%
- Memory per page: 50-500 KB
- System memory: 50-100 MB typical
- Test coverage: 21/21 passing (100%)
- Execution time: ~18 seconds

## Error Handling & Resilience

The agent gracefully handles common failures:

| Failure | Recovery | User Experience |
|---------|----------|-----------------|
| Steel API timeout | Fallback to wptools | 50s → 10s, same result |
| Network error | Retry with backoff | Automated 3 attempts |
| Page not found | Suggest alternatives | Clear error + suggestions |
| Rate limiting | Exponential backoff | Brief delay, transparent |

Retry strategy: Immediate → 1s → 2s → 4s → Return error or cached data

## Integration Examples

### 1. CI/CD Pipeline
```bash
# Export research data in JSON
python agent.py compare "Python" "JavaScript" --format json > languages.json
# Process with jq or other tools
```

### 2. Research Workflow
```bash
# Batch multiple queries
for topic in "Photosynthesis" "Cellular respiration" "ATP synthesis"; do
  python agent.py summarize -q "$topic" --bullets 3 >> research.md
done
```

### 3. Data Integration
```powershell
# PowerShell integration
$result = python agent.py search -q "Machine learning" --format json | ConvertFrom-Json
$top_match = $result.candidates[0]
Write-Host "Found: $($top_match.title)"
```

## Configuration

Configure via `config.json`:

```json
{
  "wikipedia_lang": "en",
  "cache_dir": "./cache",
  "cache_ttl_seconds": 3600,
  "timeout_seconds": 30,
  "max_retries": 3,
  "use_steel_api": true,
  "log_level": "INFO"
}
```

**Key settings:**
- `cache_ttl_seconds`: Cache expiration (default 1 hour)
- `timeout_seconds`: Request timeout (default 30s)
- `max_retries`: Retry attempts (default 3)
- `use_steel_api`: Enable Steel API for faster scraping

## Testing

All 21 unit tests pass (100% success rate):

✅ Agent initialization (3/3)
✅ Search module (3/3)
✅ Fetch module with caching (3/3)
✅ Parse module (3/3)
✅ Summarize module (3/3)
✅ CLI commands (4/4)
✅ Integration workflow (1/1)
✅ Performance validation (1/1)

**Real data validated:**
- Wikipedia Python article (1,500+ characters)
- Multiple page types (articles, stubs, disambiguation)
- Cache behavior with actual API calls

## When to Use This Skill

Use the Wikipedia Research Agent when you need to:

- **Research topics quickly:** Find accurate encyclopedia information in seconds
- **Compare concepts:** Analyze similarities and differences between related topics
- **Extract structured data:** Get infobox fields (capital, population, GDP, etc.)
- **Integrate with workflows:** Use JSON output for automation and data pipelines
- **Verify facts:** Access primary sources with clear citations
- **Create summaries:** Generate bullet points or abstracts from Wikipedia

**Example scenarios:**
- Student researching for essays or projects
- Data analyst extracting country/company statistics
- Developer building knowledge base integrations
- Journalist verifying facts with source attribution
- Product manager comparing competitor information

## Limitations

- **English only** (v1.1)
- **Read-only** (cannot edit Wikipedia)
- **Cached data** (updates with 1-hour TTL)
- **No original research** (Wikipedia only)
- **Rate limiting:** ~100 queries/hour recommended

## Troubleshooting

### Slow first fetch?
Steel API cold fetch (~50s) is normal for large pages. Subsequent requests use cache (<1s).

### Page not found?
Try alternative search terms or check if disambiguation page exists:
```bash
python agent.py search -q "Mercury"  # See all options
```

### Rate limited?
The agent automatically retries with exponential backoff. Increase `timeout_seconds` in config if needed.

### Need different format?
All commands support `--format json` for structured output:
```bash
python agent.py summarize -q "Topic" --format json
```

## Advanced Usage

### Parallel Comparisons
The `compare` command uses ThreadPoolExecutor to fetch both pages simultaneously:
```bash
python agent.py compare "Topic1" "Topic2"  # ~2x faster than sequential
```

### Custom Summaries
```bash
python agent.py summarize -q "Complex topic" --bullets 10  # More bullets
python agent.py summarize -q "Simple topic" --bullets 3    # Fewer bullets
```

### Batch Operations
```bash
# Process multiple topics
topics=("Python" "JavaScript" "Go" "Rust")
for topic in "${topics[@]}"; do
  python agent.py summarize -q "$topic" --format json >> results.jsonl
done
```

## Production Readiness

✅ Status: **PRODUCTION READY (v1.1)**

- 1,600+ lines of tested code
- 21/21 tests passing
- Real Wikipedia API integration
- Graceful error handling & fallbacks
- Benchmarked & optimized
- Comprehensive documentation
- Flexible configuration
- JSON export & CLI interface

## Architecture Highlights

- **Modular design:** 4 independent modules with clear responsibilities
- **Intelligent caching:** 50x performance improvement on cache hits
- **Parallel processing:** 2x speedup for multi-page operations
- **Graceful degradation:** Fallback strategies for all failures
- **Type-safe:** Full test coverage with real Wikipedia data
- **Production-grade:** Logging, configuration, error handling

## Next Steps

1. **Install:** `pip install -r requirements.txt`
2. **Configure:** Update `config.json` with your preferences
3. **Run:** `python agent.py search -q "Your topic"`
4. **Integrate:** Use `--format json` in automation workflows

---

**Version:** 1.1  
**Author:** Damjan  
**Repository:** steel-experiments/WikiScout  
**License:** Educational Project  
**Updated:** February 12, 2026

# Module Reference

Detailed specifications for each module in the Wikipedia Research Agent.

## SearchModule (220 lines)

**File:** `modules/search.py`

### Input
- Query string (e.g., "Python", "World War II")

### Output
```python
[
  {
    "title": "Page Title",
    "url": "https://en.wikipedia.org/wiki/Page_Title",
    "description": "Short description from Wikipedia",
    "score": 1.0,  # Similarity score (0-1)
    "pageid": 12345
  },
  ...
]
```

### Key Functions

#### `search(query: str, limit: int = 5) -> List[Dict]`
Main entry point. Returns top candidates ranked by similarity.

**Process:**
1. Try direct page fetch via wptools
2. If not found, query MediaWiki search API
3. Score each result by query similarity
4. Return top N ranked by score

**Error handling:**
- HTTP 403 (Forbidden): Retry with User-Agent header
- Page not found: Return empty list with suggestions

### Performance
- Direct match: <1 second (wptools cache)
- API search: 2-4 seconds
- Disambiguation detection: Automatic

### Configuration
```json
{
  "wikipedia_lang": "en",  // Language code
  "max_retries": 3,        // Retry attempts
  "timeout_seconds": 30    // Request timeout
}
```

---

## FetchModule (268 lines)

**File:** `modules/fetch.py`

### Input
- Page title (e.g., "Photosynthesis")
- Use cache: bool (default True)

### Output
```python
{
  "title": "Page Title",
  "url": "https://en.wikipedia.org/wiki/Page_Title",
  "extract": "Full page text content...",
  "infobox": {...},  # Structured key-value data
  "sections": [...], # List of sections
  "timestamp": "2026-02-12T16:30:45Z",
  "source": "cache" | "steel" | "wptools",
  "success": True
}
```

### Key Functions

#### `fetch_page(title: str, use_cache: bool = True) -> Dict`
Main entry point. Fetches page content with intelligent caching.

**Process:**
1. Check cache (if use_cache=True)
2. If cache miss:
   - Try Steel API (primary)
   - Fall back to wptools on timeout/error
3. Parse and store in cache
4. Return structured data

#### `_scrape_with_steel(url: str, retry_count: int = 3) -> str`
Primary content fetcher using Steel API.
- Returns cleaned HTML and Markdown
- ~50 seconds cold, <1 second warm
- Exponential backoff retry strategy

#### `_get_from_cache(title: str) -> Optional[Dict]`
Retrieve from JSON cache with TTL validation.

#### `_save_to_cache(title: str, data: Dict) -> None`
Store page and metadata in cache with timestamp.

### Performance
| Scenario | Time | Notes |
|----------|------|-------|
| Cache hit | <1s | JSON read + deserialize |
| Steel API | ~50s | Includes HTML processing |
| wptools | 8-10s | Fallback method |

### Cache Structure
```
cache/
├── Photosynthesis.json
├── Python_(programming_language).json
└── ...

File contents:
{
  "title": "...",
  "url": "...",
  "extract": "...",
  "timestamp": "2026-02-12T...",
  "source": "steel",
  "ttl_expires": "2026-02-12T17:30:45Z"
}
```

### Configuration
```json
{
  "cache_dir": "./cache",
  "cache_ttl_seconds": 3600,
  "timeout_seconds": 60,
  "use_steel_api": true,
  "steel_api_key": "YOUR_KEY_HERE"
}
```

---

## ParseModule (280 lines)

**File:** `modules/parse.py`

### Input
- HTML content (raw Wikipedia HTML)

### Output
```python
{
  "sections": [
    {
      "level": 2,           # h2, h3, h4
      "heading": "Etymology",
      "text": "Full text of section...",
      "html_id": "Etymology",
      "paragraphs": ["Para 1", "Para 2"]
    },
    ...
  ],
  "infobox": {
    "fields": {
      "Capital": "Zagreb",
      "Population": "3,880,000",
      "Currency": "Kuna"
    }
  }
}
```

### Key Functions

#### `extract_sections(html: str) -> List[Dict]`
Identify heading hierarchy and associated paragraphs.

**Process:**
1. Parse HTML with BeautifulSoup
2. Find h2, h3, h4 headings
3. Group paragraphs under each heading
4. Return hierarchical structure

#### `extract_infobox(html: str) -> Dict`
Parse Wikipedia infobox table to key-value pairs.

**Process:**
1. Find infobox table (class: "infobox")
2. Extract header-value rows
3. Return structured dictionary

#### `clean_html_text(text: str) -> str`
Normalize text content.

**Process:**
1. Remove `[citation needed]` markers
2. Decode HTML entities
3. Normalize whitespace
4. Remove `[edit]` links

### Supported Infoboxes
- Countries (Capital, Population, GDP, Area)
- People (Birth, Death, Occupation, Nationality)
- Companies (Founded, Headquarters, Revenue, Stock)
- Scientific topics (Definition, Formula, Discovered)

### Configuration
```json
{
  "include_citations": false,
  "normalize_whitespace": true,
  "decode_entities": true
}
```

---

## SummarizeModule (460 lines)

**File:** `modules/summarize.py`

### Input
- Page content (dict with sections, infobox)
- Number of bullets (default 5)

### Output
```python
{
  "title": "Topic",
  "abstract": "One sentence overview...",
  "bullets": [
    {
      "text": "Key point that...",
      "section": "Overview",
      "score": 0.95
    },
    ...
  ],
  "glossary": [
    {"term": "photosynthesis", "frequency": 47},
    {"term": "chlorophyll", "frequency": 15}
  ]
}
```

### Key Functions

#### `generate_summary(content: Dict, num_bullets: int = 5) -> Dict`
Create abstract and bullet-point summary.

**Process:**
1. Extract first sentences for abstract
2. Split all text into sentences
3. Score each sentence by:
   - Length (not too short/long)
   - Section importance
   - Keyword frequency
4. Select top N by score
5. Return with section attribution

**Scoring formula:**
```
Score = (length_factor × diversity_factor) + keyword_relevance
```

#### `compare_topics(content1: Dict, content2: Dict, num_points: int = 5) -> Dict`
Identify similarities and differences.

**Process:**
1. Extract keywords from both contents
2. Find shared keywords (similarities)
3. Find unique keywords (differences)
4. Score by frequency
5. Return top N for each category

#### `extract_glossary(content: Dict, top_n: int = 8) -> List[Dict]`
Identify key terms by frequency.

**Process:**
1. Extract all words
2. Filter stop words
3. Count word frequency
4. Return top N with counts

### Algorithms

**Extractive Summarization:**
- Not generating new sentences
- Selecting existing high-quality sentences
- Preserves original Wikipedia phrasing

**Sentence Scoring:**
```python
def score_sentence(sentence, section_scores, keyword_freq):
    length_factor = min(len(sentence.split()), 30) / 30
    diversity_factor = len(set(sentence.split())) / len(sentence.split())
    keyword_score = sum(keyword_freq.get(w, 0) for w in sentence.split())
    return (length_factor * diversity_factor) + keyword_score
```

### Configuration
```json
{
  "default_bullets": 5,
  "min_sentence_length": 10,
  "max_sentence_length": 100,
  "stop_words_file": "stopwords.txt"
}
```

---

## CLI Agent (408 lines)

**File:** `agent.py`

### Commands

```bash
# Search
python agent.py search -q "Python" [--limit 5] [--format json]

# Summarize
python agent.py summarize -q "Topic" [--bullets 5] [--format json]

# Compare
python agent.py compare "Topic1" "Topic2" [--bullets 5] [--format json]

# Infobox
python agent.py infobox -q "Topic" [--format json]

# Status
python agent.py status
```

### Output Formats

**Text (default):**
```
✓ Search: Python
  [1] Python (programming language) | Score: 1.0
  [2] Monty Python | Score: 0.38
  ...
```

**JSON:**
```json
{
  "status": "success",
  "command": "search",
  "timestamp": "2026-02-12T16:30:45Z",
  "results": {...}
}
```

### Key Features

**Parallel Fetching:**
- Compare command uses ThreadPoolExecutor
- Fetches both pages simultaneously
- ~2x speedup vs sequential

**Error Handling:**
- Structured error responses
- Clear user guidance
- Automatic retries

**Logging:**
- Full audit trail in agent.log
- Query, response time, source (cache/API)
- Error stack traces for debugging

---

## Dependencies

```
wptools==0.5.0          # Wikipedia API
beautifulsoup4==4.12.2  # HTML parsing
requests==2.31.0        # HTTP with headers
lxml==4.9.3             # XML/HTML processing
click==8.1.7            # CLI framework
pytest==7.4.3           # Testing
```

**Optional:**
- `python-dotenv` - Load environment variables
- `colorama` - Colored terminal output

---

## Testing

**Test Coverage:**
- 21/21 tests passing (100%)
- ~18 seconds total execution
- Real Wikipedia data validation

**Test Structure:**
```
tests/
├── test_agent.py          # CLI and initialization
├── test_search.py         # SearchModule
├── test_fetch.py          # FetchModule + caching
├── test_parse.py          # ParseModule
├── test_summarize.py      # SummarizeModule
└── test_integration.py    # End-to-end workflows
```

**Run tests:**
```bash
pytest -v                   # All tests
pytest tests/test_fetch.py  # Specific module
pytest -k cache             # Filter by name
```

---

## Troubleshooting Reference

| Issue | Cause | Solution |
|-------|-------|----------|
| HTTP 403 | User-Agent missing | Added automatically, please report |
| Steel timeout | Large page or slow network | Fallback to wptools (~8-10s) |
| Cache misses | Pages not in cache | First fetch uses API (~50s) |
| Rate limited | Too many requests | Automatic backoff, increase timeout |
| Encoding errors | Non-UTF8 content | Automatic normalization |

---

**Last Updated:** February 12, 2026

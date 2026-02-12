"""Test wptools integration with fetch.py"""

from modules.fetch import FetchModule

# Create fetch module instance
config = {
    'cache_dir': '.cache',
    'cache_ttl': 3600,
    'max_retries': 3,
    'lang': 'en'
}

fetch = FetchModule(config)

# Test fetch with real Wikipedia
print('[TEST] Fetching Python page from Wikipedia...')
result = fetch.fetch_page('Python_(programming_language)', use_cache=False)

if result.get('success'):
    print(f'[OK] Fetched: {result["title"]}')
    print(f'     URL: {result["url"]}')
    print(f'     Extract length: {len(result.get("extract", ""))} chars')
    print(f'     Sections: {result.get("sections", [])}')
    print(f'     Source: {result.get("source")}')
    print()
    print('[SAMPLE EXTRACT]')
    extract = result.get('extract', '')
    sample = extract[:300] + ('...' if len(extract) > 300 else '')
    print(sample)
else:
    print(f'[ERROR] {result.get("error")}')

# Test caching
print()
print('[TEST] Testing cache...')
result2 = fetch.fetch_page('Python_(programming_language)', use_cache=True)
if result2.get('success'):
    print('[OK] Cache retrieval successful')
    print(f'     Title: {result2["title"]}')
else:
    print(f'[ERROR] Cache retrieval failed')

# Test cache stats
print()
print('[TEST] Cache statistics:')
stats = fetch.get_cache_stats()
print(f'     Cached pages: {stats["cached_pages"]}')
print(f'     Cache size: {stats["cache_size_kb"]:.1f} KB')

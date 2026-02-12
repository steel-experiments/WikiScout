"""Debug search functionality"""

from modules.search import SearchModule
import json

config = {
    'cache_dir': '.cache',
    'cache_ttl_seconds': 3600,
    'max_retries': 3,
    'wikipedia_lang': 'en'
}

search = SearchModule(config)

print('[TEST] Searching for "Python"...')
try:
    results = search.search("Python")
    print(f'[RESULTS] {len(results)} candidate(s)')
    for r in results:
        print(f'  - {r.get("title")}: {r.get("score")}')
    print(json.dumps(results[:1], indent=2))
except Exception as e:
    print(f'[ERROR] {e}')
    import traceback
    traceback.print_exc()

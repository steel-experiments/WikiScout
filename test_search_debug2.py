"""Debug search functionality - more details"""

from modules.search import SearchModule
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

config = {
    'cache_dir': '.cache',
    'cache_ttl_seconds': 3600,
    'max_retries': 3,
    'wikipedia_lang': 'en'
}

search = SearchModule(config)

print('[TEST 1] Direct search for "Python"...')
try:
    direct = search._search_direct("Python", 5)
    print(f'[DIRECT] Got {len(direct)} result(s)')
    if direct:
        print(f'  - {direct[0].get("title")}')
except Exception as e:
    print(f'[DIRECT ERROR] {e}')
    import traceback
    traceback.print_exc()

print('\n[TEST 2] MediaWiki search for "Python"...')
try:
    mediawiki = search._search_mediawiki("Python", 5)
    print(f'[MEDIAWIKI] Got {len(mediawiki)} result(s)')
    if mediawiki:
        print(f'  - {mediawiki[0].get("title")}')
except Exception as e:
    print(f'[MEDIAWIKI ERROR] {e}')
    import traceback
    traceback.print_exc()

print('\n[TEST 3] Full search...')
try:
    results = search.search("Python")
    print(f'[FULL] Got {len(results)} result(s)')
except Exception as e:
    print(f'[FULL ERROR] {e}')

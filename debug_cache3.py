"""Debug cache operations test - fixed"""

from modules.fetch import FetchModule
from datetime import datetime
import json
import os

# Create fetch module with test config
config = {
    'cache_dir': './test_cache_debug3',
    'cache_ttl_seconds': 3600,
    'max_retries': 3,
    'wikipedia_lang': 'en'
}

fetch = FetchModule(config)

# Test data WITHOUT timestamp (so _save_to_cache will set current time)
test_data = {
    "title": "Test Article",
    "content": "Test content"
}

print('[DEBUG] Test data:', test_data)
print(f'[DEBUG] Cache directory: {fetch.cache_dir}')
print(f'[DEBUG] Cache TTL: {fetch.cache_ttl}')

# Save to cache
print('\n[TEST] Saving to cache...')
fetch._save_to_cache("TestArticle", test_data)

# Check if file exists
cache_file = fetch.cache_dir / "TestArticle.json"
print(f'[DEBUG] Cache file exists: {cache_file.exists()}')

if cache_file.exists():
    with open(cache_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    print('[DEBUG] Saved data:', saved_data)
    print('[DEBUG] Timestamp:', saved_data.get('timestamp'))

# Load from cache
print('\n[TEST] Loading from cache...')
try:
    cached = fetch._get_from_cache("TestArticle")
    if cached is not None:
        print('[OK] Cache loaded successfully')
        print('[DEBUG] Cached data:', cached)
    else:
        print('[ERROR] Cached data is None')
except Exception as e:
    print(f'[ERROR] Exception: {e}')
    import traceback
    traceback.print_exc()

# Clean up
import shutil
if fetch.cache_dir.exists():
    shutil.rmtree(fetch.cache_dir)
    print('\n[DEBUG] Cleaned up test cache')

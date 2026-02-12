"""Debug cache loading specifically"""

from modules.fetch import FetchModule
from datetime import datetime
import json

# Create fetch module with test config
config = {
    'cache_dir': './test_cache_debug2',
    'cache_ttl_seconds': 3600,
    'max_retries': 3,
    'wikipedia_lang': 'en'
}

fetch = FetchModule(config)

# Test data
test_data = {
    "title": "Test Article",
    "content": "Test content",
    "timestamp": "2026-02-12T00:00:00"
}

# Save to cache
fetch._save_to_cache("TestArticle", test_data)

# Now manually load to debug
cache_file = fetch.cache_dir / "TestArticle.json"
print(f'Cache file exists: {cache_file.exists()}')

with open(cache_file, 'r', encoding='utf-8') as f:
    cached_data = json.load(f)

print(f'Cached data: {cached_data}')
print(f'Timestamp from file: {cached_data.get("timestamp")}')

# Check if cache is expired
try:
    timestamp = datetime.fromisoformat(cached_data.get("timestamp", ""))
    print(f'Parsed timestamp: {timestamp}')
    
    now = datetime.now()
    print(f'Current datetime: {now}')
    
    age = (now - timestamp).total_seconds()
    print(f'Cache age (seconds): {age}')
    print(f'Cache TTL: {fetch.cache_ttl}')
    print(f'Is expired: {age > fetch.cache_ttl}')
    
except Exception as e:
    print(f'Error parsing timestamp: {e}')
    import traceback
    traceback.print_exc()

# Clean up
import shutil
if fetch.cache_dir.exists():
    shutil.rmtree(fetch.cache_dir)

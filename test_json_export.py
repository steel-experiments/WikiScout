#!/usr/bin/env python3
"""Test script for JSON export functionality"""

from src.agent import DomainSpecificAgent
import json

agent = DomainSpecificAgent()

# Test JSON export for search results
print('Testing JSON export for search results...')
search_results = agent.search('AI')
json_export = agent.export_to_json(search_results, 'search_results')
print('✓ JSON export successful')
print(f'Keys in export: {list(json_export.keys())}')
print(f'Number of results: {len(json_export.get("results", []))}')

# Verify JSON is valid
json_str = json.dumps(json_export)
print(f'✓ JSON string length: {len(json_str)} characters')

# Verify structure
assert 'metadata' in json_export, "Missing metadata in export"
assert 'results' in json_export, "Missing results in export"
assert json_export['metadata']['query_type'] == 'search_results', "Wrong query type"
print(f"✓ Metadata timestamp: {json_export['metadata']['timestamp']}")
print('✓ All JSON export functionality tests passed!')

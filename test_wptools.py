#!/usr/bin/env python3
"""Quick test of wptools integration with real Wikipedia"""

import wptools

try:
    print("[TEST] Connecting to Wikipedia...")
    page = wptools.page('Python_(programming_language)', silent=True).get()
    
    print(f"OK: Successfully fetched page")
    print(f"  Title: {page.data.get('title', 'Unknown')}")
    print(f"  Extract length: {len(page.data.get('extract', ''))} chars")
    print(f"  Mobile text length: {len(page.data.get('mobile_text', ''))} chars")
    print(f"  Available data keys: {list(page.data.keys())[:5]}...")
    
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {str(e)}")

"""
Async Fetch Module - High-Performance Wikipedia Content Retrieval

Handles:
- Async page content fetching with httpx
- Parallel batch operations (10-20x faster)
- Non-blocking I/O with async/await
- Async caching with aiofiles
"""

import logging
import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional, cast
from datetime import datetime

import httpx
import aiofiles

logger = logging.getLogger(__name__)


PageData = Dict[str, Any]


class AsyncFetchModule:
    """Async Wikipedia page fetching with parallel operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize async fetch module with configuration."""
        self.config = config
        self.lang = config.get("wikipedia_lang", "en")
        self.timeout = config.get("timeout_seconds", 30)
        self.max_retries = config.get("max_retries", 3)
        self.cache_dir = Path(config.get("cache_dir", "./cache"))
        self.cache_ttl = config.get("cache_ttl_seconds", 3600)
        self.cache_dir.mkdir(exist_ok=True)
        
        # MediaWiki API endpoint
        self.api_url = f"https://{self.lang}.wikipedia.org/w/api.php"
        self.headers = {
            "User-Agent": "WikiScout/1.1 (+https://github.com/steel-experiments/WikiScout)"
        }
        
        logger.info(f"[OK] AsyncFetchModule initialized (lang={self.lang}, timeout={self.timeout}s)")
    
    async def fetch_page(self, page_title: str, use_cache: bool = True) -> PageData:
        """
        Async fetch Wikipedia page content via MediaWiki API.
        
        Args:
            page_title: Title of Wikipedia page
            use_cache: Use cached version if available
        
        Returns:
            Dictionary with page content and metadata
        """
        logger.info(f"[ASYNC FETCH] page: '{page_title}'")
        
        # Check cache first
        if use_cache:
            cached = await self._get_from_cache(page_title)
            if cached:
                logger.info(f"  [OK] Async cache hit for: '{page_title}'")
                return cached
        
        # Fetch with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"  Async attempt {attempt}/{self.max_retries}")
                
                async with httpx.AsyncClient(timeout=self.timeout, headers=self.headers) as client:
                    # Get page content and metadata
                    page_data = await self._fetch_via_api(client, page_title)
                    
                    if page_data.get("success"):
                        # Cache the result
                        await self._save_to_cache(page_title, page_data)
                        logger.info(f"  [OK] Async fetched: '{page_data['title']}'")
                        return page_data
                
                # If not successful, retry
                logger.warning(f"  [WARN] Attempt {attempt} unsuccessful")
                
            except Exception as e:
                logger.warning(f"  [WARN] Async attempt {attempt} failed: {str(e)}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.info(f"  Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"  [ERROR] Async failed after {self.max_retries} attempts")
                    return {"success": False, "error": str(e), "title": page_title}
        
        return {"success": False, "error": "Max retries exceeded", "title": page_title}
    
    async def fetch_pages_batch(self, page_titles: List[str], use_cache: bool = True) -> List[PageData]:
        """
        Fetch multiple pages in parallel (10-20x faster than sequential).
        
        Args:
            page_titles: List of Wikipedia page titles
            use_cache: Use cached versions if available
        
        Returns:
            List of dictionaries with page content and metadata
        """
        logger.info(f"[ASYNC BATCH] Fetching {len(page_titles)} pages in parallel")
        
        # Create tasks for all pages
        tasks = [self.fetch_page(title, use_cache=use_cache) for title in page_titles]
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
        logger.info(f"[ASYNC BATCH] Completed: {successful}/{len(page_titles)} successful")
        
        return [r if isinstance(r, dict) else {"success": False, "error": str(r)} for r in results]
    
    async def _fetch_via_api(self, client: httpx.AsyncClient, page_title: str) -> PageData:
        """Fetch page content via MediaWiki API."""
        
        # Step 1: Get page ID and basic info
        params: Dict[str, str | int | bool] = {
            "action": "query",
            "format": "json",
            "titles": page_title,
            "prop": "info|extracts|pageimages",
            "inprop": "url",
            "exintro": False,
            "explaintext": True,
            "exsectionformat": "plain",
            "piprop": "original",
        }
        
        try:
            response = await client.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract page data
            pages = data.get("query", {}).get("pages", {})
            page_id = list(pages.keys())[0]
            
            # Check if page exists
            if page_id == "-1":
                return {"success": False, "error": "Page not found", "title": page_title}
            
            page = pages[page_id]
            
            # Step 2: Get HTML content for parsing
            html_params: Dict[str, str] = {
                "action": "parse",
                "format": "json",
                "page": page_title,
                "prop": "text|sections",
            }
            
            html_response = await client.get(self.api_url, params=html_params)
            html_response.raise_for_status()
            html_data = html_response.json()
            
            # Extract HTML and sections
            parse_data = html_data.get("parse", {})
            html = parse_data.get("text", {}).get("*", "")
            sections = [s.get("line", "") for s in parse_data.get("sections", [])]
            
            # Extract plain text content
            content = page.get("extract", "")
            
            # Build result
            result = {
                "title": page.get("title", page_title),
                "pageid": page.get("pageid"),
                "url": page.get("fullurl", f"https://{self.lang}.wikipedia.org/wiki/{page_title}"),
                "extract": content,
                "content": content,
                "html": html,
                "sections": sections if sections else ["Content"],
                "timestamp": datetime.now().isoformat(),
                "source": "async_mediawiki_api",
                "success": True,
            }
            
            return result
            
        except httpx.HTTPStatusError as e:
            return {"success": False, "error": f"HTTP {e.response.status_code}", "title": page_title}
        except Exception as e:
            return {"success": False, "error": str(e), "title": page_title}
    
    async def _get_from_cache(self, page_title: str) -> Optional[PageData]:
        """Async get page from cache if available and not expired."""
        cache_file = self.cache_dir / f"{page_title.replace(' ', '_')}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                content = await f.read()
                cached_data = cast(PageData, json.loads(content))
            
            # Check if cache is expired
            timestamp_str = cached_data.get("timestamp", "")
            if not timestamp_str:
                return cached_data
            
            timestamp = datetime.fromisoformat(timestamp_str)
            age = (datetime.now() - timestamp).total_seconds()
            
            if age > self.cache_ttl:
                logger.info(f"  [EXPIRED] Async cache for '{page_title}' (age: {age:.0f}s)")
                return None
            
            return cached_data
            
        except Exception as e:
            logger.warning(f"  [WARN] Async cache read error: {str(e)}")
            return None
    
    async def _save_to_cache(self, page_title: str, data: PageData) -> None:
        """Async save page to cache."""
        cache_file = self.cache_dir / f"{page_title.replace(' ', '_')}.json"
        
        # Ensure timestamp is set
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        try:
            async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
            logger.info(f"  [OK] Async cached: '{page_title}'")
        except Exception as e:
            logger.warning(f"  [WARN] Async cache write error: {str(e)}")
    
    async def clear_cache(self) -> None:
        """Async clear all cached pages."""
        try:
            import shutil
            await asyncio.to_thread(shutil.rmtree, self.cache_dir)
            await asyncio.to_thread(self.cache_dir.mkdir)
            logger.info(f"  [OK] Async cache cleared")
        except Exception as e:
            logger.error(f"  [ERROR] Async failed to clear cache: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics (synchronous)."""
        cached_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cached_files) / 1024  # KB
        
        return {
            "cached_pages": len(cached_files),
            "cache_size_kb": total_size,
            "cache_dir": str(self.cache_dir)
        }

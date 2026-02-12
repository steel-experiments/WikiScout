"""
Fetch Module - Wikipedia Content Retrieval

Handles:
- Page content fetching via MediaWiki API with wptools
- Metadata extraction (title, URL, timestamp)
- Retry logic and rate limiting
- Caching for repeated requests
"""

import logging
import json
import os
import time
import wptools
import requests
from pathlib import Path
from typing import Any, Dict, List, Optional, cast
from datetime import datetime
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


PageData = Dict[str, Any]


class FetchModule:
    """Wikipedia page fetching functionality."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize fetch module with configuration."""
        self.config = config
        self.lang = config.get("wikipedia_lang", "en")
        self.timeout = config.get("timeout_seconds", 30)
        self.max_retries = config.get("max_retries", 3)
        self.cache_dir = Path(config.get("cache_dir", "./cache"))
        self.cache_ttl = config.get("cache_ttl_seconds", 3600)
        self.use_steel_api = config.get("use_steel_api", True)
        self.steel_api_key = config.get("steel_api_key") or os.environ.get("STEEL_API_KEY")
        self.steel_api_url = config.get("steel_api_url", "https://api.steel.dev")
        self.steel_use_proxy = config.get("steel_use_proxy", False)
        self.steel_delay_ms = config.get("steel_delay_ms", 0)
        self.steel_scrape_formats: List[str] = config.get(
            "steel_scrape_formats", ["cleaned_html", "markdown"]
        )
        self.cache_dir.mkdir(exist_ok=True)
        
        # TODO: Initialize wptools or pywikibot
        
        logger.info(f"[OK] FetchModule initialized (lang={self.lang}, timeout={self.timeout}s)")
    
    def fetch_page(self, page_title: str, use_cache: bool = True) -> PageData:
        """
        Fetch Wikipedia page content using wptools.
        
        Args:
            page_title: Title of Wikipedia page
            use_cache: Use cached version if available
        
        Returns:
            Dictionary with page content and metadata
        """
        logger.info(f"[FETCH] page: '{page_title}'")
        
        # Check cache first
        if use_cache:
            cached = self._get_from_cache(page_title)
            if cached:
                logger.info(f"  [OK] Cache hit for: '{page_title}'")
                return cached
        
        # Steel API scrape (preferred) if configured
        if self.use_steel_api and self.steel_api_key:
            steel_data = self._scrape_with_steel(page_title)
            if steel_data.get("success"):
                self._save_to_cache(page_title, steel_data)
                logger.info(f"  [OK] Fetched via Steel: '{steel_data.get('title', page_title)}'")
                return steel_data

            logger.warning(
                f"  [WARN] Steel scrape failed: {steel_data.get('error', 'Unknown error')}. Falling back."
            )

        # Fetch with retries (wptools fallback)
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(f"  Attempt {attempt}/{self.max_retries}")
                
                # Fetch using wptools
                page = wptools.page(page_title, silent=True).get()
                
                # Extract data from wptools response
                page_data = {
                    "title": page.data.get('title', page_title),
                    "pageid": page.data.get('pageid'),
                    "url": f"https://en.wikipedia.org/wiki/{page.data.get('title', page_title).replace(' ', '_')}",
                    "extract": page.data.get('extract', ''),
                    "content": page.data.get('extract', ''),
                    "infobox": page.data.get('infobox', {}),
                    "timestamp": datetime.now().isoformat(),
                    "source": "wptools",
                    "success": True
                }
                
                # Extract sections from content
                content = page.data.get('extract', '')
                sections = self._extract_sections_from_text(content)
                page_data['sections'] = sections
                
                # Cache the result
                self._save_to_cache(page_title, page_data)
                logger.info(f"  [OK] Fetched: '{page_data['title']}'")
                
                return page_data
                
            except Exception as e:
                logger.warning(f"  [WARN] Attempt {attempt} failed: {str(e)}")
                
                if attempt < self.max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 2s, 4s, 8s
                    logger.info(f"  Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"  [ERROR] Failed to fetch after {self.max_retries} attempts")
                    return {"success": False, "error": str(e), "title": page_title}
        
        return {"success": False, "error": "Max retries exceeded", "title": page_title}

    def _scrape_with_steel(self, page_title: str) -> PageData:
        """Scrape Wikipedia page content via Steel API."""
        url = f"https://{self.lang}.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
        endpoint = f"{self.steel_api_url.rstrip('/')}/v1/scrape"
        headers = {
            "Content-Type": "application/json",
            "steel-api-key": self.steel_api_key,
        }
        payload = {
            "url": url,
            "format": self.steel_scrape_formats,
            "delay": self.steel_delay_ms,
            "useProxy": self.steel_use_proxy,
            "screenshot": False,
            "pdf": False,
            "region": None,
        }

        try:
            response = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Steel API returned {response.status_code}",
                    "title": page_title,
                }

            data = response.json()
            content = data.get("content", {})
            html = content.get("cleaned_html") or content.get("html") or ""
            markdown = content.get("markdown") or ""
            text = self._html_to_text(html) if html else markdown
            sections = self._extract_sections_from_text(text)
            metadata = data.get("metadata", {})

            return {
                "title": metadata.get("title", page_title),
                "url": metadata.get("urlSource", url),
                "timestamp": datetime.now().isoformat(),
                "content": text,
                "extract": text,
                "html": html,
                "markdown": markdown,
                "sections": sections,
                "source": "steel",
                "success": True,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "title": page_title}

    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text for summarization."""
        soup = BeautifulSoup(html or "", "html.parser")
        paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
        return " ".join(paragraphs).strip()
    
    def _get_from_cache(self, page_title: str) -> Optional[PageData]:
        """Get page from cache if available and not expired."""
        cache_file = self.cache_dir / f"{page_title.replace(' ', '_')}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached_data = cast(PageData, json.load(f))
            
            # Check if cache is expired
            timestamp_str = cached_data.get("timestamp", "")
            if not timestamp_str:
                return cached_data  # Return if no timestamp
            
            timestamp = datetime.fromisoformat(timestamp_str)
            age = (datetime.now() - timestamp).total_seconds()
            
            if age > self.cache_ttl:
                logger.info(f"  [EXPIRED] Cache for '{page_title}' (age: {age:.0f}s > {self.cache_ttl}s)")
                return None
            
            return cached_data
            
        except Exception as e:
            logger.warning(f"  [WARN] Cache read error: {str(e)}")
            return None
    
    def _save_to_cache(self, page_title: str, data: PageData) -> None:
        """Save page to cache."""
        cache_file = self.cache_dir / f"{page_title.replace(' ', '_')}.json"
        
        # Ensure timestamp is set to current time
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"  [OK] Cached: '{page_title}'")
        except Exception as e:
            logger.warning(f"  [WARN] Cache write error: {str(e)}")
    
    def clear_cache(self) -> None:
        """Clear all cached pages."""
        try:
            import shutil
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir()
            logger.info(f"  [OK] Cache cleared")
        except Exception as e:
            logger.error(f"  [ERROR] Failed to clear cache: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cached_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cached_files) / 1024  # KB
        
        return {
            "cached_pages": len(cached_files),
            "cache_size_kb": total_size,
            "cache_dir": str(self.cache_dir)
        }
    
    def _extract_sections_from_text(self, text: str) -> List[str]:
        """Extract section headers from extract text."""
        sections = []
        
        # Simple heuristic: split by common section patterns
        # In real implementation, would parse HTML structure
        
        if text:
            sections.append("Introduction")
            if "history" in text.lower():
                sections.append("History")
            if "properties" in text.lower() or "characteristics" in text.lower():
                sections.append("Properties")
            if "applications" in text.lower() or "uses" in text.lower():
                sections.append("Applications")
            if "see also" in text.lower():
                sections.append("See Also")
        
        return sections if sections else ["Content"]


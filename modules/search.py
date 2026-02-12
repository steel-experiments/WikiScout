"""
Search Module - Page Discovery and Disambiguation

Handles:
- Search query resolution
- Disambiguation list generation
- Page candidate ranking
"""

import logging
import re
import wptools
from typing import List, Dict, Optional
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


class SearchModule:
    """Wikipedia search functionality using wptools."""
    
    def __init__(self, config: dict):
        """Initialize search module with configuration."""
        self.config = config
        self.lang = config.get("wikipedia_lang", "en")
        self.max_retries = config.get("max_retries", 3)
        logger.info(f"  [OK] SearchModule initialized (lang={self.lang})")
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """
        Search for Wikipedia pages matching the query using wptools.
        
        Args:
            query: Search query string
            limit: Maximum number of results
        
        Returns:
            List of page candidates with metadata
        """
        logger.info(f"  [SEARCH] for: '{query}'")
        
        query = query.strip()
        if not query:
            logger.warning(f"  [WARN] Empty search query")
            return []
        
        try:
            # Try direct page fetch first (most common case)
            candidates = self._search_direct(query, limit)
            if candidates and not candidates[0].get('disambiguation', False):
                logger.info(f"  [OK] Found {len(candidates)} candidate(s)")
                return candidates
            
            # Try searching via MediaWiki search
            candidates = self._search_mediawiki(query, limit)
            logger.info(f"  [OK] Found {len(candidates)} candidate(s)")
            return candidates
            
        except Exception as e:
            logger.error(f"  [ERROR] Search failed: {str(e)}")
            return []
    
    def _search_direct(self, title: str, limit: int) -> List[Dict]:
        """
        Try fetching page directly by title using wptools.
        """
        try:
            page = wptools.page(title, silent=True).get()
            
            is_disambig = page.data.get('infobox', {}).get('type', '').lower() == 'disambiguation'
            
            candidate = {
                "title": page.data.get('title', title),
                "url": f"https://en.wikipedia.org/wiki/{page.data.get('title', title).replace(' ', '_')}",
                "description": (page.data.get('extract', '')[:100] + '...') if page.data.get('extract') else 'Main article',
                "score": 1.0,
                "disambiguation": is_disambig,
                "pageid": page.data.get('pageid')
            }
            
            logger.info(f"  [OK] Direct match found: {candidate['title']}")
            return [candidate]
        except Exception as e:
            logger.info(f"  [INFO] Direct fetch failed: {str(e)[:50]}")
            return []
    
    def _search_mediawiki(self, query: str, limit: int) -> List[Dict]:
        """
        Search Wikipedia using MediaWiki search API with proper headers.
        """
        try:
            import requests
            
            # Add proper User-Agent to avoid 403 errors
            headers = {
                'User-Agent': 'Wikipedia-CLI-Agent/1.1 (+https://en.wikipedia.org/wiki/Special:BotAccess)'
            }
            
            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srnamespace": 0,
                "srlimit": limit,
                "format": "json"
            }
            
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"  [WARN] API returned {response.status_code}")
                return []
            
            results = response.json().get('query', {}).get('search', [])
            
            candidates = []
            for result in results[:limit]:
                candidate = {
                    "title": result.get('title', ''),
                    "url": f"https://en.wikipedia.org/wiki/{result.get('title', '').replace(' ', '_')}",
                    "description": result.get('snippet', '').replace('<span class=\"searchmatch\">', '').replace('</span>', '')[:150],
                    "score": self._calculate_score(result.get('title', ''), query),
                    "disambiguation": 'disambiguation' in result.get('title', '').lower(),
                    "pageid": result.get('pageid')
                }
                candidates.append(candidate)
            
            logger.info(f"  [OK] MediaWiki search found {len(candidates)} result(s)")
            return candidates
        except Exception as e:
            logger.warning(f"  [WARN] MediaWiki search failed: {str(e)[:50]}")
            return []
    
    def _calculate_score(self, title: str, query: str) -> float:
        """
        Calculate relevance score using string similarity.
        """
        ratio = SequenceMatcher(None, title.lower(), query.lower()).ratio()
        return min(1.0, ratio + 0.1)
    
    def resolve_disambiguation(self, query: str) -> Dict:
        """
        Resolve disambiguation pages.
        
        Args:
            query: Potentially ambiguous query
        
        Returns:
            Dictionary with disambiguation candidates
        """
        logger.info(f"  [DISAMB] Resolving: '{query}'")
        
        candidates = self.search(query + " disambiguation", limit=10)
        disambig_candidates = [c for c in candidates if c.get('disambiguation', False)]
        
        if disambig_candidates:
            logger.info(f"  [OK] Found {len(disambig_candidates)} disambiguation candidate(s)")
            return {
                "is_disambiguation": True,
                "candidates": disambig_candidates
            }
        
        logger.info(f"  [INFO] No disambiguation page found")
        return {"is_disambiguation": False, "candidates": candidates}
    
    def find_best_match(self, query: str, candidates: List[Dict]) -> Optional[Dict]:
        """
        Select the best matching page from candidates.
        
        Args:
            query: Original search query
            candidates: List of candidate pages
        
        Returns:
            Best matching candidate or None
        """
        if not candidates:
            return None
        
        # Sort by score (descending), prioritize non-disambiguation pages
        sorted_candidates = sorted(
            candidates, 
            key=lambda x: (not x.get('disambiguation', False), x.get('score', 0)), 
            reverse=True
        )
        
        logger.info(f"  [OK] Best match: {sorted_candidates[0]['title']}")
        return sorted_candidates[0]
    
    def suggest_alternatives(self, query: str, max_suggestions: int = 3) -> List[str]:
        """
        Suggest alternative searches based on query analysis.
        
        Args:
            query: Failed search query
            max_suggestions: Maximum alternatives to suggest
        
        Returns:
            List of alternative queries
        """
        logger.warning(f"  [WARN] Suggesting alternatives for: '{query}'")
        
        alternatives = []
        
        # Try common suffixes
        suffixes = [" (concept)", " (person)", " (place)", " (disambiguation)"]
        for suffix in suffixes:
            if len(alternatives) < max_suggestions:
                alternatives.append(f"{query}{suffix}")
        
        # Try removing common words
        common_words = {"the", "a", "an"}
        words = query.split()
        shortened = " ".join([w for w in words if w.lower() not in common_words])
        if shortened and shortened != query and len(alternatives) < max_suggestions:
            alternatives.append(shortened)
        
        return alternatives[:max_suggestions]

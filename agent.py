#!/usr/bin/env python3
"""
Wikipedia CLI Agent - Main Entry Point

A domain-specific agent for Wikipedia browsing and summarization via CLI.
Provides fast, verifiable, and reproducible access to encyclopedic information.

Version: 1.1
Author: Damjan
Date: February 12, 2026
"""

import asyncio
import click
import json
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.search import SearchModule
from modules.fetch import FetchModule
from modules.fetch_async import AsyncFetchModule
from modules.parse import ParseModule
from modules.summarize import SummarizeModule


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Version
__version__ = "1.1"


class WikipediaAgent:
    """Main agent class for Wikipedia browsing and summarization."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the agent with configuration."""
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.cache_dir = Path(self.config.get("cache_dir", "./cache"))
        self.cache_dir.mkdir(exist_ok=True)
        self.search_module = SearchModule(self.config)
        self.fetch_module = FetchModule(self.config)
        self.async_fetch_module = AsyncFetchModule(self.config)
        self.parse_module = ParseModule(self.config)
        self.summarize_module = SummarizeModule(self.config)
        logger.info(f"OK: Agent initialized (v{__version__})")
    
    def _load_config(self) -> dict:
        """Load configuration from config.json."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("[WARN] Invalid config file. Using defaults.")
        return self._default_config()
    
    @staticmethod
    def _default_config() -> dict:
        """Return default configuration."""
        return {
            "wikipedia_lang": "en",
            "cache_dir": "./cache",
            "cache_ttl_seconds": 3600,
            "timeout_seconds": 60,
            "max_retries": 3,
            "rate_limit_delay_ms": 500,
            "default_summary_bullets": 5,
            "log_level": "INFO"
        }
    
    def search(self, query: str, candidates: int = 5) -> dict:
        """
        Search for a Wikipedia page.
        
        Args:
            query: Search query string
            candidates: Number of candidate pages to return
        
        Returns:
            Dictionary with search results
        """
        logger.info(f"[SEARCH] for: '{query}'")
        
        candidates_list = self.search_module.search(query, limit=candidates)
        if not candidates_list:
            return {
                "status": "error",
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "error": "No candidates found"
            }

        return {
            "status": "success",
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "candidates": candidates_list
        }
    
    def fetch(self, page_title: str) -> dict:
        """
        Fetch Wikipedia page content.
        
        Args:
            page_title: Title of Wikipedia page
        
        Returns:
            Dictionary with page content and metadata
        """
        logger.info(f"[FETCH] page: '{page_title}'")
        
        page_data = self.fetch_module.fetch_page(page_title)
        if not page_data.get("success"):
            return {
                "status": "error",
                "title": page_title,
                "timestamp": datetime.now().isoformat(),
                "error": page_data.get("error", "Unknown error")
            }

        return {
            "status": "success",
            "title": page_data.get("title", page_title),
            "url": page_data.get("url", ""),
            "timestamp": page_data.get("timestamp", datetime.now().isoformat()),
            "content": page_data.get("content", ""),
            "html": page_data.get("html", ""),
            "sections": page_data.get("sections", [])
        }
    
    def summarize(self, page_title: str, bullets: int = 5) -> dict:
        """
        Summarize a Wikipedia page.
        
        Args:
            page_title: Title of Wikipedia page
            bullets: Number of bullet points for summary
        
        Returns:
            Dictionary with summary
        """
        logger.info(f"[SUMMARIZE] '{page_title}' ({bullets} bullets)")
        
        page_data = self.fetch_module.fetch_page(page_title)
        if not page_data.get("success"):
            return {
                "status": "error",
                "title": page_title,
                "timestamp": datetime.now().isoformat(),
                "error": page_data.get("error", "Unknown error")
            }

        html = page_data.get("html", "")
        sections = self.parse_module.extract_sections(html) if html else []
        if not sections:
            section_titles = page_data.get("sections", [])
            content_text = page_data.get("content", "") or page_data.get("extract", "")
            if section_titles and isinstance(section_titles[0], str):
                sections = [
                    {
                        "heading": title,
                        "text": content_text[:500],
                        "html_id": title.lower().replace(" ", "_")
                    }
                    for title in section_titles
                ]
            elif content_text:
                sections = [{"heading": "Content", "text": content_text[:500], "html_id": "content"}]
        content = {
            "title": page_data.get("title", page_title),
            "url": page_data.get("url", ""),
            "extract": page_data.get("extract", ""),
            "content": page_data.get("content", ""),
            "sections": sections,
            "timestamp": page_data.get("timestamp", datetime.now().isoformat())
        }

        summary = self.summarize_module.generate_summary(content, num_bullets=bullets)
        formatted = []
        for bullet in summary.get("bullets", []):
            section = bullet.get("section", "Content")
            formatted.append(f"{bullet.get('text', '')} (Section: {section})")

        while len(formatted) < bullets:
            formatted.append(
                f"Key point about {summary.get('title', page_title)} (Section: Content)"
            )

        return {
            "status": "success",
            "title": summary.get("title", page_title),
            "timestamp": datetime.now().isoformat(),
            "summary": formatted,
            "source_url": summary.get("url", page_data.get("url", ""))
        }
    
    def compare(self, topic1: str, topic2: str, bullets: int = 5) -> dict:
        """
        Compare two Wikipedia topics.
        
        Args:
            topic1: First topic
            topic2: Second topic
            bullets: Number of comparison points
        
        Returns:
            Dictionary with comparison
        """
        logger.info(f"[COMPARE] '{topic1}' vs '{topic2}'")
        
        page1 = self.fetch_module.fetch_page(topic1)
        page2 = self.fetch_module.fetch_page(topic2)

        if not page1.get("success") or not page2.get("success"):
            return {
                "status": "error",
                "topic1": topic1,
                "topic2": topic2,
                "timestamp": datetime.now().isoformat(),
                "error": "Failed to fetch one or both topics"
            }

        comparison = self.summarize_module.compare_topics(page1, page2, num_points=bullets)
        return {
            "status": "success",
            "topic1": comparison.get("topic1", topic1),
            "topic2": comparison.get("topic2", topic2),
            "timestamp": datetime.now().isoformat(),
            "comparison": {
                "similarities": comparison.get("similarities", []),
                "differences": comparison.get("differences", [])
            }
        }

    async def search_async(self, query: str, candidates: int = 5) -> dict:
        """
        Async search for a Wikipedia page.
        """
        logger.info(f"[ASYNC SEARCH] for: '{query}'")

        candidates_list = await asyncio.to_thread(self.search_module.search, query, candidates)
        if not candidates_list:
            return {
                "status": "error",
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "error": "No candidates found"
            }

        return {
            "status": "success",
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "candidates": candidates_list
        }

    async def fetch_async(self, page_title: str, use_cache: bool = True) -> dict:
        """
        Async fetch Wikipedia page content.
        """
        logger.info(f"[ASYNC FETCH] page: '{page_title}'")

        page_data = await self.async_fetch_module.fetch_page(page_title, use_cache=use_cache)
        if not page_data.get("success"):
            return {
                "status": "error",
                "title": page_title,
                "timestamp": datetime.now().isoformat(),
                "error": page_data.get("error", "Unknown error")
            }

        return {
            "status": "success",
            "title": page_data.get("title", page_title),
            "url": page_data.get("url", ""),
            "timestamp": page_data.get("timestamp", datetime.now().isoformat()),
            "content": page_data.get("content", ""),
            "html": page_data.get("html", ""),
            "sections": page_data.get("sections", [])
        }

    async def fetch_pages_async(self, page_titles: List[str], use_cache: bool = True) -> List[dict]:
        """
        Async fetch multiple pages in parallel.
        """
        return await self.async_fetch_module.fetch_pages_batch(page_titles, use_cache=use_cache)

    async def summarize_async(self, page_title: str, bullets: int = 5) -> dict:
        """
        Async summarize a Wikipedia page.
        """
        logger.info(f"[ASYNC SUMMARIZE] '{page_title}' ({bullets} bullets)")

        page_data = await self.async_fetch_module.fetch_page(page_title)
        if not page_data.get("success"):
            return {
                "status": "error",
                "title": page_title,
                "timestamp": datetime.now().isoformat(),
                "error": page_data.get("error", "Unknown error")
            }

        html = page_data.get("html", "")
        sections = await asyncio.to_thread(self.parse_module.extract_sections, html) if html else []
        if not sections:
            section_titles = page_data.get("sections", [])
            content_text = page_data.get("content", "") or page_data.get("extract", "")
            if section_titles and isinstance(section_titles[0], str):
                sections = [
                    {
                        "heading": title,
                        "text": content_text[:500],
                        "html_id": title.lower().replace(" ", "_")
                    }
                    for title in section_titles
                ]
            elif content_text:
                sections = [{"heading": "Content", "text": content_text[:500], "html_id": "content"}]
        content = {
            "title": page_data.get("title", page_title),
            "url": page_data.get("url", ""),
            "extract": page_data.get("extract", ""),
            "content": page_data.get("content", ""),
            "sections": sections,
            "timestamp": page_data.get("timestamp", datetime.now().isoformat())
        }

        summary = await asyncio.to_thread(self.summarize_module.generate_summary, content, bullets)
        formatted = []
        for bullet in summary.get("bullets", []):
            section = bullet.get("section", "Content")
            formatted.append(f"{bullet.get('text', '')} (Section: {section})")

        while len(formatted) < bullets:
            formatted.append(
                f"Key point about {summary.get('title', page_title)} (Section: Content)"
            )

        return {
            "status": "success",
            "title": summary.get("title", page_title),
            "timestamp": datetime.now().isoformat(),
            "summary": formatted,
            "source_url": summary.get("url", page_data.get("url", ""))
        }

    async def compare_async(self, topic1: str, topic2: str, bullets: int = 5) -> dict:
        """
        Async compare two Wikipedia topics.
        """
        logger.info(f"[ASYNC COMPARE] '{topic1}' vs '{topic2}'")

        pages = await self.async_fetch_module.fetch_pages_batch([topic1, topic2])
        page1, page2 = pages[0], pages[1]

        if not page1.get("success") or not page2.get("success"):
            return {
                "status": "error",
                "topic1": topic1,
                "topic2": topic2,
                "timestamp": datetime.now().isoformat(),
                "error": "Failed to fetch one or both topics"
            }

        comparison = await asyncio.to_thread(
            self.summarize_module.compare_topics,
            page1,
            page2,
            bullets
        )
        return {
            "status": "success",
            "topic1": comparison.get("topic1", topic1),
            "topic2": comparison.get("topic2", topic2),
            "timestamp": datetime.now().isoformat(),
            "comparison": {
                "similarities": comparison.get("similarities", []),
                "differences": comparison.get("differences", [])
            }
        }


# CLI Commands
def format_output(data: dict, format_type: str = "text") -> str:
    """
    Format output as text or JSON.
    
    Args:
        data: Result dictionary
        format_type: 'text' or 'json'
    
    Returns:
        Formatted string
    """
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    return ""  # Text format handled by click.echo


@click.group()
@click.version_option(version=__version__)
def cli():
    """
    Wikipedia CLI Agent v1.1
    
    Fast, verifiable, and reproducible access to encyclopedic information.
    """
    pass


@cli.command()
@click.option('--query', '-q', required=True, help='Search query')
@click.option('--candidates', '-c', default=5, help='Number of candidates to show')
@click.option('--format', '-f', 'output_format', default='text', type=click.Choice(['text', 'json']), help='Output format')
def search(query: str, candidates: int, output_format: str):
    """Search for a Wikipedia page."""
    agent = WikipediaAgent()
    result = agent.search(query, candidates)
    
    if output_format == "json":
        click.echo(format_output(result, "json"))
        return
    
    if result['status'] == 'success':
        click.echo(f"\nOK: Search Results for: '{query}'")
        click.echo(f"  Found {len(result['candidates'])} candidate(s)\n")
        for i, candidate in enumerate(result['candidates'], 1):
            click.echo(f"  [{i}] {candidate['title']}")
            click.echo(f"      {candidate['description']}")
            click.echo(f"      {candidate['url']}\n")
    else:
        click.echo(f"ERROR: Search failed: {result.get('error', 'Unknown error')}", err=True)


@cli.command()
@click.option('--query', '-q', required=True, help='Wikipedia page title')
@click.option('--bullets', '-b', default=5, help='Number of summary bullets')
@click.option('--format', '-f', 'output_format', default='text', type=click.Choice(['text', 'json']), help='Output format')
def summarize(query: str, bullets: int, output_format: str):
    """Summarize a Wikipedia page."""
    agent = WikipediaAgent()
    
    # First search to confirm page exists
    search_result = agent.search(query)
    if search_result['status'] != 'success':
        error_msg = {"status": "error", "query": query, "error": "Page not found"}
        click.echo(format_output(error_msg, output_format) if output_format == "json" else f"ERROR: Page not found: '{query}'", err=True)
        return
    
    # Then summarize
    result = agent.summarize(query, bullets)
    
    if output_format == "json":
        click.echo(format_output(result, "json"))
        return
    
    if result['status'] == 'success':
        click.echo(f"\nOK: Summary: {result['title']}")
        click.echo(f"  Source: {result['source_url']}\n")
        for i, point in enumerate(result['summary'], 1):
            click.echo(f"  {i}) {point}")
        click.echo()
    else:
        click.echo(f"ERROR: Summarize failed: {result.get('error', 'Unknown error')}", err=True)


@cli.command()
@click.option('--topic1', '-t1', required=True, help='First topic')
@click.option('--topic2', '-t2', required=True, help='Second topic')
@click.option('--bullets', '-b', default=5, help='Number of comparison points')
@click.option('--format', '-f', 'output_format', default='text', type=click.Choice(['text', 'json']), help='Output format')
def compare(topic1: str, topic2: str, bullets: int, output_format: str):
    """Compare two Wikipedia topics (parallel fetch for speed)."""
    agent = WikipediaAgent()
    
    # Parallel fetch both pages for ~2x speed
    logger.info(f"[COMPARE] Fetching '{topic1}' and '{topic2}' in parallel...")
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(agent.fetch_module.fetch_page, topic1)
        future2 = executor.submit(agent.fetch_module.fetch_page, topic2)
        page1 = future1.result()
        page2 = future2.result()
    
    # Compare results
    result = agent.compare(topic1, topic2, bullets)
    
    if output_format == "json":
        click.echo(format_output(result, "json"))
        return
    
    if result['status'] == 'success':
        click.echo(f"\n⚖️  Comparison: {result['topic1']} vs {result['topic2']}\n")
        
        click.echo("Similarities:")
        for sim in result['comparison']['similarities']:
            click.echo(f"  • {sim}")
        
        click.echo("\nDifferences:")
        for diff in result['comparison']['differences']:
            click.echo(f"  • {diff}")
        click.echo()
    else:
        click.echo(f"ERROR: Comparison failed: {result.get('error', 'Unknown error')}", err=True)


@cli.command()
@click.option('--query', '-q', required=True, help='Wikipedia page title')
@click.option('--format', '-f', 'output_format', default='text', type=click.Choice(['text', 'json']), help='Output format')
def infobox(query: str, output_format: str):
    """Extract infobox data from a Wikipedia page."""
    agent = WikipediaAgent()
    result = agent.fetch(query)
    
    if result['status'] == 'success':
        html = result.get("html", "")
        infobox = agent.parse_module.extract_infobox(html) if html else {"fields": {}}
        fields = infobox.get("fields", {})
        
        output_data = {
            "status": "success",
            "title": result.get('title'),
            "url": result.get('url'),
            "fields": fields
        }
        
        if output_format == "json":
            click.echo(format_output(output_data, "json"))
            return

        click.echo(f"\nOK: Infobox: {result['title']}")
        click.echo(f"  Source: {result['url']}\n")

        if not fields:
            click.echo("  No infobox fields found.\n")
            return

        click.echo("  Fields:")
        for label, value in list(fields.items())[:12]:
            click.echo(f"    • {label}: {value}")
        click.echo()
    else:
        error_data = {"status": "error", "query": query, "error": result.get('error')}
        click.echo(format_output(error_data, output_format) if output_format == "json" else f"ERROR: Failed to fetch infobox: {result.get('error', 'Unknown error')}", err=True)


@cli.command()
@click.option('--format', '-f', 'output_format', default='text', type=click.Choice(['text', 'json']), help='Output format')
def status(output_format: str):
    """Check agent status and configuration."""
    agent = WikipediaAgent()
    
    status_data = {
        "status": "ok",
        "version": __version__,
        "config_file": str(agent.config_path),
        "cache_dir": str(agent.cache_dir),
        "cache_ttl_seconds": agent.config.get('cache_ttl_seconds'),
        "log_level": agent.config.get('log_level'),
        "cache_stats": agent.fetch_module.get_cache_stats()
    }
    
    if output_format == "json":
        click.echo(format_output(status_data, "json"))
        return
    
    click.echo(f"\nOK: Agent Status")
    click.echo(f"  Version: {__version__}")
    click.echo(f"  Config: {agent.config_path}")
    click.echo(f"  Cache dir: {agent.cache_dir}")
    click.echo(f"  Cache TTL: {agent.config.get('cache_ttl_seconds')}s")
    click.echo(f"  Log level: {agent.config.get('log_level')}")
    click.echo()


if __name__ == '__main__':
    try:
        cli()
    except Exception as e:
        logger.error(f"[ERROR] Agent error: {str(e)}")
        click.echo(f"ERROR: {str(e)}", err=True)
        exit(1)

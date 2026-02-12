#!/usr/bin/env python3
"""
WikiScout Modern CLI - Typer + Rich Interface

Beautiful command-line interface for Wikipedia research.

Usage:
    wikiscout search "Python programming"
    wikiscout summarize "Machine Learning" --bullets 5
    wikiscout compare "Python" "JavaScript"
"""

import asyncio
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.markdown import Markdown
from typing import List
import json
from datetime import datetime

from agent import WikipediaAgent

# Create Typer app
app = typer.Typer(
    name="wikiscout",
    help="🔍 Fast Wikipedia research agent with AI-powered summarization",
    add_completion=False,
)

# Create Rich console
console = Console()
COMPACT_MODE = False

# Initialize agent
agent = WikipediaAgent()


def print_header(title: str):
    """Print a styled header"""
    if COMPACT_MODE:
        console.print(f"[bold cyan]{title}[/bold cyan]")
        return
    console.print(Panel.fit(
        f"[bold cyan]{title}[/bold cyan]",
        border_style="cyan",
    ))


def print_success(message: str):
    """Print success message"""
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str):
    """Print error message"""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_json_syntax(data: dict):
    """Print JSON with syntax highlighting"""
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    syntax = Syntax(json_str, "json", theme="monokai", line_numbers=False)
    console.print(syntax)


def gap():
    """Print a blank line unless compact mode is enabled."""
    if not COMPACT_MODE:
        console.print()


@app.callback()
def configure_output(
    compact: bool = typer.Option(False, "--compact", help="Compact output"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Configure global output settings."""
    global console, COMPACT_MODE
    COMPACT_MODE = compact
    if no_color:
        console = Console(no_color=True, color_system=None)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    candidates: int = typer.Option(5, "--candidates", "-c", help="Number of candidates", min=1, max=20),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """
    🔍 Search Wikipedia for articles
    
    Returns a list of relevant articles with descriptions and metadata.
    """
    print_header(f"Searching: {query}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching Wikipedia...", total=None)
        result = agent.search(query, candidates=candidates)
        progress.remove_task(task)
    
    if result.get("status") == "error":
        print_error(f"Search failed: {result.get('error')}")
        raise typer.Exit(code=1)
    
    if format == "json":
        print_json_syntax(result)
        return
    
    # Beautiful text output
    candidates_list = result.get("candidates", [])
    
    if not candidates_list:
        console.print("[yellow]No results found[/yellow]")
        return
    
    print_success(f"Found {len(candidates_list)} articles")
    gap()
    
    for i, candidate in enumerate(candidates_list, 1):
        # Create table for each result
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan bold")
        table.add_column("Value")
        
        table.add_row("Title", f"[bold]{candidate['title']}[/bold]")
        table.add_row("Score", f"[green]{candidate['score']:.2f}[/green]")
        table.add_row("URL", f"[link={candidate['url']}]{candidate['url']}[/link]")
        table.add_row("Page ID", str(candidate.get('pageid', 'N/A')))
        
        if COMPACT_MODE:
            console.print(f"[bold]Result {i}[/bold]")
            console.print(table)
            gap()
        else:
            console.print(Panel(table, title=f"[bold]Result {i}[/bold]", border_style="blue"))
            gap()


@app.command()
def summarize(
    query: str = typer.Argument(..., help="Article title or query"),
    bullets: int = typer.Option(5, "--bullets", "-b", help="Number of bullet points", min=1, max=20),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """
    📝 Summarize a Wikipedia article
    
    Generates a concise bullet-point summary of key information.
    """
    print_header(f"Summarizing: {query}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching and analyzing article...", total=None)
        result = agent.summarize(query, bullets=bullets)
        progress.remove_task(task)
    
    if result.get("status") == "error":
        print_error(f"Summarization failed: {result.get('error')}")
        raise typer.Exit(code=1)
    
    if format == "json":
        print_json_syntax(result)
        return
    
    # Beautiful text output
    title = result.get("title", query)
    summary_list = result.get("summary", [])
    source_url = result.get("source_url", "")
    
    print_success(f"Summarized: {title}")
    gap()
    
    # Summary bullets
    console.print("[bold cyan]Key Points:[/bold cyan]")
    for i, bullet in enumerate(summary_list, 1):
        console.print(f"  [bold]{i}.[/bold] {bullet}")
    
    gap()
    console.print(f"[dim]Source: {source_url}[/dim]")


@app.command()
def compare(
    topic1: str = typer.Option(..., "--topic1", "-t1", help="First topic"),
    topic2: str = typer.Option(..., "--topic2", "-t2", help="Second topic"),
    bullets: int = typer.Option(5, "--bullets", "-b", help="Number of points", min=1, max=20),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """
    ⚖️  Compare two Wikipedia topics
    
    Finds similarities and differences between two subjects.
    """
    print_header(f"Comparing: {topic1} vs {topic2}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching articles...", total=None)
        result = agent.compare(topic1, topic2, bullets=bullets)
        progress.remove_task(task)
    
    if result.get("status") == "error":
        print_error(f"Comparison failed: {result.get('error')}")
        raise typer.Exit(code=1)
    
    if format == "json":
        print_json_syntax(result)
        return
    
    # Beautiful text output
    comparison = result.get("comparison", {})
    similarities = comparison.get("similarities", [])
    differences = comparison.get("differences", [])
    
    # Similarities
    if similarities:
        gap()
        console.print("[bold green]✓ Similarities:[/bold green]")
        for sim in similarities:
            console.print(f"  • {sim}")
    else:
        gap()
        console.print("[yellow]No clear similarities found[/yellow]")
    
    # Differences
    if differences:
        gap()
        console.print("[bold yellow]⚡ Differences:[/bold yellow]")
        for diff in differences:
            console.print(f"  • {diff}")
    else:
        gap()
        console.print("[yellow]No clear differences found[/yellow]")

    gap()


@app.command()
def infobox(
    query: str = typer.Argument(..., help="Article title"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """
    📊 Extract structured data from Wikipedia infobox
    
    Returns key facts and metadata from the article's infobox.
    """
    print_header(f"Extracting infobox: {query}")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching article data...", total=None)
        
        # Fetch page
        page_data = agent.fetch(query)
        progress.remove_task(task)
    
    if page_data.get("status") == "error":
        print_error(f"Failed to fetch article: {page_data.get('error')}")
        raise typer.Exit(code=1)
    
    # Parse infobox
    html = page_data.get("html", "")
    if html:
        from modules.parse import ParseModule
        parser = ParseModule(agent.config)
        infobox_data = parser.extract_infobox(html)
    else:
        infobox_data = {}
    
    if format == "json":
        result = {
            "status": "success",
            "title": page_data.get("title", query),
            "data": infobox_data,
            "timestamp": datetime.now().isoformat(),
        }
        print_json_syntax(result)
        return
    
    # Beautiful text output
    if not infobox_data:
        console.print("[yellow]No infobox data found[/yellow]")
        return
    
    print_success(f"Extracted {len(infobox_data)} fields")
    gap()
    
    # Create table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Field", style="cyan")
    table.add_column("Value")
    
    for key, value in infobox_data.items():
        table.add_row(key, str(value))
    
    console.print(table)


@app.command()
def batch(
    titles: List[str] = typer.Argument(..., help="Article titles (space-separated)"),
    use_cache: bool = typer.Option(True, "--cache/--no-cache", help="Use cache when available"),
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """
    📦 Fetch multiple Wikipedia pages in parallel
    """
    print_header(f"Batch fetch ({len(titles)} pages)")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching pages...", total=None)
        results = asyncio.run(agent.async_fetch_module.fetch_pages_batch(titles, use_cache=use_cache))
        progress.remove_task(task)

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    if format == "json":
        payload = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "count": len(results),
            "results": results,
        }
        print_json_syntax(payload)
        return

    print_success(f"Fetched {len(successful)}/{len(results)} pages")
    if failed:
        print_error(f"Failed: {len(failed)}")
    gap()

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Status", style="cyan", width=7)
    table.add_column("Title", style="bold")
    table.add_column("URL")
    table.add_column("Error")

    for result in results:
        status = "OK" if result.get("success") else "ERR"
        title = result.get("title", "")
        url = result.get("url", "")
        error = "" if result.get("success") else result.get("error", "Unknown error")
        table.add_row(status, title, url, error)

    console.print(table)


@app.command()
def health(
    format: str = typer.Option("text", "--format", "-f", help="Output format: text or json"),
):
    """
    ❤️  Quick health check
    """
    print_header("Health Check")

    result = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0",
        "cache_status": "active",
    }

    if format == "json":
        print_json_syntax(result)
        return

    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan bold")
    table.add_column("Value", style="green")
    table.add_row("Status", "[green]✓ Healthy[/green]")
    table.add_row("Timestamp", result["timestamp"])
    table.add_row("Version", result["version"])
    table.add_row("Cache", result["cache_status"])
    console.print(table)


@app.command()
def status():
    """
    📊 Show agent status and cache statistics
    """
    print_header("WikiScout Status")
    
    # Get cache info
    cache_dir = agent.cache_dir
    cache_files = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0
    cache_size = sum(f.stat().st_size for f in cache_dir.glob("*.json")) if cache_dir.exists() else 0
    
    # Create status table
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="cyan bold")
    table.add_column("Value", style="green")
    
    table.add_row("Status", "[green]✓ Operational[/green]")
    table.add_row("Version", "1.1.0")
    table.add_row("Cache Directory", str(cache_dir))
    table.add_row("Cached Articles", str(cache_files))
    table.add_row("Cache Size", f"{cache_size / 1024 / 1024:.2f} MB")
    table.add_row("Language", agent.config.get("wikipedia_lang", "en"))
    table.add_row("Cache TTL", f"{agent.config.get('cache_ttl_seconds', 3600)}s")
    table.add_row("Timeout", f"{agent.config.get('timeout_seconds', 60)}s")
    
    console.print(table)


@app.command()
def version():
    """
    Show version information
    """
    console.print("[bold cyan]WikiScout[/bold cyan] v1.1.0")
    console.print("Fast Wikipedia research agent")
    console.print("\n[dim]Built with:[/dim]")
    console.print("  • Python 3.14")
    console.print("  • Typer + Rich")
    console.print("  • wptools + BeautifulSoup")


def main():
    """Entry point"""
    app()


if __name__ == "__main__":
    main()

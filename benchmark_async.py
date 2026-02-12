#!/usr/bin/env python3
"""
Quick benchmark comparing sync vs async fetch.

Note: Results depend on network conditions and Wikipedia response times.
"""

import asyncio
import time

from agent import WikipediaAgent


def run_sync(agent: WikipediaAgent, titles: list[str]) -> float:
    start = time.perf_counter()
    for title in titles:
        agent.fetch_module.fetch_page(title, use_cache=False)
    return time.perf_counter() - start


async def run_async(agent: WikipediaAgent, titles: list[str]) -> float:
    start = time.perf_counter()
    await agent.fetch_pages_async(titles, use_cache=False)
    return time.perf_counter() - start


def main() -> None:
    titles = [
        "Python (programming language)",
        "Machine learning",
        "Artificial intelligence",
        "Computer science",
        "Data science",
    ]
    agent = WikipediaAgent()

    sync_time = run_sync(agent, titles)
    async_time = asyncio.run(run_async(agent, titles))

    speedup = sync_time / async_time if async_time > 0 else 0.0
    print("Benchmark results (lower is better)")
    print(f"  Sync:  {sync_time:.2f}s")
    print(f"  Async: {async_time:.2f}s")
    print(f"  Speedup: {speedup:.2f}x")


if __name__ == "__main__":
    main()

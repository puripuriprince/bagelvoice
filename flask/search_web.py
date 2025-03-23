import os
import asyncio
import json
from pydantic import BaseModel, Field
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, LLMConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy

from search import google_search


def get_llm_strategy():
    """Returns an LLM extraction strategy for extracting blog posts."""
    return LLMExtractionStrategy(
        llm_config=LLMConfig(provider="ollama/llama3:latest", api_token="no-token"),
        extraction_type="schema",
        instruction="Extract all blog post objects with blog title and date from the content.",
        chunk_token_threshold=1000,
        overlap_rate=0.0,
        apply_chunking=True,
        input_format="markdown",
        extra_args={"temperature": 0.0, "max_tokens": 800},
    )


async def crawl_website(url: str):
    """Crawls the given URL and extracts blog post data."""
    llm_strategy = get_llm_strategy()

    crawl_config = CrawlerRunConfig(
        extraction_strategy=llm_strategy,
        cache_mode=CacheMode.BYPASS,
    )

    browser_cfg = BrowserConfig(headless=True)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url=url, config=crawl_config)

        if result.success:
            print("Crawling successful!")
            data = json.loads(result.extracted_content)
            llm_strategy.show_usage()
            return data
        else:
            print("Crawling failed:", result.error_message)
            return None


async def main(query: str, num_results: int = 2):
    urls = await google_search(query, num_results)

    if not urls:
        print("No search results found.")
        return

    tasks = [crawl_website(url) for url in urls]
    results = await asyncio.gather(*tasks)

    for i, data in enumerate(results):
        if data:
            print(f"Result {i + 1}:\n", json.dumps(data, indent=2))


if __name__ == "__main__":
    asyncio.run(main("Big Data", num_results=1))

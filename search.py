"""
Playwright-based web search and news feed for agents.
Agents search live web + news to gather real-world data for deep analysis.
"""

import asyncio
from playwright.async_api import async_playwright


_browser = None
_context = None


async def init_browser():
    global _browser, _context
    p = await async_playwright().start()
    _browser = await p.chromium.launch(headless=True)
    _context = await _browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    return _browser


async def close_browser():
    global _browser, _context
    if _browser:
        await _browser.close()
        _browser = None
        _context = None


async def search_web(query: str, max_results: int = 6) -> str:
    """
    General web search via DuckDuckGo → Bing fallback.
    Returns formatted results with title, snippet, URL.
    """
    results = await _search_duckduckgo(query, max_results)
    if results:
        return results
    results = await _search_bing(query, max_results)
    return results or "No search results found."


async def search_news(query: str, max_results: int = 6) -> str:
    """
    News-specific search. Returns recent news articles.
    Combines DuckDuckGo news + Google News search.
    """
    news_query = f"{query} news 2025 2026"
    results = await _search_duckduckgo(news_query, max_results)

    # Also try Google News
    news_results = await _search_google_news(query, max_results)
    if news_results:
        tag = "\n\n--- Recent News ---\n"
        if results:
            results += tag + news_results
        else:
            results = tag + news_results

    return results or "No news results found."


async def _search_duckduckgo(query: str, n: int) -> str | None:
    global _browser, _context
    if not _browser:
        await init_browser()
    page = await _context.new_page()
    try:
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)

        results = []
        items = await page.query_selector_all(".result")
        for item in items[:n]:
            try:
                title_el = await item.query_selector(".result__title a")
                snippet_el = await item.query_selector(".result__snippet")
                title = await title_el.inner_text() if title_el else "No title"
                link = await title_el.get_attribute("href") if title_el else ""
                snippet = await snippet_el.inner_text() if snippet_el else ""
                results.append(f"📄 {title}\n   {snippet}\n   🔗 {link[:100]}")
            except Exception:
                continue
        return "\n\n".join(results) if results else None
    except Exception:
        return None
    finally:
        await page.close()


async def _search_bing(query: str, n: int) -> str | None:
    global _browser, _context
    if not _browser:
        await init_browser()
    page = await _context.new_page()
    try:
        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)

        results = []
        items = await page.query_selector_all("#b_results .b_algo")
        for item in items[:n]:
            try:
                title_el = await item.query_selector("h2 a")
                snippet_el = await item.query_selector(".b_caption p")
                title = await title_el.inner_text() if title_el else "No title"
                link = await title_el.get_attribute("href") if title_el else ""
                snippet = await snippet_el.inner_text() if snippet_el else ""
                results.append(f"📄 {title}\n   {snippet}\n   🔗 {link[:100]}")
            except Exception:
                continue
        return "\n\n".join(results) if results else None
    except Exception:
        return None
    finally:
        await page.close()


async def _search_google_news(query: str, n: int) -> str | None:
    global _browser, _context
    if not _browser:
        await init_browser()
    page = await _context.new_page()
    try:
        url = f"https://news.google.com/search?q={query.replace(' ', '+')}&hl=en-US&gl=US&ceid=US:en"
        await page.goto(url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(1)

        results = []
        articles = await page.query_selector_all("article")
        for article in articles[:n]:
            try:
                title_el = await article.query_selector("a[aria-label]")
                if title_el:
                    title = await title_el.get_attribute("aria-label") or ""
                    results.append(f"📰 {title}")
            except Exception:
                continue
        return "\n".join(results) if results else None
    except Exception:
        return None
    finally:
        await page.close()

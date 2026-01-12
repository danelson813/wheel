import asyncio
import random
import tomllib
import functools
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async
from fake_useragent import UserAgent
from selectolax.lexbor import LexborHTMLParser

# Initialize UserAgent once
ua = UserAgent()


def load_config():
    path = Path("pyproject.toml")
    if not path.exists():
        return {}
    with open(path, "rb") as f:
        return tomllib.load(f).get("tool", {}).get("scraper", {})


def retry_on_429(retries=3):
    """Specific decorator to handle rate limits with backoff."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                result = await func(*args, **kwargs)
                if result == "RETRY":
                    wait = (attempt + 1) * 5  # Exponential wait: 5s, 10s, 15s
                    print(f"⚠️ Rate limited. Backing off for {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                return result
            return None

        return wrapper

    return decorator


@retry_on_429(retries=3)
async def fetch_url(url, browser, semaphore, config):
    async with semaphore:
        # 1. Randomize Identity
        current_ua = ua.random
        proxy_list = config.get("proxies", [])
        proxy = {"server": random.choice(proxy_list)} if proxy_list else None

        context = await browser.new_context(
            user_agent=current_ua, proxy=proxy, viewport={"width": 1920, "height": 1080}
        )

        page = await context.new_page()
        # 2. Apply Stealth to mask Playwright fingerprints
        await stealth_async(page)

        try:
            # Human-like delay before navigation
            await asyncio.sleep(random.uniform(1, 3))

            response = await page.goto(
                url, wait_until="domcontentloaded", timeout=30000
            )

            if response.status == 429:
                return "RETRY"

            html = await page.content()
            return parse_data(html, url)
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
        finally:
            await context.close()


def parse_data(html, url):
    parser = LexborHTMLParser(html)
    return {
        "url": url,
        "title": parser.css_first("title").text().strip()
        if parser.css_first("title")
        else "N/A",
        "scraped_at": datetime.now().isoformat(),
    }


async def main():
    config = load_config()
    urls = config.get("urls", [])
    sem = asyncio.Semaphore(config.get("max_concurrent", 2))
    print(urls)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=config.get("headless", True))

        tasks = [fetch_url(url, browser, sem, config) for url in urls]
        results = await asyncio.gather(*tasks)

        # Filter None and process output
        final_results = [r for r in results if r and r != "RETRY"]
        print(f"✅ Finished! Scraped {len(final_results)} pages.")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

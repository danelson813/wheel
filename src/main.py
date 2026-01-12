import csv
import asyncio
import httpx
from selectolax.lexbor import LexborHTMLParser
from loguru import logger

from helpers.config import load_config


# Configs
app_config = load_config()
MAX_PAGES = app_config.get("MAX_PAGES")
BASE_URL = app_config.get("BASE_URL")
CONCURRENCY = app_config.get("CONCURRENCY")

# Define global headers to mimic a browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


async def fetch(client, url, semaphore):
    async with semaphore:
        try:
            # Use the client with headers
            response = await client.get(url, headers=HEADERS, timeout=10.0)
            if response.status_code != 200:
                logger.error(f"Failed to fetch {url}: Status {response.status_code}")
                return ""
            return response.text
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return ""


def save_2disk(list_data: list) -> None:
    if not list_data:
        return []
    keys = list_data[0].keys()
    with open("output.csv", "w", newline="", encoding="utf-8") as f:
        dict_writer = csv.DictWriter(f, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(list_data)


async def parse_page(html):
    if not html:
        return []

    parser = LexborHTMLParser(html)
    items = []

    # Update selectors to match your target site
    for node in parser.css("article"):
        title_node = node.css_first("a img")
        price_node = node.css_first(".price_color")
        rating_node = node.css_first("p")
        res = {
            "product": title_node.attributes.get("alt").strip()
            if title_node
            else "N/A",
            "price": float(price_node.text()[1:]) if price_node else "N/A",
            "rating": rating_node.attributes.get("class").split()[1]
            if rating_node
            else "N/A",
        }
        items.append(res)
    return items


async def main():
    semaphore = asyncio.Semaphore(CONCURRENCY)
    urls = [BASE_URL.format(i) for i in range(1, MAX_PAGES + 1)]

    async with httpx.AsyncClient() as client:
        # 1. Fetch all pages first
        fetch_tasks = [fetch(client, url, semaphore) for url in urls]
        pages_html = await asyncio.gather(*fetch_tasks)

        # 2. Parse the HTML results
        parse_tasks = [parse_page(html) for html in pages_html]
        results = await asyncio.gather(*parse_tasks)

        # Flatten the list of lists
        all_items = [item for page in results for item in page]

        logger.info(f"Scraped {len(all_items)} items from {len(urls)} pages.")
        save_2disk(all_items)


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
from playwright.async_api import async_playwright
from selectolax.lexbor import LexborHTMLParser


class AsyncScraper:
    def __init__(self, urls):
        self.urls = urls
        self.results = []

    async def fetch_page(self, context, url):
        """Fetches the HTML content of a single page using Playwright."""
        page = await context.new_page()
        try:
            # wait_until="networkidle" is useful for JS-heavy sites
            await page.goto(url, timeout=60000, wait_until="domcontentloaded")

            # Optional: Scroll or wait for specific elements if needed
            # await page.wait_for_selector(".target-element")

            html = await page.content()
            return html
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
        finally:
            await page.close()

    def parse_data(self, html):
        """Parses the HTML using Selectolax."""
        if not html:
            return None

        parser = LexborHTMLParser(html)

        # --- CUSTOM PARSING LOGIC GOES HERE ---
        # Example: Extracting all H1 text and links
        data = {
            "title": parser.css_first("title").text()
            if parser.css_first("title")
            else "N/A",
            "links": [
                node.attributes.get("href")
                for node in parser.css("a")
                if "href" in node.attributes
            ],
        }
        return data

    async def run(self):
        """Orchestrates the scraping process."""
        async with async_playwright() as p:
            # Launch browser (headless=True for speed)
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            )

            # Create a list of tasks for all URLs
            tasks = [self.fetch_page(context, url) for url in self.urls]

            # Execute tasks concurrently
            pages_content = await asyncio.gather(*tasks)

            # Parse each page's content
            for html in pages_content:
                if html:
                    parsed_item = self.parse_data(html)
                    self.results.append(parsed_item)

            await browser.close()
            return self.results


# --- Usage ---
if __name__ == "__main__":
    target_urls = [
        "https://www.google.com",
        "https://www.github.com",
        "https://www.python.org",
    ]

    scraper = AsyncScraper(target_urls)
    scraped_data = asyncio.run(scraper.run())

    for entry in scraped_data:
        print(f"Scraped: {entry['title']} with {len(entry['links'])} links found.")

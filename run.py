import asyncio
import json
import os
import re
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL")
OUTPUT_FILE = os.getenv("OUTPUT_FILE")
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36"
}


async def fetch_page(url):
    async with aiohttp.ClientSession() as session:
        response = await session.get(url, headers=headers)
        return await response.text()


async def extract_quotes_from_js(html_content):
    pattern = r"var data = (\[.*?\]);"
    match = re.search(pattern, html_content, re.DOTALL)
    if match:
        json_data = match.group(1)
        quotes_data = json.loads(json_data)

        quotes = []
        for q in quotes_data:
            soup = BeautifulSoup(q["text"], "html5lib")
            text = soup.get_text()
            quotes.append(
                {
                    "author": {
                        "name": q["author"]["name"],
                        "goodreads_link": q["author"]["goodreads_link"],
                        "slug": q["author"]["slug"],
                    },
                    "text": text,
                }
            )
        return quotes
    return []


async def scrape_quotes(url, collected=[]):
    content = await fetch_page(url)

    quotes = await extract_quotes_from_js(content)
    collected.extend(quotes)

    next_link_pattern = r'<li class="next">\s*<a href="(.*?)"'
    match = re.search(next_link_pattern, content)
    if match:
        next_url = urljoin(BASE_URL, match.group(1))
        await scrape_quotes(next_url, collected)

    return collected


async def main():
    quotes = await scrape_quotes(BASE_URL)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(quotes, file, ensure_ascii=False, indent=4)


asyncio.run(main())

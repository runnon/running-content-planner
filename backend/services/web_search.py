from typing import List, Optional

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def search_web(query: str, max_results: int = 8) -> List[dict]:
    """Search via DuckDuckGo using the ddgs library."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, max_results=max_results))
        return [
            {
                "title": r.get("title", ""),
                "url": r.get("href", ""),
                "snippet": r.get("body", ""),
            }
            for r in raw
        ]
    except Exception as e:
        print(f"[web_search] Search error: {e}")
        return []


def scrape_article(url: str, timeout: int = 10) -> Optional[str]:
    """Scrape readable text content from a URL."""
    try:
        if "amazon.com" in url or "ebay.com" in url or "facebook.com" in url:
            return None

        resp = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        resp.raise_for_status()

        if "text/html" not in resp.headers.get("Content-Type", ""):
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "iframe", "form"]):
            tag.decompose()

        candidates = [
            soup.find("article"),
            soup.find("main"),
            soup.find("div", {"class": lambda c: c and ("content" in c or "post" in c or "entry" in c or "article" in c)}) if soup else None,
            soup.find("body"),
        ]
        container = next((c for c in candidates if c), None)

        if not container:
            return None

        text = container.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.split("\n") if line.strip() and len(line.strip()) > 20]
        text = "\n".join(lines)

        if len(text) < 100:
            return None

        return text[:8000]
    except Exception:
        return None


def search_and_scrape(query: str, max_results: int = 5) -> List[dict]:
    """Search the web and scrape top results for full content."""
    search_results = search_web(query, max_results=max_results)
    enriched = []

    for result in search_results:
        content = scrape_article(result["url"])
        enriched.append({
            "title": result["title"],
            "url": result["url"],
            "snippet": result["snippet"],
            "full_text": content or result["snippet"],
        })

    return enriched


def search_races_broad() -> List[dict]:
    """Run broad searches for unsanctioned/underground races."""
    queries = [
        '"unsanctioned race" running',
        '"underground running race"',
        '"pop up race" running',
        '"guerrilla marathon"',
        '"bandit race" running',
        '"underground endurance race"',
        '"midnight run" race underground',
        '"alleycat race"',
        'unsanctioned running event history',
        'underground race culture running',
        'craziest unsanctioned races world',
    ]

    all_results = []
    seen_urls = set()

    for query in queries:
        results = search_web(query, max_results=5)
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_results.append({**r, "query": query})

    return all_results

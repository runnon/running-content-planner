from typing import List, Optional

import requests


SUBREDDITS = ["running", "ultrarunning", "trailrunning", "AdvancedRunning"]

HEADERS = {
    "User-Agent": "RunnnonContentEngine/1.0 (research tool for underground racing content)"
}


def search_reddit(query: str, subreddit: Optional[str] = None, limit: int = 10) -> List[dict]:
    """Search Reddit for posts matching a query using the public JSON API."""
    results = []

    subs = [subreddit] if subreddit else SUBREDDITS

    for sub in subs:
        try:
            url = f"https://www.reddit.com/r/{sub}/search.json"
            params = {
                "q": query,
                "restrict_sr": "on",
                "sort": "relevance",
                "t": "all",
                "limit": limit,
            }
            resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            for post in data.get("data", {}).get("children", []):
                p = post.get("data", {})
                results.append({
                    "title": p.get("title", ""),
                    "selftext": (p.get("selftext", "") or "")[:2000],
                    "url": f"https://reddit.com{p.get('permalink', '')}",
                    "subreddit": sub,
                    "score": p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                })
        except Exception:
            continue

    results.sort(key=lambda x: x.get("score", 0), reverse=True)
    return results


def search_races_reddit() -> List[dict]:
    """Search Reddit broadly for unsanctioned/underground race mentions."""
    queries = [
        "unsanctioned race",
        "underground race",
        "guerrilla running",
        "bandit race",
        "pop up race",
        "underground endurance",
        "alleycat race",
        "midnight run race",
    ]

    all_results = []
    seen_urls = set()

    for query in queries:
        results = search_reddit(query, limit=5)
        for r in results:
            if r["url"] not in seen_urls:
                seen_urls.add(r["url"])
                all_results.append(r)

    return all_results

"""
Instagram content discovery via web search.

Direct Instagram scraping requires authentication and is fragile.
Instead we search for Instagram content via DuckDuckGo and parse
what we can from the results — post URLs, usernames, caption previews.
"""

import re
from typing import List, Optional
from services.web_search import search_web, scrape_article

RACING_HASHTAGS = [
    "undergroundrace", "undergroundracing", "unsanctionedrace",
    "unsanctionedracing", "popuprace", "popupracing",
    "guerrillarunning", "guerrillarace", "alleycatrace",
    "alleycatracing", "midnightrun", "midnightrace",
    "banditrunner", "banditrace", "banditracing",
    "hashrun", "hashrunning", "roguerace",
    "illegalrace", "streetrace", "streetracing",
    "undergroundmarathon", "unsanctionedultra",
    "undergroundendurance", "popupmarathon",
]

CULTURE_HASHTAGS = [
    "runculture", "streetrunning", "runningcrew", "runcrew",
    "runclub", "buildinpublic",
]

ALL_HASHTAGS = RACING_HASHTAGS + CULTURE_HASHTAGS


def _parse_instagram_url(url: str) -> Optional[str]:
    """Extract a post shortcode from an Instagram URL."""
    match = re.search(r"instagram\.com/(?:p|reel)/([A-Za-z0-9_-]+)", url)
    return match.group(1) if match else None


def _extract_username_from_snippet(snippet: str) -> str:
    """Try to pull a username from a search snippet."""
    match = re.search(r"@([A-Za-z0-9_.]{2,})", snippet)
    if match:
        return match.group(1)
    match = re.search(r"from\s+([A-Za-z0-9_.]+)\s+on Instagram", snippet, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"([A-Za-z0-9_.]+)\s*[•·]\s*Follow", snippet)
    if match:
        return match.group(1)
    match = re.search(r"-\s+([A-Za-z0-9_.]+)\s+on\s+", snippet)
    if match:
        return match.group(1)
    return ""


def _try_scrape_ig_page(url: str) -> Optional[dict]:
    """Attempt to scrape extra info from an Instagram post page."""
    try:
        text = scrape_article(url, timeout=8)
        if not text:
            return None
        likes = 0
        like_match = re.search(r"([\d,]+)\s+likes?", text, re.IGNORECASE)
        if like_match:
            likes = int(like_match.group(1).replace(",", ""))
        comments = 0
        comment_match = re.search(r"([\d,]+)\s+comments?", text, re.IGNORECASE)
        if comment_match:
            comments = int(comment_match.group(1).replace(",", ""))
        caption = ""
        for line in text.split("\n"):
            if len(line) > 40 and ("#" in line or any(word in line.lower() for word in ["race", "run", "mile", "marathon", "trail"])):
                caption = line[:500]
                break
        return {"likes": likes, "comments": comments, "caption_extra": caption}
    except Exception:
        return None


def _parse_ig_search_snippet(title: str, snippet: str) -> dict:
    """Extract structured data from a DuckDuckGo search result about an IG post.
    Title format is often: 'Username on Instagram: "caption text..."'
    Snippet often has: 'N likes, N comments - username on Date: "caption"'
    """
    data = {"username": "", "caption": "", "likes": 0, "comments": 0, "posted_at": None}

    cleaned = re.sub(r"^[A-Z][a-z]{2}\s+\d{1,2},\s*\d{4}\s*[·\-]\s*", "", snippet)

    meta_match = re.match(
        r"([\d,]+)\s+likes?,\s*([\d,]+)\s+comments?\s*-\s*(.+?)\s+on\s+(.+?):\s*(.+)",
        cleaned, re.DOTALL
    )
    if meta_match:
        data["likes"] = int(meta_match.group(1).replace(",", ""))
        data["comments"] = int(meta_match.group(2).replace(",", ""))
        data["username"] = meta_match.group(3).strip().replace(" ", "")
        data["posted_at"] = meta_match.group(4).strip()
        caption_text = meta_match.group(5).strip().strip('""\u201c\u201d.').strip()
        data["caption"] = caption_text
        return data

    title_match = re.match(r"(.+?)\s+on Instagram:\s*(.+)", title, re.DOTALL)
    if title_match:
        data["username"] = title_match.group(1).strip().lstrip("@")
        data["caption"] = title_match.group(2).strip().strip('""\u201c\u201d').strip()
    else:
        data["username"] = _extract_username_from_snippet(cleaned + " " + title)
        data["caption"] = cleaned

    like_match = re.search(r"(\d[\d,]*)\s+likes?", cleaned, re.IGNORECASE)
    if like_match:
        data["likes"] = int(like_match.group(1).replace(",", ""))
    comment_match = re.search(r"(\d[\d,]*)\s+comments?", cleaned, re.IGNORECASE)
    if comment_match:
        data["comments"] = int(comment_match.group(1).replace(",", ""))

    return data


def scrape_hashtag(hashtag: str, max_posts: int = 20) -> List[dict]:
    """Find Instagram posts for a hashtag via web search."""
    results = search_web(
        f'site:instagram.com "#{hashtag}"',
        max_results=max_posts,
    )

    posts = []
    seen = set()

    for r in results:
        shortcode = _parse_instagram_url(r["url"])
        if not shortcode or shortcode in seen:
            continue
        seen.add(shortcode)

        parsed = _parse_ig_search_snippet(r.get("title", ""), r.get("snippet", ""))

        posts.append({
            "post_id": shortcode,
            "username": parsed["username"],
            "caption": parsed["caption"],
            "media_url": r["url"],
            "likes": parsed["likes"],
            "comments": parsed["comments"],
            "hashtags": [f"#{hashtag}"],
            "posted_at": parsed.get("posted_at"),
            "scraped_from": f"#{hashtag}",
        })

    return posts


BROAD_SEARCH_QUERIES = [
    'site:instagram.com "unsanctioned race"',
    'site:instagram.com "unsanctioned racing"',
    'site:instagram.com "underground race" running',
    'site:instagram.com "underground racing" running',
    'site:instagram.com "pop up race" running',
    'site:instagram.com "popup race" running',
    'site:instagram.com "bandit race" running',
    'site:instagram.com "alleycat race"',
    'site:instagram.com "guerrilla run"',
    'site:instagram.com "midnight run" race',
    'site:instagram.com "rogue race" running',
    'site:instagram.com "illegal race" running',
    'site:instagram.com "street race" running',
    'site:instagram.com underground marathon',
    'site:instagram.com unsanctioned ultramarathon',
]


def scrape_multiple_hashtags(
    hashtags: Optional[List[str]] = None, max_per_hashtag: int = 15
) -> List[dict]:
    """Search for posts across hashtags and broad keyword queries."""
    hashtags = hashtags or ALL_HASHTAGS
    seen = set()
    all_posts = []

    for tag in hashtags:
        posts = scrape_hashtag(tag, max_posts=max_per_hashtag)
        for post in posts:
            if post["post_id"] not in seen:
                seen.add(post["post_id"])
                all_posts.append(post)

    for query in BROAD_SEARCH_QUERIES:
        results = search_web(query, max_results=max_per_hashtag)
        for r in results:
            shortcode = _parse_instagram_url(r["url"])
            if not shortcode or shortcode in seen:
                continue
            seen.add(shortcode)
            parsed = _parse_ig_search_snippet(r.get("title", ""), r.get("snippet", ""))
            all_posts.append({
                "post_id": shortcode,
                "username": parsed["username"],
                "caption": parsed["caption"],
                "media_url": r["url"],
                "likes": parsed["likes"],
                "comments": parsed["comments"],
                "hashtags": [],
                "posted_at": parsed.get("posted_at"),
                "scraped_from": query.replace("site:instagram.com ", ""),
            })

    all_posts.sort(key=lambda x: x.get("likes", 0), reverse=True)
    return all_posts


def search_hashtag_for_race(race_name: str, max_posts: int = 10) -> List[dict]:
    """Find Instagram posts about a specific race via web search."""
    tag = race_name.lower().replace(" ", "").replace("-", "").replace("'", "")

    posts = scrape_hashtag(tag, max_posts=max_posts)

    if len(posts) < 3:
        extra = search_web(
            f'site:instagram.com "{race_name}" race',
            max_results=max_posts,
        )
        seen = {p["post_id"] for p in posts}
        for r in extra:
            shortcode = _parse_instagram_url(r["url"])
            if not shortcode or shortcode in seen:
                continue
            seen.add(shortcode)
            parsed = _parse_ig_search_snippet(r.get("title", ""), r.get("snippet", ""))
            posts.append({
                "post_id": shortcode,
                "username": parsed["username"],
                "caption": parsed["caption"],
                "media_url": r["url"],
                "likes": parsed["likes"],
                "comments": parsed["comments"],
                "hashtags": [],
                "posted_at": parsed.get("posted_at"),
                "scraped_from": f"search:{race_name}",
            })

    return posts

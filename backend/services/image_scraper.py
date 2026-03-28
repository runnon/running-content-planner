"""
Multi-source image scraper for finding race and topic photos.

Sources:
  1. DuckDuckGo Image Search — broad image results
  2. Reddit — image posts from running subreddits
  3. Instagram — DDG image search + CDN extraction from IG posts
  4. Web page scraping — extract high-quality images from relevant articles
"""

import hashlib
import os
import re
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

SKIP_DOMAINS = {
    "facebook.com", "amazon.com", "ebay.com", "tiktok.com",
    "pinterest.com", "shutterstock.com", "gettyimages.com",
    "istockphoto.com", "alamy.com", "dreamstime.com",
    "depositphotos.com", "123rf.com", "stock.adobe.com",
}

MIN_IMAGE_BYTES = 15_000
MIN_DIMENSION = 300


def _is_valid_image_url(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        return False
    domain = parsed.netloc.lower().replace("www.", "")
    ig_cdn = "cdninstagram.com" in domain or "fbcdn.net" in domain
    if not ig_cdn and any(skip in domain for skip in SKIP_DOMAINS):
        return False
    path_lower = parsed.path.lower()
    if any(path_lower.endswith(ext) for ext in (".svg", ".gif", ".ico")):
        return False
    return True


def _url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()[:16]


def _download_image(url: str, timeout: int = 12) -> Optional[dict]:
    """Download an image and save it locally. Returns metadata or None."""
    try:
        if not _is_valid_image_url(url):
            return None

        resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type:
            return None

        data = resp.content
        if len(data) < MIN_IMAGE_BYTES:
            return None

        ext = ".jpg"
        if "png" in content_type:
            ext = ".png"
        elif "webp" in content_type:
            ext = ".webp"

        filename = f"{_url_hash(url)}{ext}"
        filepath = IMAGES_DIR / filename
        filepath.write_bytes(data)

        width, height = _get_dimensions(data)
        if width and height and (width < MIN_DIMENSION or height < MIN_DIMENSION):
            filepath.unlink(missing_ok=True)
            return None

        return {
            "filename": filename,
            "local_path": str(filepath),
            "file_size": len(data),
            "width": width,
            "height": height,
        }
    except Exception:
        return None


def _get_dimensions(data: bytes) -> tuple:
    """Extract width/height from image binary without PIL."""
    try:
        if data[:8] == b'\x89PNG\r\n\x1a\n':
            w = int.from_bytes(data[16:20], 'big')
            h = int.from_bytes(data[20:24], 'big')
            return w, h
        if data[:2] == b'\xff\xd8':
            idx = 2
            while idx < len(data) - 8:
                if data[idx] != 0xFF:
                    break
                marker = data[idx + 1]
                size = int.from_bytes(data[idx + 2:idx + 4], 'big')
                if marker in (0xC0, 0xC1, 0xC2):
                    h = int.from_bytes(data[idx + 5:idx + 7], 'big')
                    w = int.from_bytes(data[idx + 7:idx + 9], 'big')
                    return w, h
                idx += 2 + size
    except Exception:
        pass
    return None, None


def search_ddg_images(query: str, max_results: int = 20) -> List[dict]:
    """Search DuckDuckGo for images matching a query."""
    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            raw = list(ddgs.images(query, max_results=max_results))
        results = []
        for r in raw:
            image_url = r.get("image", "")
            if not image_url or not _is_valid_image_url(image_url):
                continue
            results.append({
                "source_url": image_url,
                "title": r.get("title", ""),
                "source_page": r.get("url", ""),
                "source_type": "ddg",
                "width": r.get("width"),
                "height": r.get("height"),
            })
        return results
    except Exception as e:
        print(f"[image_scraper] DDG image search error: {e}")
        return []


def search_reddit_images(
    query: str,
    subreddits: Optional[List[str]] = None,
    limit: int = 15,
) -> List[dict]:
    """Search Reddit for image posts matching a query."""
    subs = subreddits or [
        "running", "ultrarunning", "trailrunning",
        "AdvancedRunning", "Marathon", "pics",
    ]
    results = []
    seen_urls = set()

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
            resp = requests.get(
                url,
                headers={"User-Agent": "RunnnonImageScraper/1.0"},
                params=params,
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            for post in data.get("data", {}).get("children", []):
                p = post.get("data", {})
                post_url = p.get("url", "")

                is_image = (
                    post_url.endswith((".jpg", ".jpeg", ".png"))
                    or "i.redd.it" in post_url
                    or "i.imgur.com" in post_url
                )
                if not is_image or post_url in seen_urls:
                    continue
                seen_urls.add(post_url)

                if post_url.startswith("https://i.imgur.com/") and "." not in post_url.split("/")[-1]:
                    post_url += ".jpg"

                results.append({
                    "source_url": post_url,
                    "title": p.get("title", ""),
                    "source_page": f"https://reddit.com{p.get('permalink', '')}",
                    "source_type": "reddit",
                })

                preview = p.get("preview", {})
                if preview and preview.get("images"):
                    source_img = preview["images"][0].get("source", {})
                    if source_img.get("url"):
                        hi_res = source_img["url"].replace("&amp;", "&")
                        if hi_res not in seen_urls:
                            seen_urls.add(hi_res)
                            results.append({
                                "source_url": hi_res,
                                "title": p.get("title", "") + " (hi-res)",
                                "source_page": f"https://reddit.com{p.get('permalink', '')}",
                                "source_type": "reddit",
                            })
            time.sleep(0.5)
        except Exception:
            continue

    return results


def _extract_ig_cdn_urls(html: str) -> List[str]:
    """Pull Instagram CDN image URLs from an IG page's HTML."""
    urls = []
    patterns = [
        re.compile(r'"display_url"\s*:\s*"([^"]+)"'),
        re.compile(r'"display_src"\s*:\s*"([^"]+)"'),
        re.compile(r'"src"\s*:\s*"(https://scontent[^"]+)"'),
        re.compile(r'"thumbnail_src"\s*:\s*"([^"]+)"'),
    ]
    for pat in patterns:
        for match in pat.finditer(html):
            raw = match.group(1).replace("\\u0026", "&").replace("\\/", "/")
            if "scontent" in raw and raw not in urls:
                urls.append(raw)

    soup = BeautifulSoup(html, "html.parser")
    for meta in soup.find_all("meta", property="og:image"):
        content = meta.get("content", "")
        if content and "scontent" in content and content not in urls:
            urls.append(content)
    for meta in soup.find_all("meta", attrs={"name": "twitter:image"}):
        content = meta.get("content", "")
        if content and "scontent" in content and content not in urls:
            urls.append(content)

    return urls


def search_instagram_images(
    query: str,
    max_results: int = 15,
) -> List[dict]:
    """
    Find Instagram images for a topic via multiple strategies:
      1. DDG image search scoped to instagram.com
      2. DDG text search for IG post URLs, then extract CDN images from the pages
    """
    results = []
    seen_urls = set()

    try:
        from ddgs import DDGS

        ig_queries = [
            f'site:instagram.com "{query}" race',
            f'site:instagram.com "{query}"',
            f'site:instagram.com #{query.lower().replace(" ", "")}',
        ]

        for q in ig_queries:
            try:
                with DDGS() as ddgs:
                    raw = list(ddgs.images(q, max_results=max_results))
                for r in raw:
                    image_url = r.get("image", "")
                    if not image_url or image_url in seen_urls:
                        continue
                    if not image_url.startswith("http"):
                        continue
                    seen_urls.add(image_url)
                    results.append({
                        "source_url": image_url,
                        "title": r.get("title", ""),
                        "source_page": r.get("url", ""),
                        "source_type": "instagram",
                        "width": r.get("width"),
                        "height": r.get("height"),
                    })
            except Exception:
                continue

        ig_post_urls = []
        for q in ig_queries[:2]:
            try:
                with DDGS() as ddgs:
                    text_results = list(ddgs.text(q, max_results=10))
                for r in text_results:
                    url = r.get("href", "")
                    if re.search(r"instagram\.com/(?:p|reel)/[A-Za-z0-9_-]+", url):
                        ig_post_urls.append(url)
            except Exception:
                continue

        for post_url in ig_post_urls[:8]:
            try:
                resp = requests.get(
                    post_url,
                    headers=HEADERS,
                    timeout=8,
                    allow_redirects=True,
                )
                if resp.status_code != 200:
                    continue
                cdn_urls = _extract_ig_cdn_urls(resp.text)
                for cdn_url in cdn_urls[:2]:
                    if cdn_url not in seen_urls:
                        seen_urls.add(cdn_url)
                        results.append({
                            "source_url": cdn_url,
                            "title": f"Instagram post",
                            "source_page": post_url,
                            "source_type": "instagram",
                        })
            except Exception:
                continue

    except Exception as e:
        print(f"[image_scraper] Instagram search error: {e}")

    return results


def scrape_page_images(url: str, min_size: int = 400) -> List[dict]:
    """Scrape a web page for large, relevant images."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        if "text/html" not in resp.headers.get("Content-Type", ""):
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        images = []
        seen = set()

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src") or ""
            srcset = img.get("srcset", "")

            if srcset:
                parts = srcset.split(",")
                best_src = parts[-1].strip().split()[0]
                if best_src.startswith("http"):
                    src = best_src

            if not src.startswith("http"):
                if src.startswith("//"):
                    src = "https:" + src
                elif src.startswith("/"):
                    parsed = urlparse(url)
                    src = f"{parsed.scheme}://{parsed.netloc}{src}"
                else:
                    continue

            if src in seen:
                continue
            seen.add(src)

            w = _parse_int(img.get("width"))
            h = _parse_int(img.get("height"))
            if (w and w < min_size) or (h and h < min_size):
                continue

            if not _is_valid_image_url(src):
                continue

            alt = img.get("alt", "")
            images.append({
                "source_url": src,
                "title": alt or img.get("title", ""),
                "source_page": url,
                "source_type": "web",
                "width": w,
                "height": h,
            })

        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            og_src = og_image["content"]
            if og_src not in seen and _is_valid_image_url(og_src):
                images.insert(0, {
                    "source_url": og_src,
                    "title": "Featured image",
                    "source_page": url,
                    "source_type": "web",
                })

        return images
    except Exception:
        return []


def _parse_int(val) -> Optional[int]:
    if not val:
        return None
    try:
        return int(re.sub(r"[^\d]", "", str(val)))
    except (ValueError, TypeError):
        return None


def find_images_for_topic(
    topic: str,
    race_name: Optional[str] = None,
    source_links: Optional[List[str]] = None,
    max_total: int = 40,
) -> List[dict]:
    """
    Orchestrate multi-source image search for a topic/race.
    Returns a list of image metadata dicts ready for download.
    """
    all_images = []
    seen_urls = set()

    def _add(images: List[dict]):
        for img in images:
            url = img["source_url"]
            if url not in seen_urls:
                seen_urls.add(url)
                all_images.append(img)

    search_term = race_name or topic
    queries = [
        f'"{search_term}" race photos',
        f'"{search_term}" running race',
        f'{search_term} marathon race course',
    ]

    for q in queries:
        _add(search_ddg_images(q, max_results=15))
        if len(all_images) >= max_total:
            break

    _add(search_instagram_images(search_term, max_results=15))

    _add(search_reddit_images(search_term, limit=10))

    if source_links:
        for link in source_links[:5]:
            _add(scrape_page_images(link))

    if len(all_images) < 10:
        fallback_queries = [
            f"{search_term} race",
            f"{search_term} running event",
            f"{search_term} race start line finish",
        ]
        for q in fallback_queries:
            _add(search_ddg_images(q, max_results=10))
            if len(all_images) >= max_total:
                break

    return all_images[:max_total]


def download_and_save_images(
    images: List[dict],
    max_downloads: int = 30,
) -> List[dict]:
    """Download images and return metadata for successfully saved ones."""
    saved = []
    for img in images[:max_downloads]:
        result = _download_image(img["source_url"])
        if result:
            saved.append({
                **img,
                **result,
            })
    return saved

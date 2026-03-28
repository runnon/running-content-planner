import re
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from database import get_db
from models import Content
from services.instagram import scrape_multiple_hashtags, RACING_HASHTAGS, CULTURE_HASHTAGS, ALL_HASHTAGS

router = APIRouter(prefix="/api/content", tags=["content"])


def _try_parse_date(val) -> datetime:
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except (ValueError, TypeError):
        pass
    from dateutil import parser as dateparser
    try:
        return dateparser.parse(str(val))
    except Exception:
        return None


def _parse_ig_meta_caption(raw: str) -> dict:
    """Parse Instagram's metadata caption format:
    '108 likes, 13 comments - username on March 27, 2026: "actual caption".'
    """
    pattern = r'^([\d,]+)\s+likes?,\s*([\d,]+)\s+comments?\s*-\s*(.+?)\s+on\s+(.+?):\s*["\u201c]?(.*?)["\u201d]?\s*\.?\s*$'
    match = re.match(pattern, raw, re.DOTALL)
    if not match:
        return {}

    return {
        "likes": int(match.group(1).replace(",", "")),
        "comments": int(match.group(2).replace(",", "")),
        "username": match.group(3).strip().replace(" ", ""),
        "date": match.group(4).strip(),
        "caption": match.group(5).strip(),
    }


EXCLUDE_KEYWORDS = {
    "car", "cars", "automotive", "automobile", "motorsport", "motorsports",
    "nascar", "formula1", "f1", "drifting", "drift", "dragrace", "dragracing",
    "xdrive", "bmw", "mercedes", "audi", "porsche", "ferrari", "lamborghini",
    "mustang", "corvette", "camaro", "supra", "gtr", "turbo", "horsepower",
    "assettocorsa", "videogames", "gaming", "simulator", "simracing",
    "carbmeet", "carmeet", "carshow", "carsofinstagram", "carculture",
    "jdm", "tuner", "tuning", "supercar", "hypercar", "exhaust",
    "motorcycle", "motorbike", "moto", "motocross", "superbike",
    "boat", "boatracing", "jetski", "horse", "horseracing", "derby",
    "germanycars", "germancar", "americanmuscle", "v8", "v12",
}

REQUIRE_KEYWORDS = {
    "run", "running", "runner", "runners", "marathon", "marathons",
    "ultra", "ultramarathon", "ultrarunning", "trail", "trailrunning",
    "5k", "10k", "halfmarathon", "mile", "miler", "relay",
    "cycling", "cyclist", "bike", "biking", "gravel", "roadbike",
    "triathlon", "triathlete", "ironman", "endurance", "race", "racing",
    "sprint", "track", "trackandfield", "crosscountry", "xc",
    "runcrew", "runclub", "runningcrew", "jogger", "jogging",
    "obstacle", "ocr", "spartan", "toughmudder",
    "unsanctioned", "underground", "bandit", "guerrilla", "alleycat",
    "popuprace", "midnightrun", "hashrun",
}


def _is_endurance_content(caption: str, hashtags: list) -> bool:
    """Return True only if the post is about running/cycling/endurance, not cars."""
    text = (caption + " " + " ".join(hashtags)).lower()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    words = set(text.split())

    if words & EXCLUDE_KEYWORDS:
        return False

    if words & REQUIRE_KEYWORDS:
        return True

    return False


class ScrapeRequest(BaseModel):
    hashtags: Optional[List[str]] = None
    category: Optional[str] = None
    max_per_hashtag: int = 15


@router.get("")
async def list_content(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Content).order_by(Content.likes.desc()).offset(offset).limit(limit)
    )
    items = result.scalars().all()
    return [
        {
            "id": c.id,
            "platform": c.platform,
            "post_id": c.post_id,
            "username": c.username,
            "caption": c.caption,
            "media_url": c.media_url,
            "likes": c.likes,
            "comments": c.comments,
            "hashtags": c.hashtags or [],
            "scraped_from": c.scraped_from,
            "posted_at": c.posted_at.isoformat() if c.posted_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in items
    ]


@router.post("/scrape")
async def scrape_content(req: ScrapeRequest, db: AsyncSession = Depends(get_db)):
    if req.hashtags:
        hashtags = req.hashtags
    elif req.category == "racing":
        hashtags = RACING_HASHTAGS
    elif req.category == "culture":
        hashtags = CULTURE_HASHTAGS
    else:
        hashtags = ALL_HASHTAGS

    posts = scrape_multiple_hashtags(hashtags=hashtags, max_per_hashtag=req.max_per_hashtag)

    saved = 0
    for post in posts:
        existing = await db.execute(
            select(Content).where(Content.post_id == post["post_id"])
        )
        if existing.scalar_one_or_none():
            continue

        caption = post["caption"] or ""
        username = post["username"] or ""
        likes = post["likes"] or 0
        comments = post["comments"] or 0
        posted_at_val = post.get("posted_at")

        parsed = _parse_ig_meta_caption(caption)
        if parsed:
            if not username:
                username = parsed["username"]
            if likes == 0:
                likes = parsed["likes"]
            if comments == 0:
                comments = parsed["comments"]
            caption = parsed["caption"]
            if not posted_at_val and parsed.get("date"):
                posted_at_val = parsed["date"]

        if (likes + comments) < 500:
            continue

        all_hashtags = post.get("hashtags", [])
        if not _is_endurance_content(caption, all_hashtags):
            continue

        content = Content(
            platform="instagram",
            post_id=post["post_id"],
            username=username,
            caption=caption,
            media_url=post["media_url"],
            likes=likes,
            comments=comments,
            hashtags=post["hashtags"],
            scraped_from=post["scraped_from"],
            posted_at=_try_parse_date(posted_at_val),
        )
        db.add(content)
        saved += 1

    await db.commit()
    return {"scraped": len(posts), "new_saved": saved}

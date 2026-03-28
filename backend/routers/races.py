import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Race, DiscoveredRace, RaceImage
from services.race_researcher import research_race, discover_races, enrich_race_with_url, deepen_research
from services.image_scraper import find_images_for_topic, download_and_save_images

router = APIRouter(prefix="/api/races", tags=["races"])


class ResearchRequest(BaseModel):
    race_name: str


class AddSourceRequest(BaseModel):
    url: str


class QueueUpdate(BaseModel):
    queued_for_weekly: bool


def normalize_race_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


async def mark_discovered_as_researched(db: AsyncSession, race_name: str, race_id: int) -> None:
    normalized_name = normalize_race_name(race_name)
    result = await db.execute(select(DiscoveredRace).where(DiscoveredRace.researched == False))
    matches = [
        item for item in result.scalars().all()
        if normalize_race_name(item.name) == normalized_name
    ]
    for item in matches:
        item.researched = True
        item.race_id = race_id


@router.get("")
async def list_races(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Race).order_by(Race.created_at.desc()))
    races = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "location": r.location,
            "origin_year": r.origin_year,
            "origin_story": r.origin_story,
            "what_makes_it_wild": r.what_makes_it_wild,
            "status": r.status,
            "last_known_date": r.last_known_date,
            "next_upcoming_date": r.next_upcoming_date,
            "notable_moments": r.notable_moments,
            "source_links": r.source_links or [],
            "video_angle": r.video_angle,
            "queued_for_weekly": r.queued_for_weekly,
            "queue_date": r.queue_date.isoformat() if r.queue_date else None,
            "covered": r.covered or False,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in races
    ]


@router.get("/{race_id}")
async def get_race(race_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Race).where(Race.id == race_id))
    race = result.scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    return {
        "id": race.id,
        "name": race.name,
        "location": race.location,
        "origin_year": race.origin_year,
        "origin_story": race.origin_story,
        "what_makes_it_wild": race.what_makes_it_wild,
        "status": race.status,
        "last_known_date": race.last_known_date,
        "next_upcoming_date": race.next_upcoming_date,
        "notable_moments": race.notable_moments,
        "source_links": race.source_links or [],
        "video_angle": race.video_angle,
        "queued_for_weekly": race.queued_for_weekly,
        "queue_date": race.queue_date.isoformat() if race.queue_date else None,
        "covered": race.covered or False,
        "raw_research": race.raw_research,
        "created_at": race.created_at.isoformat() if race.created_at else None,
    }


@router.post("/research")
async def research_race_endpoint(req: ResearchRequest, db: AsyncSession = Depends(get_db)):
    normalized_name = normalize_race_name(req.race_name.strip())
    if not normalized_name:
        raise HTTPException(status_code=422, detail="Race name is required")

    existing = await db.execute(select(Race))
    existing_race = next(
        (race for race in existing.scalars().all() if normalize_race_name(race.name) == normalized_name),
        None,
    )
    if existing_race:
        await mark_discovered_as_researched(db, existing_race.name, existing_race.id)
        await db.commit()
        return {"id": existing_race.id, "name": existing_race.name, "existing": True}

    profile = await research_race(req.race_name)

    # Require actual research details before adding to the vault
    detail_fields = ["origin_story", "what_makes_it_wild", "notable_moments"]
    has_details = any(
        profile.get(f, "").strip() for f in detail_fields
    )
    if not has_details:
        raise HTTPException(
            status_code=422,
            detail=f"Not enough information found for '{req.race_name}'. Research returned empty details — try a different name or add a source URL manually.",
        )

    race = Race(
        name=profile.get("name", req.race_name),
        location=profile.get("location", ""),
        origin_year=profile.get("origin_year", ""),
        origin_story=profile.get("origin_story", ""),
        what_makes_it_wild=profile.get("what_makes_it_wild", ""),
        status=profile.get("status", ""),
        last_known_date=profile.get("last_known_date", ""),
        next_upcoming_date=profile.get("next_upcoming_date", ""),
        notable_moments=profile.get("notable_moments", ""),
        source_links=profile.get("source_links", []),
        video_angle=profile.get("video_angle", ""),
        raw_research=profile.get("raw_research", ""),
    )
    db.add(race)
    await db.commit()
    await db.refresh(race)
    await mark_discovered_as_researched(db, race.name, race.id)
    await db.commit()

    return {"id": race.id, "name": race.name, "profile": profile}


@router.post("/discover")
async def discover_races_endpoint(db: AsyncSession = Depends(get_db)):
    discovered = await discover_races()

    existing = await db.execute(select(Race.name))
    existing_names = {normalize_race_name(r) for r in existing.scalars().all()}

    already_discovered = await db.execute(select(DiscoveredRace.name))
    already_names = {normalize_race_name(r) for r in already_discovered.scalars().all()}

    new_races = []
    for race_data in discovered:
        name = race_data.get("name", "").strip()
        normalized_name = normalize_race_name(name)
        if not normalized_name:
            continue
        if normalized_name in existing_names or normalized_name in already_names:
            continue

        dr = DiscoveredRace(
            name=name,
            snippet=race_data.get("snippet", ""),
            source=race_data.get("source", ""),
            source_url=race_data.get("source_url", ""),
        )
        db.add(dr)
        new_races.append(race_data)
        already_names.add(normalized_name)

    await db.commit()
    return {"discovered": new_races, "count": len(new_races)}


@router.get("/discovered/list")
async def list_discovered(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DiscoveredRace).where(DiscoveredRace.researched == False).order_by(DiscoveredRace.created_at.desc())
    )
    items = result.scalars().all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "snippet": d.snippet,
            "source": d.source,
            "source_url": d.source_url,
            "created_at": d.created_at.isoformat() if d.created_at else None,
        }
        for d in items
    ]


@router.patch("/{race_id}")
async def update_race(race_id: int, update: QueueUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Race).where(Race.id == race_id))
    race = result.scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    race.queued_for_weekly = update.queued_for_weekly
    race.queue_date = datetime.utcnow() if update.queued_for_weekly else None
    await db.commit()
    return {"id": race.id, "queued_for_weekly": race.queued_for_weekly}


@router.patch("/{race_id}/covered")
async def toggle_covered(race_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Race).where(Race.id == race_id))
    race = result.scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    race.covered = not (race.covered or False)
    await db.commit()
    return {"id": race.id, "covered": race.covered}


@router.delete("/{race_id}")
async def delete_race(race_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Race).where(Race.id == race_id))
    race = result.scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")
    await db.delete(race)
    await db.commit()
    return {"deleted": True}


@router.post("/{race_id}/research-more")
async def research_more_endpoint(race_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Race).where(Race.id == race_id))
    race = result.scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    existing_profile = {
        "name": race.name,
        "location": race.location,
        "origin_year": race.origin_year,
        "origin_story": race.origin_story,
        "what_makes_it_wild": race.what_makes_it_wild,
        "status": race.status,
        "last_known_date": race.last_known_date,
        "next_upcoming_date": race.next_upcoming_date,
        "notable_moments": race.notable_moments,
        "source_links": race.source_links or [],
        "video_angle": race.video_angle,
        "raw_research": race.raw_research or "",
    }

    updated = await deepen_research(race.name, existing_profile)

    race.location = updated.get("location", race.location)
    race.origin_year = updated.get("origin_year", race.origin_year)
    race.origin_story = updated.get("origin_story", race.origin_story)
    race.what_makes_it_wild = updated.get("what_makes_it_wild", race.what_makes_it_wild)
    race.status = updated.get("status", race.status)
    race.last_known_date = updated.get("last_known_date", race.last_known_date)
    race.next_upcoming_date = updated.get("next_upcoming_date", race.next_upcoming_date)
    race.notable_moments = updated.get("notable_moments", race.notable_moments)
    race.source_links = updated.get("source_links", race.source_links)
    race.video_angle = updated.get("video_angle", race.video_angle)
    race.raw_research = updated.get("raw_research", race.raw_research)
    race.updated_at = datetime.utcnow()

    await db.commit()
    return {"id": race.id, "name": race.name, "updated": True}


@router.post("/{race_id}/add-source")
async def add_source(race_id: int, req: AddSourceRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Race).where(Race.id == race_id))
    race = result.scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    existing_profile = {
        "name": race.name,
        "location": race.location,
        "origin_year": race.origin_year,
        "origin_story": race.origin_story,
        "what_makes_it_wild": race.what_makes_it_wild,
        "status": race.status,
        "last_known_date": race.last_known_date,
        "next_upcoming_date": race.next_upcoming_date,
        "notable_moments": race.notable_moments,
        "source_links": race.source_links or [],
        "video_angle": race.video_angle,
    }

    updated = await enrich_race_with_url(existing_profile, req.url)

    race.location = updated.get("location", race.location)
    race.origin_year = updated.get("origin_year", race.origin_year)
    race.origin_story = updated.get("origin_story", race.origin_story)
    race.what_makes_it_wild = updated.get("what_makes_it_wild", race.what_makes_it_wild)
    race.status = updated.get("status", race.status)
    race.notable_moments = updated.get("notable_moments", race.notable_moments)
    race.source_links = updated.get("source_links", race.source_links)
    race.video_angle = updated.get("video_angle", race.video_angle)
    race.updated_at = datetime.utcnow()

    await db.commit()
    return {"id": race.id, "name": race.name, "updated": True}


# --- Image endpoints ---


def _image_to_dict(img: RaceImage) -> dict:
    return {
        "id": img.id,
        "race_id": img.race_id,
        "source_url": img.source_url,
        "local_url": f"/images/{img.filename}" if img.filename else "",
        "filename": img.filename,
        "title": img.title,
        "source_page": img.source_page,
        "source_type": img.source_type,
        "width": img.width,
        "height": img.height,
        "file_size": img.file_size,
        "starred": img.starred,
        "created_at": img.created_at.isoformat() if img.created_at else None,
    }


@router.get("/{race_id}/images")
async def list_race_images(race_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RaceImage)
        .where(RaceImage.race_id == race_id)
        .order_by(RaceImage.starred.desc(), RaceImage.created_at.desc())
    )
    images = result.scalars().all()
    return [_image_to_dict(img) for img in images]


@router.post("/{race_id}/images/scrape")
async def scrape_race_images(race_id: int, db: AsyncSession = Depends(get_db)):
    """Find and download images for a race from multiple sources."""
    result = await db.execute(select(Race).where(Race.id == race_id))
    race = result.scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    existing = await db.execute(
        select(RaceImage.source_url).where(RaceImage.race_id == race_id)
    )
    existing_urls = {row for row in existing.scalars().all()}

    candidates = find_images_for_topic(
        topic=race.name,
        race_name=race.name,
        source_links=race.source_links or [],
    )

    new_candidates = [c for c in candidates if c["source_url"] not in existing_urls]

    saved = download_and_save_images(new_candidates, max_downloads=30)

    new_count = 0
    for img_data in saved:
        race_image = RaceImage(
            race_id=race_id,
            source_url=img_data["source_url"],
            local_path=img_data.get("local_path", ""),
            filename=img_data.get("filename", ""),
            title=img_data.get("title", ""),
            source_page=img_data.get("source_page", ""),
            source_type=img_data.get("source_type", ""),
            width=img_data.get("width"),
            height=img_data.get("height"),
            file_size=img_data.get("file_size"),
        )
        db.add(race_image)
        new_count += 1

    await db.commit()

    all_images = await db.execute(
        select(RaceImage)
        .where(RaceImage.race_id == race_id)
        .order_by(RaceImage.starred.desc(), RaceImage.created_at.desc())
    )
    return {
        "new_count": new_count,
        "total": len(saved) + len(existing_urls),
        "images": [_image_to_dict(img) for img in all_images.scalars().all()],
    }


@router.patch("/{race_id}/images/{image_id}/star")
async def toggle_star_image(race_id: int, image_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RaceImage).where(RaceImage.id == image_id, RaceImage.race_id == race_id)
    )
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    img.starred = not img.starred
    await db.commit()
    return _image_to_dict(img)


@router.delete("/{race_id}/images/{image_id}")
async def delete_race_image(race_id: int, image_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(RaceImage).where(RaceImage.id == image_id, RaceImage.race_id == race_id)
    )
    img = result.scalar_one_or_none()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")

    if img.local_path:
        import os
        try:
            os.unlink(img.local_path)
        except OSError:
            pass

    await db.delete(img)
    await db.commit()
    return {"deleted": True}

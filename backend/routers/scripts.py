from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import Script, Race
from services.script_writer import generate_script

router = APIRouter(prefix="/api/scripts", tags=["scripts"])


class GenerateRequest(BaseModel):
    topic: str
    script_type: str = "race_history"
    target_duration: str = "60_90"
    tone: str = "full_send"
    race_id: Optional[int] = None


@router.get("")
async def list_scripts(race_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    query = select(Script)
    if race_id is not None:
        query = query.where(Script.race_id == race_id)
    result = await db.execute(query.order_by(Script.created_at.desc()))
    scripts = result.scalars().all()
    return [
        {
            "id": s.id,
            "race_id": s.race_id,
            "script_type": s.script_type,
            "target_duration": s.target_duration or "60_90",
            "tone": s.tone,
            "topic": s.topic,
            "hooks": s.hooks or [],
            "body": s.body,
            "visual_notes": s.visual_notes,
            "cta": s.cta,
            "hashtags": s.hashtags,
            "caption": s.caption,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in scripts
    ]


@router.get("/{script_id}")
async def get_script(script_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Script).where(Script.id == script_id))
    script = result.scalar_one_or_none()
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")
    return {
        "id": script.id,
        "race_id": script.race_id,
        "script_type": script.script_type,
        "target_duration": script.target_duration or "60_90",
        "tone": script.tone,
        "topic": script.topic,
        "hooks": script.hooks or [],
        "body": script.body,
        "visual_notes": script.visual_notes,
        "cta": script.cta,
        "hashtags": script.hashtags,
        "caption": script.caption,
        "created_at": script.created_at.isoformat() if script.created_at else None,
    }


@router.post("/generate")
async def generate_script_endpoint(req: GenerateRequest, db: AsyncSession = Depends(get_db)):
    race_context = ""
    if req.race_id:
        result = await db.execute(select(Race).where(Race.id == req.race_id))
        race = result.scalar_one_or_none()
        if race:
            race_context = (
                f"Race: {race.name}\n"
                f"Location: {race.location}\n"
                f"Origin Year: {race.origin_year}\n"
                f"Origin Story: {race.origin_story}\n"
                f"What Makes It Wild: {race.what_makes_it_wild}\n"
                f"Status: {race.status}\n"
                f"Notable Moments: {race.notable_moments}\n"
            )

    result = await generate_script(
        topic=req.topic,
        script_type=req.script_type,
        tone=req.tone,
        target_duration=req.target_duration,
        race_context=race_context,
    )

    script = Script(
        race_id=req.race_id,
        script_type=req.script_type,
        target_duration=req.target_duration,
        tone=req.tone,
        topic=req.topic,
        hooks=result.get("hooks", []),
        body=result.get("body", ""),
        visual_notes=result.get("visual_notes", ""),
        cta=result.get("cta", ""),
        hashtags=result.get("hashtags", ""),
        caption=result.get("caption", ""),
    )
    db.add(script)
    await db.commit()
    await db.refresh(script)

    return {
        "id": script.id,
        "hooks": script.hooks,
        "body": script.body,
        "visual_notes": script.visual_notes,
        "cta": script.cta,
        "hashtags": script.hashtags,
        "caption": script.caption,
        "script_type": script.script_type,
        "target_duration": script.target_duration,
        "tone": script.tone,
        "topic": script.topic,
    }

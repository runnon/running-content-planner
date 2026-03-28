from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import CalendarDay, Theme, DailyAnswer, GeneratedContent, Race, RaceImage, ContentImage

router = APIRouter(prefix="/api/questions", tags=["questions"])


class AnswerRequest(BaseModel):
    question_order: int
    answer_text: str


class GenerateRequest(BaseModel):
    tone: str = "full_send"
    target_duration: str = "60_90"


class LinkRaceRequest(BaseModel):
    race_id: int


@router.get("/{calendar_day_id}")
async def get_questions(calendar_day_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CalendarDay).where(CalendarDay.id == calendar_day_id)
    )
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(status_code=404, detail="Calendar day not found")

    result = await db.execute(select(Theme).where(Theme.id == day.theme_id))
    theme = result.scalar_one_or_none()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found for this day")

    result = await db.execute(
        select(DailyAnswer)
        .where(DailyAnswer.calendar_day_id == calendar_day_id)
        .order_by(DailyAnswer.question_order)
    )
    answers = result.scalars().all()

    if not answers:
        for i, q in enumerate(theme.questions or []):
            answer = DailyAnswer(
                calendar_day_id=calendar_day_id,
                question_text=q,
                answer_text="",
                question_order=i,
            )
            db.add(answer)
        await db.commit()

        result = await db.execute(
            select(DailyAnswer)
            .where(DailyAnswer.calendar_day_id == calendar_day_id)
            .order_by(DailyAnswer.question_order)
        )
        answers = result.scalars().all()

    return {
        "calendar_day_id": calendar_day_id,
        "theme_name": theme.name,
        "theme_slug": theme.slug,
        "questions": [
            {
                "question_text": a.question_text,
                "answer_text": a.answer_text,
                "question_order": a.question_order,
            }
            for a in answers
        ],
    }


@router.post("/{calendar_day_id}/answer")
async def save_answer(
    calendar_day_id: int, req: AnswerRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(DailyAnswer).where(
            DailyAnswer.calendar_day_id == calendar_day_id,
            DailyAnswer.question_order == req.question_order,
        )
    )
    answer = result.scalar_one_or_none()
    if not answer:
        raise HTTPException(status_code=404, detail="Answer not found for this question")

    answer.answer_text = req.answer_text
    await db.flush()

    result = await db.execute(
        select(CalendarDay).where(CalendarDay.id == calendar_day_id)
    )
    day = result.scalar_one_or_none()
    if day and day.status == "empty":
        day.status = "in_progress"

    await db.commit()

    return {
        "calendar_day_id": calendar_day_id,
        "question_text": answer.question_text,
        "answer_text": answer.answer_text,
        "question_order": answer.question_order,
    }


@router.post("/{calendar_day_id}/generate")
async def generate_content(
    calendar_day_id: int, req: GenerateRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CalendarDay).where(CalendarDay.id == calendar_day_id)
    )
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(status_code=404, detail="Calendar day not found")

    result = await db.execute(select(Theme).where(Theme.id == day.theme_id))
    theme = result.scalar_one_or_none()
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found for this day")

    result = await db.execute(
        select(DailyAnswer)
        .where(DailyAnswer.calendar_day_id == calendar_day_id)
        .order_by(DailyAnswer.question_order)
    )
    answers = result.scalars().all()
    if not answers:
        raise HTTPException(status_code=400, detail="No answers found — answer questions first")

    answers_dict = {a.question_text: a.answer_text for a in answers}

    race_context = ""
    if day.race_id:
        result = await db.execute(select(Race).where(Race.id == day.race_id))
        race = result.scalar_one_or_none()
        if race:
            race_context = (
                f"Race: {race.name}\n"
                f"Location: {race.location}\n"
                f"Origin: {race.origin_story}\n"
                f"What makes it wild: {race.what_makes_it_wild}\n"
                f"Notable moments: {race.notable_moments}\n"
                f"Video angle: {race.video_angle}"
            )

    from services.content_generator import generate_daily_content

    generated = await generate_daily_content(
        theme_slug=theme.slug,
        theme_context=theme.script_type_context,
        answers=answers_dict,
        tone=req.tone,
        target_duration=req.target_duration,
        race_context=race_context,
    )

    result = await db.execute(
        select(GeneratedContent).where(
            GeneratedContent.calendar_day_id == calendar_day_id
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.hooks = generated.get("hooks", [])
        existing.body = generated.get("body", "")
        existing.visual_notes = generated.get("visual_notes", "")
        existing.cta = generated.get("cta", "")
        existing.hashtags = generated.get("hashtags", "")
        existing.caption = generated.get("caption", "")
        existing.tone = req.tone
        existing.target_duration = req.target_duration
        existing.suggested_images = generated.get("suggested_images", [])
        content = existing
    else:
        content = GeneratedContent(
            calendar_day_id=calendar_day_id,
            hooks=generated.get("hooks", []),
            body=generated.get("body", ""),
            visual_notes=generated.get("visual_notes", ""),
            cta=generated.get("cta", ""),
            hashtags=generated.get("hashtags", ""),
            caption=generated.get("caption", ""),
            tone=req.tone,
            target_duration=req.target_duration,
            suggested_images=generated.get("suggested_images", []),
        )
        db.add(content)

    day.status = "generated"
    await db.commit()
    await db.refresh(content)

    return {
        "id": content.id,
        "calendar_day_id": content.calendar_day_id,
        "hooks": content.hooks,
        "body": content.body,
        "visual_notes": content.visual_notes,
        "cta": content.cta,
        "hashtags": content.hashtags,
        "caption": content.caption,
        "tone": content.tone,
        "target_duration": content.target_duration,
        "suggested_images": content.suggested_images or [],
        "edited_body": content.edited_body,
        "created_at": content.created_at.isoformat() if content.created_at else None,
    }


@router.post("/{calendar_day_id}/link-race")
async def link_race(
    calendar_day_id: int, req: LinkRaceRequest, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(CalendarDay).where(CalendarDay.id == calendar_day_id)
    )
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(status_code=404, detail="Calendar day not found")

    result = await db.execute(select(Race).where(Race.id == req.race_id))
    race = result.scalar_one_or_none()
    if not race:
        raise HTTPException(status_code=404, detail="Race not found")

    day.race_id = req.race_id

    result = await db.execute(
        select(RaceImage).where(RaceImage.race_id == req.race_id)
    )
    race_images = result.scalars().all()

    result = await db.execute(
        select(ContentImage)
        .where(ContentImage.calendar_day_id == calendar_day_id)
        .order_by(ContentImage.display_order.desc())
    )
    existing = result.scalars().all()
    next_order = (existing[0].display_order + 1) if existing else 0

    imported = 0
    existing_race_image_ids = {
        img.race_image_id for img in existing if img.race_image_id is not None
    }

    for ri in race_images:
        if ri.id in existing_race_image_ids:
            continue
        content_img = ContentImage(
            calendar_day_id=calendar_day_id,
            image_path=ri.local_path or "",
            filename=ri.filename or "",
            caption=ri.title or "",
            source="race_vault",
            display_order=next_order,
            race_image_id=ri.id,
        )
        db.add(content_img)
        next_order += 1
        imported += 1

    await db.commit()

    return {
        "calendar_day_id": calendar_day_id,
        "race_id": req.race_id,
        "race_name": race.name,
        "images_imported": imported,
    }

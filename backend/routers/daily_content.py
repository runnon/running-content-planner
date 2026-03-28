from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from database import get_db
from models import GeneratedContent, ContentImage, CalendarDay

router = APIRouter(prefix="/api/daily-content", tags=["daily_content"])


class ContentUpdate(BaseModel):
    hooks: Optional[list] = None
    body: Optional[str] = None
    visual_notes: Optional[str] = None
    cta: Optional[str] = None
    hashtags: Optional[str] = None
    caption: Optional[str] = None
    edited_body: Optional[str] = None


class ImageReorder(BaseModel):
    image_ids: list[int]


@router.get("/{calendar_day_id}")
async def get_daily_content(
    calendar_day_id: int,
    db: AsyncSession = Depends(get_db),
):
    day_result = await db.execute(
        select(CalendarDay).where(CalendarDay.id == calendar_day_id)
    )
    day = day_result.scalar_one_or_none()
    if not day:
        raise HTTPException(status_code=404, detail="Calendar day not found")

    content_result = await db.execute(
        select(GeneratedContent)
        .where(GeneratedContent.calendar_day_id == calendar_day_id)
        .order_by(GeneratedContent.created_at.desc())
    )
    content = content_result.scalar_one_or_none()

    images_result = await db.execute(
        select(ContentImage)
        .where(ContentImage.calendar_day_id == calendar_day_id)
        .order_by(ContentImage.display_order)
    )
    images = images_result.scalars().all()

    return {
        "content": {
            "id": content.id,
            "hooks": content.hooks,
            "body": content.body,
            "visual_notes": content.visual_notes,
            "cta": content.cta,
            "hashtags": content.hashtags,
            "caption": content.caption,
            "tone": content.tone,
            "target_duration": content.target_duration,
            "edited_body": content.edited_body,
            "created_at": content.created_at.isoformat(),
        } if content else None,
        "images": [
            {
                "id": img.id,
                "image_path": img.image_path,
                "filename": img.filename,
                "caption": img.caption,
                "source": img.source,
                "display_order": img.display_order,
            }
            for img in images
        ],
    }


@router.patch("/{calendar_day_id}")
async def update_daily_content(
    calendar_day_id: int,
    body: ContentUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GeneratedContent)
        .where(GeneratedContent.calendar_day_id == calendar_day_id)
    )
    content = result.scalar_one_or_none()
    if not content:
        raise HTTPException(status_code=404, detail="No generated content for this day")

    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(content, field, value)

    await db.commit()
    await db.refresh(content)

    return {
        "id": content.id,
        "hooks": content.hooks,
        "body": content.body,
        "visual_notes": content.visual_notes,
        "cta": content.cta,
        "hashtags": content.hashtags,
        "caption": content.caption,
        "tone": content.tone,
        "target_duration": content.target_duration,
        "edited_body": content.edited_body,
    }


@router.delete("/{calendar_day_id}/images/{image_id}")
async def delete_image(
    calendar_day_id: int,
    image_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentImage).where(
            ContentImage.id == image_id,
            ContentImage.calendar_day_id == calendar_day_id,
        )
    )
    image = result.scalar_one_or_none()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    await db.delete(image)
    await db.commit()
    return {"deleted": True, "id": image_id}


@router.patch("/{calendar_day_id}/images/reorder")
async def reorder_images(
    calendar_day_id: int,
    body: ImageReorder,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ContentImage)
        .where(ContentImage.calendar_day_id == calendar_day_id)
    )
    images_by_id = {img.id: img for img in result.scalars().all()}

    for order, image_id in enumerate(body.image_ids):
        if image_id not in images_by_id:
            raise HTTPException(
                status_code=404,
                detail=f"Image {image_id} not found for this day",
            )
        images_by_id[image_id].display_order = order

    await db.commit()
    return {"reordered": True, "order": body.image_ids}

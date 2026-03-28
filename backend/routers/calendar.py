from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from datetime import date, timedelta
import calendar as cal

from database import get_db
from models import CalendarDay, Theme

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class StatusUpdate(BaseModel):
    status: str


def _parse_month(month_str: str) -> tuple[date, date]:
    """Parse 'YYYY-MM' into (first_day, last_day) of that month."""
    parts = month_str.split("-")
    year, month = int(parts[0]), int(parts[1])
    first = date(year, month, 1)
    last_day_num = cal.monthrange(year, month)[1]
    last = date(year, month, last_day_num)
    return first, last


@router.get("")
async def get_month(
    month: str = Query(..., description="YYYY-MM format, e.g. 2026-04"),
    db: AsyncSession = Depends(get_db),
):
    first, last = _parse_month(month)

    result = await db.execute(
        select(CalendarDay)
        .where(CalendarDay.date >= first.isoformat(), CalendarDay.date <= last.isoformat())
        .order_by(CalendarDay.date)
    )
    existing = {row.date: row for row in result.scalars().all()}

    theme_result = await db.execute(select(Theme))
    themes_by_dow = {t.day_of_week: t for t in theme_result.scalars().all()}

    days = []
    current = first
    while current <= last:
        date_str = current.isoformat()
        row = existing.get(date_str)
        if row:
            days.append({
                "id": row.id,
                "date": row.date,
                "theme_name": row.theme_name,
                "theme_slug": row.theme_slug,
                "status": row.status,
                "race_id": row.race_id,
            })
        else:
            theme = themes_by_dow.get(current.weekday())
            days.append({
                "id": None,
                "date": date_str,
                "theme_name": theme.name if theme else "",
                "theme_slug": theme.slug if theme else "",
                "status": "empty",
                "race_id": None,
            })
        current += timedelta(days=1)

    return days


@router.get("/today")
async def get_today(db: AsyncSession = Depends(get_db)):
    today_str = date.today().isoformat()

    result = await db.execute(
        select(CalendarDay).where(CalendarDay.date == today_str)
    )
    day = result.scalar_one_or_none()

    if day:
        theme_result = await db.execute(
            select(Theme).where(Theme.id == day.theme_id)
        )
        theme = theme_result.scalar_one_or_none()
    else:
        theme_result = await db.execute(
            select(Theme).where(Theme.day_of_week == date.today().weekday())
        )
        theme = theme_result.scalar_one_or_none()

        day = CalendarDay(
            date=today_str,
            theme_id=theme.id if theme else None,
            theme_name=theme.name if theme else "",
            theme_slug=theme.slug if theme else "",
            status="empty",
        )
        db.add(day)
        await db.commit()
        await db.refresh(day)

    return {
        "id": day.id,
        "date": day.date,
        "theme_name": day.theme_name,
        "theme_slug": day.theme_slug,
        "theme_id": day.theme_id,
        "status": day.status,
        "race_id": day.race_id,
        "questions": theme.questions if theme else [],
        "description": theme.description if theme else "",
    }


class EnsureDayRequest(BaseModel):
    date: str  # "2026-04-07"


@router.post("/ensure")
async def ensure_day(req: EnsureDayRequest, db: AsyncSession = Depends(get_db)):
    """Create a CalendarDay for the given date if it doesn't exist, then return it."""
    result = await db.execute(
        select(CalendarDay).where(CalendarDay.date == req.date)
    )
    day = result.scalar_one_or_none()

    if not day:
        target_date = date.fromisoformat(req.date)
        theme_result = await db.execute(
            select(Theme).where(Theme.day_of_week == target_date.weekday())
        )
        theme = theme_result.scalar_one_or_none()

        day = CalendarDay(
            date=req.date,
            theme_id=theme.id if theme else None,
            theme_name=theme.name if theme else "",
            theme_slug=theme.slug if theme else "",
            status="empty",
        )
        db.add(day)
        await db.commit()
        await db.refresh(day)

    return {
        "id": day.id,
        "date": day.date,
        "theme_name": day.theme_name,
        "theme_slug": day.theme_slug,
        "theme_id": day.theme_id,
        "status": day.status,
        "race_id": day.race_id,
    }


@router.patch("/{day_id}/status")
async def update_status(
    day_id: int,
    body: StatusUpdate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CalendarDay).where(CalendarDay.id == day_id)
    )
    day = result.scalar_one_or_none()
    if not day:
        raise HTTPException(status_code=404, detail="Calendar day not found")

    day.status = body.status
    await db.commit()
    return {"id": day.id, "date": day.date, "status": day.status}


@router.get("/streak")
async def get_streak(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(CalendarDay)
        .where(CalendarDay.status == "posted")
        .order_by(CalendarDay.date.desc())
    )
    posted_days = result.scalars().all()
    posted_dates = {d.date for d in posted_days}

    current_streak = 0
    check = date.today()
    while check.isoformat() in posted_dates:
        current_streak += 1
        check -= timedelta(days=1)

    longest_streak = 0
    if posted_days:
        sorted_dates = sorted(date.fromisoformat(d.date) for d in posted_days)
        streak = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
                streak += 1
            else:
                longest_streak = max(longest_streak, streak)
                streak = 1
        longest_streak = max(longest_streak, streak)

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
    }

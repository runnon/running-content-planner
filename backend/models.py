from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON
from database import Base


class Race(Base):
    __tablename__ = "races"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255), default="")
    origin_year = Column(String(50), default="")
    origin_story = Column(Text, default="")
    what_makes_it_wild = Column(Text, default="")
    status = Column(String(100), default="")
    last_known_date = Column(String(255), default="")
    next_upcoming_date = Column(String(255), default="")
    notable_moments = Column(Text, default="")
    source_links = Column(JSON, default=list)
    video_angle = Column(Text, default="")
    queued_for_weekly = Column(Boolean, default=False)
    queue_date = Column(DateTime, nullable=True)
    raw_research = Column(Text, default="")
    covered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, nullable=True)
    script_type = Column(String(50), nullable=False)
    target_duration = Column(String(50), default="60_90")
    tone = Column(String(50), nullable=False)
    topic = Column(String(500), nullable=False)
    hooks = Column(JSON, default=list)
    body = Column(Text, default="")
    visual_notes = Column(Text, default="")
    cta = Column(Text, default="")
    hashtags = Column(Text, default="")
    caption = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), default="instagram")
    post_id = Column(String(255), unique=True, nullable=False)
    username = Column(String(255), default="")
    caption = Column(Text, default="")
    media_url = Column(Text, default="")
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    hashtags = Column(JSON, default=list)
    scraped_from = Column(String(255), default="")
    posted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RaceImage(Base):
    __tablename__ = "race_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    race_id = Column(Integer, nullable=False, index=True)
    source_url = Column(Text, nullable=False)
    local_path = Column(Text, default="")
    filename = Column(String(255), default="")
    title = Column(Text, default="")
    source_page = Column(Text, default="")
    source_type = Column(String(50), default="")  # ddg, reddit, web
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    file_size = Column(Integer, nullable=True)
    starred = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DiscoveredRace(Base):
    __tablename__ = "discovered_races"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    snippet = Column(Text, default="")
    source = Column(String(255), default="")
    source_url = Column(Text, default="")
    researched = Column(Boolean, default=False)
    race_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Theme(Base):
    __tablename__ = "themes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, default="")
    questions = Column(JSON, default=list)
    script_type_context = Column(Text, default="")


class CalendarDay(Base):
    __tablename__ = "calendar_days"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String(10), unique=True, nullable=False)  # "2026-04-07"
    theme_id = Column(Integer, nullable=True)
    theme_name = Column(String(100), default="")
    theme_slug = Column(String(100), default="")
    status = Column(String(20), default="empty")  # empty, in_progress, generated, posted
    race_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyAnswer(Base):
    __tablename__ = "daily_answers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calendar_day_id = Column(Integer, nullable=False, index=True)
    question_text = Column(Text, nullable=False)
    answer_text = Column(Text, default="")
    question_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class GeneratedContent(Base):
    __tablename__ = "generated_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calendar_day_id = Column(Integer, nullable=False, index=True)
    hooks = Column(JSON, default=list)
    body = Column(Text, default="")
    visual_notes = Column(Text, default="")
    cta = Column(Text, default="")
    hashtags = Column(Text, default="")
    caption = Column(Text, default="")
    tone = Column(String(50), default="full_send")
    target_duration = Column(String(50), default="60_90")
    suggested_images = Column(JSON, default=list)
    edited_body = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ContentImage(Base):
    __tablename__ = "content_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    calendar_day_id = Column(Integer, nullable=False, index=True)
    image_path = Column(Text, default="")
    filename = Column(String(255), default="")
    caption = Column(Text, default="")
    source = Column(String(100), default="")  # "race_vault", "upload"
    display_order = Column(Integer, default=0)
    race_image_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

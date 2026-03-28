from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session


def _migrate_scripts_target_duration(sync_conn):
    from sqlalchemy import inspect

    insp = inspect(sync_conn)
    if "scripts" not in insp.get_table_names():
        return
    cols = {c["name"] for c in insp.get_columns("scripts")}
    if "target_duration" not in cols:
        sync_conn.execute(
            text("ALTER TABLE scripts ADD COLUMN target_duration VARCHAR(50) DEFAULT '60_90'")
        )


async def init_db():
    async with engine.begin() as conn:
        from models import Base  # noqa: F811
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_scripts_target_duration)

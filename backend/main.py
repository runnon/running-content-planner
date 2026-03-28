from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import APP_PASSWORD
from database import init_db, async_session
from seed_races import seed_database
from routers import races, scripts, content

IMAGES_DIR = Path(__file__).resolve().parent / "images"
IMAGES_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    async with async_session() as db:
        seeded = await seed_database(db)
        if seeded:
            print(f"Seeded {seeded} races into the database")
    yield


app = FastAPI(title="Runnon Content Engine", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

app.include_router(races.router)
app.include_router(scripts.router)
app.include_router(content.router)


class PasswordCheck(BaseModel):
    password: str


@app.post("/api/auth/check")
async def check_password(req: PasswordCheck):
    if req.password == APP_PASSWORD:
        return {"authenticated": True}
    return {"authenticated": False}


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "Runnon Content Engine"}

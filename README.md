# Runnon Content Engine

Internal research and content tooling for [Runnon](https://www.runnon.io).

Runnon lives in the world of grassroots, unsanctioned endurance racing. This repo is the operating layer behind that editorial work: it helps the team find races worth covering, build a structured race vault, pull high-signal social references, and turn research into scripts for short-form content.

## What This App Does

### 1. Build the race vault

The app stores a structured database of race profiles, including:

- race name and location
- origin story and what makes it notable
- status, dates, and notable moments
- source links and research notes
- queue and coverage state for editorial planning

### 2. Discover new races

The discovery flow scans for races that are not already in the vault, saves candidate discoveries, and lets the team research and promote the strong ones into the main database.

### 3. Generate scripts

The script generator uses AWS Bedrock to turn race research into ready-to-edit short-form scripts, including:

- multiple hooks
- main body copy
- visual notes
- CTA
- hashtags
- caption text

### 4. Pull reference content

The backend can scrape Instagram content by hashtag, filter for endurance-relevant posts, and save high-engagement references for content research.

### 5. Collect race imagery

For individual races, the app can scrape and store reference images to support visual research and content packaging.

## Product Surfaces

- **The Vault**: searchable database of researched races
- **Discover**: queue of newly found race candidates
- **The Forge**: script generation workflow for selected races
- **Password Gate**: lightweight internal access check for the frontend

## Typical Workflow

1. Run discovery to surface races not already tracked.
2. Research and save the promising ones into the vault.
3. Deepen research and collect image references for a race.
4. Queue races for the weekly content pipeline.
5. Generate a script in the desired tone and duration.
6. Mark a race as covered once content is published.

## Stack

- **Frontend**: Next.js 16, React 19, TypeScript
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **AI**: AWS Bedrock
- **Data collection**: DuckDuckGo search, BeautifulSoup, Reddit, Instaloader

## Repo Layout

```text
.
├── backend/   # FastAPI API, database models, scraping, research, generation
├── frontend/  # Next.js UI for vault, discovery, and script generation
└── .env.example
```

## Local Setup

### Prerequisites

- Python 3.10+
- Node.js 20+
- AWS credentials with Bedrock access

### 1. Configure environment

Copy the root env file into the backend:

```bash
cd backend
cp ../.env.example .env
```

Set values in `backend/.env`:

```bash
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-opus-4-6-v1
APP_PASSWORD=ALLEYKAT
```

### 2. Start the backend

```bash
cd backend
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000
```

Notes:

- the SQLite database lives at `backend/runnon.db`
- the app initializes and seeds core data on startup
- image assets are stored in `backend/images/`

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

By default:

- browser requests to `/api/*` are proxied by Next.js to `http://127.0.0.1:8000`
- the frontend is protected by the password in `APP_PASSWORD`

If you need the frontend to talk to a different API host, set:

- `BACKEND_URL` for Next server-side requests and dev rewrites
- `NEXT_PUBLIC_API_URL` for browser-side requests when not using same-origin `/api`

## API Overview

### Races

- `GET /api/races`
- `GET /api/races/:id`
- `POST /api/races/research`
- `POST /api/races/discover`
- `GET /api/races/discovered/list`
- `PATCH /api/races/:id`
- `PATCH /api/races/:id/covered`
- `POST /api/races/:id/research-more`
- `POST /api/races/:id/add-source`
- `GET /api/races/:id/images`
- `POST /api/races/:id/images/scrape`

### Scripts

- `GET /api/scripts`
- `GET /api/scripts/:id`
- `POST /api/scripts/generate`

### Content

- `GET /api/content`
- `POST /api/content/scrape`

### Auth / Health

- `POST /api/auth/check`
- `GET /api/health`

## Current Positioning

This is an internal tool, not a polished public product. The value is speed:

- faster research on obscure races
- better editorial memory across the team
- tighter script generation from structured source material
- a more repeatable pipeline for Runnon's content output

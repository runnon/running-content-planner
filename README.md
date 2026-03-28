# Runnon Content Engine

Internal content tool for [Runnon](https://runnon.io) — the unsanctioned racing platform.

Scrapes the web, Reddit, and Instagram for underground racing content. Discovers races you've never heard of. Researches their history. Writes scripts in Runnon's voice with scroll-stopping hooks.

## Features

- **Race Vault** — Database of the world's wildest unsanctioned races. Discover new ones or deep-dive research with multi-source scraping (web, Reddit, Instagram).
- **Script Forge** — AI script writer with Runnon's counter-culture voice baked in. 3 hook options per script. Supports race history, short-form, building in public, and race promo formats.
- **Content Feed** — Scrape Instagram by underground racing hashtags. See what's performing in the niche.

## Quick Start

### Backend

```bash
cd backend
cp ../.env.example .env
# Edit .env with your AWS credentials
python3 -m pip install -r requirements.txt
python3 -m uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm run dev
```

Open http://localhost:3000. Password: `ALLEYKAT`

## Environment Variables

```
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
APP_PASSWORD=ALLEYKAT
```

## Tech Stack

- **Backend**: Python / FastAPI / SQLite / SQLAlchemy
- **Frontend**: Next.js / Tailwind CSS
- **AI**: AWS Bedrock (Claude)
- **Scraping**: Instaloader, DuckDuckGo Search, BeautifulSoup, Reddit JSON API

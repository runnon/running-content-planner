from typing import List

from services.web_search import search_and_scrape, search_races_broad, scrape_article
from services.reddit_scraper import search_reddit, search_races_reddit
from services.instagram import search_hashtag_for_race
from services.bedrock import invoke_bedrock_json, invoke_bedrock
from brand import RACE_RESEARCHER_PROMPT, RACE_DISCOVERY_PROMPT, RUNNON_SYSTEM_PROMPT


async def research_race(race_name: str) -> dict:
    """Run multi-source research on a specific race and compile a profile."""

    web_results = search_and_scrape(
        f'"{race_name}" unsanctioned race history origin', max_results=5
    )
    web_results += search_and_scrape(
        f'"{race_name}" underground race endurance', max_results=3
    )

    reddit_results = search_reddit(race_name)

    ig_results = search_hashtag_for_race(race_name, max_posts=5)

    research_parts = []
    source_links = []

    for r in web_results:
        research_parts.append(f"[WEB] {r['title']}\nURL: {r['url']}\n{r['full_text']}\n---")
        source_links.append(r["url"])

    for r in reddit_results[:10]:
        research_parts.append(
            f"[REDDIT] r/{r['subreddit']} - {r['title']} (score: {r['score']})\n"
            f"URL: {r['url']}\n{r['selftext']}\n---"
        )
        source_links.append(r["url"])

    for p in ig_results:
        research_parts.append(
            f"[INSTAGRAM] @{p['username']} ({p['likes']} likes)\n{p['caption'][:500]}\n---"
        )

    research_text = "\n\n".join(research_parts)

    if not research_text.strip():
        research_text = f"No detailed sources found for '{race_name}'. Use your knowledge to compile what you know about this race, but be transparent about what is well-documented vs speculative."

    prompt = RACE_RESEARCHER_PROMPT.format(
        research_text=research_text[:15000],
        race_name=race_name,
    )

    profile = await invoke_bedrock_json(prompt, system=RUNNON_SYSTEM_PROMPT)

    profile["source_links"] = list(set(source_links))
    profile["raw_research"] = research_text[:20000]

    return profile


async def discover_races() -> List[dict]:
    """Discover new unsanctioned/underground races from multiple sources."""

    web_results = search_races_broad()
    reddit_results = search_races_reddit()

    content_parts = []

    for r in web_results:
        content_parts.append(f"[WEB - query: {r.get('query', '')}] {r['title']}\n{r['snippet']}")

    for r in reddit_results:
        content_parts.append(
            f"[REDDIT r/{r['subreddit']}] {r['title']}\n{r['selftext'][:500]}"
        )

    content = "\n\n---\n\n".join(content_parts)

    if not content.strip():
        return []

    prompt = RACE_DISCOVERY_PROMPT.format(content=content[:20000])

    races = await invoke_bedrock_json(prompt, system=RUNNON_SYSTEM_PROMPT)

    if isinstance(races, list):
        return races
    return []


async def deepen_research(race_name: str, existing_profile: dict) -> dict:
    """Run additional multi-source research and merge into an existing profile."""

    web_results = search_and_scrape(
        f'"{race_name}" race stories participants experience', max_results=5
    )
    web_results += search_and_scrape(
        f'"{race_name}" race controversy records moments', max_results=3
    )

    reddit_results = search_reddit(race_name)
    ig_results = search_hashtag_for_race(race_name, max_posts=5)

    research_parts = []
    source_links = list(existing_profile.get("source_links", []))

    for r in web_results:
        if r["url"] not in source_links:
            research_parts.append(f"[WEB] {r['title']}\nURL: {r['url']}\n{r['full_text']}\n---")
            source_links.append(r["url"])

    for r in reddit_results[:10]:
        if r["url"] not in source_links:
            research_parts.append(
                f"[REDDIT] r/{r['subreddit']} - {r['title']} (score: {r['score']})\n"
                f"URL: {r['url']}\n{r['selftext']}\n---"
            )
            source_links.append(r["url"])

    for p in ig_results:
        research_parts.append(
            f"[INSTAGRAM] @{p['username']} ({p['likes']} likes)\n{p['caption'][:500]}\n---"
        )

    new_research = "\n\n".join(research_parts)

    if not new_research.strip():
        return existing_profile

    prompt = f"""You are a researcher for Runnon. You have an existing race profile and NEW research material.
Your job is to MERGE the new findings into the existing profile — add new details, stories, moments,
and context you find. Keep everything from the original and expand it. Don't remove or shorten anything.
Write in Runnon's voice — raw, excited, counter-culture.

EXISTING PROFILE:
{existing_profile}

NEW RESEARCH MATERIAL:
{new_research[:12000]}

Return the updated profile as JSON with this structure:
{{
  "name": "{race_name}",
  "location": "City, Country",
  "origin_year": "Year or approximate era",
  "origin_story": "Expanded origin story with any new details merged in.",
  "what_makes_it_wild": "Expanded — add any new wild details found.",
  "status": "Active / Defunct / Underground / Evolved",
  "last_known_date": "Most recent date held.",
  "next_upcoming_date": "Upcoming edition date or Unknown.",
  "notable_moments": "Expanded with any new stories, records, controversies found.",
  "video_angle": "Updated video angle if the new research reveals a better hook."
}}"""

    updated = await invoke_bedrock_json(prompt, system=RUNNON_SYSTEM_PROMPT)
    updated["source_links"] = list(set(source_links))
    updated["raw_research"] = (existing_profile.get("raw_research", "") + "\n\n--- ADDITIONAL RESEARCH ---\n\n" + new_research)[:20000]

    return updated


async def enrich_race_with_url(existing_profile: dict, url: str) -> dict:
    """Scrape a URL and use it to enrich an existing race profile."""
    content = scrape_article(url)
    if not content:
        return existing_profile

    prompt = f"""You have an existing race profile and new source material. \
Update the profile with any new information from this source. Keep all existing info \
and ADD to it. Return the updated profile in the same JSON format.

EXISTING PROFILE:
{existing_profile}

NEW SOURCE ({url}):
{content[:5000]}

Return the updated JSON profile with the same structure. Add the new URL to source_links."""

    updated = await invoke_bedrock_json(prompt, system=RUNNON_SYSTEM_PROMPT)

    if "source_links" not in updated:
        updated["source_links"] = existing_profile.get("source_links", [])
    if url not in updated["source_links"]:
        updated["source_links"].append(url)

    return updated

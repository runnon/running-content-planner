from services.bedrock import invoke_bedrock_json
from brand import (
    RUNNON_SYSTEM_PROMPT,
    TONE_DESCRIPTIONS,
    SCRIPT_DURATION_CONTEXTS,
)


async def generate_daily_content(
    theme_slug: str,
    theme_context: str,
    answers: dict,
    tone: str = "full_send",
    target_duration: str = "60_90",
    race_context: str = "",
) -> dict:
    """Generate a full content script from the user's daily Q&A answers."""

    tone_desc = TONE_DESCRIPTIONS.get(tone, TONE_DESCRIPTIONS["full_send"])
    duration_ctx = SCRIPT_DURATION_CONTEXTS.get(
        target_duration, SCRIPT_DURATION_CONTEXTS["60_90"]
    )

    qa_block = "\n".join(
        f"Q: {question}\nA: {answer}\n"
        for question, answer in answers.items()
    )

    prompt_parts = [
        f"Today's theme: {theme_slug.replace('_', ' ').title()}",
        f"\n{theme_context}",
        f"\nTone: {tone_desc}",
        f"\n{duration_ctx}",
        "\n--- YOUR ANSWERS (the raw material — build the script from these) ---",
        f"\n{qa_block}",
    ]

    if race_context:
        prompt_parts.insert(3, f"\nRace context for today:\n{race_context}")

    prompt_parts.append(
        "\n--- INSTRUCTIONS ---\n"
        "Take those answers and turn them into a scroll-stopping piece of content. "
        "This is NOT a summary of the answers — it's a script that a real human reads "
        "on camera. Use the answers as raw material and creative fuel.\n\n"
        "Write it like you're actually talking. Pauses, emphasis, energy shifts. "
        "Add [TIMING] markers (e.g. [0:05], [0:15]) so the creator knows pacing.\n\n"
        "Output EXACTLY this JSON:\n"
        "{\n"
        '  "hooks": ["Hook 1 - stop the scroll", "Hook 2 - alternative", "Hook 3 - alternative"],\n'
        '  "body": "Full script with [TIMING] markers. Written as spoken word for camera.",\n'
        '  "visual_notes": "B-roll suggestions, on-screen text ideas, visual cues for each section.",\n'
        '  "cta": "Natural call to action — not salesy, just real.",\n'
        '  "hashtags": "#relevant #hashtags #here",\n'
        '  "caption": "The Instagram/TikTok caption to post with this."\n'
        "}"
    )

    prompt = "\n".join(prompt_parts)

    result = await invoke_bedrock_json(
        prompt, system=RUNNON_SYSTEM_PROMPT, max_tokens=2048
    )

    return {
        "hooks": result.get("hooks", []),
        "body": result.get("body", ""),
        "visual_notes": result.get("visual_notes", ""),
        "cta": result.get("cta", ""),
        "hashtags": result.get("hashtags", ""),
        "caption": result.get("caption", ""),
    }

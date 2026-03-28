from services.bedrock import invoke_bedrock_json
from brand import (
    RUNNON_SYSTEM_PROMPT,
    SCRIPT_WRITER_PROMPT,
    TONE_DESCRIPTIONS,
    SCRIPT_TYPE_CONTEXTS,
    SCRIPT_DURATION_CONTEXTS,
)


async def generate_script(
    topic: str,
    script_type: str = "race_history",
    tone: str = "full_send",
    target_duration: str = "60_90",
    race_context: str = "",
    content_context: str = "",
) -> dict:
    """Generate a script with hooks in Runnon's voice."""

    tone_desc = TONE_DESCRIPTIONS.get(tone, TONE_DESCRIPTIONS["full_send"])
    type_ctx = SCRIPT_TYPE_CONTEXTS.get(
        script_type, SCRIPT_TYPE_CONTEXTS["race_history"]
    )
    duration_ctx = SCRIPT_DURATION_CONTEXTS.get(
        target_duration, SCRIPT_DURATION_CONTEXTS["60_90"]
    )

    context_parts = [type_ctx, duration_ctx]

    if race_context:
        context_parts.append(f"\nRace information for context:\n{race_context}")

    if content_context:
        context_parts.append(f"\nTrending content for inspiration:\n{content_context}")

    context = "\n".join(context_parts)

    prompt = SCRIPT_WRITER_PROMPT.format(
        system_prompt=RUNNON_SYSTEM_PROMPT,
        script_type=script_type.replace("_", " "),
        tone_description=tone_desc,
        context=context,
        topic=topic,
    )

    result = await invoke_bedrock_json(prompt, max_tokens=2048)

    return {
        "hooks": result.get("hooks", []),
        "body": result.get("body", ""),
        "visual_notes": result.get("visual_notes", ""),
        "cta": result.get("cta", ""),
        "hashtags": result.get("hashtags", ""),
        "caption": result.get("caption", ""),
    }

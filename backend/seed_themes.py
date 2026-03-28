"""Pre-seed the database with the 7 weekly content themes."""

SEED_THEMES = [
    {
        "day_of_week": 4,  # Friday
        "name": "Race History",
        "slug": "race_history",
        "description": "Tell the story of an unsanctioned race. Pull from the Vault or research a new one.",
        "questions": [
            "What race are you covering today?",
            "What year did it start and where?",
            "Who started it and why?",
            "What makes this race insane or unique?",
            "What's the wildest moment or story from this race?",
            "What lesson from this race applies to what you're building?",
            "Why does this matter for Runnon?"
        ],
        "script_type_context": "This is a race history piece for Runnon. Tell the story of this race — its origin, what makes it insane, why people should care. Match the target length below; pace your beats and [TIMING] markers accordingly."
    },
    {
        "day_of_week": 1,  # Tuesday
        "name": "Hard Thing",
        "slug": "hard_thing",
        "description": "The hardest part of building today. Real founder struggle, no sugar coating.",
        "questions": [
            "What problem did you face today?",
            "When did it happen?",
            "What caused it?",
            "What did you try first?",
            "What worked?",
            "What failed?",
            "What did you learn from it?"
        ],
        "script_type_context": "This is a founder struggle story for Runnon. Raw, honest, no sugar coating. Show the real fight of building something. Match the target length below; pace your beats and [TIMING] markers accordingly."
    },
    {
        "day_of_week": 2,  # Wednesday
        "name": "Positive Win",
        "slug": "positive_win",
        "description": "Something went right. Celebrate the momentum, big or small.",
        "questions": [
            "What went well today?",
            "Who was involved?",
            "Why did it matter?",
            "Was it expected or a surprise?",
            "How did it make you feel?"
        ],
        "script_type_context": "This is a momentum and wins piece for Runnon. Celebrate what's working, share the energy. Keep it real but let the excitement show. Match the target length below; pace your beats and [TIMING] markers accordingly."
    },
    {
        "day_of_week": 3,  # Thursday
        "name": "Feature Update",
        "slug": "feature_update",
        "description": "What did you ship? Show the product evolving in real time.",
        "questions": [
            "What feature did you ship or work on?",
            "What problem does it solve?",
            "Who benefits from this?",
            "How long did it take to build?",
            "What changed from before?"
        ],
        "script_type_context": "This is a product update piece for Runnon. Show what you're building, why it matters, and how it helps runners. Keep it tangible and specific. Match the target length below; pace your beats and [TIMING] markers accordingly."
    },
    {
        "day_of_week": 0,  # Monday
        "name": "Founder Philosophy",
        "slug": "founder_philosophy",
        "description": "What do you believe about racing that most people get wrong?",
        "questions": [
            "What belief about racing do you hold strongly?",
            "What experience shaped that belief?",
            "Why do most people misunderstand this?",
            "Why does this matter long term for running culture?"
        ],
        "script_type_context": "This is a thought leadership piece for Runnon. Share a strong opinion about racing culture, running, or building in public. Be provocative, be real. Match the target length below; pace your beats and [TIMING] markers accordingly."
    },
    {
        "day_of_week": 5,  # Saturday
        "name": "Metrics",
        "slug": "metrics",
        "description": "Transparency content. Share the numbers — good, bad, and real.",
        "questions": [
            "How many races happened this week?",
            "What was revenue this week?",
            "How many new registrations?",
            "Biggest win this week?",
            "Biggest loss or miss this week?"
        ],
        "script_type_context": "This is a metrics and transparency piece for Runnon. Share real numbers, real results. Founders love this content because it's honest. Match the target length below; pace your beats and [TIMING] markers accordingly."
    },
    {
        "day_of_week": 6,  # Sunday
        "name": "Feature Stress Test",
        "slug": "feature_stress_test",
        "description": "Thinking about building something? Stress test it publicly and get feedback.",
        "questions": [
            "What feature are you considering building?",
            "Who would use it?",
            "What problem does it solve?",
            "What's the biggest risk or downside?",
            "What feedback do you want from your audience?"
        ],
        "script_type_context": "This is a feature stress test for Runnon. Think out loud about what you're considering building, invite feedback. Vulnerability + product thinking. Match the target length below; pace your beats and [TIMING] markers accordingly."
    },
]


async def seed_themes(db):
    """Seed the database with weekly content themes if empty."""
    from sqlalchemy import select, func
    from models import Theme

    result = await db.execute(select(func.count(Theme.id)))
    count = result.scalar()

    if count > 0:
        return 0

    seeded = 0
    for theme_data in SEED_THEMES:
        theme = Theme(
            day_of_week=theme_data["day_of_week"],
            name=theme_data["name"],
            slug=theme_data["slug"],
            description=theme_data["description"],
            questions=theme_data["questions"],
            script_type_context=theme_data["script_type_context"],
        )
        db.add(theme)
        seeded += 1

    await db.commit()
    return seeded

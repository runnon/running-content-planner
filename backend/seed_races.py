"""Pre-seed the database with ~20 famous unsanctioned/underground races."""

SEED_RACES = [
    {
        "name": "Barkley Marathons",
        "location": "Frozen Head State Park, Tennessee, USA",
        "origin_year": "1986",
        "status": "Active - by invitation/application only",
    },
    {
        "name": "Hash House Harriers",
        "location": "Worldwide (originated in Kuala Lumpur, Malaysia)",
        "origin_year": "1938",
        "status": "Active - thousands of chapters globally",
    },
    {
        "name": "Beer Mile",
        "location": "Worldwide",
        "origin_year": "1989 (first documented)",
        "status": "Active - has gone mainstream with world championships",
    },
    {
        "name": "Bay to Breakers",
        "location": "San Francisco, California, USA",
        "origin_year": "1912",
        "status": "Active - evolved from legit race to chaotic street party",
    },
    {
        "name": "Alleycat Races",
        "location": "Worldwide (originated in Toronto/NYC bike messenger culture)",
        "origin_year": "1989",
        "status": "Active - underground bike messenger racing",
    },
    {
        "name": "Midnight Runners",
        "location": "London, UK (expanded globally)",
        "origin_year": "2015",
        "status": "Active - underground run crew turned global movement",
    },
    {
        "name": "Badwater 135",
        "location": "Death Valley to Mt. Whitney, California, USA",
        "origin_year": "1987",
        "status": "Active - invite only, 135 miles through Death Valley",
    },
    {
        "name": "Marathon des Sables",
        "location": "Sahara Desert, Morocco",
        "origin_year": "1986",
        "status": "Active - self-supported multi-stage desert ultra",
    },
    {
        "name": "Barkley Fall Classic",
        "location": "Frozen Head State Park, Tennessee, USA",
        "origin_year": "2014",
        "status": "Active - the 'fun' version of Barkley Marathons",
    },
    {
        "name": "Tough Guy",
        "location": "Wolverhampton, England",
        "origin_year": "1987",
        "status": "Defunct (2020) - the original obstacle course race, inspired Tough Mudder",
    },
    {
        "name": "Dipsea Race",
        "location": "Mill Valley to Stinson Beach, California, USA",
        "origin_year": "1905",
        "status": "Active - oldest trail race in America, handicap start system",
    },
    {
        "name": "Western States 100",
        "location": "Squaw Valley to Auburn, California, USA",
        "origin_year": "1974",
        "status": "Active - started when a horse rider decided to run instead",
    },
    {
        "name": "Comrades Marathon",
        "location": "Durban to Pietermaritzburg, South Africa",
        "origin_year": "1921",
        "status": "Active - world's oldest ultra, alternates direction each year",
    },
    {
        "name": "Caballo Blanco Ultra",
        "location": "Copper Canyons, Mexico",
        "origin_year": "2003",
        "status": "Active - founded by Micah True (Born to Run), runs with Tarahumara",
    },
    {
        "name": "Bridge the Gap",
        "location": "Various cities worldwide",
        "origin_year": "2010s",
        "status": "Active - underground crew runs across iconic bridges, often unsanctioned",
    },
    {
        "name": "Nolan's 14",
        "location": "Colorado, USA",
        "origin_year": "1999",
        "status": "Active - unsupported traverse of 14 fourteen-thousanders, no official race",
    },
    {
        "name": "Backyard Ultra",
        "location": "Worldwide (originated in Tennessee, USA)",
        "origin_year": "2011",
        "status": "Active - last person standing format, created by Lazarus Lake",
    },
    {
        "name": "Man vs Horse Marathon",
        "location": "Llanwrtyd Wells, Wales",
        "origin_year": "1980",
        "status": "Active - started from a pub bet, humans have won twice",
    },
    {
        "name": "The Speed Project",
        "location": "Los Angeles to Las Vegas, USA",
        "origin_year": "2014",
        "status": "Active - unsanctioned relay, no permits, run through the desert",
    },
    {
        "name": "Krispy Kreme Challenge",
        "location": "Raleigh, North Carolina, USA",
        "origin_year": "2004",
        "status": "Active - run 5 miles, eat a dozen donuts, run back",
    },
]


async def seed_database(db):
    """Seed the database with known races if empty."""
    from sqlalchemy import select, func
    from models import Race

    result = await db.execute(select(func.count(Race.id)))
    count = result.scalar()

    if count > 0:
        return 0

    seeded = 0
    for race_data in SEED_RACES:
        race = Race(
            name=race_data["name"],
            location=race_data.get("location", ""),
            origin_year=race_data.get("origin_year", ""),
            status=race_data.get("status", ""),
        )
        db.add(race)
        seeded += 1

    await db.commit()
    return seeded

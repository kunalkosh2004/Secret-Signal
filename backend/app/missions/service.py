import random
import re
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.game_engine import repository as game_repository
from app.missions import repository as mission_repository
from app.missions.models import Mission


COUNTRY_NAMES = {
    "argentina",
    "australia",
    "brazil",
    "canada",
    "china",
    "egypt",
    "france",
    "germany",
    "india",
    "indonesia",
    "italy",
    "japan",
    "mexico",
    "nepal",
    "netherlands",
    "norway",
    "pakistan",
    "russia",
    "singapore",
    "south africa",
    "spain",
    "sweden",
    "switzerland",
    "thailand",
    "turkey",
    "uk",
    "united kingdom",
    "usa",
    "united states",
}

COUNTRY_PATTERN = re.compile(
    r"\b("
    + "|".join(
        re.escape(country)
        for country in sorted(COUNTRY_NAMES, key=len, reverse=True)
    )
    + r")\b",
    re.IGNORECASE,
)

NUMBER_PATTERN = re.compile(
    r"\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|"
    r"eighteen|nineteen|twenty|thirty|forty|fifty|hundred|thousand|"
    r"million|billion|\d+(?:\.\d+)?)\b",
    re.IGNORECASE,
)

FOOD_WORDS = {
    "pizza", "burger", "sushi", "pasta", "rice", "chicken", "beef",
    "fish", "bread", "cake", "chocolate", "coffee", "tea", "beer",
    "wine", "apple", "banana", "orange", "mango", "strawberry",
    "biriyani", "biryani", "dosa", "idli", "samosa", "curry",
    "noodle", "noodles", "taco", "burrito", "steak", "salad",
    "soup", "sandwich", "fries", "ice cream", "donut", "pancake",
    "waffle", "cookie", "brownie", "muffin", "croissant", "bagel",
    "sushi", "ramen", "pho", "tacos", "burritos", "kebab",
}

MOVIE_WORDS = {
    "movie", "movies", "film", "films", "cinema", "theater",
    "hollywood", "bollywood", "netflix", "amazon prime",
    "disney", "marvel", "dc", "anime", "series", "show",
    "episode", "season", "director", "actor", "actress",
    "oscar", "award", "trailer", "scene", "character",
    "batman", "spiderman", "avengers", "inception", "interstellar",
    "titanic", "avatar", "frozen", "toy story", "shrek",
}

MUSIC_WORDS = {
    "music", "song", "songs", "album", "band", "singer",
    "concert", "playlist", "spotify", "guitar", "piano",
    "drums", "bass", "melody", "rhythm", "beat", "lyrics",
    "rap", "rock", "pop", "jazz", "classical", "hip hop",
    "bts", "ed sheeran", "taylor swift", "drake", "ariana",
    "concert", "gig", "festival", "dj", "remix",
}

SPORTS_WORDS = {
    "sports", "football", "soccer", "cricket", "basketball",
    "tennis", "hockey", "baseball", "volleyball", "golf",
    "boxing", "mma", "ufc", "wrestling", "f1", "formula 1",
    "olympics", "world cup", "championship", "tournament",
    "nba", "nfl", "ipl", "premier league", "champions league",
    "messi", "ronaldo", "kohli", "dhoni", "sachin",
    "serena", "federer", "nadal", "lebron", "jordan",
}

EMOTION_WORDS = {
    "happy", "sad", "angry", "excited", "scared", "afraid",
    "worried", "anxious", "nervous", "proud", "grateful",
    "lonely", "jealous", "surprised", "confused", "frustrated",
    "disappointed", "hopeful", "relieved", "embarrassed",
    "love", "hate", "fear", "joy", "trust", "regret",
    "passionate", "obsessed", "addicted", "obsession",
}

TIME_WORDS = {
    "morning", "afternoon", "evening", "night", "midnight",
    "dawn", "dusk", "today", "tomorrow", "yesterday",
    "week", "month", "year", "decade", "century",
    "hour", "minute", "second", "o'clock", "am", "pm",
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday", "weekend", "weekday",
}

WEATHER_WORDS = {
    "weather", "rain", "raining", "sunny", "cloudy", "storm",
    "stormy", "snow", "snowing", "wind", "windy", "hot",
    "cold", "warm", "humid", "dry", "flood", "drought",
    "thunder", "lightning", "fog", "foggy", "hail",
    "climate", "temperature", "forecast", "season",
}

ANIMAL_WORDS = {
    "dog", "cat", "bird", "fish", "lion", "tiger", "elephant",
    "bear", "wolf", "fox", "rabbit", "horse", "cow", "pig",
    "chicken", "duck", "snake", "monkey", "ape", "dolphin",
    "whale", "shark", "eagle", "hawk", "penguin", "owl",
    "butterfly", "bee", "ant", "spider", "crab", "lobster",
    "turtle", "frog", "hamster", "parrot", "peacock",
}

COLOR_WORDS = {
    "red", "blue", "green", "yellow", "orange", "purple",
    "pink", "brown", "black", "white", "gray", "grey",
    "silver", "gold", "cyan", "magenta", "indigo", "violet",
    "teal", "maroon", "navy", "olive", "lime", "coral",
    "turquoise", "beige", "ivory", "lavender",
}

PLACE_WORDS = {
    "city", "town", "village", "country", "state", "capital",
    "beach", "mountain", "lake", "river", "forest", "desert",
    "island", "park", "garden", "museum", "temple", "church",
    "mosque", "palace", "castle", "bridge", "tower", "monument",
    "airport", "station", "hospital", "school", "university",
    "mumbai", "delhi", "bangalore", "chennai", "kolkata",
    "new york", "london", "paris", "tokyo", "dubai",
    "sydney", "berlin", "rome", "madrid", "bangkok",
}

JOB_WORDS = {
    "job", "career", "work", "profession", "engineer", "doctor",
    "teacher", "lawyer", "artist", "musician", "writer",
    "developer", "designer", "manager", "ceo", "founder",
    "scientist", "researcher", "nurse", "chef", "pilot",
    "architect", "accountant", "journalist", "photographer",
    "athlete", "actor", "professor", "banker", "consultant",
}

TECH_WORDS = {
    "technology", "tech", "computer", "laptop", "phone",
    "smartphone", "app", "software", "hardware", "ai",
    "artificial intelligence", "machine learning", "robot",
    "internet", "wifi", "bluetooth", "cloud", "data",
    "coding", "programming", "python", "javascript",
    "apple", "google", "microsoft", "amazon", "meta",
    "openai", "chatgpt", "blockchain", "crypto", "bitcoin",
}

HEALTH_WORDS = {
    "health", "fitness", "exercise", "workout", "gym",
    "diet", "nutrition", "protein", "vitamin", "medicine",
    "doctor", "hospital", "sleep", "meditation", "yoga",
    "running", "jogging", "swimming", "cycling", "weight",
    "calorie", "sugar", "blood", "heart", "brain",
    "mental health", "stress", "anxiety", "depression",
}

EDUCATION_WORDS = {
    "education", "school", "college", "university", "study",
    "learn", "learning", "exam", "test", "homework",
    "assignment", "project", "thesis", "research", "degree",
    "diploma", "certificate", "course", "class", "lecture",
    "professor", "teacher", "student", "grade", "gpa",
    "scholarship", "phd", "masters", "bachelors",
}

FAMILY_WORDS = {
    "family", "mom", "dad", "mother", "father", "brother",
    "sister", "son", "daughter", "husband", "wife",
    "grandma", "grandpa", "grandmother", "grandfather",
    "uncle", "aunt", "cousin", "nephew", "niece",
    "sibling", "parent", "child", "children", "baby",
    "wedding", "anniversary", "reunion", "household",
}

MONEY_WORDS = {
    "money", "cash", "rich", "poor", "salary", "income",
    "expense", "savings", "invest", "investment", "stock",
    "crypto", "bitcoin", "bank", "loan", "debt", "credit",
    "debit", "tax", "budget", "profit", "loss", "billionaire",
    "millionaire", "afford", "expensive", "cheap", "cost",
    "price", "value", "worth", "dollar", "rupee", "euro",
}

NATURE_WORDS = {
    "nature", "tree", "flower", "plant", "garden", "leaf",
    "ocean", "sea", "mountain", "hill", "valley", "canyon",
    "waterfall", "river", "lake", "pond", "stream",
    "forest", "jungle", "wildlife", "animal", "bird",
    "insect", "butterfly", "bee", "ant", "flower",
    "seed", "soil", "earth", "ground", "rock", "stone",
}

ART_WORDS = {
    "art", "painting", "drawing", "sketch", "sculpture",
    "photography", "dance", "dancing", "theater", "drama",
    "poetry", "poem", "literature", "novel", "book",
    "reading", "writing", "creative", "creativity", "design",
    "fashion", "style", "beauty", "aesthetic", "gallery",
    "museum", "exhibition", "masterpiece", "canvas",
}

AGREEMENT_WORDS = {
    "yes", "yeah", "yep", "yup", "agree", "agreed",
    "exactly", "right", "true", "correct", "absolutely",
    "definitely", "totally", "completely", "100%", "sure",
    "of course", "indeed", "precisely", "spot on",
}

DISAGREEMENT_WORDS = {
    "no", "nope", "nah", "disagree", "wrong", "actually",
    "but", "however", "unfortunately", "not really",
    "i don't think", "i disagree", "that's wrong",
    "not at all", "i don't agree", "on the contrary",
}

OPINION_WORDS = {
    "i think", "i believe", "in my opinion", "i feel",
    "personally", "i guess", "i suppose", "i reckon",
    "from my perspective", "in my view", "i'd say",
    "the way i see it", "as far as i know",
}

CELEBRITY_WORDS = {
    "elon musk", "jeff bezos", "mark zuckerberg", "bill gates",
    "taylor swift", "beyonce", "rihanna", "lady gaga",
    "kanye west", "kim kardashian", "cristiano ronaldo",
    "lionel messi", "neymar", "virat kohli", "sachin tendulkar",
    "shah rukh khan", "salman khan", "tom cruise",
    "morgan freeman", "scarlett johansson", "tom hanks",
    "barack obama", "donald trump", "narendra modi",
}

BRAND_WORDS = {
    "apple", "samsung", "google", "microsoft", "amazon",
    "nike", "adidas", "gucci", "prada", "zara",
    "cocacola", "pepsi", "starbucks", "mcdonalds", "burger king",
    "tesla", "bmw", "mercedes", "ferrari", "porsche",
    "netflix", "spotify", "instagram", "tiktok", "youtube",
}

DAY_WORDS = {
    "monday", "tuesday", "wednesday", "thursday", "friday",
    "saturday", "sunday",
}

SEASON_WORDS = {
    "spring", "summer", "autumn", "fall", "winter",
    "monsoon", "rainy season", "dry season", "holiday season",
}

FEAR_WORDS = {
    "fear", "afraid", "scared", "terrified", "horror",
    "nightmare", "phobia", "anxiety", "panic", "creepy",
    "haunted", "ghost", "ghosts", "zombie", "monster",
    "serial killer", "dark", "darkness", "alone", "lonely",
}

DREAM_WORDS = {
    "dream", "dreams", "ambition", "goal", "aspiration",
    "future", "someday", "one day", "hope", "wish",
    "fantasy", "imagine", "vision", "plan", "plan to",
    "want to be", "grow up", "when i grow up",
}

CHILDHOOD_WORDS = {
    "childhood", "kid", "kids", "growing up", "young",
    "child", "children", "school days", "playground",
    "cartoon", "cartoons", "toy", "toys", "game boy",
    "playstation", "xbox", " recess", "summer vacation",
    "homework", "backpack", "lunchbox",
}

FUTURE_WORDS = {
    "future", "tomorrow", "next year", "next week",
    "someday", "one day", "eventually", "plans",
    "going to", "will", "shall", "promise",
    "prediction", "forecast", "expect", "anticipate",
}

PAST_WORDS = {
    "remember", "used to", "back in the day", "before",
    "ago", "past", "history", "ancient", "old days",
    "those days", "in those times", "previously",
    "formerly", "earlier", "once upon a time",
}

RELATIONSHIP_WORDS = {
    "relationship", "dating", "couple", "boyfriend",
    "girlfriend", "partner", "crush", "love", "romance",
    "breakup", "marriage", "wedding", "engaged",
    "single", "committed", "flirty", "flirt", "attract",
}

HUMOR_WORDS = {
    "lol", "lmao", "rofl", "haha", "hehe", "funny",
    "joke", "jokes", "hilarious", "comedy", "comedian",
    "laugh", "laughing", "meme", "memes", "pun",
    "witty", "sarcastic", "sarcasm", "tongue",
}

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u200d"
    "\u2640-\u2642"
    "\ufe0f"
    "\u2600-\u2B55"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\u3030"
    "\u2934"
    "\u2935"
    "]+",
    re.UNICODE,
)

ALL_CAPS_PATTERN = re.compile(r"\b[A-Z]{2,}\b")

EMPHASIS_WORDS = {
    "definitely", "absolutely", "certainly", "obviously",
    "clearly", "undoubtedly", "surely", "honestly",
    "seriously", "literally", "actually", "basically",
}

MISSION_TEMPLATES = [
    {
        "mission_type": "send_messages",
        "title": "Stay Active",
        "description": "Send 5 messages during the interaction phase.",
        "target_value": 5,
    },
    {
        "mission_type": "ask_questions",
        "title": "Lead the Room",
        "description": "Ask 3 questions during the interaction phase.",
        "target_value": 3,
    },
    {
        "mission_type": "country_mentions",
        "title": "Border Crossing",
        "description": "Get other players to mention countries 3 times.",
        "target_value": 3,
    },
    {
        "mission_type": "use_emojis",
        "title": "Express Yourself",
        "description": "Send 3 messages with emojis.",
        "target_value": 3,
    },
    {
        "mission_type": "use_emphasis",
        "title": "Make It Bold",
        "description": "Send 2 messages with emphasized words.",
        "target_value": 2,
    },
    {
        "mission_type": "long_messages",
        "title": "Deep Thoughts",
        "description": "Send 2 messages longer than 100 characters.",
        "target_value": 2,
    },
    {
        "mission_type": "short_messages",
        "title": "Quick Fire",
        "description": "Send 4 messages shorter than 20 characters.",
        "target_value": 4,
    },
    {
        "mission_type": "use_humor",
        "title": "Comedy Hour",
        "description": "Send 3 messages with humor markers.",
        "target_value": 3,
    },
    {
        "mission_type": "be_active",
        "title": "Life of the Party",
        "description": "Send 8 messages during the interaction phase.",
        "target_value": 8,
    },
    {
        "mission_type": "mention_numbers",
        "title": "Number Crunch",
        "description": "Get other players to mention numbers 3 times.",
        "target_value": 3,
    },
    {
        "mission_type": "mention_food",
        "title": "Foodie Talk",
        "description": "Get other players to mention food 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_movies",
        "title": "Cinema Buff",
        "description": "Get other players to mention movies/TV 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_music",
        "title": "Music Lover",
        "description": "Get other players to mention music 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_sports",
        "title": "Sports Fan",
        "description": "Get other players to mention sports 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_emotions",
        "title": "Emotional Intelligence",
        "description": "Get other players to mention emotions 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_time",
        "title": "Time Warp",
        "description": "Get other players to mention time 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_weather",
        "title": "Weather Talk",
        "description": "Get other players to mention weather 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_animals",
        "title": "Animal Kingdom",
        "description": "Get other players to mention animals 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_colors",
        "title": "Colorful Conversation",
        "description": "Get other players to mention colors 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_places",
        "title": "World Traveler",
        "description": "Get other players to mention places 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_jobs",
        "title": "Career Day",
        "description": "Get other players to mention jobs 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_technology",
        "title": "Tech Savvy",
        "description": "Get other players to mention technology 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_health",
        "title": "Wellness Check",
        "description": "Get other players to mention health 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_education",
        "title": "Knowledge Seeker",
        "description": "Get other players to mention education 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_family",
        "title": "Family Matters",
        "description": "Get other players to mention family 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_money",
        "title": "Money Talks",
        "description": "Get other players to mention money 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_nature",
        "title": "Nature Lover",
        "description": "Get other players to mention nature 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_art",
        "title": "Artistic Soul",
        "description": "Get other players to mention art 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "get_agreements",
        "title": "Smooth Talker",
        "description": "Get other players to agree with you 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "get_disagreements",
        "title": "Devil's Advocate",
        "description": "Get other players to disagree 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "get_questions_back",
        "title": "Curiosity Spark",
        "description": "Get other players to ask questions 3 times.",
        "target_value": 3,
    },
    {
        "mission_type": "mention_opinions",
        "title": "Opinion Leader",
        "description": "Get other players to share opinions 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_celebrities",
        "title": "Name Dropper",
        "description": "Get other players to mention celebrities 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_brands",
        "title": "Brand Awareness",
        "description": "Get other players to mention brands 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_days",
        "title": "Day Dreamer",
        "description": "Get other players to mention days of the week 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_seasons",
        "title": "Seasonal Vibes",
        "description": "Get other players to mention seasons 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_fears",
        "title": "Face Your Fears",
        "description": "Get other players to mention fears 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_dreams",
        "title": "Dream Catcher",
        "description": "Get other players to mention dreams 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_childhood",
        "title": "Nostalgia Trip",
        "description": "Get other players to mention childhood 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_future",
        "title": "Future Forward",
        "description": "Get other players to mention the future 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_past",
        "title": "Looking Back",
        "description": "Get other players to mention the past 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_relationships",
        "title": "Love Talk",
        "description": "Get other players to mention relationships 2 times.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_food_self",
        "title": "Foodie",
        "description": "Mention food 2 times in your messages.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_travel_self",
        "title": "Wanderlust",
        "description": "Mention travel/places 2 times in your messages.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_emotions_self",
        "title": "Emotional Openness",
        "description": "Mention emotions 2 times in your messages.",
        "target_value": 2,
    },
    {
        "mission_type": "ask_controversial",
        "title": "Provocateur",
        "description": "Ask 2 thought-provoking or controversial questions.",
        "target_value": 2,
    },
    {
        "mission_type": "get_reactions",
        "title": "Crowd Pleaser",
        "description": "Get other players to react with short exclamations 3 times.",
        "target_value": 3,
    },
    {
        "mission_type": "change_topic",
        "title": "Topic Switcher",
        "description": "Initiate 3 topic changes in the conversation.",
        "target_value": 3,
    },
    {
        "mission_type": "use_sarcasm",
        "title": "Sarcastic Genius",
        "description": "Send 2 messages with sarcastic undertones.",
        "target_value": 2,
    },
    {
        "mission_type": "mention_beliefs",
        "title": "Belief System",
        "description": "Get other players to mention beliefs/values 2 times.",
        "target_value": 2,
    },
]


async def generate_missions(
    db: AsyncSession,
    game_id: int,
    coordinator_user_id: int,
    round_number: int,
    mission_count: int = 1,
):
    existing_missions = await mission_repository.get_game_missions(
        db=db,
        game_id=game_id,
        round_number=round_number,
    )

    if existing_missions:
        return existing_missions
    if mission_count > len(MISSION_TEMPLATES):
        raise ValueError(
            "Mission count exceeds available mission templates"
        )

    selected_templates = random.sample(
        MISSION_TEMPLATES,
        k=mission_count,
    )

    missions = []

    try:
        for template in selected_templates:
            mission = await mission_repository.create_mission(
                db=db,
                game_id=game_id,
                assigned_to_user_id=coordinator_user_id,
                mission_type=template["mission_type"],
                title=template["title"],
                description=template["description"],
                target_value=template["target_value"],
                round_number=round_number,
            )

            missions.append(mission)

        await db.flush()

        for mission in missions:
            await db.refresh(mission)

        return missions

    except Exception:
        raise


async def check_mission_completion(
    db: AsyncSession,
    mission_id: int,
) -> bool:
    mission = await mission_repository.get_by_id(
        db=db,
        mission_id=mission_id,
    )

    if mission is None:
        raise ValueError("Mission not found")

    if mission.status == "completed":
        return True

    if mission.current_value < mission.target_value:
        return False

    mission.status = "completed"
    mission.completed_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(mission)

        return True

    except Exception:
        await db.rollback()
        raise


async def get_mission_progress(
    db: AsyncSession,
    game_id: int,
    round_number: int,
):
    missions = await mission_repository.get_game_missions(
        db=db,
        game_id=game_id,
        round_number=round_number,
    )

    return [
        {
            "mission_id": mission.id,
            "current_value": mission.current_value,
            "target_value": mission.target_value,
            "status": mission.status,
        }
        for mission in missions
    ]


async def increment_mission_progress(
    db: AsyncSession,
    game_id: int,
    user_id: int,
    mission_type: str,
    round_number: int,
    increment_by: int = 1,
):
    mission = await mission_repository.get_active_mission_by_type(
        db=db,
        game_id=game_id,
        user_id=user_id,
        mission_type=mission_type,
        round_number=round_number,
    )

    if mission is None:
        return None

    new_value = min(
        mission.current_value + increment_by,
        mission.target_value,
    )

    await mission_repository.update_mission_progress(
        db=db,
        mission=mission,
        current_value=new_value,
    )

    if mission.current_value >= mission.target_value:
        mission.status = "completed"
        mission.completed_at = datetime.now(timezone.utc)

    await db.flush()

    return mission


async def evaluate_message_missions(
    db: AsyncSession,
    game_id: int,
    sender_user_id: int,
    content: str,
    round_number: int,
) -> list[Mission]:
    coordinator = await game_repository.get_player_by_role(
        db=db,
        game_id=game_id,
        role="coordinator",
    )

    if coordinator is None:
        return []

    missions = await mission_repository.get_active_user_missions(
        db=db,
        game_id=game_id,
        user_id=coordinator.user_id,
        round_number=round_number,
    )

    updated_missions: list[Mission] = []

    for mission in missions:
        if not mission_matches_message(
            mission_type=mission.mission_type,
            content=content,
            sender_user_id=sender_user_id,
            coordinator_user_id=coordinator.user_id,
        ):
            continue

        new_value = min(
            mission.current_value + 1,
            mission.target_value,
        )

        await mission_repository.update_mission_progress(
            db=db,
            mission=mission,
            current_value=new_value,
        )

        if mission.current_value >= mission.target_value:
            mission.status = "completed"
            mission.completed_at = datetime.now(timezone.utc)

        updated_missions.append(mission)

    await db.flush()

    return updated_missions


def _word_set_match(words: set, content: str) -> bool:
    content_lower = content.lower()
    for word in words:
        if word in content_lower:
            return True
    return False


def _count_word_set_matches(words: set, content: str) -> int:
    content_lower = content.lower()
    count = 0
    for word in words:
        if word in content_lower:
            count += 1
    return count


def mission_matches_message(
    mission_type: str,
    content: str,
    sender_user_id: int,
    coordinator_user_id: int,
) -> bool:
    if mission_type == "send_messages":
        return sender_user_id == coordinator_user_id

    if mission_type == "ask_questions":
        return (
            sender_user_id == coordinator_user_id
            and "?" in content
        )

    if mission_type == "country_mentions":
        return (
            sender_user_id != coordinator_user_id
            and COUNTRY_PATTERN.search(content) is not None
        )

    if mission_type == "use_emojis":
        return (
            sender_user_id == coordinator_user_id
            and len(EMOJI_PATTERN.findall(content)) > 0
        )

    if mission_type == "use_emphasis":
        return (
            sender_user_id == coordinator_user_id
            and (
                len(ALL_CAPS_PATTERN.findall(content)) > 0
                or _word_set_match(EMPHASIS_WORDS, content)
            )
        )

    if mission_type == "long_messages":
        return (
            sender_user_id == coordinator_user_id
            and len(content) > 100
        )

    if mission_type == "short_messages":
        return (
            sender_user_id == coordinator_user_id
            and len(content) < 20
        )

    if mission_type == "use_humor":
        return (
            sender_user_id == coordinator_user_id
            and _word_set_match(HUMOR_WORDS, content)
        )

    if mission_type == "be_active":
        return sender_user_id == coordinator_user_id

    if mission_type == "mention_numbers":
        return (
            sender_user_id != coordinator_user_id
            and NUMBER_PATTERN.search(content) is not None
        )

    if mission_type == "mention_food":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(FOOD_WORDS, content)
        )

    if mission_type == "mention_movies":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(MOVIE_WORDS, content)
        )

    if mission_type == "mention_music":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(MUSIC_WORDS, content)
        )

    if mission_type == "mention_sports":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(SPORTS_WORDS, content)
        )

    if mission_type == "mention_emotions":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(EMOTION_WORDS, content)
        )

    if mission_type == "mention_time":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(TIME_WORDS, content)
        )

    if mission_type == "mention_weather":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(WEATHER_WORDS, content)
        )

    if mission_type == "mention_animals":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(ANIMAL_WORDS, content)
        )

    if mission_type == "mention_colors":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(COLOR_WORDS, content)
        )

    if mission_type == "mention_places":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(PLACE_WORDS, content)
        )

    if mission_type == "mention_jobs":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(JOB_WORDS, content)
        )

    if mission_type == "mention_technology":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(TECH_WORDS, content)
        )

    if mission_type == "mention_health":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(HEALTH_WORDS, content)
        )

    if mission_type == "mention_education":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(EDUCATION_WORDS, content)
        )

    if mission_type == "mention_family":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(FAMILY_WORDS, content)
        )

    if mission_type == "mention_money":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(MONEY_WORDS, content)
        )

    if mission_type == "mention_nature":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(NATURE_WORDS, content)
        )

    if mission_type == "mention_art":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(ART_WORDS, content)
        )

    if mission_type == "get_agreements":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(AGREEMENT_WORDS, content)
        )

    if mission_type == "get_disagreements":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(DISAGREEMENT_WORDS, content)
        )

    if mission_type == "get_questions_back":
        return (
            sender_user_id != coordinator_user_id
            and "?" in content
        )

    if mission_type == "mention_opinions":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(OPINION_WORDS, content)
        )

    if mission_type == "mention_celebrities":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(CELEBRITY_WORDS, content)
        )

    if mission_type == "mention_brands":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(BRAND_WORDS, content)
        )

    if mission_type == "mention_days":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(DAY_WORDS, content)
        )

    if mission_type == "mention_seasons":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(SEASON_WORDS, content)
        )

    if mission_type == "mention_fears":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(FEAR_WORDS, content)
        )

    if mission_type == "mention_dreams":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(DREAM_WORDS, content)
        )

    if mission_type == "mention_childhood":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(CHILDHOOD_WORDS, content)
        )

    if mission_type == "mention_future":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(FUTURE_WORDS, content)
        )

    if mission_type == "mention_past":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(PAST_WORDS, content)
        )

    if mission_type == "mention_relationships":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(RELATIONSHIP_WORDS, content)
        )

    if mission_type == "mention_food_self":
        return (
            sender_user_id == coordinator_user_id
            and _word_set_match(FOOD_WORDS, content)
        )

    if mission_type == "mention_travel_self":
        return (
            sender_user_id == coordinator_user_id
            and _word_set_match(PLACE_WORDS, content)
        )

    if mission_type == "mention_emotions_self":
        return (
            sender_user_id == coordinator_user_id
            and _word_set_match(EMOTION_WORDS, content)
        )

    if mission_type == "ask_controversial":
        return (
            sender_user_id == coordinator_user_id
            and "?" in content
            and _word_set_match(
                {
                    "should", "would you", "do you think",
                    "is it okay", "is it wrong", "is it right",
                    "debate", "unpopular opinion", "hot take",
                    "controversial", "most overrated", "most underrated",
                    "worst", "best", "overrated", "underrated",
                },
                content,
            )
        )

    if mission_type == "get_reactions":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(
                {
                    "wow", "omg", "no way", "seriously",
                    "shut up", "really", "are you serious",
                    "that's crazy", "insane", "unbelievable",
                    "what", "wait", "hold on",
                },
                content,
            )
        )

    if mission_type == "change_topic":
        return (
            sender_user_id == coordinator_user_id
            and _word_set_match(
                {
                    "but", "anyway", "speaking of", "that reminds me",
                    "on a different note", "unrelated", " shifting gears",
                    "let's talk about", "what about", "have you considered",
                    "moving on", "changing the subject",
                },
                content,
            )
        )

    if mission_type == "use_sarcasm":
        return (
            sender_user_id == coordinator_user_id
            and _word_set_match(
                {
                    "oh really", "wow shocker", "what a surprise",
                    "totally", "obviously", "clearly",
                    "as if", "yeah right", "sure thing",
                    "oh great", "wonderful", "fantastic",
                },
                content,
            )
        )

    if mission_type == "mention_beliefs":
        return (
            sender_user_id != coordinator_user_id
            and _word_set_match(
                {
                    "believe", "faith", "religion", "spiritual",
                    "values", "morals", "principles", "philosophy",
                    "meaning of life", "purpose", "destiny", "fate",
                    "karma", "god", "universe", "consciousness",
                },
                content,
            )
        )

    return False

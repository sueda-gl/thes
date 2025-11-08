"""
Rich biographical narrative templates for realistic agent personas.

Creates diverse, personal backstories that shape how agents think and communicate.
Includes: family situations, life circumstances, political views, personal struggles,
          conspiracy beliefs, activism, trauma, etc.

Makes agents sound like REAL people on social media (messy, opinionated, personal)
rather than sanitized corporate voices.
"""
import random
from typing import Dict, List, Any


# ============================================
# FAMILY & LIFE CIRCUMSTANCES
# ============================================

FAMILY_SITUATIONS = [
    "single parent raising two kids while working full-time",
    "recently divorced after a 15-year marriage",
    "happily married with three young children",
    "widowed 5 years ago, living alone with your cat Mittens",
    "child-free by choice and loving your freedom",
    "caring for your elderly mother with dementia",
    "expecting your first baby in 3 months",
    "struggling with infertility treatments",
    "in a long-distance relationship across different states",
    "living with your adult daughter who moved back home",
    "recently engaged and planning your wedding",
    "foster parent to two teenage boys",
    "empty nester whose kids just left for college",
    "living with chronic illness while managing work",
    "caring for your disabled veteran husband",
    "helping raise your grandchildren full-time",
    "single and actively dating via apps",
    "in recovery from addiction, 3 years sober",
    "sharing custody of your two dogs with your ex",
    "living with your partner and their elderly father",
]

PETS = [
    "Your golden retriever Luna is your best friend",
    "You have three cats that run your life",
    "Your rescue pit bull changed your perspective on judgment",
    "You foster dogs for a local shelter",
    "Your parrot won't stop talking during Zoom calls",
    "You're obsessed with your backyard chickens",
    "Your service dog helps you manage anxiety",
    "You recently lost your 14-year-old dog and you're grieving",
    None,  # No pets
    None,
]

JOBS = [
    "work as a nurse in an understaffed ER",
    "teach high school English to disengaged teens",
    "drive for Uber while looking for something better",
    "own a small coffee shop that's barely breaking even",
    "work from home as a freelance graphic designer",
    "are a stay-at-home parent (hardest job you've ever had)",
    "work in retail and deal with awful customers daily",
    "are unemployed and feeling anxious about finances",
    "work in tech and feel guilty about your high salary",
    "are a union organizer fighting for workers' rights",
    "work two part-time jobs to make ends meet",
    "recently retired and figuring out what's next",
    "are a social worker who's burned out but can't quit",
    "work in construction and your body is wearing down",
    "run a nonprofit on a shoestring budget",
]

# ============================================
# POLITICAL & IDEOLOGICAL VIEWS
# ============================================

POLITICAL_LEANINGS = [
    # Progressive
    {
        'label': 'progressive activist',
        'description': "You're politically progressive and actively involved in local organizing. You believe systemic change is necessary and individual actions aren't enough.",
        'keywords': ['systemic', 'capitalism', 'organize', 'collective action']
    },
    # Liberal mainstream
    {
        'label': 'mainstream liberal',
        'description': "You're politically liberal and vote Democrat, but you're not super political. You believe in science and think we need sensible regulations.",
        'keywords': ['vote', 'science-based', 'common sense']
    },
    # Moderate/centrist
    {
        'label': 'moderate centrist',
        'description': "You're frustrated with both parties and think the truth is somewhere in the middle. You're skeptical of extreme positions on either side.",
        'keywords': ['both sides', 'nuanced', 'pragmatic']
    },
    # Conservative
    {
        'label': 'fiscal conservative',
        'description': "You're politically conservative and skeptical of government solutions. You believe in free markets and personal responsibility over regulations.",
        'keywords': ['free market', 'personal responsibility', 'overregulation']
    },
    # Libertarian
    {
        'label': 'libertarian',
        'description': "You believe in maximum personal freedom and minimal government. You're skeptical of corporate AND government power.",
        'keywords': ['freedom', 'liberty', 'both parties corrupt']
    },
    # Apolitical
    {
        'label': 'politically disengaged',
        'description': "You avoid politics entirely - it's too depressing and nothing ever changes anyway. You focus on your own life and family.",
        'keywords': ['don\'t follow politics', 'tune it out', 'all the same']
    },
]

CONSPIRACY_BELIEFS = [
    None,  # No conspiracy beliefs (70% of population)
    None,
    None,
    None,
    None,
    None,
    None,
    "You're suspicious that climate science is exaggerated by elites to control people",
    "You think big corporations deliberately suppress clean energy to protect profits",
    "You believe the media is controlled by a few powerful interests",
    "You question whether we're being told the truth about environmental data",
    "You think most charities and nonprofits are scams",
    "You're convinced social media platforms manipulate what you see",
]

# ============================================
# PERSONAL STRUGGLES & LIFE EVENTS
# ============================================

RECENT_EVENTS = [
    None,  # Nothing major (50%)
    None,
    None,
    None,
    None,
    "Your best friend just died from cancer and you're reevaluating everything",
    "You just lost your job and you're scared about money",
    "You recently moved to a new city where you don't know anyone",
    "Your teenager is going through a crisis and you're worried sick",
    "You were diagnosed with a chronic illness last month",
    "Your house was damaged in a storm and insurance is fighting you",
    "You're going through bankruptcy after medical bills",
    "Your parent just passed away and you're dealing with their estate",
    "You recently had a mental health crisis",
    "Your relationship is falling apart and you're considering divorce",
]

# ============================================
# ENVIRONMENTAL ATTITUDES & BEHAVIORS
# ============================================

ENVIRONMENTAL_STANCES = {
    'very_high': [
        "You're vegan for ethical and environmental reasons and it's part of your identity",
        "You bike everywhere and get angry at SUV drivers",
        "You've organized climate protests and gotten arrested twice",
        "You quit your corporate job to work in sustainability for half the pay",
        "You live in an off-grid tiny house and make your own soap",
    ],
    'high': [
        "You compost, recycle religiously, and guilt-trip friends who don't",
        "You're vegetarian and trying to reduce your carbon footprint",
        "You drive a Prius and feel smug about it",
        "You've installed solar panels and love telling people about it",
        "You shop at farmers markets and avoid fast fashion",
    ],
    'moderate': [
        "You care about the environment but you're not perfect - you try when it's convenient",
        "You recycle and bring reusable bags but don't stress about it too much",
        "You think climate change is real but you're overwhelmed about what to do",
        "You want to do better environmentally but it's expensive and complicated",
        "You care in theory but your day-to-day life doesn't reflect it much",
    ],
    'low': [
        "You recycle if it's easy but it's not a priority",
        "You think environmentalists are often annoying and preachy",
        "You care about the environment but think individual actions are pointless",
        "You're skeptical that your choices matter when corporations pollute freely",
        "You're tired of being lectured about climate change",
    ],
    'very_low': [
        "You think climate change is overblown by alarmists",
        "You're sick of environmental guilt-tripping and virtue signaling",
        "You drive a pickup truck and don't apologize for it",
        "You think environmentalism is a luxury belief for wealthy liberals",
        "You're annoyed by people who make their entire personality about being eco-friendly",
    ]
}

# ============================================
# SOCIAL MEDIA BEHAVIOR TYPES
# ============================================

SOCIAL_MEDIA_STYLES = [
    "You overshare about your personal life constantly",
    "You lurk mostly but comment when something really pisses you off",
    "You post inspirational quotes and your friends find it annoying",
    "You share every article you read without checking if it's true",
    "You get into arguments in comments and can't let things go",
    "You post photos of your meals and kids constantly",
    "You use social media to humble-brag about your life",
    "You're the person who always comments 'thoughts and prayers'",
    "You share memes constantly but rarely post your actual thoughts",
    "You post rants late at night that you regret in the morning",
]

# ============================================
# GENERATION FUNCTIONS
# ============================================

def generate_rich_backstory(
    env_concern: float,
    personality: Dict[str, float],
    interests: List[str],
    age: int,
    rng: random.Random
) -> str:
    """
    Generate a rich, personal narrative backstory.
    
    Combines family situation, political views, life circumstances, and
    environmental behaviors into a coherent personal narrative.
    """
    
    # Select components
    family = rng.choice(FAMILY_SITUATIONS)
    pet = rng.choice(PETS)
    job = rng.choice(JOBS)
    politics = rng.choice(POLITICAL_LEANINGS)
    conspiracy = rng.choice(CONSPIRACY_BELIEFS)
    recent_event = rng.choice(RECENT_EVENTS)
    social_style = rng.choice(SOCIAL_MEDIA_STYLES)
    
    # Environmental stance based on concern level
    if env_concern > 0.7:
        env_stance = rng.choice(ENVIRONMENTAL_STANCES['very_high'])
    elif env_concern > 0.55:
        env_stance = rng.choice(ENVIRONMENTAL_STANCES['high'])
    elif env_concern > 0.4:
        env_stance = rng.choice(ENVIRONMENTAL_STANCES['moderate'])
    elif env_concern > 0.25:
        env_stance = rng.choice(ENVIRONMENTAL_STANCES['low'])
    else:
        env_stance = rng.choice(ENVIRONMENTAL_STANCES['very_low'])
    
    # Build narrative
    narrative_parts = []
    
    # Core identity
    narrative_parts.append(f"You're a {age}-year-old who {job}.")
    
    # Family
    narrative_parts.append(f"You're {family}.")
    
    # Pet (if has one)
    if pet:
        narrative_parts.append(pet + ".")
    
    # Political stance
    narrative_parts.append(f"Politically, {politics['description']}")
    
    # Environmental behavior
    narrative_parts.append(env_stance + ".")
    
    # Recent life event (if any)
    if recent_event:
        narrative_parts.append(recent_event + ".")
    
    # Conspiracy belief (if any)
    if conspiracy:
        narrative_parts.append(conspiracy + ".")
    
    # Social media style
    narrative_parts.append(f"On social media, {social_style.lower()}")
    
    # Personality-specific additions
    if personality['neuroticism'] > 0.7:
        narrative_parts.append("You tend to worry a lot and feel anxious about world events.")
    
    if personality['extraversion'] > 0.7:
        narrative_parts.append("You're very social and love engaging with people online.")
    elif personality['extraversion'] < 0.3:
        narrative_parts.append("You're pretty introverted and prefer observing to posting.")
    
    if personality['agreeableness'] < 0.3:
        narrative_parts.append("You don't sugarcoat your opinions and sometimes come across as harsh.")
    
    if personality['openness'] > 0.7:
        narrative_parts.append("You love exploring new ideas and unconventional perspectives.")
    
    return " ".join(narrative_parts)


def generate_political_keywords(politics: Dict) -> List[str]:
    """Generate keywords that reflect political leaning."""
    return politics['keywords']


if __name__ == '__main__':
    """Test generation."""
    rng = random.Random(42)
    
    # Test with different profiles
    test_cases = [
        (0.8, {'openness': 0.8, 'neuroticism': 0.6, 'extraversion': 0.7, 'agreeableness': 0.7, 'conscientiousness': 0.6}, 35),
        (0.3, {'openness': 0.3, 'neuroticism': 0.4, 'extraversion': 0.3, 'agreeableness': 0.4, 'conscientiousness': 0.5}, 55),
        (0.6, {'openness': 0.6, 'neuroticism': 0.8, 'extraversion': 0.4, 'agreeableness': 0.3, 'conscientiousness': 0.4}, 28),
    ]
    
    print("=" * 80)
    print("SAMPLE BIOGRAPHICAL NARRATIVES")
    print("=" * 80)
    
    for i, (env, pers, age) in enumerate(test_cases, 1):
        print(f"\n--- EXAMPLE {i} (env_concern={env}, age={age}) ---")
        backstory = generate_rich_backstory(
            env_concern=env,
            personality=pers,
            interests=['sustainability', 'cooking'],
            age=age,
            rng=rng
        )
        print(backstory)
        print()


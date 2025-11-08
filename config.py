"""
Central configuration for the AI Social Media Simulation.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ============================================
# API CONFIGURATION
# ============================================
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_API_VERSION = os.getenv("AZURE_API_VERSION", "2025-01-01-preview")

# ============================================
# SIMULATION PARAMETERS
# ============================================
# ============================================
# EXPERIMENT TIMELINE
# ============================================
# Simulation timeline (1 step = 1 minute):
#
# Phase 1: BURN-IN (Steps 0-1439, Day 0)
#   Duration: 1440 steps = 24 hours = 1 day
#   Purpose: Establish organic social timeline before intervention
#   Activity: Agents post organically, build initial content base
#   Expected: ~25-50 organic posts from Activity-driven Poisson posting
#
# Phase 2: CAMPAIGN INJECTION (Step 1440, Start of Day 1)
#   Hope campaign → 10% of agents (stratified by Activity×Degree)
#   Fear campaign → 10% of agents (stratified by Activity×Degree)  
#   Control group → 80% (may see campaigns via friends' reshares)
#
# Phase 3: OBSERVATION (Steps 1440-7199, Days 1-5)
#   Duration: 5760 steps = 96 hours = 4 days
#   Purpose: Track responses, reshares, cascades
#   Metrics: Engagement rates, cascade size/depth, structural virality
#
# TOTAL: 7200 steps = 120 hours = 5 days

NUM_AGENTS = int(os.getenv("NUM_AGENTS", 100))  # Number of agents
SIMULATION_STEPS = int(os.getenv("SIMULATION_STEPS", 7200))  # 5 days total
CAMPAIGN_LAUNCH_STEP = int(os.getenv("CAMPAIGN_LAUNCH_STEP", 1440))  # After 1 day
RANDOM_SEED = int(os.getenv("RANDOM_SEED", 42))

# ============================================
# LLM PARAMETERS
# ============================================
LLM_MODEL = "gpt-4o"  # Azure OpenAI deployment name (not model name)
LLM_TEMPERATURE = 0.4  # Lower temperature for more consistent decisions (reduced variance)
LLM_MAX_TOKENS = 300  # Full responses for better quality
LLM_MAX_CONCURRENT = 5  # Optimal balance of speed and stability
LLM_MAX_RETRIES = 3

# Token pricing (per 1K tokens) - GPT-4o rates
INPUT_TOKEN_COST = 0.0025 / 1000  # $0.0025 per 1K input tokens (GPT-4o)
OUTPUT_TOKEN_COST = 0.01 / 1000   # $0.01 per 1K output tokens (GPT-4o)

# ============================================
# TEMPORAL MECHANICS
# ============================================
# Activity-driven heterogeneity model based on empirical social media patterns:
#
# HETEROGENEOUS USER ACTIVITY:
# Social media users exhibit highly skewed activity levels. Studies show:
# - 75% of users are "lurkers" with minimal activity (Murdock et al., 2024)
# - Top 25% produce 97% of content (McClain et al., 2021, cited in Murdock 2024)
# - Top 2% create 80% of tweets (Liang & Kw, 2015, cited in Murdock 2024)
#
# IMPLEMENTATION - ENGAGED USER SUBSET:
# We model Activity ∈ [0.3, 1.0] (engaged users) rather than [0, 1.0] (full population).
# This focuses on users who meaningfully participate in information diffusion,
# excluding extreme lurkers (Activity < 0.3) who rarely interact.
#
# Justification:
# - Statistical power: Lurkers dilute treatment effects without adding insight
# - Theoretical: Research question concerns engaged users who drive cascades
# - Empirical: Murdock et al. show lurkers contribute minimally to diffusion
#
# TEMPORAL SCALING:
# - Online duration = Activity × 143 min/day (DataReportal 2024 global average)
#   → With Activity ∈ [0.3, 1.0]: 43–143 min/day (casual to power users)
# - Posting rate = Activity × 15 posts/month (typical active user behavior)
#   → Produces heterogeneous engagement consistent with empirical patterns
#
# REFERENCES:
# - Murdock, I., Carley, K. M., & Yağan, O. (2024). An agent-based model of
#   cross-platform information diffusion. Social Network Analysis & Mining, 14, 145.
# - DataReportal (2024). Digital 2024: Global Overview Report.

STEP_MINUTES = 1            # 1 simulation step = 1 minute
DAY_MINUTES = 1440          # 1440 minutes per day (24 × 60)
AVG_LOGIN = 143             # Average daily minutes online (DataReportal 2024)
AVG_POSTRATE = 15           # Average monthly posts for typical active user
MONTH_STEPS = int(30 * DAY_MINUTES)  # 43,200 steps per month

# Activity scaling (linear, no multipliers):
# - Activity = 0.5 → 71.5 min/day online (lurker/casual)
# - Activity = 0.85 → 121.5 min/day online (medium user)
# - Activity = 1.0 → 143 min/day online (high-activity user)

# ============================================
# NETWORK PARAMETERS (Barabási & Albert 1999)
# ============================================
BA_M0 = 8                   # Seed clique size
BA_M = 8                    # Edges per new node (controls density)

# ============================================
# AGENT MEMORY & REFLECTION PARAMETERS (Park et al. 2023)
# ============================================
FEED_SIZE = 7               # Number of posts shown in feed

# Memory Stream Settings
MEMORY_SIZE = 50  # Maximum memories to store (increased from 10)
REFLECT_EVERY = 3  # Steps between reflection summaries
MEMORY_SUMMARY_K = 10  # Number of memories to retrieve for reflection (increased from 5)

# Reflection Generation Settings
REFLECTION_TEMPERATURE = 0.5  # Lower temp for consistent reflections
REFLECTION_MAX_TOKENS = 100  # Shorter than decision prompts

# Importance Calculation Weights
IMPORTANCE_CAMPAIGN_BOOST = 0.3  # Boost for campaign posts
IMPORTANCE_ACTION_BOOST = 0.2  # Boost for own actions
IMPORTANCE_HIGH_ENGAGEMENT_THRESHOLD = 10  # Likes+comments threshold
IMPORTANCE_INTEREST_ALIGNMENT_BOOST = 0.15  # Boost for aligned content

# Retrieval Scoring
RETRIEVAL_RECENCY_WEIGHT = 0.5  # Balance between importance (0.5) and recency (0.5)

# ============================================
# CAMPAIGN MESSAGES
# ============================================
CAMPAIGNS = {
    "hope": {
        "type": "hope",
        "message": (
            "The great reversal has begun. "
            "For the first time in history, renewables are outpacing fossil fuels. "
            "Entire regions once smothered in smoke now glow with wind-powered light. "
            "Coral reefs once declared dead are flickering back to life. "
            "Air once toxic has turned blue again. "
            "And your choice matters. "
            "A five-minute switch to clean power adds your share to the comeback — "
            "cutting pollution that sends thousands to hospitals each year and keeping warming below 1.5 °C. "
            "The process is verified, quick, and confirmed within a day. "
            "Be the reason your family breathes cleaner air and the planet wins its fight."
        )
    },
    "fear": {
        "type": "fear",
        "message": (
            "This is how civilisation collapses — quietly, degree by degree. "
            "We're on track to cross 1.5 °C by 2030. Once that line is crossed, the world we know unravels: "
            "Cities suffocate under heat so intense the human body can't survive outdoors. "
            "Rivers that feed billions run dry. "
            "Entire coastlines disappear under rising seas. "
            "Food prices skyrocket as harvests fail across continents. "
            "This isn't distant — it's your world, your future. "
            "But you can still push back. "
            "A five-minute switch to verified clean energy keeps about a tonne of CO₂ out of the air each year — "
            "enough to power your home for two months or cool a neighbourhood for days. "
            "The window to act is closing. Every day of delay locks in another disaster. "
            "Act before the tipping point becomes permanent."
        )
    }
}

# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_PATH = "data/simulation.db"

# ============================================
# PERSONA CONFIGURATION
# ============================================
PERSONA_FILE = "personas/personas.json"
DISTRIBUTIONS_FILE = "personas/distributions.json"

# Social behavior distribution
SOCIAL_BEHAVIOR_DIST = {
    "lurker": 0.30,
    "casual": 0.40,
    "active": 0.25,
    "power_user": 0.05
}

# ============================================
# FEED PARAMETERS
# ============================================
# Reverse chronological feed with recency window
# Users prefer chronological ordering for transparency (Rader & Gray, 2015)
# Message visibility decays with position/time (Hodas & Lerman, 2014)
#
# REFERENCES:
# - Rader, E., & Gray, R. (2015). Understanding user beliefs about algorithmic
#   curation in the Facebook News Feed. CHI '15, 173-182.
# - Hodas, N. O., & Lerman, K. (2014). The simple rules of social contagion.
#   Scientific Reports, 4, 4343.

VISIBILITY_WINDOW = 100  # Posts visible within last N steps (recency-only)
FEED_SIZE = 7               # Number of posts shown to agent


# ============================================
# CAMPAIGN TARGETING CONFIGURATION
# ============================================
CAMPAIGN_FRAC_HOPE = 0.1  # Fraction of agents to target with Hope campaign (default 10%)
CAMPAIGN_FRAC_FEAR = 0.1  # Fraction of agents to target with Fear campaign (default 10%)

# ============================================
# BELIEF MEASUREMENT CONFIGURATION
# ============================================
# Longitudinal belief measurement at T0 (pre-campaign), T1 (immediate), T2 (sustained)
# Tracks environmental_concern evolution in response to Hope vs Fear campaigns

BELIEF_MEASUREMENT_STEPS = [
    1439,  # T0: Right before campaign launch (baseline)
    2880,  # T1: 1 day after campaign (immediate effect, 1440 steps post-launch)
    7200   # T2: End of simulation (sustained effect, 4 days post-launch)
]

BELIEF_ATTRIBUTE = 'environmental_concern'  # Primary outcome variable
BELIEF_CONCURRENCY_LIMIT = 30  # Max parallel belief measurements

# ============================================
# EXPORT CONFIGURATION
# ============================================
RESULTS_DIR = "data/results"


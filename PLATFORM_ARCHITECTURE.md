# Platform Architecture - Final Clean Version

## What Your Social Media Simulator Does

Your implementation creates a **hybrid platform** combining realistic social mechanics with LLM semantic reasoning:

### 1. Network Layer (Barabási-Albert 1999)
**Purpose:** Determines who sees whose content
```python
# personas/social_graph.py
G = generate_ba(n=1000, m0=8, m=8, seed=42)
# Creates scale-free network: few hubs, many peripheral users
# Agent A sees posts from people A follows
```

### 2. Temporal Layer (Murdock et al. 2024; DataReportal 2024)
**Purpose:** Controls when agents are online and posting
```python
# simulation/agent.py
self.activity = rng.random()  # e.g., 0.3, 0.7
# High activity → more time online, more frequent posts
# FSM: online ↔ offline with Activity-driven durations
```

### 3. Feed Layer (Hodas & Lerman 2014; Rader & Gray 2015)
**Purpose:** Determines which posts agents see
```python
# simulation/platform.py - build_feed()
# Show posts from followed users
# Filter: only last 100 steps (recency window)
# Sort: newest first (reverse chronological)
# Return: top 7 posts
```

### 4. Decision Layer (Park et al. 2023 + LLM)
**Purpose:** How agents respond to content
```python
# simulation/agent.py - decide_action()
# LLM reads post text + persona
# Decides: like, reshare, comment, or ignore
# Based on: semantic content, not numeric scores
```

### 5. Cascade Layer (Serrano 2016, Goel 2016)
**Purpose:** Track how information spreads
```python
# Posts store parent_id → forms trees
# Reshares link to original → enables tracking
# Structural virality ξ measures shape (broadcast vs viral)
```

## What Was Removed (No Longer Used)

### ✗ Numeric Engagement Formula
```python
# DELETED from platform.py
def engagement_prob(activity, score, age):
    return activity × score
```
**Why removed:** LLM makes all decisions semantically; numeric gating not needed

### ✗ Post Numeric Attributes
```sql
-- DELETED from schema
interest_score REAL  -- Beta(2,2)
reading_time REAL    -- Log-normal
```
**Why removed:** LLM reads text content, doesn't need numeric appeal scores

### ✗ Configuration Parameters
```python
# DELETED from config.py
INTEREST_SCORE_ALPHA/BETA
READING_TIME_MU/SIGMA
NOVELTY_DECAY_ENABLED/LAMBDA
```
**Why removed:** No numeric scoring, no decay factors needed

## Complete Data Flow: Hope vs Fear Experiment

### Setup Phase
```
1. Generate BA network (1000 agents, m=8)
   → Agent 1 follows agents 3,7,12,45,67,88,91,102
   
2. Initialize agents
   → Agent 1 gets Activity=0.47 (online ~22 min/day)
   → Agent 2 gets Activity=0.83 (online ~38 min/day)
   
3. Run burn-in (0-200 steps)
   → Agents go online/offline via FSM
   → Create organic posts via Poisson schedule
   → Build social timeline
```

### Campaign Injection (Step 200)
```
4. Inject Hope campaign to 10% of agents (e.g., Agent 1)
   → Creates post: "Together we're building a cleaner planet..."
   → post_type='campaign', parent_id=NULL
   
5. Inject Fear campaign to different 10% (e.g., Agent 50)
   → Creates post: "Time is running out. Environmental damage..."
   → post_type='campaign', parent_id=NULL
```

### Agent Response Loop (Steps 201-2000)
```
6. Each step:
   FOR each agent:
     a) agent.tick(step)  # FSM advances
     b) IF agent.online:
          - feed = platform.build_feed(agent_id, step)
            → Queries: followed users' posts
            → Filters: created_step > (step - 100)
            → Sorts: newest first
            → Returns: top 7
          
          - action = agent.decide_action(feed, step)
            → LLM reads post texts
            → LLM sees persona (values, interests)
            → LLM outputs: like/reshare/comment/none
          
          - IF action == 'like':
              platform.create_like(agent_id, post_id, step)
          
          - IF action == 'reshare':
              platform.create_reshare(agent_id, post_id, None, step)
              → Creates new post with parent_id link
              → Appears in followers' feeds
```

### Analysis Phase
```
7. After 2000 steps:
   - Extract all posts from database
   - Build cascade trees using parent_id links
   - Calculate ξ for each cascade (Goel Algorithm 1)
   - Compare Hope vs Fear:
     → Like rates
     → Reshare rates
     → Cascade sizes
     → Structural virality ξ
```

## What Papers Contribute to Each Layer

| System Component | What It Does | From Which Paper |
|-----------------|--------------|------------------|
| **Network structure** | Who follows whom (scale-free) | Barabási & Albert (1999) |
| **Activity variable** | Individual engagement intensity | Murdock et al. (2024) |
| **Online/offline FSM** | When agents are present | Generic FSM |
| **Posting schedule** | When organic posts created | Murdock et al. (2024) |
| **Feed visibility** | Which posts agents see (recency) | Hodas & Lerman (2014) |
| **Feed ranking** | Order of posts (newest first) | Rader & Gray (2015) |
| **Parent-id trees** | Cascade structure | Serrano & Iglesias (2016) |
| **Structural virality** | Cascade shape metric | Goel et al. (2016) |
| **Memory stream** | Agent memory architecture | Park et al. (2023) |
| **LLM decisions** | Content-based engagement | **Your work** |

## Key Architectural Principle

**Selective adoption**: Use published models where they serve the experiment (network, timing, visibility); replace with LLM where semantic interpretation is required (engagement decisions).

**Result**: A platform that is:
- ✓ Realistic (validated against empirical benchmarks)
- ✓ Transparent (every component has clear source)
- ✓ Semantic-capable (agents interpret meaning, not just statistics)
- ✓ Traceable (code maps to cited algorithms)

## For Your Thesis: What To Write

### Methodology Chapter
"We synthesize structural models from Barabási & Albert (1999), activity heterogeneity from Murdock et al. (2024), feed visibility from Hodas & Lerman (2014) and Rader & Gray (2015), and cascade metrics from Goel et al. (2016) and Serrano & Iglesias (2016). LLM agents make engagement decisions based on semantic interpretation of content rather than numeric formulas."

### Implementation Chapter
"The platform combines async SQLite persistence with NetworkX graph operations and LLM API calls. All engagement decisions are LLM-driven; hope vs fear effects emerge from agents' qualitative responses to message framing rather than numeric scoring differences."

### Experiment Chapter
"Hope and fear campaigns have identical platform mechanics (network position, feed visibility, cascade structure). Observed differences in engagement rates and diffusion patterns reflect LLM agents' semantic interpretation of persuasive framing."

## Validation Checklist

Before claiming "valid social media simulation":
- ✓ Network power-law exponent γ̂ ∈ [2.7, 3.3]
- ✓ Average clustering < 0.1
- ✓ Activity distribution uniform U(0,1)
- ✓ Average online time ≈ 23 min/day
- ✓ Engagement inequality Gini > 0.6
- ✓ Cascade ξ ∈ [2, 8]
- ✓ Weak size-ξ correlation (ρ < 0.3)

Run `analysis/validation.py` after each simulation to verify.


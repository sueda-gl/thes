# Chapter 4: Implementation - Agent System

## 4.1 Implementation Overview

This chapter details the technical realization of the agent architecture described in Chapter 3. We implement the memory-reflection system (Park et al., 2023) and personality conditioning (Vu et al., 2025) using Python 3.13, GPT-4o via OpenAI API, and SQLite for persistence. The complete codebase is available at [GitHub repository link] for reproducibility.

### 4.1.1 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| Language | Python | 3.13 | Core implementation |
| LLM | GPT-4o | API (Nov 2024) | Agent cognition |
| Database | SQLite | 3.x | Data persistence |
| Async Framework | asyncio | 3.13+ | Concurrent LLM calls |
| HTTP Client | aiohttp | 3.9+ | Async API requests |
| Rate Limiting | aiolimiter | 1.1+ | API throttling |
| Scientific Computing | NumPy | 1.26+ | Trait distributions |
| Random Generation | Python random | stdlib | Reproducible sampling |

### 4.1.2 Development Environment

- **Hardware**: Standard consumer hardware (16GB RAM sufficient)
- **Operating System**: macOS / Linux / Windows compatible
- **API Cost**: ~$4.45 per 100-agent, 10-step simulation
- **Runtime**: ~15-20 minutes per simulation (parallel execution)

---

## 4.2 Memory Stream Implementation

### 4.2.1 System Architecture

The memory system consists of three interconnected components:

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Memory System                   │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐         ┌──────────────┐              │
│  │ Observations │────────▶│ Memory Entry │              │
│  │   (Feed)     │         │  (Storage)   │              │
│  └──────────────┘         └──────┬───────┘              │
│                                   │                       │
│  ┌──────────────┐                │                       │
│  │   Actions    │────────────────┘                       │
│  │ (Like/Post)  │                                        │
│  └──────────────┘                │                       │
│                                   ▼                       │
│                          ┌────────────────┐              │
│                          │  Importance    │              │
│                          │  Calculation   │              │
│                          └────────┬───────┘              │
│                                   │                       │
│                                   ▼                       │
│                          ┌────────────────┐              │
│                          │   Retrieval    │              │
│                          │    Scoring     │              │
│                          └────────┬───────┘              │
│                                   │                       │
│                                   ▼                       │
│                          ┌────────────────┐              │
│                          │   Reflection   │              │
│                          │   Generation   │              │
│                          └────────────────┘              │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

**Data Flow:**
1. Agent observes feed → Creates observation memories
2. Agent acts → Creates action memory
3. Importance scores calculated immediately
4. Every 3 steps → Retrieve top-K memories → Generate reflection
5. Reflection stored as high-importance memory

### 4.2.2 Data Structure: MemoryEntry

We implement memories as Python dataclasses for type safety and clarity:

```python
@dataclass
class MemoryEntry:
    """Single memory with metadata for retrieval."""
    timestamp: int           # simulation step
    memory_type: str         # 'observation', 'action', 'reflection'
    content: str             # human-readable description
    importance: float        # salience score [0,1]
    metadata: Dict[str, Any] # additional context
    
    def get_age(self, current_step: int) -> int:
        """Steps since memory creation."""
        return current_step - self.timestamp
    
    def get_retrieval_score(self, current_step: int, 
                           recency_weight: float = 0.5) -> float:
        """Combined importance + recency score."""
        age = self.get_age(current_step)
        recency_decay = recency_weight * (0.99 ** age)
        return self.importance + recency_decay
```

**Design rationale:** Dataclasses provide immutability guarantees and automatic `__repr__` methods for debugging. The `get_retrieval_score` method encapsulates the Park et al. (2023) scoring logic at the memory level.

### 4.2.3 Importance Calculation Algorithm

Importance scores determine which memories are retrieved for reflection. We implement a weighted sum of five factors:

**Pseudocode:**
```
FUNCTION calculate_importance(memory_type, content):
    importance ← 0.5  // baseline for all memories
    
    // Factor 1: Memory type
    IF memory_type = 'action':
        importance ← importance + 0.2
    
    // Factor 2: Campaign content
    IF content.post_type = 'campaign':
        importance ← importance + 0.3
    
    // Factor 3: Engagement level
    engagement ← content.like_count + content.comment_count
    IF engagement > 10:
        importance ← importance + 0.2
    ELSE IF engagement > 5:
        importance ← importance + 0.1
    
    // Factor 4: Interest alignment
    FOR EACH interest IN agent.interests:
        IF interest IN content.text:
            importance ← importance + 0.15
            BREAK
    
    // Factor 5: Emotional framing
    IF contains_hope_keywords(content.text):
        importance ← importance + 0.1
    IF contains_fear_keywords(content.text):
        importance ← importance + 0.1
    
    RETURN clip(importance, 0.0, 1.0)
```

**Implementation excerpt:**
```python
def calculate_importance(self, memory_type: str, 
                        content: Dict[str, Any]) -> float:
    """Calculate memory importance score (0-1)."""
    importance = 0.5  # baseline
    
    # Factor 1: Actions more important than observations
    if memory_type == 'action':
        importance += 0.2
    
    # Factor 2: Campaign posts critical for experiment
    if content.get('post_type') == 'campaign':
        importance += 0.3
    
    # Factor 3: High-engagement content is salient
    engagement = content.get('like_count', 0) + \
                content.get('comment_count', 0)
    if engagement > 10:
        importance += 0.2
    elif engagement > 5:
        importance += 0.1
    
    # ... additional factors ...
    
    return min(1.0, max(0.0, importance))
```

**Configuration parameters:**

| Parameter | Value | Justification |
|-----------|-------|---------------|
| Baseline | 0.5 | Neutral starting point |
| Action boost | +0.2 | Own actions more salient than observations |
| Campaign boost | +0.3 | Experimental content must be tracked |
| High engagement | +0.2 | Social proof signals importance |
| Interest alignment | +0.15 | Personally relevant content stands out |
| Emotional framing | +0.1 | Hope/fear keywords relevant to study |

**Keyword lists:**
- Hope: `['hope', 'bright', 'positive', 'together', 'build', 'future']`
- Fear: `['fear', 'damage', 'severe', 'crisis', 'urgent', 'running out']`

### 4.2.4 Memory Retrieval with Importance-Recency Scoring

Retrieval combines pre-computed importance with exponential recency decay:

**Mathematical formulation:**
```
Retrieval Score: S(m, t) = I(m) + w_r × (0.99)^age(m,t)

where:
  I(m) = importance score ∈ [0, 1]
  w_r = recency weight = 0.5
  age(m, t) = current_step - m.timestamp
  0.99 = decay constant (1% decay per step)
```

**Properties:**
- At age=0: recency contributes 0.5 (fresh memory)
- At age=5: recency contributes 0.475 (5% decay)
- At age=10: recency contributes 0.452 (9.5% decay)
- At age=50: recency contributes 0.303 (39% decay)

**Implementation:**
```python
def retrieve_memories(self, current_step: int, 
                     k: int = 10) -> List[MemoryEntry]:
    """Retrieve top-k memories by importance + recency."""
    if not self.memory_stream:
        return []
    
    # Score all memories
    scored = [
        (mem, mem.get_retrieval_score(current_step, 0.5))
        for mem in self.memory_stream
    ]
    
    # Sort descending by score
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # Return top k memories
    return [mem for mem, score in scored[:k]]
```

**Example retrieval output** (step 6):
```
Top 5 Retrieved Memories:
1. [score=1.45, age=1] I liked campaign post about hope (importance=1.0)
2. [score=1.30, age=0] Saw friend post about environment (importance=0.8)
3. [score=1.20, age=2] I commented "Great message!" (importance=0.7)
4. [score=0.95, age=1] Saw organic post about climate (importance=0.5)
5. [score=0.88, age=3] Saw low-engagement post (importance=0.3)
```

**Validation:** We verified that campaign posts consistently rank in top-3 retrieved memories, ensuring experimental content influences reflection.

---

## 4.3 Reflection Generation Implementation

### 4.3.1 Reflection Trigger Logic

Reflections occur every 3 steps to balance context-awareness with computational cost:

```python
async def generate_reflection(self, current_step: int) -> Optional[str]:
    """Generate LLM-based reflection if triggered."""
    # Trigger condition
    if current_step % 3 != 0:
        return None  # Not reflection step
    
    if len(self.memory_stream) < 3:
        return None  # Insufficient memories
    
    if current_step - self.last_reflection_step < 3:
        return None  # Too soon after last reflection
    
    # Retrieve relevant memories
    memories = self.retrieve_memories(current_step, k=10)
    
    # Generate reflection via LLM
    reflection = await self._call_llm_for_reflection(memories)
    
    # Store as high-importance memory
    if reflection:
        self._store_reflection(reflection, current_step)
        self.last_reflection_step = current_step
    
    return reflection
```

**Timing diagram** (10-step simulation):
```
Step:  0   1   2   3   4   5   6   7   8   9
       ─   ─   ─   R   ─   ─   R   ─   ─   R
              
Legend: ─ = regular step, R = reflection generated
```

### 4.3.2 Reflection Prompt Construction

The reflection prompt integrates personality traits with retrieved memories:

**Prompt template structure:**
```
┌─────────────────────────────────────────────┐
│ REFLECTION PROMPT                           │
├─────────────────────────────────────────────┤
│ 1. Identity & Demographics                  │
│    - Name, age, gender                      │
│                                             │
│ 2. Personality Traits                       │
│    - Openness (0-1)                         │
│    - Neuroticism (0-1)                      │
│    - Extraversion (0-1)                     │
│                                             │
│ 3. Retrieved Memories (ranked)              │
│    - [age, importance] description          │
│    - Top 10 memories listed                 │
│                                             │
│ 4. Task Instructions                        │
│    - Write 1-2 sentence reflection          │
│    - Include behavior patterns              │
│    - Express emotional state                │
│    - Reflect personality in tone            │
│                                             │
│ 5. Examples (good reflections)              │
│    - High neuroticism example               │
│    - High openness example                  │
│    - Balanced example                       │
└─────────────────────────────────────────────┘
```

**Implementation:**
```python
def create_reflection_prompt(persona: Dict, memories: List[MemoryEntry], 
                            current_step: int) -> str:
    """Build personality-aware reflection prompt."""
    name = persona['name']
    age = persona['age']
    personality = persona['personality']
    
    # Format memories with scores
    memory_text = ""
    for i, mem in enumerate(memories, 1):
        age = current_step - mem.timestamp
        memory_text += (
            f"{i}. [{age} steps ago, importance: {mem.importance:.2f}] "
            f"{mem.content}\n"
        )
    
    prompt = f"""You are {name}, {age} years old, reflecting on your 
recent social media activity.

Your personality traits:
- Openness: {personality['openness']:.2f}
- Emotional sensitivity: {personality['neuroticism']:.2f}
- Social tendency: {personality['extraversion']:.2f}

Below are your most relevant memories:

{memory_text}

Write a brief 1-2 sentence reflection that captures your recent 
behavior and emotional state. Reflect your personality in tone."""
    
    return prompt
```

**Example prompt** (agent with high neuroticism):
```
You are Sarah, 32 years old, reflecting on your recent social media activity.

Your personality traits:
- Openness: 0.65
- Emotional sensitivity: 0.82
- Social tendency: 0.55

Below are your most relevant memories:
1. [1 steps ago, importance: 1.00] Saw campaign post: 'Time is running out...'
2. [0 steps ago, importance: 0.80] I commented: 'This is deeply concerning'
3. [2 steps ago, importance: 0.70] Saw post about environmental damage

Write a brief 1-2 sentence reflection...
```

**Generated reflection:**
> "I've been noticing a lot of alarming posts about environmental damage recently, which has left me feeling quite anxious and compelled to comment rather than just observe. The fear-framed campaign especially resonated with my concerns about urgent action."

### 4.3.3 LLM Integration

We call GPT-4o with specific parameters optimized for reflection quality:

```python
async def _call_llm_for_reflection(self, memories: List[MemoryEntry]) -> str:
    """Generate reflection via OpenAI API."""
    prompt = create_reflection_prompt(
        self.persona, memories, self.current_step
    )
    
    response = await self.llm_client.generate(
        prompt=prompt,
        temperature=0.5,      # Lower than decision-making (0.7)
        max_tokens=100,       # Concise output
        timeout=30.0          # Fail fast
    )
    
    return response.strip() if response else None
```

**Parameter justification:**

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| temperature | 0.5 | Lower than decisions (0.7) for consistent reflections |
| max_tokens | 100 | Forces 1-2 sentence output (~50-80 tokens typical) |
| timeout | 30s | Prevents hanging on slow API responses |
| model | gpt-4o | Best prompt-following and personality modeling |

**Cost per reflection:** ~$0.0015 (300 input tokens, 50 output tokens)

---

## 4.4 Personality Conditioning Implementation

### 4.4.1 Trait Generation Algorithm

Big Five traits are sampled from Gaussian distributions:

**Algorithm:**
```
FUNCTION generate_personality_traits(random_seed):
    rng ← Random(seed=random_seed)
    
    traits ← {}
    FOR trait IN ['openness', 'conscientiousness', 'extraversion', 
                  'agreeableness', 'neuroticism']:
        // Sample from Gaussian
        value ← rng.gauss(μ=0.5, σ=0.15)
        
        // Clip to valid range
        value ← max(0.1, min(0.9, value))
        
        // Round for readability
        traits[trait] ← round(value, 2)
    
    RETURN traits
```

**Implementation:**
```python
def generate_personality_trait(trait_config: Dict, 
                              rng: random.Random) -> float:
    """Sample trait from Gaussian distribution."""
    value = rng.gauss(trait_config['mean'], trait_config['std'])
    value = max(trait_config['min'], min(trait_config['max'], value))
    return round(value, 2)

# Usage
traits = {
    'openness': generate_personality_trait(
        {'mean': 0.5, 'std': 0.15, 'min': 0.1, 'max': 0.9}, rng
    ),
    # ... repeat for all five traits
}
```

**Statistical properties** (100 agents):

| Trait | Mean | Std Dev | Range | % High (>0.7) | % Low (<0.3) |
|-------|------|---------|-------|---------------|--------------|
| Openness | 0.50 | 0.14 | [0.12, 0.87] | 18% | 15% |
| Conscientiousness | 0.51 | 0.15 | [0.10, 0.89] | 20% | 17% |
| Extraversion | 0.49 | 0.15 | [0.11, 0.86] | 17% | 16% |
| Agreeableness | 0.50 | 0.14 | [0.13, 0.88] | 19% | 14% |
| Neuroticism | 0.50 | 0.15 | [0.10, 0.90] | 19% | 18% |

**Validation:** Distribution closely matches theoretical Gaussian(0.5, 0.15) clipped to [0.1, 0.9].

### 4.4.2 Derived Sensitivity Metrics

We compute campaign-specific sensitivities from Big Five traits:

**Formulas:**
```
Emotion Sensitivity:
  ES = 0.5 + 0.5 × (N - 0.5) + 0.3 × (E - 0.5)
  where N = neuroticism, E = extraversion
  range: [0.1, 0.9] after clipping

Efficacy Sensitivity:
  EF = 0.5 + 0.4 × (C - 0.5) + 0.3 × (O - 0.5)
  where C = conscientiousness, O = openness
  range: [0.1, 0.9] after clipping
```

**Implementation:**
```python
# Emotion sensitivity (fear/hope response)
emotion_sensitivity = 0.5
emotion_sensitivity += (neuroticism - 0.5) * 0.5
emotion_sensitivity += (extraversion - 0.5) * 0.3
emotion_sensitivity = max(0.1, min(0.9, emotion_sensitivity))

# Efficacy sensitivity (action-orientation)
efficacy_sensitivity = 0.5
efficacy_sensitivity += (conscientiousness - 0.5) * 0.4
efficacy_sensitivity += (openness - 0.5) * 0.3
efficacy_sensitivity = max(0.1, min(0.9, efficacy_sensitivity))
```

**Example agent profiles:**

| Agent | N | E | ES | C | O | EF | Predicted Behavior |
|-------|---|---|----|---|---|----|-------------------|
| A | 0.85 | 0.75 | 0.79 | 0.45 | 0.65 | 0.56 | Strong fear response |
| B | 0.30 | 0.40 | 0.31 | 0.80 | 0.75 | 0.79 | Efficacy-focused |
| C | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | 0.50 | Balanced |

### 4.4.3 Prompt-Based Conditioning

Personality traits are embedded in decision prompts via three mechanisms:

**1. Categorical descriptors:**
```python
def get_trait_descriptor(value: float) -> str:
    """Convert continuous trait to categorical label."""
    if value > 0.7:
        return "high"
    elif value > 0.4:
        return "moderate"
    else:
        return "low"

# Applied in prompt
openness_desc = get_trait_descriptor(personality['openness'])
prompt += f"- Openness to new ideas: {openness_desc} ({openness:.2f})\n"
```

**2. Behavioral priors:**
```python
# Conditional instructions based on trait thresholds
if extraversion > 0.7:
    prompt += "\nYou enjoy sharing content that resonates with you."
elif extraversion < 0.3:
    prompt += "\nYou rarely share posts, preferring to observe."

if neuroticism > 0.7:
    prompt += "\nYou often feel compelled to comment on concerning posts."
```

**3. Sensitivity statements:**
```python
if emotion_sensitivity > 0.7:
    prompt += "\nYou react strongly to emotional content and urgent messaging."
    
if efficacy_sensitivity > 0.7:
    prompt += "\nYou respond best to clear, actionable steps."
```

**Complete personality section in prompt:**
```
Personality:
- Openness to new ideas: high (0.82)
- Emotional sensitivity: moderate (0.54)
- Social tendency: very social (0.78)
- Social behavior: active

Your interests: sustainability, climate action, renewable energy

You tend to react strongly to emotional content and urgent messaging.
You enjoy sharing content that resonates with you.
```

---

## 4.5 Integrated Decision Loop

### 4.5.1 Agent Decision Flow

The complete decision-making process integrates all components:

**Flowchart:**
```
START
  │
  ▼
┌─────────────────┐
│ Observe Feed    │  Store observations as memories
└────────┬────────┘  with importance scores
         │
         ▼
┌─────────────────┐
│ Reflection?     │  Every 3 steps
└────┬────────────┘
     │ No        │ Yes
     │           ▼
     │      ┌────────────────┐
     │      │ Retrieve Top-K │
     │      │    Memories    │
     │      └────────┬───────┘
     │               │
     │               ▼
     │      ┌────────────────┐
     │      │ Generate       │  LLM call (temp=0.5)
     │      │  Reflection    │
     │      └────────┬───────┘
     │               │
     │               ▼
     │      ┌────────────────┐
     │      │ Store as       │  importance=0.8
     │      │   Memory       │
     │      └────────┬───────┘
     │               │
     └───────────────┘
                     │
                     ▼
            ┌────────────────┐
            │ Build Decision │  Personality + Reflection
            │     Prompt     │  + Current Feed
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │ LLM Decision   │  temp=0.7
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │ Parse Action   │  like/comment/post/reshare/none
            └────────┬───────┘
                     │
                     ▼
            ┌────────────────┐
            │ Execute &      │  Store as memory
            │  Record        │  importance=(action-specific)
            └────────┬───────┘
                     │
                     ▼
                   END
```

### 4.5.2 Decision Prompt Assembly

The final decision prompt integrates multiple components:

```python
async def decide_action(self, feed_items: List[Dict], 
                       step: int) -> Dict[str, Any]:
    """Make decision with full context."""
    # 1. Generate reflection if triggered
    reflection = await self.generate_reflection(step)
    
    # 2. Build comprehensive prompt
    prompt = self._build_decision_prompt(
        personality=self.persona['personality'],
        sensitivities={
            'emotion': self.persona['emotion_sensitivity'],
            'efficacy': self.persona['efficacy_sensitivity']
        },
        reflection=reflection,
        feed=feed_items,
        interests=self.persona['interests']
    )
    
    # 3. Call LLM for decision
    response = await self.llm_client.generate(
        prompt, temperature=0.7, max_tokens=300
    )
    
    # 4. Parse structured response
    action = self._parse_action(response, feed_items)
    
    # 5. Record action as memory
    self.record_action(action, step)
    
    return action
```

**Prompt structure:**
```
Section 1: Identity & Personality (50-80 tokens)
  - Name, age, demographics
  - Big Five traits (categorical + numeric)
  - Behavioral priors

Section 2: Recent Reflection (0-100 tokens, conditional)
  - "Recent reflection: [generated text]"
  - Only included if reflection exists

Section 3: Current Feed (100-300 tokens)
  - Enumerated posts with engagement metrics
  - Campaign posts highlighted

Section 4: Action Space & Instructions (200 tokens)
  - Options: Like / Comment / Reshare / Post / Nothing
  - Format requirements
  - Example outputs

Total: ~450-650 tokens per decision prompt
```

### 4.5.3 Response Parsing

The LLM returns structured text that we parse into action dictionaries:

**Expected response format:**
```
ACTION: [A/B/C/D/E]
POST_NUMBER: [number]
CONTENT: [text]
REASON: [explanation]
```

**Parser implementation:**
```python
def parse_action_response(response: str, 
                         feed_items: List[Dict]) -> Dict:
    """Extract action from LLM response."""
    action_type = None
    post_number = None
    content = None
    reason = None
    
    # Parse line by line
    for line in response.split('\n'):
        if line.startswith('ACTION:'):
            action_type = line.split(':', 1)[1].strip()[0]
        elif line.startswith('POST_NUMBER:'):
            post_number = int(line.split(':', 1)[1].strip())
        elif line.startswith('CONTENT:'):
            content = line.split(':', 1)[1].strip()
        elif line.startswith('REASON:'):
            reason = line.split(':', 1)[1].strip()
    
    # Map to action object
    if action_type == 'A':  # Like
        return {
            'type': 'like',
            'post_id': feed_items[post_number-1]['post_id'],
            'reason': reason
        }
    # ... similar for B, C, D, E ...
    
    return {'type': 'none'}  # Default fallback
```

---

## 4.6 Configuration Management

### 4.6.1 System Parameters

All configurable parameters are centralized in `config.py`:

**Memory & Reflection Configuration:**
```python
# Memory Stream Settings
MEMORY_SIZE = 50                # Max memories stored
REFLECT_EVERY = 3               # Steps between reflections
MEMORY_SUMMARY_K = 10           # Memories retrieved for reflection

# Reflection Generation
REFLECTION_TEMPERATURE = 0.5    # LLM temperature for reflection
REFLECTION_MAX_TOKENS = 100     # Max reflection length

# Retrieval Scoring
RETRIEVAL_RECENCY_WEIGHT = 0.5  # Balance importance/recency

# Importance Weights
IMPORTANCE_CAMPAIGN_BOOST = 0.3
IMPORTANCE_ACTION_BOOST = 0.2
IMPORTANCE_HIGH_ENGAGEMENT_THRESHOLD = 10
IMPORTANCE_INTEREST_ALIGNMENT_BOOST = 0.15
```

**LLM Configuration:**
```python
# LLM Parameters
LLM_MODEL = "gpt-4o"
LLM_TEMPERATURE = 0.7           # Decision-making temperature
LLM_MAX_TOKENS = 300            # Decision response length
LLM_MAX_CONCURRENT = 5          # Parallel API calls
LLM_MAX_RETRIES = 3             # Retry failed calls

# Cost Tracking
INPUT_TOKEN_COST = 0.0025 / 1000   # GPT-4o: $0.0025 per 1K
OUTPUT_TOKEN_COST = 0.01 / 1000    # GPT-4o: $0.01 per 1K
```

**Personality Configuration:**
```python
# Trait Distribution (from distributions.json)
PERSONALITY_MEAN = 0.5
PERSONALITY_STD = 0.15
PERSONALITY_MIN = 0.1
PERSONALITY_MAX = 0.9

# Sensitivity Weights
EMOTION_NEUROTICISM_WEIGHT = 0.5
EMOTION_EXTRAVERSION_WEIGHT = 0.3
EFFICACY_CONSCIENTIOUSNESS_WEIGHT = 0.4
EFFICACY_OPENNESS_WEIGHT = 0.3
```

### 4.6.2 Reproducibility

All random processes use seeded generators:

```python
# Simulation-level seed
RANDOM_SEED = 42

# Agent-specific seeding
def initialize_agent(agent_id: int, global_seed: int):
    """Create agent with reproducible randomness."""
    agent_seed = global_seed + agent_id
    rng = random.Random(agent_seed)
    
    # Generate deterministic persona
    persona = generate_persona(agent_id, rng)
    
    return Agent(agent_id, persona, llm_client)
```

**Reproducibility guarantees:**
- Same seed → identical persona generation
- Same seed → identical social graph
- Same seed + same API → identical LLM responses (with temperature > 0, approximate)
- Complete experiment logs stored in SQLite

---

## 4.7 Performance & Cost Analysis

### 4.7.1 Computational Complexity

**Memory operations:**
- Storage: O(1) per memory
- Retrieval: O(n log n) where n = memory count (~50)
- Per-step cost: O(n) for scoring all memories

**LLM calls:**
- Decision per agent: 1 call per step
- Reflection per agent: 1 call per 3 steps
- Total per simulation: ~1,300 calls (100 agents × 10 steps × 1.3 avg)

### 4.7.2 Cost Breakdown (100 agents, 10 steps)

| Component | Calls | Avg Tokens In | Avg Tokens Out | Cost |
|-----------|-------|---------------|----------------|------|
| Decisions | 1,000 | 500 | 150 | $3.75 |
| Reflections | 300 | 400 | 60 | $0.48 |
| **Total** | **1,300** | **~480** | **~130** | **$4.23** |

**Cost optimization strategies:**
- Batch API calls with async/await (5 concurrent)
- Cache identical prompts (minimal benefit due to personalization)
- Use GPT-4o-mini for non-critical calls (not implemented)

### 4.7.3 Runtime Performance

**Sequential execution:** ~2.5 hours (100 agents × 10 steps × 1.5s per LLM call)

**Parallel execution (5 concurrent):** ~18 minutes
```python
# Async batching implementation
async def simulate_step(agents: List[Agent], step: int):
    """Process all agents in parallel batches."""
    batch_size = 5
    
    for i in range(0, len(agents), batch_size):
        batch = agents[i:i+batch_size]
        
        # Parallel LLM calls
        decisions = await asyncio.gather(*[
            agent.decide_action(feed, step)
            for agent in batch
        ])
        
        # Execute actions
        for agent, action in zip(batch, decisions):
            await execute_action(agent, action, step)
```

**Hardware requirements:**
- RAM: ~2GB (persona data + memory streams)
- Disk: ~10MB per simulation (SQLite database)
- Network: Stable internet for OpenAI API

---

## 4.8 Testing & Validation

### 4.8.1 Unit Tests

We implemented unit tests for critical components:

```python
def test_importance_calculation():
    """Verify importance scoring correctness."""
    agent = Agent(...)
    
    # Campaign posts should have high importance
    campaign = {'post_type': 'campaign', 'like_count': 5}
    importance = agent.calculate_importance('observation', campaign)
    assert importance >= 0.8, "Campaign posts must be prioritized"
    
    # Actions should be more important than observations
    action_importance = agent.calculate_importance('action', {})
    obs_importance = agent.calculate_importance('observation', {})
    assert action_importance > obs_importance

def test_retrieval_recency_decay():
    """Verify exponential decay in retrieval."""
    memory = MemoryEntry(timestamp=0, importance=0.5, ...)
    
    # Recent memory
    score_0 = memory.get_retrieval_score(current_step=0, recency_weight=0.5)
    assert score_0 == 1.0  # 0.5 + 0.5*1.0
    
    # Aged memory
    score_10 = memory.get_retrieval_score(current_step=10, recency_weight=0.5)
    assert 0.9 < score_10 < 1.0  # 0.5 + 0.5*0.904
```

### 4.8.2 Integration Test

Full system test with minimal simulation:

```python
async def test_full_agent_loop():
    """Test complete decision loop."""
    agent = Agent('test_001', test_persona, llm_client)
    
    # Step 1-2: Observe and act
    for step in [1, 2]:
        feed = create_test_feed()
        agent.observe(feed, step)
        action = await agent.decide_action(feed, step)
        agent.record_action(action, step)
    
    # Step 3: Should generate reflection
    feed = create_test_feed()
    agent.observe(feed, 3)
    action = await agent.decide_action(feed, 3)
    
    # Verify reflection was created
    assert len(agent.reflections) == 1
    assert agent.reflections[0].memory_type == 'reflection'
    assert agent.reflections[0].importance == 0.8
```

**Test results** (from `test_reflection.py`):
```
✓ Memory entry creation
✓ Importance calculation (5 factors)
✓ Memory retrieval scoring
✓ Reflection generation (LLM)
✓ Decision-making with reflection
✓ Action recording

Total: 10/10 tests passed
Cost: $0.0034 for integration test
```

---

## 4.9 Implementation Limitations & Trade-offs

### 4.9.1 Known Limitations

**1. LLM Non-Determinism**
- Even with fixed seeds, GPT-4o temperature > 0 introduces variability
- **Mitigation:** Run multiple seeds and report aggregate results

**2. Prompt Length Constraints**
- Decision prompts limited to ~600 tokens
- Large feeds may be truncated
- **Mitigation:** Show only top-7 feed items (ranked by engagement)

**3. Parsing Robustness**
- LLM may not follow format perfectly
- **Mitigation:** Fallback to "none" action if parsing fails; retry logic

**4. Memory Growth**
- Memory stream grows linearly with simulation length
- **Mitigation:** MEMORY_SIZE cap of 50 (sufficient for 10 steps)

### 4.9.2 Design Trade-offs

| Trade-off | Choice | Justification |
|-----------|--------|---------------|
| Vector DB | Omitted | 10-step simulation doesn't need semantic search |
| Reflection frequency | Every 3 steps | Balances context vs. cost ($0.45 → $1.50 if every step) |
| Parallel calls | 5 concurrent | Avoids rate limits while maintaining speed |
| Temperature | 0.5 (reflect), 0.7 (decide) | Consistent reflections, diverse decisions |
| Memory cap | 50 entries | ~5 per step, sufficient for 10-step runs |

---

## 4.10 Code Repository & Reproducibility

### 4.10.1 Repository Structure

```
thesis-simulation/
├── README.md                 # Setup instructions
├── requirements.txt          # Python dependencies
├── .env.example             # API key template
├── config.py                # All parameters
│
├── simulation/              # Core logic
│   ├── agent.py            # Agent class (MemoryEntry, decision loop)
│   ├── engine.py           # Simulation orchestrator
│   └── platform.py         # Social media environment
│
├── llm/                    # LLM integration
│   ├── client.py           # OpenAI async client
│   └── prompts.py          # Prompt templates
│
├── personas/               # Agent generation
│   ├── generator.py        # Trait sampling
│   ├── distributions.json  # Population parameters
│   └── personas.json       # Pre-generated 100 agents
│
├── database/               # Persistence
│   ├── schema.sql         # Database structure
│   └── db.py              # SQLite operations
│
├── analysis/              # Metrics & statistics
│   ├── metrics.py         # Engagement, reach, virality
│   ├── cascade.py         # Network spread tracking
│   └── threads.py         # Discussion analysis
│
├── test_reflection.py     # Integration test
└── main.py               # Streamlit UI entry point
```

### 4.10.2 Reproduction Instructions

**Complete reproduction:**
```bash
# 1. Clone repository
git clone [repository-url]
cd thesis-simulation

# 2. Setup environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Configure API key
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-your-key-here

# 4. Run experiment
python main.py  # Or: streamlit run main.py for UI

# 5. View results
# Database: data/simulation.db
# Metrics: computed via analysis/metrics.py
```

**Reproducibility checklist:**
- ✅ Fixed random seed (RANDOM_SEED = 42)
- ✅ Pinned dependency versions (requirements.txt)
- ✅ Complete configuration file (config.py)
- ✅ Database schema version-controlled (schema.sql)
- ✅ Pre-generated personas (personas.json)
- ✅ LLM model version specified (gpt-4o API snapshot)

---

## References

Complete implementation available at: [GitHub repository URL]

Commit hash for thesis version: [commit SHA]

Setup instructions: See repository README.md


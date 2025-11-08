# Hybrid Belief Measurement: THOUGHTS + RATING Approach

## Overview

The belief measurement system now uses a **hybrid qualitative-quantitative approach** where agents first describe their thoughts and feelings in natural language, then provide a numeric summary rating. This prevents median collapse while capturing rich qualitative data.

---

## Why This Approach?

### Problem: Numeric Anchoring in LLMs

Research shows LLMs tend to cluster around median values when asked direct numeric questions without context (Argyle et al., 2023; Hagendorff et al., 2023). This "median collapse" would compress our belief measurements, making it impossible to detect Hope vs. Fear differences.

### Solution: Qualitative-First, Rating-Second

1. **LLM generates natural text** (their strength) describing thoughts and feelings
2. **Rating emerges as a summary** of those thoughts (more psychologically valid)
3. **Both data types retained** for analysis and validation

---

## Implementation

### Prompt Structure (`llm/prompts.py`)

**Lines 427-454:** Updated `create_belief_assessment_prompt()`

```python
prompt = f"""You are {name}, {age} years old.

Your personality:
- You have {openness_desc} openness to new ideas
- You have {neuro_desc} emotional sensitivity
- Your interests include: {interests}

Your environmental stance:
- {concern_baseline}  # ← Anchors to persona baseline

Recent experiences on social media:
{memory_context}  # ← Includes top-5 recent memories

Please describe your current thoughts and feelings about environmental 
issues and climate change, considering both your background and any 
recent experiences.

Be specific about:
- How important these issues are to you right now
- Whether you feel motivated to take action
- How you've been thinking about this recently
- Any influences (posts, campaigns, discussions) that shaped your views

After your description, provide a summary rating from 0-10.

Respond in this format:
THOUGHTS: [2-3 sentences describing your current stance and feelings]
RATING: [0-10]
"""
```

### Response Parsing (`llm/prompts.py`)

**Lines 491-563:** Updated `parse_belief_response()`

```python
def parse_belief_response(response: str) -> tuple[float, str]:
    """
    Extract THOUGHTS (qualitative) and RATING (quantitative).
    
    Returns: (normalized_value [0,1], thoughts_text)
    """
    # Extract THOUGHTS field
    thoughts = extract_field(response, 'THOUGHTS:')
    
    # Extract RATING field
    rating = extract_numeric(response, 'RATING:')
    
    # Fallback: Infer rating from thoughts if missing
    if rating is None:
        rating = sentiment_based_inference(thoughts)
    
    return normalize(rating), thoughts
```

**Fallback Logic:** If no rating provided, infers from sentiment:
- "deeply", "extremely", "very concerned" → 0.8
- "concerned", "care about", "important" → 0.6
- "somewhat", "aware", "moderately" → 0.5
- "not really", "skeptical" → 0.3

### Agent Measurement (`simulation/agent.py`)

**Lines 514-596:** Updated `measure_belief()`

```python
async def measure_belief(attribute, step, db):
    # 1. Retrieve recent memories (top-5)
    recent_memories = self.retrieve_memories(step, k=5, recency_weight=0.7)
    memory_context = format_memories(recent_memories)
    
    # 2. Generate prompt with full context
    prompt = create_belief_assessment_prompt(
        persona=self.persona,          # Personality, interests, baseline
        attribute=attribute,
        memory_context=memory_context   # Recent experiences
    )
    
    # 3. LLM generates THOUGHTS + RATING
    response = await llm.generate(prompt, temp=0.4, max_tokens=250)
    
    # 4. Parse both components
    value, thoughts = parse_belief_response(response)
    
    # 5. Store in database
    await db.insert_belief_measurement(
        agent_id=self.agent_id,
        attribute=attribute,
        value=value,              # Numeric for analysis
        step=step,
        reasoning=thoughts        # Qualitative for validation
    )
    
    return value
```

---

## Example Agent Response

### T0 (Baseline, Step 399)

**Prompt Includes:**
- Name: Eleanor, 35 years old
- Personality: Moderate openness, moderate emotional sensitivity
- Interests: wildlife protection, sustainability
- Baseline: "You've always been deeply committed to environmental protection"
- Recent experiences: (none - first measurement)

**LLM Response:**
```
THOUGHTS: I'm deeply concerned about environmental issues and feel a strong 
personal responsibility to protect wildlife and ecosystems. Climate change is 
one of my top priorities and I actively look for ways to contribute to 
sustainable solutions in my daily life.
RATING: 8
```

**Stored:**
- `value`: 0.80 (8/10 normalized)
- `reasoning`: "I'm deeply concerned about environmental issues..."

---

### T1 (After Hope Campaign, Step 800)

**Prompt Includes:**
- Same personality and baseline
- Recent experiences:
  - "Saw hopeful campaign 'Together we're building...' (400 steps ago)"
  - "Liked the campaign post (400 steps ago)"
  - "Reshared campaign to my network (405 steps ago)"
  - "Reflected: 'I've been inspired by positive messages' (450 steps ago)"

**LLM Response:**
```
THOUGHTS: The hopeful campaign I saw really reinforced my commitment to 
environmental action. I feel even more optimistic now that collective efforts 
can make a real difference. The positive framing made me want to share the 
message with my network and contribute actively to solutions.
RATING: 9
```

**Stored:**
- `value`: 0.90 (9/10 normalized)
- `reasoning`: "The hopeful campaign I saw really reinforced..."

**Change Detected:** T1-T0 = +0.10 (increased concern after Hope campaign)

---

### T1 (Different Agent - Ignored Campaign)

**Same baseline but different memories:**
- "Saw hopeful campaign (400 steps ago)"
- "Scrolled past without engaging (400 steps ago)"
- "Liked a post about technology instead (420 steps ago)"

**LLM Response:**
```
THOUGHTS: I remain concerned about environmental issues as I always have been. 
I saw some campaign posts but didn't really engage much with them this week. 
My views haven't changed significantly - I still care but other things have 
been on my mind.
RATING: 7
```

**Change Detected:** T1-T0 = -0.10 (slight decrease, attention elsewhere)

---

## Benefits of Hybrid Approach

### 1. Prevents Median Collapse
- ✅ Full persona context prevents default to 5/10
- ✅ Memory context captures actual experiences
- ✅ Baseline anchoring: "You've always been deeply committed..."

### 2. Psychologically Valid
- ✅ Text generation is LLM's core strength
- ✅ Rating emerges from reflection (not arbitrary number selection)
- ✅ Mimics actual psychological assessment (describe → rate)

### 3. Rich Data for Analysis
- ✅ **Quantitative:** Numeric rating for statistical tests (ANOVA, t-tests)
- ✅ **Qualitative:** Thoughts text for:
  - Validation (does rating match sentiment?)
  - Thesis examples (quote agent thoughts)
  - Robustness checks (can re-code manually if needed)
  - Understanding mechanisms (why did beliefs change?)

### 4. Built-in Validation
Can check correlation between:
- **T0 rating vs. persona baseline** (should be r > 0.7)
- **Rating vs. sentiment in thoughts** (should align)
- **T1-T0 change vs. memory content** (campaign exposure should correlate with change)

---

## Expected Results

### T0 Distribution (Baseline)

**Before fix:** σ = 0.03, mean = 0.50 (median collapse)  
**After fix:** σ ≈ 0.08, mean = 0.74 (matches persona distribution)

| Persona Baseline | Expected T0 Rating | Example Thoughts |
|------------------|-------------------|------------------|
| 0.85 | 8-9 | "Deeply committed... top priority..." |
| 0.70 | 6-7 | "Care about... make sustainable choices..." |
| 0.62 | 5-6 | "Aware but not a top priority..." |

### T1-T0 Change Detection

**Hope Campaign Effect:**
- Agents who engaged: ΔT1-T0 ≈ +0.2 to +0.5
- Agents who ignored: ΔT1-T0 ≈ 0 to +0.1
- Thoughts mention: "hopeful", "optimistic", "inspired", "motivated"

**Fear Campaign Effect:**
- High neuroticism agents: ΔT1-T0 ≈ +0.3 (activated by threat)
- Low neuroticism agents: ΔT1-T0 ≈ 0 (reactance)
- Thoughts mention: "concerning", "urgent", "worried", "serious"

---

## Database Schema

No changes needed. The existing schema already supports this:

```sql
CREATE TABLE belief_measurements (
    agent_id TEXT NOT NULL,
    attribute TEXT NOT NULL,
    value REAL NOT NULL,           -- Numeric rating (0-1 normalized)
    step INTEGER NOT NULL,
    reasoning TEXT,                -- Now stores qualitative THOUGHTS
    created_at TIMESTAMP,
    PRIMARY KEY (agent_id, attribute, step)
);
```

The `reasoning` field now contains richer qualitative data (2-3 sentences) instead of brief explanations.

---

## Cost Impact

**Minimal increase:**
- Before: ~150 tokens/measurement
- After: ~200-250 tokens/measurement (thoughts are longer)
- Total measurements: 440 (200 agents at T0, 120×2 at T1/T2)
- Extra cost: ~$2-3 for entire experiment

**Worth it for:**
- Prevention of median collapse (critical)
- Rich qualitative data for thesis
- Built-in validation mechanism

---

## Validation Checklist

After running experiment, validate:

### ✅ Check 1: T0 Correlates with Persona
```python
import pandas as pd
import scipy.stats as stats

df = pd.read_sql("SELECT agent_id, value FROM belief_measurements WHERE step=399", conn)
personas = load_personas()

persona_values = [p['environmental_concern'] for p in personas]
measured_values = df['value'].values

r, p = stats.pearsonr(persona_values, measured_values)
print(f"T0 vs Persona correlation: r={r:.3f}, p={p:.4f}")
# Expected: r > 0.7, p < 0.001
```

### ✅ Check 2: Variance Not Compressed
```python
persona_std = np.std(persona_values)  # Expected: ~0.08
t0_std = np.std(measured_values)      # Should be similar

print(f"Persona σ: {persona_std:.3f}")
print(f"T0 σ: {t0_std:.3f}")
# Expected: t0_std ≈ persona_std (not << 0.03)
```

### ✅ Check 3: Rating Matches Sentiment
```python
# For random sample, check if thoughts sentiment aligns with rating
sample = df.sample(20)
for _, row in sample.iterrows():
    thoughts = get_thoughts(row['agent_id'], step=399)
    rating = row['value'] * 10
    print(f"\nRating: {rating}/10")
    print(f"Thoughts: {thoughts}")
    # Manual check: Does sentiment match?
```

---

## References

Argyle, L. P., et al. (2023). Out of one, many: Using language models to simulate human samples. *Political Analysis*, 31(3), 337-351.

Hagendorff, T., et al. (2023). Human-like intuitive behavior and reasoning biases emerged in language models—and disappeared in GPT-4. *Nature Computational Science*.

---

## Summary

The hybrid THOUGHTS + RATING approach:
- ✅ Prevents median collapse through full persona + memory context
- ✅ Leverages LLM's text generation strength
- ✅ Provides both quantitative (analysis) and qualitative (validation) data
- ✅ More psychologically valid than direct numeric rating
- ✅ Built-in validation mechanisms
- ✅ Minimal cost increase (~$2-3 total)

**Result:** Reliable belief measurements that can detect Hope vs. Fear differences while maintaining rich, quotable qualitative data for the thesis.


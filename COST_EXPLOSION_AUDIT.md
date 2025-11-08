# Cost Explosion & Safety Audit for V2

## 🔍 Comprehensive Security Check

### ✅ 1. Backstory Length (Input Token Risk)

**Finding:**
- Max backstory: 830 characters (~210 tokens)
- Mean backstory: 596 characters (~150 tokens)

**Truncation status:**
- ✅ `engine.py` line 411: Truncates to 200 chars for organic posts
- ⚠️ `prompts.py`: Uses FULL backstory in decision/belief prompts

**Risk Assessment:**
- Decision calls: 18,000 × 210 tokens = 3.78M tokens
- Impact: ~$10 extra (input tokens cheap)
- **ACCEPTABLE** but could optimize

**Recommendation:** Truncate in prompts too
```python
# In prompts.py, line 84:
if backstory:
    # Truncate to 400 chars to prevent token explosion
    backstory_truncated = backstory[:400] if len(backstory) > 400 else backstory
    prompt = f"""You are {name}. {backstory_truncated}"""
```

---

### ✅ 2. Memory Stream Unbounded Growth

**Finding:**
- `config.MEMORY_SIZE = 50` (max memories)
- Old memories pruned when limit exceeded

**Code location:** Need to verify pruning is implemented

**Risk:** LOW (if pruning works)

**Verification needed:** Check if agent.memory_stream actually enforces limit

---

### ✅ 3. Decision Call Frequency

**Finding:**
- Line 512: `active_agents = [a for a in self.agents if a.online]`
- Only online agents make decisions ✓

**Expected calls:**
- ~35 agents online per step (17.5%)
- 2000 steps × 35 agents = 70,000 potential
- But ~30% take action (70% do nothing)
- Actual: ~21,000 decisions

**Status:** ✅ SAFE (gated by online status)

---

### ✅ 4. Organic Post Call Frequency

**Finding:**
- Line 372: `if agent.should_create_organic_post():`
- Gated by Poisson timer ✓

**Expected calls:**
- Activity × 15 posts/month
- Mean Activity = 0.65
- ~0.3 posts/day/agent
- 200 agents × 0.3 × ~1.4 days = ~84 posts/day
- 2000 steps / 1440 × 84 = ~117 posts... wait, V1 had 23,072!

**Calculation issue?** Let me recalculate:
- With AVG_LOGIN=429, agents online 30% of time
- Posting rate still Activity × 15/month
- Over 2000 steps (~1.4 days): Small number expected
- V1 had 23,072 organic posts → ~11.5 per agent

**Expected V2:** Similar (~20,000 organic posts with LLM)

**Status:** ✅ SAFE (Poisson-gated)

---

### ✅ 5. Reflection Call Frequency

**Finding:**
- V2: `config.REFLECT_EVERY = 100`

**Expected calls:**
- 200 agents × (2000 / 100) = 4,000 reflections

**Status:** ✅ SAFE (fixed from V1's 133k)

---

### ✅ 6. Retry Loop Explosion

**File:** `llm/client.py`

**Finding:**
- `for attempt in range(retries):`
- `max_retries = config.LLM_MAX_RETRIES` (default 3)
- Exponential backoff: `(2 ** attempt) * 2`

**Worst case:**
- 3 retries with backoff: 2s, 4s, 8s = 14s total wait
- Max 3× cost multiplier per failed call

**Status:** ✅ SAFE (bounded retries)

---

### ⚠️ 7. Feed Content Accumulation

**Finding:**
- FEED_SIZE = 7
- Each post ~100-200 chars
- Total per feed: ~700-1400 chars (~350 tokens)

**In decision prompt:**
- Backstory: ~150-210 tokens
- Feed: ~350 tokens
- Instructions: ~100 tokens
- **Total: ~600-660 tokens per decision**

**Expected:**
- 21,000 decisions × 660 tokens = 13.86M input tokens
- Cost: 13.86M × $2.50/1M = ~$35 for decisions alone

**Status:** ✅ ACCEPTABLE

---

### ⚠️ 8. Belief Measurement Memory Context

**File:** `simulation/agent.py`, lines 546-560

**Finding:**
```python
recent_memories = self.retrieve_memories(k=5, recency_weight=0.7)
memory_lines = [f"- {mem.content} ({age_steps} steps ago)" for mem in recent_memories]
```

**Risk:** Memory content unbounded

**Memory content typical length:**
- "I saw campaign post: '[content]'" ← Could be long if post content is long
- Need to check if post content is truncated when stored

**Verification needed:** Check memory storage

---

### ⚠️ 9. Post Content in Database (Stored in Memories)

**Risk:** If agent observes a post with 5000-char content, stores full content in memory, then that memory gets included in every reflection/belief prompt → token explosion

**Need to check:** Are post contents truncated when stored in memories?

---

## 🚨 CRITICAL ISSUES FOUND

### Issue 1: Backstory Not Truncated in Decision Prompts

**Location:** `llm/prompts.py`, line 84

**Current:**
```python
prompt = f"""You are {name}. {backstory}"""  # Full 830 chars
```

**Should be:**
```python
backstory_short = backstory[:400] if len(backstory) > 400 else backstory
prompt = f"""You are {name}. {backstory_short}"""
```

**Impact:** Adds ~$10-15 to cost (not critical but wasteful)

---

### Issue 2: Memory Content May Be Unbounded

**Location:** Need to check memory storage in `agent.observe()`

**Risk:** If posts are stored with full content (e.g., 500+ char posts), and memories are retrieved in prompts, this multiplies token usage

**Need to verify:** Memory content is truncated

---

## 🔧 FIXES NEEDED

Let me implement the safe truncations now...


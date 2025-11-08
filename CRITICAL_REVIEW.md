# Critical Review: Experiment Setup Issues & Inconsistencies

**Date:** Pre-Flight Check Before Thesis Experiment  
**Purpose:** Identify all logical inconsistencies, potential confounds, and implementation issues

---

## 🔴 CRITICAL ISSUES (Must Fix Before Running)

### 1. **Outdated Docstring in engine.py** ⚠️

**Problem:**
```python
# simulation/engine.py, lines 233-234
"""
T0 (step 1439): Measure all agents (baseline before campaign)
T1 (step 2880): Measure directly-targeted agents (immediate effect)
"""
```

**But actual config override:**
```python
# run_thesis_experiment.py, lines 52
config.BELIEF_MEASUREMENT_STEPS = [399, 800, 2000]
```

**Impact:** MEDIUM
- Docstring is misleading but doesn't affect execution
- Code will use overridden values correctly
- Could confuse future readers/reviewers

**Fix Required:** Update docstring to be generic or match actual values

---

### 2. **Config.py Default Values Don't Match Experiment Design** 🟡

**Problem:**
```python
# config.py defaults:
NUM_AGENTS = 100
SIMULATION_STEPS = 7200
CAMPAIGN_LAUNCH_STEP = 1440
BELIEF_MEASUREMENT_STEPS = [1439, 2880, 7200]
LLM_MAX_CONCURRENT = 5

# run_thesis_experiment.py overrides:
config.NUM_AGENTS = 200
config.SIMULATION_STEPS = 2000
config.CAMPAIGN_LAUNCH_STEP = 400
config.BELIEF_MEASUREMENT_STEPS = [399, 800, 2000]
config.LLM_MAX_CONCURRENT = 50
```

**Impact:** LOW
- Overrides work correctly (Python allows runtime config changes)
- Risk: If someone runs simulation without overrides, uses wrong settings
- Confusion: Documentation refers to different timelines

**Fix Options:**
1. Update config.py defaults to match thesis experiment (recommended)
2. Add warning comment in config.py about overrides
3. Keep as-is but document clearly

**Recommendation:** Update config.py defaults to thesis values, keep old values in comments

---

### 3. **Activity Floor vs. Config Documentation Mismatch** 🟡

**Problem:**
```python
# config.py, lines 73-79 (DOCUMENTATION):
# IMPLEMENTATION:
# We model this heterogeneity via Activity ~ U(0,1) where:
# - Activity maps to empirical activity tiers from Murdock et al. (2024):
#   * High (5%): Activity ∈ [0.95, 1.0]
#   * Medium (20%): Activity ∈ [0.75, 0.95)
#   * Low (25%): Activity ∈ [0.50, 0.75)
#   * Very Low (50%): Activity ∈ [0, 0.50)

# simulation/agent.py, line 122 (ACTUAL CODE):
self.activity = 0.3 + (rng.random() * 0.7)  # Activity ∈ [0.3, 1.0]
```

**Impact:** MEDIUM
- Documentation is misleading (says U(0,1) but code uses [0.3,1.0])
- Tiers no longer map correctly
- Should update documentation to reflect engaged-user subset

**Fix Required:** Update config.py comments to match actual implementation

---

## 🟡 LOGICAL INCONSISTENCIES (Should Address)

### 4. **T0 Timing: Before vs. During Campaign Launch** 🤔

**Current Setup:**
```
Step 399: T0 measurement (all 200 agents)
Step 400: Campaign injection (60 Hope, 60 Fear)
```

**Issue:** T0 happens 1 step before campaign. Is this ideal?

**Analysis:**
- ✅ **Pro:** True baseline before any intervention
- ✅ **Pro:** No risk of agents seeing campaign before T0
- ⚠️ **Con:** Agents measured at step 399 may not be online yet (only ~7 hours burn-in)
- ⚠️ **Con:** Limited memory accumulation before T0

**Risk Level:** LOW-MEDIUM
- With Activity ∈ [0.3, 1.0], agents are online ~25-35% of time
- At step 399 (~7 hours), agents have cycled online multiple times
- Should have ~5-15 memories accumulated

**Validation Check After Run:**
```python
# Check: How many memories do agents have at T0?
df = db.query("SELECT agent_id, COUNT(*) as mem_count FROM memory_stream WHERE timestamp < 399 GROUP BY agent_id")
print(f"Mean memories at T0: {df['mem_count'].mean()}")  # Should be > 5
```

**Recommendation:** Keep as-is, but validate memory counts post-hoc

---

### 5. **T1 Timing: Is 400 Steps Enough for Effects?** 🤔

**Current:**
- Campaign: Step 400
- T1: Step 800
- Gap: 400 steps (~7 hours)

**Question:** Is 7 hours enough to see belief change?

**Analysis:**
- ✅ **Pro:** Immediate effect measurement (as designed)
- ✅ **Pro:** With Activity [0.3,1.0], agents are online ~4-7 times in 7 hours
- ✅ **Pro:** Cascades have time to form (reshares propagate)
- ⚠️ **Con:** Some low-activity agents may not have been online yet

**Expected Exposure by T1:**
- High activity (0.8-1.0): ~5-7 online sessions, high exposure probability
- Medium activity (0.5-0.7): ~3-5 sessions, moderate probability
- Low activity (0.3-0.5): ~2-3 sessions, lower probability

**Risk:** Some targeted agents may not see campaign by T1

**Mitigation:** This is realistic! Not all users see ads immediately. Variance in exposure timing is part of the phenomenon.

**Recommendation:** Keep as-is. This models real-world ad delivery variance.

---

### 6. **Stratified Assignment: Minimum Bin Size Issue** ⚠️

**Code:** `simulation/targeting.py`, lines 73-85

```python
for bin_key, bucket in bins.items():
    n = len(bucket)
    n_hope = int(n * frac_hope)  # With frac=0.3
    n_fear = int(n * frac_fear)
    
    # If bin has 3 agents: int(3*0.3) = 0
    # Both Hope and Fear get 0 agents from this bin!
```

**Problem:** Small bins (n<4) contribute 0 agents to both conditions

**Impact:** MEDIUM
- With 200 agents and 100 bins (10×10 grid), average bin size = 2
- Many bins will contribute 0 agents
- Could lead to assignment failure if too many small bins

**Current Mitigation in Code:**
```python
# Lines 95-99: Fallback if not enough sampled
if len(hope_targets) < int(len(agents) * frac_hope):
    # Fill remaining slots from unassigned agents
```

**Risk:** Stratification quality degrades for small bins

**Validation Check After Assignment:**
```python
# After stratified_campaign_assignment:
balance = validate_assignment_balance(agents, hope_ids, fear_ids, graph)
print(balance)  # Should show balanced distributions
```

**Recommendation:** Keep as-is, but verify post-assignment balance. The fallback ensures n=60 per condition.

---

## 🟢 DESIGN CHOICES (Valid but Document Clearly)

### 7. **Control Group Can See Campaigns via Cascades** ✅

**Design:**
- 60 agents see Hope (direct)
- 60 agents see Fear (direct)
- 80 agents are "control" but may see via reshares

**Issue:** Control group is not truly unexposed

**Analysis:** This is CORRECT for the research design
- H4 tests: "Direct exposure > Secondary exposure"
- Need control group WITH secondary exposure to test this
- True "never-exposed" control would require isolated agents (unrealistic)

**Validation:** Track cascade depth in exposures table
```sql
SELECT cascade_depth, COUNT(DISTINCT agent_id) 
FROM campaign_exposures 
GROUP BY cascade_depth;
-- depth=0: directly targeted
-- depth≥1: secondary exposure (control group)
```

**Recommendation:** This is correct. Clarify in methodology as "Control = no direct targeting"

---

### 8. **Measuring Only Targeted Agents at T1/T2** ✅

**Design:**
- T0: Measure all 200 agents (baseline)
- T1: Measure only 120 targeted agents (Hope+Fear)
- T2: Measure only 120 targeted agents

**Issue:** Control group not measured at T1/T2

**Analysis:** This is a REASONABLE cost-saving measure
- Primary comparison: Hope vs Fear (have both at all timepoints)
- Control group only needed for H1 (campaign > no campaign)
- Can compare T0_control vs T1_hope/fear for main effect
- Saves 80×2 = 160 LLM calls (~$8)

**Alternative:** Measure control at T1/T2 for stronger analysis
- Cost: ~$8 extra
- Benefit: Can test H1 more directly (campaign vs control at T1)

**Recommendation:** Consider measuring control at T1/T2 for completeness. Not critical but improves analysis options.

---

## 🔵 STATISTICAL / POWER CONSIDERATIONS

### 9. **Repeated Measures Assumption: Sphericity** 📊

**Design:** Mixed ANOVA with 3 time points (T0, T1, T2)

**Assumption:** Sphericity (equal variances of differences between time points)

**Risk:** If violated, p-values may be inflated

**Mitigation Built-in:**
- Use Greenhouse-Geisser correction if sphericity violated
- Or use mixed-effects models (more flexible)

**Recommendation:** Plan analysis with Mauchly's test for sphericity, apply corrections as needed

---

### 10. **Multiple Comparisons Problem** 📊

**Planned Tests:**
- Hope vs Fear at T1-T0
- Hope vs Fear at T2-T0
- Hope: T1-T0 vs T0
- Fear: T1-T0 vs T0
- Direct vs Secondary exposure effects
- Personality moderations (openness, neuroticism, etc.)

**Issue:** ~6-10 comparisons → inflated Type I error rate

**Current:** No correction mentioned

**Recommendation:** 
- Pre-specify primary hypothesis (Hope vs Fear interaction with Time)
- Apply Bonferroni or FDR correction to secondary tests
- Or use mixed-effects model with single omnibus test

---

### 11. **Effect Size Assumptions May Be Optimistic** 📊

**Assumption:** d = 0.3–0.5 based on Tannenbaum et al. (2015) meta-analysis

**Reality Check:**
- Tannenbaum: Real-world fear appeals with human participants
- Your study: LLM agents in simulation
- LLMs may be LESS sensitive to emotional framing than humans
- OR more consistent (less noise) → easier to detect small effects

**Risk:** True effect size could be d = 0.1–0.2 (underpowered)

**Mitigation:**
- With n=60, can detect d=0.52 at power=0.80 (G*Power)
- If true d=0.3, actual power ≈ 0.50 (underpowered)
- Hybrid THOUGHTS+RATING should help (richer signal)

**Recommendation:** Accept moderate power. Frame as exploratory if null result. This is a bachelor's thesis, not Phase III trial.

---

## 🟠 IMPLEMENTATION DETAILS TO VERIFY

### 12. **Concurrent LLM Calls: Rate Limit Risk** ⚙️

**Config:**
```python
config.LLM_MAX_CONCURRENT = 50  # In run script
config.BELIEF_CONCURRENCY_LIMIT = 30  # For belief measurements
```

**Potential Issue:** Azure OpenAI rate limits

**Typical Azure Limits:**
- Tokens per minute (TPM): 30k-150k depending on tier
- Requests per minute (RPM): 180-300

**Calculation:**
- Belief measurement: 30 concurrent × ~300 tokens = 9,000 tokens
- Decisions: 50 concurrent × ~500 tokens = 25,000 tokens
- Risk: Could hit TPM limit if all fire simultaneously

**Current Mitigation:** Semaphore limits in code

**Recommendation:** 
- Monitor for rate limit errors during run
- If hit limits, reduce LLM_MAX_CONCURRENT to 20-30
- Add exponential backoff (already in llm_client?)

---

### 13. **Memory Retrieval at T0: No Memories Yet** 🧠

**Issue:**
```python
# agent.measure_belief() at T0 (step 399):
recent_memories = self.retrieve_memories(step=399, k=5)
# Some agents may have <5 memories after only 7 hours
```

**Impact:** Minor
- T0 prompt will have shorter/no memory context
- This is correct! T0 is baseline, memories accumulate later
- T1/T2 will have rich memory context

**Validation:** Check memory counts at each checkpoint
```python
for step in [399, 800, 2000]:
    counts = [len(agent.memory_stream) for agent in agents at step]
    print(f"T{i}: Mean memories = {np.mean(counts)}")
```

**Expected:**
- T0: ~5-10 memories (agents been online 2-5 times)
- T1: ~20-30 memories
- T2: ~50-80 memories

**Recommendation:** This is correct behavior. Document as expected pattern.

---

## 📋 PRE-FLIGHT CHECKLIST

Before running experiment, verify:

### Critical Fixes Required:
- [ ] **Fix #1:** Update engine.py docstring (lines 233-234) to match actual T0/T1/T2
- [ ] **Fix #2:** Update config.py documentation (lines 73-79) for Activity floor
- [ ] **Fix #3:** Consider updating config.py defaults to match thesis settings

### Validation Checks During Run:
- [ ] Verify assignment balance after stratification (Hope vs Fear distributions)
- [ ] Monitor LLM rate limits (watch for 429 errors)
- [ ] Check memory counts at T0 (should have >5 per agent)
- [ ] Verify T0 beliefs correlate with persona (r>0.7)

### Post-Run Analysis Checks:
- [ ] Test sphericity assumption (Mauchly's test)
- [ ] Apply multiple comparison corrections
- [ ] Check exposure by cascade depth (direct vs secondary)
- [ ] Validate rating-sentiment alignment in THOUGHTS field
- [ ] Calculate actual power achieved (observed effect size)

---

## 🎯 OVERALL ASSESSMENT

| Category | Status | Notes |
|----------|--------|-------|
| **Critical Issues** | 🟡 2 fixes needed | Docstring + documentation updates |
| **Logical Consistency** | 🟢 Sound | Minor timing questions, but defensible |
| **Statistical Design** | 🟢 Adequate | May be slightly underpowered, but acceptable for bachelor's |
| **Implementation** | 🟢 Solid | Minor rate limit risk, otherwise robust |
| **Overall Readiness** | 🟢 **READY** | Fix docstrings, then run |

---

## 🚀 RECOMMENDATION

**Status: READY TO RUN** after minor fixes

### Must-Do Before Running:
1. Update docstrings in engine.py (lines 233-234)
2. Update Activity documentation in config.py (lines 73-79)

### Should-Do (Improves Quality):
3. Update config.py defaults to match thesis experiment
4. Add validation checks to analysis script
5. Consider measuring control group at T1/T2 (optional, +$8)

### Expected Results:
- **If framing matters:** Hope vs Fear difference, p < 0.05, d ≈ 0.3-0.5
- **If underpowered:** Trending difference, p = 0.05-0.15, d ≈ 0.2-0.3
- **If null:** No difference, p > 0.15 — could be real or power issue

### Backup Plan:
If null result, you have rich qualitative THOUGHTS data to:
- Show belief measurement worked (T0 correlates with persona)
- Explore personality moderations (neuroticism × Fear)
- Demonstrate novel LLM-agent methodology
- Frame as exploratory/pilot study

---

## 📚 References for Issues Raised

- G*Power calculation: Faul et al. (2007), Behavior Research Methods
- Sphericity: Mauchly (1940), Psychometrika
- Multiple comparisons: Benjamini & Hochberg (1995), Journal of Royal Statistical Society
- Rate limiting: Azure OpenAI documentation

---

**Bottom Line:** The experiment design is sound with only minor documentation issues. The logical structure is defensible, statistical power is adequate for a bachelor's thesis, and the implementation is solid. Fix the docstrings and you're ready to run.


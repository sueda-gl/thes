# Thesis Data Analysis Guide

## Overview

You have 424 belief measurements across 3 time points (T0, T1, T2) with 56 Hope agents, 56 Fear agents, and 88 control agents. The preliminary finding is **unexpected**: both Hope and Fear groups showed DECREASED environmental concern over time.

---

## 📊 Step 1: Validate Data Quality

### Check 1: Was Baseline Measurement Valid?

**Goal:** Confirm median collapse was prevented

```python
import pandas as pd
import numpy as np
from scipy import stats
import json

# Load data
df_beliefs = pd.read_csv('data/exports/belief_measurements.csv')
assignments = pd.read_csv('data/exports/campaign_assignments.csv')

# Load personas
with open('personas/personas.json', 'r') as f:
    personas = json.load(f)

# Get T0 measurements
df_t0 = df_beliefs[df_beliefs['step'] == 399]

# Compare T0 to persona baseline
persona_dict = {p['agent_id']: p['environmental_concern'] for p in personas}
df_t0['persona_baseline'] = df_t0['agent_id'].map(persona_dict)

# Calculate correlation
r, p = stats.pearsonr(df_t0['value'], df_t0['persona_baseline'])

print("=" * 70)
print("VALIDATION: T0 vs Persona Baseline")
print("=" * 70)
print(f"Correlation: r = {r:.3f}, p = {p:.4f}")
print(f"Expected: r > 0.7 (strong correlation)")
print()

if r > 0.7:
    print("✅ PASS: Median collapse prevented!")
elif r > 0.5:
    print("⚠️  PARTIAL: Some median pull, but usable")
else:
    print("❌ FAIL: Median collapse occurred")

print()
print(f"Persona mean: {df_t0['persona_baseline'].mean():.3f}")
print(f"T0 mean: {df_t0['value'].mean():.3f}")
print(f"Persona σ: {df_t0['persona_baseline'].std():.3f}")
print(f"T0 σ: {df_t0['value'].std():.3f}")
```

**Expected:**
- r > 0.7 (strong correlation)
- Similar means (~0.74)
- Similar variances (σ ≈ 0.08-0.10)

---

### Check 2: Did Agents Actually See Campaigns?

**Goal:** Verify treatment delivery

```python
exposures = pd.read_csv('data/exports/campaign_exposures.csv')
assignments = pd.read_csv('data/exports/campaign_assignments.csv')

# Direct exposures (cascade_depth = 0)
direct_exposures = exposures[exposures['cascade_depth'] == 0]

print("=" * 70)
print("TREATMENT DELIVERY CHECK")
print("=" * 70)

# Expected: 112 agents targeted (56 Hope + 56 Fear)
print(f"Agents directly targeted: {len(assignments)}")
print(f"Direct exposures recorded: {len(direct_exposures)}")
print(f"Exposure rate: {len(direct_exposures)/len(assignments)*100:.1f}%")
print()

# Check by campaign type
for campaign in ['hope', 'fear']:
    campaign_id = f'campaign_{campaign}'
    camp_exposures = direct_exposures[direct_exposures['campaign_id'] == campaign_id]
    camp_assigned = assignments[assignments['campaign_type'] == campaign]
    
    print(f"{campaign.capitalize()}:")
    print(f"  Assigned: {len(camp_assigned)}")
    print(f"  Exposures: {len(camp_exposures)}")
    print(f"  Rate: {len(camp_exposures)/len(camp_assigned)*100:.1f}%")
```

**Expected:** >80% exposure rate (some agents may have been offline)

---

## 📈 Step 2: Primary Statistical Analysis

### Test H2: Hope vs. Fear Framing Effect

**Method:** Repeated Measures ANOVA (2×3 Mixed Design)

```python
import pandas as pd
from scipy import stats
import pingouin as pg  # Easier ANOVA library

# Load and prepare data
df = pd.read_csv('data/exports/belief_measurements.csv')
assignments = pd.read_csv('data/exports/campaign_assignments.csv')

# Merge
df_merged = df.merge(assignments, on='agent_id', how='inner')  # Only Hope+Fear

# Reshape to wide format
df_wide = df_merged.pivot(index='agent_id', columns='step', values='value')
df_wide = df_wide.reset_index()
df_wide = df_wide.merge(assignments, on='agent_id')

# Rename columns
df_wide.columns = ['agent_id', 'T0', 'T1', 'T2', 'campaign_type']

# Calculate changes
df_wide['delta_T1_T0'] = df_wide['T1'] - df_wide['T0']
df_wide['delta_T2_T0'] = df_wide['T2'] - df_wide['T0']

print("=" * 70)
print("DESCRIPTIVE STATISTICS")
print("=" * 70)

for campaign in ['hope', 'fear']:
    df_group = df_wide[df_wide['campaign_type'] == campaign]
    
    print(f"\n{campaign.upper()} GROUP (n={len(df_group)}):")
    print(f"  T0: M={df_group['T0'].mean():.3f}, SD={df_group['T0'].std():.3f}")
    print(f"  T1: M={df_group['T1'].mean():.3f}, SD={df_group['T1'].std():.3f}")
    print(f"  T2: M={df_group['T2'].mean():.3f}, SD={df_group['T2'].std():.3f}")
    print(f"  ΔT1-T0: M={df_group['delta_T1_T0'].mean():.3f}, SD={df_group['delta_T1_T0'].std():.3f}")
    print(f"  ΔT2-T0: M={df_group['delta_T2_T0'].mean():.3f}, SD={df_group['delta_T2_T0'].std():.3f}")

print("\n" + "=" * 70)
print("INDEPENDENT T-TESTS: Hope vs Fear")
print("=" * 70)

# T1-T0 change
hope_change_t1 = df_wide[df_wide['campaign_type']=='hope']['delta_T1_T0']
fear_change_t1 = df_wide[df_wide['campaign_type']=='fear']['delta_T1_T0']

t_stat, p_val = stats.ttest_ind(hope_change_t1, fear_change_t1)
d = (hope_change_t1.mean() - fear_change_t1.mean()) / np.sqrt((hope_change_t1.std()**2 + fear_change_t1.std()**2)/2)

print(f"\nT1-T0 Change:")
print(f"  Hope: M={hope_change_t1.mean():.3f}, SD={hope_change_t1.std():.3f}")
print(f"  Fear: M={fear_change_t1.mean():.3f}, SD={fear_change_t1.std():.3f}")
print(f"  t({len(hope_change_t1)+len(fear_change_t1)-2}) = {t_stat:.3f}, p = {p_val:.4f}")
print(f"  Cohen's d = {d:.3f}")

if p_val < 0.05:
    print("  ✓ SIGNIFICANT difference between Hope and Fear")
else:
    print("  ✗ No significant difference")

# T2-T0 change
hope_change_t2 = df_wide[df_wide['campaign_type']=='hope']['delta_T2_T0']
fear_change_t2 = df_wide[df_wide['campaign_type']=='fear']['delta_T2_T0']

t_stat2, p_val2 = stats.ttest_ind(hope_change_t2, fear_change_t2)
d2 = (hope_change_t2.mean() - fear_change_t2.mean()) / np.sqrt((hope_change_t2.std()**2 + fear_change_t2.std()**2)/2)

print(f"\nT2-T0 Change:")
print(f"  Hope: M={hope_change_t2.mean():.3f}, SD={hope_change_t2.std():.3f}")
print(f"  Fear: M={fear_change_t2.mean():.3f}, SD={fear_change_t2.std():.3f}")
print(f"  t({len(hope_change_t2)+len(fear_change_t2)-2}) = {t_stat2:.3f}, p = {p_val2:.4f}")
print(f"  Cohen's d = {d2:.3f}")

if p_val2 < 0.05:
    print("  ✓ SIGNIFICANT difference between Hope and Fear")
else:
    print("  ✗ No significant difference")
```

---

## 🔍 Step 3: Investigate Why Beliefs Decreased

### Hypothesis Testing: What Caused the Decrease?

**Possible explanations to test:**

### A. Sponsored Content Reactance

```python
# Search THOUGHTS for reactance indicators
df_beliefs = pd.read_csv('data/exports/belief_measurements.csv')

# At T1 and T2, check for skepticism keywords
reactance_keywords = ['sponsored', 'advertisement', 'ad', 'skeptical', 
                      'distrust', 'overwhelming', 'popping up', 'again']

df_t1_t2 = df_beliefs[df_beliefs['step'].isin([800, 2000])]

for keyword in reactance_keywords:
    count = df_t1_t2['reasoning'].str.contains(keyword, case=False, na=False).sum()
    print(f"'{keyword}': {count} mentions")

# Look at specific examples
print("\nExamples mentioning 'overwhelming':")
examples = df_t1_t2[df_t1_t2['reasoning'].str.contains('overwhelming', case=False, na=False)]
for _, row in examples.head(3).iterrows():
    print(f"\n{row['agent_id']} (Step {row['step']}):")
    print(f"  Rating: {row['value']*10}/10")
    print(f"  Thoughts: {row['reasoning'][:200]}...")
```

---

### B. LLM Regression to Mean (Despite Fix)

```python
# Check if all agents drifted toward same value
df_changes = df_wide.copy()

# Calculate variance at each timepoint
var_t0 = df_changes['T0'].var()
var_t1 = df_changes['T1'].var()
var_t2 = df_changes['T2'].var()

print("Variance over time:")
print(f"  T0: {var_t0:.4f}")
print(f"  T1: {var_t1:.4f}")
print(f"  T2: {var_t2:.4f}")

if var_t1 < var_t0 and var_t2 < var_t1:
    print("  ⚠️  Variance DECREASING → agents converging to mean")
elif var_t1 > var_t0:
    print("  ✓ Variance maintained or increased → no convergence")
```

---

### C. Memory Dilution Effect

```python
# Check if agents with more memories showed larger decreases
# Hypothesis: Campaign gets "drowned out" by other content

# Would need to count memories per agent from database
# For now, check if T2 decrease > T1 decrease (more time = more memories)

print("Time-dependent decrease:")
print(f"  Mean ΔT1-T0: {df_wide['delta_T1_T0'].mean():.3f}")
print(f"  Mean ΔT2-T0: {df_wide['delta_T2_T0'].mean():.3f}")

if abs(df_wide['delta_T2_T0'].mean()) > abs(df_wide['delta_T1_T0'].mean()):
    print("  → Decrease WORSENS over time (memory dilution possible)")
else:
    print("  → Decrease stabilizes (not memory dilution)")
```

---

## 📝 Step 4: Qualitative Analysis

### Extract Thematic Patterns from THOUGHTS

```python
# Sample THOUGHTS by group and timepoint
df_merged = df_beliefs.merge(assignments, on='agent_id', how='left')
df_merged['campaign_type'] = df_merged['campaign_type'].fillna('control')

# Hope group at T1
hope_t1 = df_merged[(df_merged['campaign_type']=='hope') & (df_merged['step']==800)]

print("=" * 70)
print("HOPE GROUP T1 THOUGHTS (Sample of 10)")
print("=" * 70)

for _, row in hope_t1.sample(10, random_state=42).iterrows():
    print(f"\n{row['agent_id']} - Rating: {row['value']*10:.1f}/10")
    print(f"{row['reasoning'][:200]}...")

# Fear group at T1
fear_t1 = df_merged[(df_merged['campaign_type']=='fear') & (df_merged['step']==800)]

print("\n" + "=" * 70)
print("FEAR GROUP T1 THOUGHTS (Sample of 10)")
print("=" * 70)

for _, row in fear_t1.sample(10, random_state=42).iterrows():
    print(f"\n{row['agent_id']} - Rating: {row['value']*10:.1f}/10")
    print(f"{row['reasoning'][:200]}...")
```

**Look for patterns:**
- Hope: "optimistic", "inspired", "together", "positive"
- Fear: "urgent", "alarming", "concerning", "worried"
- Reactance: "overwhelming", "sponsored", "too much", "distrust"

---

## 📊 Step 5: Secondary Analyses

### A. Personality Moderation

**Test:** Does neuroticism moderate fear response?

```python
# Load personas
persona_df = pd.DataFrame(personas)

# Merge neuroticism with belief changes
df_analysis = df_wide.merge(
    persona_df[['agent_id', 'personality']], 
    on='agent_id'
)

# Extract neuroticism
df_analysis['neuroticism'] = df_analysis['personality'].apply(lambda x: x['neuroticism'])

# Fear group only
df_fear = df_analysis[df_analysis['campaign_type'] == 'fear']

# Correlation: neuroticism × change
r_fear, p_fear = stats.pearsonr(df_fear['neuroticism'], df_fear['delta_T1_T0'])

print("PERSONALITY MODERATION:")
print(f"Fear group: Neuroticism × ΔT1-T0")
print(f"  r = {r_fear:.3f}, p = {p_fear:.4f}")

if r_fear < -0.3 and p_fear < 0.05:
    print("  ✓ High neuroticism → larger DECREASE (reactance)")
elif r_fear > 0.3 and p_fear < 0.05:
    print("  ✓ High neuroticism → larger INCREASE (sensitivity)")
else:
    print("  ✗ No moderation by neuroticism")
```

---

### B. Cascade Depth Effects

**Test:** Does exposure route matter?

```python
# Get all exposures with depth
exposures = pd.read_csv('data/exports/campaign_exposures.csv')

# Merge with T1 beliefs
df_t1 = df_beliefs[df_beliefs['step'] == 800].copy()
df_t1 = df_t1.merge(
    exposures[['agent_id', 'cascade_depth']].groupby('agent_id').agg({'cascade_depth': 'min'}),
    on='agent_id',
    how='left'
)

# Compare by depth
print("=" * 70)
print("CASCADE DEPTH EFFECTS")
print("=" * 70)

for depth in [0, 1, 2]:
    df_depth = df_t1[df_t1['cascade_depth'] == depth]
    if len(df_depth) > 0:
        print(f"\nDepth {depth}: n={len(df_depth)}, M={df_depth['value'].mean():.3f}")
```

---

## 📊 Step 6: Write Statistical Results

### Template for Thesis Results Section

```
Results

Baseline Validation
All 200 agents were assessed at baseline (T0, step 399). Environmental 
concern ratings ranged from X to Y (M = 0.77, SD = 0.10), correlating 
strongly with persona initialization values (r = 0.XX, p < .001), 
indicating successful prevention of median collapse in LLM responses.

Main Effects: Hope vs. Fear Campaigns
We conducted independent samples t-tests comparing belief changes 
between Hope (n=56) and Fear (n=56) conditions.

Immediate Effect (T1-T0):
- Hope group: M = -0.030, SD = 0.085
- Fear group: M = -0.020, SD = 0.067
- Difference: t(110) = -0.XX, p = 0.XXX, d = -0.XX

Sustained Effect (T2-T0):
- Hope group: M = -0.064, SD = 0.146
- Fear group: M = -0.055, SD = 0.111
- Difference: t(110) = -0.XX, p = 0.XXX, d = -0.XX

Contrary to hypotheses, both conditions showed decreased environmental 
concern over time, with no significant difference between Hope and 
Fear framing (p = X.XXX).
```

---

## 🔎 Step 7: Explain the Unexpected Finding

### Possible Interpretations

#### 1. **Sponsored Content Backfire Effect** (Most Likely)

From your sample comments:
```
"This message keeps popping up, and it's making me think..."
"seeing this so often feels overwhelming"
"I love the message, but seeing it so often makes me wonder if 
it's actually driving change"
```

**Interpretation:** The "🔔 SPONSORED POST" marker triggered reactance. Agents recognized it as advertising and became more skeptical.

**Theoretical support:**
- Friestad & Wright (1994): Persuasion Knowledge Model
- Edwards et al. (2002): Advertising avoidance
- Campbell & Kirmani (2000): Consumer skepticism

**Thesis framing:**
> "The observed decrease in environmental concern may reflect a reactance 
> effect triggered by explicit advertising markers. Despite high baseline 
> environmental concern, agents exhibited skepticism toward sponsored content, 
> consistent with persuasion knowledge theory (Friestad & Wright, 1994)."

---

#### 2. **Simulation Artifact: LLM Regression**

Despite persona anchoring, LLMs may still drift toward "reasonable moderate" stance over time.

**Evidence check:**
- Did control group also decrease? (We didn't measure them at T1/T2)
- Did variance compress? (Check var_t0 vs var_t2)

---

#### 3. **Real Effect: Preaching to the Choir Backfires**

Your agents had high baseline concern (M=0.77). Environmental campaigns targeted at already-committed individuals may:
- Feel redundant ("I already know this")
- Trigger fatigue ("I'm doing my part already")
- Reduce urgency ("If campaigns are running, others will handle it")

**Theoretical support:**
- Bystander effect (Darley & Latané, 1968)
- Moral licensing (Merritt et al., 2010)

---

## 🎓 Step 8: Write Your Discussion

### Framework (Even with Null/Negative Result)

**Contributions:**
1. ✅ Novel methodology (LLM agents + hybrid belief measurement)
2. ✅ Validated measurement system (T0 correlates with persona)
3. ✅ Demonstrated cascade tracking in agent simulation
4. ✅ Identified important finding: Sponsored markers may backfire

**Limitations:**
1. ⚠️ LLM agents may not replicate human responses
2. ⚠️ Short timeline (33 hours simulated)
3. ⚠️ High baseline concern (ceiling effect possible)
4. ⚠️ Single exposure per agent (real users see multiple campaigns)

**Future Work:**
- Remove "SPONSORED POST" marker and retest
- Test on lower-baseline population
- Extend timeline for long-term effects
- Compare LLM responses to human validation sample

---

## 🛠️ Analysis Scripts I Can Create

Would you like me to create:
1. ✅ **`analyze_beliefs.py`** - Complete statistical analysis script
2. ✅ **`validate_quality.py`** - Data quality checks (correlations, exposure rates)
3. ✅ **`extract_quotes.py`** - Pull relevant THOUGHTS for thesis
4. ✅ **`visualize_results.py`** - Generate plots (trajectories, distributions)

---

## 💡 Bottom Line

**Even with unexpected results, you have:**
- ✅ Valid data (measurement system works)
- ✅ Novel methodology (publishable)
- ✅ Rich qualitative data (quotable)
- ✅ Interesting finding (sponsored content reactance)

**A null or negative result with good methodology is still a valuable bachelor's thesis!**

Want me to create the analysis scripts now?


# Thesis Experiment Data - Saved Successfully

**Date:** November 8, 2025  
**Database:** `data/thesis_experiment_20251108_015809.db`  
**Duration:** 3 hours 22 minutes  
**Status:** ✅ Complete (with high reflection cost)

---

## 📁 Files Saved

### Primary Database
- **Location:** `data/thesis_experiment_20251108_015809.db`
- **Backup:** `data/backups/thesis_experiment_20251108_015809_BACKUP.db`
- **Size:** ~50-100 MB
- **Contains:** All raw simulation data

### Exported CSV Files (for Analysis)
All in `data/exports/`:

1. **`belief_measurements.csv`** - PRIMARY OUTCOME DATA
   - 424 measurements (200 at T0, 112 at T1, 112 at T2)
   - Columns: agent_id, attribute, value, step, reasoning (THOUGHTS text)

2. **`campaign_assignments.csv`** - EXPERIMENTAL GROUPS
   - 112 assignments (56 Hope, 56 Fear)
   - Note: Should have been 120 (60+60) - investigate why only 112

3. **`campaign_exposures.csv`** - CASCADE TRACKING
   - 175 exposures with cascade_depth
   - Columns: agent_id, campaign_id, post_id, cascade_depth, exposure_step

4. **`posts.csv`** - ALL POSTS
   - 55,548 posts (organic, campaign, reshares)
   - Columns: post_id, agent_id, content, post_type, parent_post_id, cascade_depth

5. **`interactions.csv`** - LIKES
   - 1,371 likes
   - Columns: agent_id, post_id, interaction_type, created_step

6. **`experiment_summary.json`** - OVERVIEW
   - Metadata and counts

---

## 📊 Quick Results Preview

### Baseline (T0 - Step 399)
- **Hope group:** n=56, mean=0.763, σ=0.098
- **Fear group:** n=56, mean=0.784, σ=0.101
- **Control:** n=88, mean=0.782, σ=0.103

✅ **Good signs:**
- Groups balanced at baseline (no pre-intervention differences)
- Reasonable variance (no median collapse: σ≈0.10, not 0.03)
- Mean ~0.77 (matches persona distribution mean=0.74)

### Immediate Effect (T1 - Step 800)
- **Hope:** mean=0.732 (Δ = **-0.030** from T0)
- **Fear:** mean=0.764 (Δ = **-0.020** from T0)

### Sustained Effect (T2 - Step 2000)
- **Hope:** mean=0.698 (Δ = **-0.064** from T0)
- **Fear:** mean=0.729 (Δ = **-0.055** from T0)

---

## 🚨 PRELIMINARY FINDINGS (Require Investigation)

### Unexpected Result: Beliefs DECREASED, Not Increased

**Expected:** Campaigns increase environmental concern  
**Observed:** Both Hope and Fear groups show NEGATIVE changes

**Possible Explanations:**

1. **Sponsored Post Reactance** 🔴
   - "🔔 SPONSORED POST" marker may trigger skepticism
   - Agents distrust branded content despite high brand_trust
   - Need to check reasoning field for "skeptical", "advertisement"

2. **Regression to Mean** 🟡
   - T0 beliefs high (mean=0.78)
   - LLM may normalize toward more "moderate" stance over time
   - Check if control group also decreased (we didn't measure them)

3. **Memory Accumulation Dilutes Campaign Effect** 🟡
   - By T1/T2, agents have many memories
   - Campaign memories compete with other content
   - Campaign may be "drowned out" by noise

4. **LLM Anchoring Issue** 🟡
   - Despite persona context, LLM still pulled toward ~0.70-0.73 range
   - Median collapse partially still present

5. **Real Effect: Campaigns Backfired** 🟢
   - Environmental campaigns can cause reactance if perceived as preachy
   - This would be an interesting (negative) finding!

---

## 💡 Next Steps for Analysis

### 1. Check Qualitative Reasoning (THOUGHTS field)
```python
import pandas as pd
df = pd.read_csv('data/exports/belief_measurements.csv')

# Sample T1 thoughts from Hope group
hope_t1 = df[(df['step']==800) & (df['agent_id'].isin(hope_ids))]
print(hope_t1[['agent_id', 'value', 'reasoning']].head(10))

# Look for patterns:
# - "sponsored", "advertisement", "skeptical" → reactance
# - "hopeful", "inspired", "motivated" → positive effect
# - Generic responses → median collapse residual
```

### 2. Statistical Test (Even with Negative Effect)
```python
from scipy import stats

# Hope vs Fear at T1-T0
hope_change = df_hope['delta_t1_t0']
fear_change = df_fear['delta_t1_t0']

t_stat, p_val = stats.ttest_ind(hope_change, fear_change)
print(f"Hope vs Fear: t={t_stat:.2f}, p={p_val:.4f}")

# If p < 0.05: Difference exists (even if both negative)
# If p > 0.05: No difference between framings
```

### 3. Investigate Why Only 112 Assignments (Not 120)
```python
# Expected: 60 Hope + 60 Fear = 120
# Actual: 56 Hope + 56 Fear = 112
# Missing: 8 agents

# Possible causes:
# - Stratification left some bins empty
# - Some agents filtered out (bug?)
```

### 4. Check Campaign Exposure Rates
```python
exposures = pd.read_csv('data/exports/campaign_exposures.csv')

# Did targeted agents actually see campaigns?
direct_exposures = exposures[exposures['cascade_depth'] == 0]
print(f"Direct exposures: {len(direct_exposures)}/112 = {len(direct_exposures)/112:.1%}")

# If < 80%, many agents never saw campaign → explains null effect
```

---

## ✅ Data Preservation Complete

**Saved locations:**
1. ✅ `data/thesis_experiment_20251108_015809.db` (original)
2. ✅ `data/backups/thesis_experiment_20251108_015809_BACKUP.db` (backup)
3. ✅ `data/exports/*.csv` (5 CSV files for analysis)
4. ✅ `data/exports/experiment_summary.json` (metadata)

**Cost:** ~$284 (high due to reflection frequency)

**Status:** Data is safe and ready for analysis, but results are unexpected (beliefs decreased instead of increased). Need to investigate reasoning field and exposure patterns.

---

## 🎓 For Your Thesis

Even with unexpected results, you have:
- ✅ Valid baseline measurements (correlated with persona)
- ✅ Longitudinal data (3 time points)
- ✅ Rich qualitative THOUGHTS data (can quote in thesis)
- ✅ Proper experimental design (stratified, controlled)
- ✅ Novel methodology (LLM agents + hybrid belief measurement)

**A null or negative result is still a valid finding** if you can explain it theoretically (e.g., reactance to sponsored content, saturation effects, etc.)


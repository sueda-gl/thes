# V2 Additional Analyses: Beyond Primary Results

## ✅ Your Data is Safe

**Storage:**
- Primary: `data/thesis_experiment_v2_20251108_084342.db` (52 MB)
- Backup: `data/backups/thesis_experiment_v2_20251108_084342.db`
- Exports: `data/v2_exports/*.csv` (4 CSV files)

**Contains:**
- 424 belief measurements (with qualitative THOUGHTS)
- 51,131 posts (organic, comments, reshares)
- 1,580 campaign exposures (tracked by depth)
- 112 campaign assignments
- 200 agent personas with rich backstories
- Complete network structure
- All token usage data

---

## 📊 Additional Analyses You Can Do

### 1. Personality Moderation Analysis

**Research Question:** Does personality moderate campaign effectiveness?

**Hypothesis:** High neuroticism → stronger fear response

```python
import pandas as pd
from scipy import stats
import json

# Load data
df_beliefs = pd.read_csv('data/v2_exports/v2_belief_measurements.csv')
assignments = pd.read_csv('data/v2_exports/v2_campaign_assignments.csv')
personas = json.load(open('personas/personas_v2_final.json'))

# Extract personality
persona_df = pd.DataFrame(personas)
persona_df['neuroticism'] = persona_df['personality'].apply(lambda x: x['neuroticism'])
persona_df['openness'] = persona_df['personality'].apply(lambda x: x['openness'])

# Calculate changes
df_wide = df_beliefs.merge(assignments, on='agent_id').pivot(...)
df_wide['delta'] = df_wide[800] - df_wide[399]
df_analysis = df_wide.merge(persona_df[['agent_id', 'neuroticism', 'openness']], on='agent_id')

# Test moderation
fear_group = df_analysis[df_analysis['campaign_type'] == 'fear']
r_neuro, p_neuro = stats.pearsonr(fear_group['neuroticism'], fear_group['delta'])

print(f"Fear group: Neuroticism × Belief Change")
print(f"  r = {r_neuro:.3f}, p = {p_neuro:.4f}")

if r_neuro > 0.3 and p_neuro < 0.05:
    print("✓ High neuroticism → Stronger fear response")
```

**Expected:** High neuroticism agents respond more strongly to fear appeals

---

### 2. Cascade Depth Effects

**Research Question:** Does exposure route matter?

```python
exposures = pd.read_csv('data/v2_exports/v2_campaign_exposures.csv')

# Get first exposure depth per agent
first_exposure = exposures.groupby('agent_id').agg({
    'cascade_depth': 'min',  # 0=direct, 1+=secondary
    'post_id': 'count'       # Total exposures
}).reset_index()
first_exposure.columns = ['agent_id', 'first_depth', 'exposure_count']

# Merge with belief changes
df_analysis = df_wide.merge(first_exposure, on='agent_id', how='left')

# Compare by exposure route
print("Belief change by exposure route:")
print(f"  Direct (depth=0): M={df_analysis[df_analysis['first_depth']==0]['delta'].mean():.3f}")
print(f"  Secondary (depth≥1): M={df_analysis[df_analysis['first_depth']>=1]['delta'].mean():.3f}")

# Dose-response: exposure count
r_dose, p_dose = stats.pearsonr(
    df_analysis['exposure_count'].fillna(0), 
    df_analysis['delta']
)
print(f"\nDose-response: r={r_dose:.3f}, p={p_dose:.4f}")
```

**Expected:** Direct exposure > Secondary exposure (H4)

---

### 3. Network Position Effects

**Research Question:** Do hubs respond differently?

```python
import networkx as nx

# Load network
# (You'll need to export or regenerate the BA network)

# Get degree centrality per agent
degrees = dict(network.degree())
df_analysis['degree'] = df_analysis['agent_id'].map(degrees)

# Split by network position
hubs = df_analysis[df_analysis['degree'] > df_analysis['degree'].median()]
periphery = df_analysis[df_analysis['degree'] <= df_analysis['degree'].median()]

print("Belief change by network position:")
print(f"  Hubs: M={hubs['delta'].mean():.3f}")
print(f"  Periphery: M={periphery['delta'].mean():.3f}")

# Test
t_stat, p_val = stats.ttest_ind(hubs['delta'], periphery['delta'])
print(f"  Difference: t={t_stat:.3f}, p={p_val:.4f}")
```

**Expected:** Hubs may respond more (higher visibility) or less (information overload)

---

### 4. Temporal Dynamics

**Research Question:** When do beliefs change?

```python
# Get all belief measurements, not just T0/T1/T2
df_beliefs_all = pd.read_sql("SELECT * FROM belief_measurements", conn)

# Plot trajectory by group
import matplotlib.pyplot as plt

for campaign in ['hope', 'fear']:
    df_camp = df_beliefs_all.merge(assignments, on='agent_id')
    df_camp = df_camp[df_camp['campaign_type'] == campaign]
    
    # Group by step
    trajectory = df_camp.groupby('step')['value'].agg(['mean', 'std', 'count'])
    
    plt.plot(trajectory.index, trajectory['mean'], label=campaign)
    plt.fill_between(trajectory.index, 
                     trajectory['mean'] - trajectory['std'],
                     trajectory['mean'] + trajectory['std'],
                     alpha=0.2)

plt.axvline(x=400, color='red', linestyle='--', label='Campaign')
plt.xlabel('Step')
plt.ylabel('Environmental Concern')
plt.legend()
plt.title('Belief Trajectories Over Time')
plt.savefig('belief_trajectories.png')
```

**Shows:** Exact timing of belief shifts

---

### 5. Qualitative Content Analysis

**Research Question:** How do agents express belief changes?

```python
# Extract THOUGHTS from agents who increased most
df_beliefs = pd.read_csv('data/v2_exports/v2_belief_measurements.csv')

# Get top increasers in fear group
fear_agents = assignments[assignments['campaign_type']=='fear']['agent_id']
fear_beliefs = df_beliefs[df_beliefs['agent_id'].isin(fear_agents)]

# Calculate individual changes
changes = {}
for aid in fear_agents:
    agent_beliefs = fear_beliefs[fear_beliefs['agent_id']==aid]
    t0 = agent_beliefs[agent_beliefs['step']==399]['value'].iloc[0]
    t1 = agent_beliefs[agent_beliefs['step']==800]['value'].iloc[0]
    changes[aid] = t1 - t0

# Top 5 increasers
top_increasers = sorted(changes.items(), key=lambda x: x[1], reverse=True)[:5]

print("Top 5 Fear Campaign Increasers:")
for aid, delta in top_increasers:
    t0_thought = fear_beliefs[(fear_beliefs['agent_id']==aid) & (fear_beliefs['step']==399)]['reasoning'].iloc[0]
    t1_thought = fear_beliefs[(fear_beliefs['agent_id']==aid) & (fear_beliefs['step']==800)]['reasoning'].iloc[0]
    
    print(f"\n{aid}: +{delta:.2f}")
    print(f"  T0: {t0_thought[:100]}...")
    print(f"  T1: {t1_thought[:100]}...")
```

**Use for:** Thesis quotes showing mechanism of belief change

---

### 6. Political Ideology Effects

**Research Question:** Do progressives vs conservatives respond differently?

```python
# From backstories, extract political stance
personas = json.load(open('personas/personas_v2_final.json'))

# Categorize by political keywords in backstory
def extract_politics(backstory):
    if 'progressive' in backstory.lower():
        return 'progressive'
    elif 'conservative' in backstory.lower():
        return 'conservative'
    elif 'libertarian' in backstory.lower():
        return 'libertarian'
    else:
        return 'moderate'

persona_df = pd.DataFrame(personas)
persona_df['politics'] = persona_df['backstory'].apply(extract_politics)

# Merge with belief changes
df_analysis = df_wide.merge(persona_df[['agent_id', 'politics']], on='agent_id')

# Compare by ideology
for politics in ['progressive', 'conservative', 'libertarian', 'moderate']:
    df_group = df_analysis[df_analysis['politics'] == politics]
    if len(df_group) > 5:
        print(f"{politics.capitalize()}: M={df_group['delta'].mean():+.3f}, n={len(df_group)}")
```

**Expected:** Different ideologies respond differently to environmental messaging

---

### 7. Conspiracy Belief Effects

**Research Question:** Do conspiracy believers distrust campaigns?

```python
# Extract conspiracy beliefs from backstories
persona_df['has_conspiracy'] = persona_df['backstory'].str.contains(
    'convinced|skeptical|distrust|manipulate|control',
    case=False
)

# Compare conspiracy vs non-conspiracy
df_analysis = df_wide.merge(persona_df[['agent_id', 'has_conspiracy']], on='agent_id')

conspiracy = df_analysis[df_analysis['has_conspiracy']]
no_conspiracy = df_analysis[~df_analysis['has_conspiracy']]

print(f"Conspiracy believers: Δ={conspiracy['delta'].mean():+.3f}")
print(f"Non-believers: Δ={no_conspiracy['delta'].mean():+.3f}")
```

---

### 8. Content Analysis: What Did Agents Actually Say?

**Research Question:** How do responses reflect personality?

```python
# Load posts
df_posts = pd.read_csv('data/v2_exports/v2_posts.csv')

# Comments on campaign posts
campaign_comments = df_posts[
    (df_posts['post_type'] == 'response') &
    (df_posts['parent_post_id'].str.contains('campaign', na=False))
]

# Merge with persona
df_comments = campaign_comments.merge(persona_df[['agent_id', 'backstory']], on='agent_id')

# Sample diverse responses
print("Sample campaign responses by persona:")
for idx, row in df_comments.sample(10).iterrows():
    print(f"\n{row['agent_id']}:")
    print(f"  Backstory: {row['backstory'][:100]}...")
    print(f"  Comment: {row['content']}")
```

**Use for:** Showing how backstories produce diverse responses

---

### 9. Engagement Patterns

**Research Question:** Who engages with campaigns?

```python
# Calculate engagement by baseline concern
df_exposures = pd.read_csv('data/v2_exports/v2_campaign_exposures.csv')

# Merge with persona baseline
df_exposures = df_exposures.merge(persona_df[['agent_id', 'environmental_concern']], on='agent_id')

# Split by baseline
low_concern = df_exposures[df_exposures['environmental_concern'] < 0.3]
high_concern = df_exposures[df_exposures['environmental_concern'] > 0.6]

print(f"Response rates:")
print(f"  Low concern (<0.3): {low_concern['responded'].mean():.1%}")
print(f"  High concern (>0.6): {high_concern['responded'].mean():.1%}")
```

**Expected:** Baseline concern predicts engagement

---

### 10. Cascade Structure Analysis

**Research Question:** How do campaigns spread?

```python
# Structural virality for each campaign
from analysis.validation import ValidationPipeline

validator = ValidationPipeline()

# Get all campaign-related posts
hope_cascade = df_posts[df_posts['post_id'].str.contains('hope|reshare', na=False)]
fear_cascade = df_posts[df_posts['post_id'].str.contains('fear|reshare', na=False)]

# Calculate structural virality
xi_hope = validator._calculate_structural_virality(hope_cascade.to_dict('records'))
xi_fear = validator._calculate_structural_virality(fear_cascade.to_dict('records'))

print(f"Structural virality (ξ):")
print(f"  Hope: ξ={xi_hope:.2f}")
print(f"  Fear: ξ={xi_fear:.2f}")
```

**Interpretation:** ξ=2 (broadcast), ξ>5 (viral spread)

---

## 📝 Additional Thesis Sections You Can Write

### 1. **Moderation Analysis** (Personality × Campaign)
"We examined whether Big Five personality traits moderated campaign effectiveness..."

### 2. **Cascade Dynamics** (H4 - Direct vs Secondary)
"Direct campaign exposure (depth=0) produced stronger effects than secondary exposure..."

### 3. **Individual Differences** (Who responds?)
"Baseline concern predicted engagement rates but not belief change magnitude..."

### 4. **Qualitative Analysis** (Rich THOUGHTS data)
Quote actual agent thoughts showing diverse responses

### 5. **Network Effects**
"Network position (degree centrality) did not significantly moderate effects..."

---

## 🎓 For Your Thesis

**You now have:**
- ✅ Primary finding: Fear > Hope (p=.016) ← Main result
- ✅ 8-10 additional analyses possible ← Enrichment
- ✅ Qualitative quotes ← Examples
- ✅ Methodological contribution ← Novel approach

**This is a STRONG bachelor's thesis with:**
- Significant main effect
- Multiple secondary analyses
- Rich data
- Rigorous methodology

---

## 💾 Data Security Checklist

✅ **Primary database:** `data/thesis_experiment_v2_20251108_084342.db` (52MB)  
✅ **Backup copies:** `data/backups/` (multiple versions)  
✅ **CSV exports:** `data/v2_exports/` (portable format)  
✅ **V1 data preserved:** `data/thesis_experiment_20251108_015809.db` (comparison)  

**Recommendation:** Copy to external drive or cloud storage

---

**Want me to create analysis scripts for any of these additional analyses?** They would strengthen your thesis significantly!

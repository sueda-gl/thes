import pandas as pd
import numpy as np
from scipy import stats
import sqlite3

# Connect to V2.1 database
db_path = 'data/thesis_experiment_v2_20251108_133520.db'
conn = sqlite3.connect(db_path)

print("=" * 80)
print("V2.1 RESULTS: HOPE vs FEAR (WITH EFFICACY)")
print("=" * 80)
print()

# Load belief measurements
beliefs_df = pd.read_sql_query("""
    SELECT agent_id, attribute, value, step, reasoning
    FROM belief_measurements
    WHERE attribute = 'environmental_concern'
    ORDER BY agent_id, step
""", conn)

# Load campaign assignments
assignments_df = pd.read_sql_query("""
    SELECT agent_id, campaign_type
    FROM (
        SELECT DISTINCT ce.agent_id,
               CASE 
                   WHEN c.campaign_type = 'hope' THEN 'hope'
                   WHEN c.campaign_type = 'fear' THEN 'fear'
                   ELSE 'control'
               END as campaign_type
        FROM campaign_exposures ce
        JOIN campaigns c ON ce.campaign_id = c.campaign_id
        WHERE ce.cascade_depth = 0
    )
""", conn)

conn.close()

# Merge
df = beliefs_df.merge(assignments_df, on='agent_id', how='inner')

# Pivot to wide format
pivot = df.pivot(index='agent_id', columns='step', values='value')
pivot = pivot.merge(assignments_df, on='agent_id')

# Calculate changes
pivot['change_T1'] = pivot[800] - pivot[399]
pivot['change_T2'] = pivot[2000] - pivot[399]

# Split by condition
hope = pivot[pivot['campaign_type'] == 'hope']
fear = pivot[pivot['campaign_type'] == 'fear']

print(f"Sample sizes: Hope n={len(hope)}, Fear n={len(fear)}")
print()

# HOPE results
print("HOPE CAMPAIGN (Progress + Efficacy):")
print("-" * 80)
print(f"  T0 (baseline):  M={hope[399].mean():.3f}, SD={hope[399].std():.3f}")
print(f"  T1 (immediate): M={hope[800].mean():.3f}, SD={hope[800].std():.3f}")
print(f"  T2 (sustained): M={hope[2000].mean():.3f}, SD={hope[2000].std():.3f}")
print(f"  Change T1-T0:   M={hope['change_T1'].mean():.3f}, SD={hope['change_T1'].std():.3f}")
t_hope_t1, p_hope_t1 = stats.ttest_rel(hope[800], hope[399])
print(f"                  t({len(hope)-1})={t_hope_t1:.3f}, p={p_hope_t1:.4f}")
print(f"  Change T2-T0:   M={hope['change_T2'].mean():.3f}, SD={hope['change_T2'].std():.3f}")
t_hope_t2, p_hope_t2 = stats.ttest_rel(hope[2000], hope[399])
print(f"                  t({len(hope)-1})={t_hope_t2:.3f}, p={p_hope_t2:.4f}")
print()

# FEAR results
print("FEAR CAMPAIGN (Threat + Efficacy):")
print("-" * 80)
print(f"  T0 (baseline):  M={fear[399].mean():.3f}, SD={fear[399].std():.3f}")
print(f"  T1 (immediate): M={fear[800].mean():.3f}, SD={fear[800].std():.3f}")
print(f"  T2 (sustained): M={fear[2000].mean():.3f}, SD={fear[2000].std():.3f}")
print(f"  Change T1-T0:   M={fear['change_T1'].mean():.3f}, SD={fear['change_T1'].std():.3f}")
t_fear_t1, p_fear_t1 = stats.ttest_rel(fear[800], fear[399])
print(f"                  t({len(fear)-1})={t_fear_t1:.3f}, p={p_fear_t1:.4f}")
print(f"  Change T2-T0:   M={fear['change_T2'].mean():.3f}, SD={fear['change_T2'].std():.3f}")
t_fear_t2, p_fear_t2 = stats.ttest_rel(fear[2000], fear[399])
print(f"                  t({len(fear)-1})={t_fear_t2:.3f}, p={p_fear_t2:.4f}")
print()

# Between-group comparison
print("=" * 80)
print("BETWEEN-GROUP COMPARISON: HOPE vs FEAR")
print("=" * 80)
print()

print("Change T1-T0 (Immediate Effect):")
t_between_t1, p_between_t1 = stats.ttest_ind(hope['change_T1'], fear['change_T1'])
d_t1 = (hope['change_T1'].mean() - fear['change_T1'].mean()) / np.sqrt((hope['change_T1'].std()**2 + fear['change_T1'].std()**2) / 2)
print(f"  Hope: M={hope['change_T1'].mean():.3f}, SD={hope['change_T1'].std():.3f}")
print(f"  Fear: M={fear['change_T1'].mean():.3f}, SD={fear['change_T1'].std():.3f}")
print(f"  t({len(hope)+len(fear)-2})={t_between_t1:.3f}, p={p_between_t1:.4f}, d={d_t1:.3f}")
print()

print("Change T2-T0 (Sustained Effect):")
t_between_t2, p_between_t2 = stats.ttest_ind(hope['change_T2'], fear['change_T2'])
d_t2 = (hope['change_T2'].mean() - fear['change_T2'].mean()) / np.sqrt((hope['change_T2'].std()**2 + fear['change_T2'].std()**2) / 2)
print(f"  Hope: M={hope['change_T2'].mean():.3f}, SD={hope['change_T2'].std():.3f}")
print(f"  Fear: M={fear['change_T2'].mean():.3f}, SD={fear['change_T2'].std():.3f}")
print(f"  t({len(hope)+len(fear)-2})={t_between_t2:.3f}, p={p_between_t2:.4f}, d={d_t2:.3f}")
print()

# Summary
print("=" * 80)
print("KEY FINDINGS")
print("=" * 80)
print()

# Hope findings
if p_hope_t2 < 0.05:
    direction = "INCREASED" if hope['change_T2'].mean() > 0 else "DECREASED"
    print(f"✓ Hope: {direction} environmental concern (p={p_hope_t2:.4f})")
else:
    print(f"✗ Hope: No significant effect (p={p_hope_t2:.4f})")

# Fear findings
if p_fear_t2 < 0.05:
    direction = "INCREASED" if fear['change_T2'].mean() > 0 else "DECREASED"
    print(f"✓ Fear: {direction} environmental concern (p={p_fear_t2:.4f})")
else:
    print(f"✗ Fear: No significant effect (p={p_fear_t2:.4f})")

# Between-group findings
if p_between_t2 < 0.05:
    winner = "Fear" if fear['change_T2'].mean() > hope['change_T2'].mean() else "Hope"
    print(f"✓ Significant difference: {winner} > other (p={p_between_t2:.4f}, d={abs(d_t2):.2f})")
else:
    print(f"✗ No significant difference between conditions (p={p_between_t2:.4f})")

print()
print("=" * 80)
print("COMPARISON WITH V2 (ORIGINAL)")
print("=" * 80)
print()
print("V2 (Original - No Efficacy in Hope):")
print("  • Hope: M=-0.005 (p=.721) - No effect")
print("  • Fear: M=+0.030 (p=.061) - Marginal effect")
print("  • Difference: p=.105 - Not significant")
print()
print("V2.1 (Current - Efficacy in Both):")
print(f"  • Hope: M={hope['change_T2'].mean():+.3f} (p={p_hope_t2:.3f})")
print(f"  • Fear: M={fear['change_T2'].mean():+.3f} (p={p_fear_t2:.3f})")
print(f"  • Difference: p={p_between_t2:.3f}, d={abs(d_t2):.2f}")
print()

if p_hope_t2 < 0.05 and p_fear_t2 < 0.05:
    print("✓ BOTH campaigns now effective (efficacy worked!)")
elif p_hope_t2 < 0.05:
    print("✓ Hope became effective with efficacy added")
elif p_fear_t2 < 0.05:
    print("✓ Fear remains effective")
else:
    print("✗ Neither campaign showed significant effects")


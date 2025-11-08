import pandas as pd
import numpy as np
from scipy import stats

# Load V2 belief data
df = pd.read_csv('data/v2_exports/v2_belief_measurements.csv')

# Load campaign assignments
assignments = pd.read_csv('data/v2_exports/v2_campaign_assignments.csv')

# Merge
df = df.merge(assignments[['agent_id', 'campaign_type']], on='agent_id')

# Pivot to wide format
pivot = df.pivot(index='agent_id', columns='step', values='value')
pivot = pivot.merge(assignments[['agent_id', 'campaign_type']], on='agent_id')

# Calculate changes
pivot['change_T1'] = pivot[800] - pivot[399]
pivot['change_T2'] = pivot[2000] - pivot[399]

# Split by condition
hope = pivot[pivot['campaign_type'] == 'hope']
fear = pivot[pivot['campaign_type'] == 'fear']

print('=' * 70)
print('V2 RESULTS: HOPE vs FEAR CAMPAIGNS')
print('=' * 70)
print()
print('CAMPAIGN MESSAGES:')
print()
print('HOPE:')
print('  "Together we\'re building a cleaner planet. Every choice')
print('   you make creates positive change. Join thousands making')
print('   a difference. Small actions lead to big impact. The')
print('   future is bright when we act together."')
print()
print('FEAR:')
print('  "Time is running out. Environmental damage is accelerating.')
print('   Without immediate action, consequences will be severe.')
print('   Don\'t wait until it\'s too late. Act now before the')
print('   window closes."')
print()
print('=' * 70)
print('RESULTS')
print('=' * 70)
print()
print(f'Sample sizes: Hope n={len(hope)}, Fear n={len(fear)}')
print()
print('HOPE CAMPAIGN:')
print(f'  T0 (baseline):  M={hope[399].mean():.3f}, SD={hope[399].std():.3f}')
print(f'  T1 (immediate): M={hope[800].mean():.3f}, SD={hope[800].std():.3f}')
print(f'  T2 (sustained): M={hope[2000].mean():.3f}, SD={hope[2000].std():.3f}')
print(f'  Change T1-T0:   M={hope["change_T1"].mean():.3f}, SD={hope["change_T1"].std():.3f}')
t_hope_t1, p_hope_t1 = stats.ttest_rel(hope[800], hope[399])
print(f'                  t({len(hope)-1})={t_hope_t1:.3f}, p={p_hope_t1:.3f}')
print(f'  Change T2-T0:   M={hope["change_T2"].mean():.3f}, SD={hope["change_T2"].std():.3f}')
t_hope_t2, p_hope_t2 = stats.ttest_rel(hope[2000], hope[399])
print(f'                  t({len(hope)-1})={t_hope_t2:.3f}, p={p_hope_t2:.3f}')
print()
print('FEAR CAMPAIGN:')
print(f'  T0 (baseline):  M={fear[399].mean():.3f}, SD={fear[399].std():.3f}')
print(f'  T1 (immediate): M={fear[800].mean():.3f}, SD={fear[800].std():.3f}')
print(f'  T2 (sustained): M={fear[2000].mean():.3f}, SD={fear[2000].std():.3f}')
print(f'  Change T1-T0:   M={fear["change_T1"].mean():.3f}, SD={fear["change_T1"].std():.3f}')
t_fear_t1, p_fear_t1 = stats.ttest_rel(fear[800], fear[399])
print(f'                  t({len(fear)-1})={t_fear_t1:.3f}, p={p_fear_t1:.3f}')
print(f'  Change T2-T0:   M={fear["change_T2"].mean():.3f}, SD={fear["change_T2"].std():.3f}')
t_fear_t2, p_fear_t2 = stats.ttest_rel(fear[2000], fear[399])
print(f'                  t({len(fear)-1})={t_fear_t2:.3f}, p={p_fear_t2:.3f}')
print()
print('=' * 70)
print('BETWEEN-GROUP COMPARISON: HOPE vs FEAR')
print('=' * 70)
print()
print('Change T1-T0 (Immediate Effect):')
t_between_t1, p_between_t1 = stats.ttest_ind(hope['change_T1'], fear['change_T1'])
d_t1 = (hope['change_T1'].mean() - fear['change_T1'].mean()) / np.sqrt((hope['change_T1'].std()**2 + fear['change_T1'].std()**2) / 2)
print(f'  Hope: M={hope["change_T1"].mean():.3f}, SD={hope["change_T1"].std():.3f}')
print(f'  Fear: M={fear["change_T1"].mean():.3f}, SD={fear["change_T1"].std():.3f}')
print(f'  t({len(hope)+len(fear)-2})={t_between_t1:.3f}, p={p_between_t1:.3f}, d={d_t1:.3f}')
print()
print('Change T2-T0 (Sustained Effect):')
t_between_t2, p_between_t2 = stats.ttest_ind(hope['change_T2'], fear['change_T2'])
d_t2 = (hope['change_T2'].mean() - fear['change_T2'].mean()) / np.sqrt((hope['change_T2'].std()**2 + fear['change_T2'].std()**2) / 2)
print(f'  Hope: M={hope["change_T2"].mean():.3f}, SD={hope["change_T2"].std():.3f}')
print(f'  Fear: M={fear["change_T2"].mean():.3f}, SD={fear["change_T2"].std():.3f}')
print(f'  t({len(hope)+len(fear)-2})={t_between_t2:.3f}, p={p_between_t2:.3f}, d={d_t2:.3f}')
print()
print('=' * 70)
print('KEY FINDINGS')
print('=' * 70)
if p_hope_t2 < 0.05:
    sig_str = '✓ SIGNIFICANT' if hope['change_T2'].mean() > 0 else '✓ SIGNIFICANT DECREASE'
    print(f'• Hope: {sig_str} (p={p_hope_t2:.3f})')
else:
    print(f'• Hope: No significant effect (p={p_hope_t2:.3f})')
    
if p_fear_t2 < 0.05:
    sig_str = '✓ SIGNIFICANT' if fear['change_T2'].mean() > 0 else '✓ SIGNIFICANT INCREASE'
    print(f'• Fear: {sig_str} (p={p_fear_t2:.3f})')
else:
    print(f'• Fear: No significant effect (p={p_fear_t2:.3f})')
    
if p_between_t2 < 0.05:
    winner = 'Fear > Hope' if fear['change_T2'].mean() > hope['change_T2'].mean() else 'Hope > Fear'
    print(f'• Hope vs Fear: ✓ SIGNIFICANT DIFFERENCE ({winner}, p={p_between_t2:.3f}, d={d_t2:.2f})')
else:
    print(f'• Hope vs Fear: No significant difference (p={p_between_t2:.3f})')
print()


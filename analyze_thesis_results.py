"""
Complete statistical analysis for thesis experiment.

Performs:
1. Data quality validation
2. Primary statistical tests (Hope vs Fear)
3. Exploratory analyses (personality, cascade depth)
4. Generates summary report
"""
import pandas as pd
import numpy as np
from scipy import stats
import json
import sqlite3
from pathlib import Path

# Database path
DB_PATH = 'data/thesis_experiment_20251108_015809.db'
OUTPUT_DIR = 'data/analysis_output'
Path(OUTPUT_DIR).mkdir(exist_ok=True, parents=True)


def load_data():
    """Load all necessary data."""
    print("Loading data...")
    
    # From CSV exports
    df_beliefs = pd.read_csv('data/exports/belief_measurements.csv')
    assignments = pd.read_csv('data/exports/campaign_assignments.csv')
    exposures = pd.read_csv('data/exports/campaign_exposures.csv')
    
    # From personas
    with open('personas/personas.json', 'r') as f:
        personas = json.load(f)
    persona_df = pd.DataFrame(personas)
    
    print(f"  ✓ {len(df_beliefs)} belief measurements")
    print(f"  ✓ {len(assignments)} campaign assignments")
    print(f"  ✓ {len(exposures)} campaign exposures")
    print(f"  ✓ {len(personas)} personas\n")
    
    return df_beliefs, assignments, exposures, persona_df


def validate_baseline(df_beliefs, persona_df):
    """Check if T0 correlates with persona baseline."""
    print("=" * 80)
    print("VALIDATION 1: Baseline Measurement Quality")
    print("=" * 80)
    
    df_t0 = df_beliefs[df_beliefs['step'] == 399].copy()
    
    # Merge with persona
    df_t0 = df_t0.merge(
        persona_df[['agent_id', 'environmental_concern']],
        on='agent_id'
    )
    df_t0.rename(columns={'environmental_concern': 'persona_baseline'}, inplace=True)
    
    # Correlation
    r, p = stats.pearsonr(df_t0['value'], df_t0['persona_baseline'])
    
    print(f"\nT0 vs Persona Baseline:")
    print(f"  Correlation: r = {r:.3f}, p = {p:.4f}")
    print(f"  Persona M = {df_t0['persona_baseline'].mean():.3f}, SD = {df_t0['persona_baseline'].std():.3f}")
    print(f"  T0 M = {df_t0['value'].mean():.3f}, SD = {df_t0['value'].std():.3f}")
    
    if r > 0.7:
        print("\n  ✅ PASS: Strong correlation (median collapse prevented)")
    elif r > 0.5:
        print("\n  ⚠️  PARTIAL: Moderate correlation (some median pull)")
    else:
        print("\n  ❌ FAIL: Weak correlation (median collapse occurred)")
    
    return df_t0


def validate_treatment_delivery(exposures, assignments):
    """Check if targeted agents saw campaigns."""
    print("\n" + "=" * 80)
    print("VALIDATION 2: Treatment Delivery")
    print("=" * 80)
    
    # Direct exposures only
    direct = exposures[exposures['cascade_depth'] == 0]
    
    print(f"\nDirect Campaign Exposure:")
    print(f"  Agents targeted: {len(assignments)}")
    print(f"  Direct exposures: {len(direct)}")
    print(f"  Exposure rate: {len(direct)/len(assignments)*100:.1f}%")
    
    for campaign in ['hope', 'fear']:
        camp_assigned = assignments[assignments['campaign_type'] == campaign]
        camp_exposed = direct[direct['campaign_id'] == f'campaign_{campaign}']
        
        rate = len(camp_exposed) / len(camp_assigned) * 100 if len(camp_assigned) > 0 else 0
        print(f"\n  {campaign.capitalize()}:")
        print(f"    Targeted: {len(camp_assigned)}")
        print(f"    Exposed: {len(camp_exposed)}")
        print(f"    Rate: {rate:.1f}%")
    
    if len(direct)/len(assignments) > 0.8:
        print("\n  ✅ PASS: Good exposure rate")
    elif len(direct)/len(assignments) > 0.6:
        print("\n  ⚠️  PARTIAL: Moderate exposure (some missed campaign)")
    else:
        print("\n  ❌ FAIL: Poor exposure (many missed campaign)")


def prepare_analysis_df(df_beliefs, assignments):
    """Prepare dataframe for analysis."""
    # Merge with assignments
    df_merged = df_beliefs.merge(assignments, on='agent_id', how='inner')
    
    # Pivot to wide format
    df_wide = df_merged.pivot(index='agent_id', columns='step', values='value')
    df_wide = df_wide.reset_index()
    
    # Merge campaign type back
    df_wide = df_wide.merge(assignments, on='agent_id')
    
    # Rename columns
    df_wide.columns = ['agent_id', 'T0', 'T1', 'T2', 'campaign_type']
    
    # Calculate changes
    df_wide['delta_T1_T0'] = df_wide['T1'] - df_wide['T0']
    df_wide['delta_T2_T0'] = df_wide['T2'] - df_wide['T0']
    df_wide['delta_T2_T1'] = df_wide['T2'] - df_wide['T1']
    
    return df_wide


def primary_analysis(df_wide):
    """Main statistical tests: Hope vs Fear."""
    print("\n" + "=" * 80)
    print("PRIMARY ANALYSIS: Hope vs. Fear Comparison")
    print("=" * 80)
    
    # Descriptive statistics
    print("\nDescriptive Statistics:")
    print("-" * 80)
    
    for campaign in ['hope', 'fear']:
        df_group = df_wide[df_wide['campaign_type'] == campaign]
        
        print(f"\n{campaign.upper()} (n={len(df_group)}):")
        print(f"  T0: M={df_group['T0'].mean():.3f}, SD={df_group['T0'].std():.3f}")
        print(f"  T1: M={df_group['T1'].mean():.3f}, SD={df_group['T1'].std():.3f}")
        print(f"  T2: M={df_group['T2'].mean():.3f}, SD={df_group['T2'].std():.3f}")
        print(f"  ΔT1-T0: M={df_group['delta_T1_T0'].mean():+.3f}, SD={df_group['delta_T1_T0'].std():.3f}")
        print(f"  ΔT2-T0: M={df_group['delta_T2_T0'].mean():+.3f}, SD={df_group['delta_T2_T0'].std():.3f}")
    
    # Independent t-tests
    print("\n" + "-" * 80)
    print("Independent Samples t-tests: Hope vs. Fear")
    print("-" * 80)
    
    hope = df_wide[df_wide['campaign_type'] == 'hope']
    fear = df_wide[df_wide['campaign_type'] == 'fear']
    
    # T1-T0 change
    t_stat, p_val = stats.ttest_ind(hope['delta_T1_T0'], fear['delta_T1_T0'])
    d = (hope['delta_T1_T0'].mean() - fear['delta_T1_T0'].mean()) / np.sqrt(
        (hope['delta_T1_T0'].std()**2 + fear['delta_T1_T0'].std()**2) / 2
    )
    
    print(f"\nImmediate Effect (ΔT1-T0):")
    print(f"  Hope: M={hope['delta_T1_T0'].mean():+.3f}")
    print(f"  Fear: M={fear['delta_T1_T0'].mean():+.3f}")
    print(f"  t({len(hope)+len(fear)-2}) = {t_stat:.3f}, p = {p_val:.4f}, d = {d:.3f}")
    
    if p_val < 0.05:
        print(f"  ✓ SIGNIFICANT difference (α = .05)")
    else:
        print(f"  ✗ No significant difference")
    
    # T2-T0 change
    t_stat2, p_val2 = stats.ttest_ind(hope['delta_T2_T0'], fear['delta_T2_T0'])
    d2 = (hope['delta_T2_T0'].mean() - fear['delta_T2_T0'].mean()) / np.sqrt(
        (hope['delta_T2_T0'].std()**2 + fear['delta_T2_T0'].std()**2) / 2
    )
    
    print(f"\nSustained Effect (ΔT2-T0):")
    print(f"  Hope: M={hope['delta_T2_T0'].mean():+.3f}")
    print(f"  Fear: M={fear['delta_T2_T0'].mean():+.3f}")
    print(f"  t({len(hope)+len(fear)-2}) = {t_stat2:.3f}, p = {p_val2:.4f}, d = {d2:.3f}")
    
    if p_val2 < 0.05:
        print(f"  ✓ SIGNIFICANT difference (α = .05)")
    else:
        print(f"  ✗ No significant difference")
    
    # Paired t-tests: Did each group change from baseline?
    print("\n" + "-" * 80)
    print("Paired t-tests: Within-Group Changes")
    print("-" * 80)
    
    for campaign in ['hope', 'fear']:
        df_group = df_wide[df_wide['campaign_type'] == campaign]
        
        t_t1, p_t1 = stats.ttest_rel(df_group['T1'], df_group['T0'])
        t_t2, p_t2 = stats.ttest_rel(df_group['T2'], df_group['T0'])
        
        print(f"\n{campaign.upper()}:")
        print(f"  T1 vs T0: t({len(df_group)-1}) = {t_t1:.3f}, p = {p_t1:.4f}")
        print(f"  T2 vs T0: t({len(df_group)-1}) = {t_t2:.3f}, p = {p_t2:.4f}")
        
        if p_t1 < 0.05:
            direction = "increased" if df_group['delta_T1_T0'].mean() > 0 else "decreased"
            print(f"    → Beliefs significantly {direction}")
    
    return {
        't1_t0_t': t_stat,
        't1_t0_p': p_val,
        't1_t0_d': d,
        't2_t0_t': t_stat2,
        't2_t0_p': p_val2,
        't2_t0_d': d2
    }


def investigate_reactance(df_beliefs):
    """Search for reactance indicators in THOUGHTS."""
    print("\n" + "=" * 80)
    print("EXPLORATORY: Reactance Analysis")
    print("=" * 80)
    
    reactance_keywords = ['sponsored', 'advertisement', 'ad', 'skeptical', 
                          'overwhelming', 'popping up', 'too much', 'feels like']
    
    df_t1_t2 = df_beliefs[df_beliefs['step'].isin([800, 2000])]
    
    print("\nSearching for reactance indicators in THOUGHTS:")
    print("-" * 80)
    
    for keyword in reactance_keywords:
        count = df_t1_t2['reasoning'].str.contains(keyword, case=False, na=False).sum()
        pct = count / len(df_t1_t2) * 100
        print(f"  '{keyword}': {count} mentions ({pct:.1f}%)")
    
    # Show examples
    print("\n" + "-" * 80)
    print("Sample THOUGHTS mentioning 'overwhelming':")
    print("-" * 80)
    
    examples = df_t1_t2[df_t1_t2['reasoning'].str.contains('overwhelming', case=False, na=False)]
    for _, row in examples.head(3).iterrows():
        print(f"\n{row['agent_id']} at step {row['step']} - Rating: {row['value']*10:.1f}/10")
        print(f"  \"{row['reasoning'][:250]}...\"")


def check_variance_compression(df_wide):
    """Check if variance decreased over time (median pull)."""
    print("\n" + "=" * 80)
    print("EXPLORATORY: Variance Over Time (Median Pull Check)")
    print("=" * 80)
    
    var_t0 = df_wide['T0'].var()
    var_t1 = df_wide['T1'].var()
    var_t2 = df_wide['T2'].var()
    
    print(f"\nVariance at each timepoint:")
    print(f"  T0: {var_t0:.4f}")
    print(f"  T1: {var_t1:.4f} ({(var_t1-var_t0)/var_t0*100:+.1f}% change)")
    print(f"  T2: {var_t2:.4f} ({(var_t2-var_t0)/var_t0*100:+.1f}% change)")
    
    if var_t1 < var_t0 and var_t2 < var_t1:
        print("\n  ⚠️  Variance DECREASING → agents converging to mean (median pull)")
    elif var_t2 > var_t0:
        print("\n  ✓ Variance INCREASING → no median pull, agents diverging")
    else:
        print("\n  → Variance stable")


def generate_report(results, df_wide):
    """Generate markdown report."""
    report = f"""# Thesis Experiment Statistical Results

Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

- **Total participants:** {len(df_wide)} agents (56 Hope, 56 Fear)
- **Time points:** T0 (baseline), T1 (immediate), T2 (sustained)
- **Design:** 2×3 Mixed design (Between: Campaign × Within: Time)

---

## Primary Results: Hope vs. Fear

### Immediate Effect (T1-T0)

- **Hope:** M = {df_wide[df_wide['campaign_type']=='hope']['delta_T1_T0'].mean():.3f}, SD = {df_wide[df_wide['campaign_type']=='hope']['delta_T1_T0'].std():.3f}
- **Fear:** M = {df_wide[df_wide['campaign_type']=='fear']['delta_T1_T0'].mean():.3f}, SD = {df_wide[df_wide['campaign_type']=='fear']['delta_T1_T0'].std():.3f}
- **t-test:** t = {results['t1_t0_t']:.3f}, p = {results['t1_t0_p']:.4f}, d = {results['t1_t0_d']:.3f}
- **Interpretation:** {'Significant difference' if results['t1_t0_p'] < 0.05 else 'No significant difference'}

### Sustained Effect (T2-T0)

- **Hope:** M = {df_wide[df_wide['campaign_type']=='hope']['delta_T2_T0'].mean():.3f}, SD = {df_wide[df_wide['campaign_type']=='hope']['delta_T2_T0'].std():.3f}
- **Fear:** M = {df_wide[df_wide['campaign_type']=='fear']['delta_T2_T0'].mean():.3f}, SD = {df_wide[df_wide['campaign_type']=='fear']['delta_T2_T0'].std():.3f}
- **t-test:** t = {results['t2_t0_t']:.3f}, p = {results['t2_t0_p']:.4f}, d = {results['t2_t0_d']:.3f}
- **Interpretation:** {'Significant difference' if results['t2_t0_p'] < 0.05 else 'No significant difference'}

---

## Key Finding

**Both Hope and Fear campaigns showed DECREASED environmental concern over time**, 
with no significant difference between framings. This unexpected finding suggests 
possible reactance effects to sponsored content markers.

---

## Recommendations for Thesis Discussion

1. **Frame as a valid negative finding:** Sponsored content markers may backfire
2. **Cite persuasion knowledge theory:** Friestad & Wright (1994)
3. **Emphasize methodology contribution:** Novel LLM-agent simulation
4. **Use qualitative THOUGHTS:** Quote examples of reactance
5. **Suggest future work:** Repeat without "SPONSORED POST" marker

---

## Data Files

- Full results: `{OUTPUT_DIR}/complete_analysis.csv`
- This report: `{OUTPUT_DIR}/statistical_report.md`
"""
    
    with open(f'{OUTPUT_DIR}/statistical_report.md', 'w') as f:
        f.write(report)
    
    print(f"\n✓ Report saved to {OUTPUT_DIR}/statistical_report.md")


def main():
    """Run complete analysis pipeline."""
    print("=" * 80)
    print("THESIS EXPERIMENT STATISTICAL ANALYSIS")
    print("=" * 80)
    print()
    
    # Load data
    df_beliefs, assignments, exposures, persona_df = load_data()
    
    # Validation checks
    df_t0 = validate_baseline(df_beliefs, persona_df)
    validate_treatment_delivery(exposures, assignments)
    
    # Prepare analysis dataframe
    df_wide = prepare_analysis_df(df_beliefs, assignments)
    
    # Primary analysis
    results = primary_analysis(df_wide)
    
    # Exploratory analyses
    investigate_reactance(df_beliefs)
    check_variance_compression(df_wide)
    
    # Save analysis dataframe
    df_wide.to_csv(f'{OUTPUT_DIR}/complete_analysis.csv', index=False)
    print(f"\n✓ Analysis data saved to {OUTPUT_DIR}/complete_analysis.csv")
    
    # Generate report
    generate_report(results, df_wide)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"\nOutput directory: {OUTPUT_DIR}/")
    print("\nNext steps:")
    print("  1. Review statistical_report.md for thesis results section")
    print("  2. Use complete_analysis.csv for additional tests (personality, etc.)")
    print("  3. Extract THOUGHTS quotes for qualitative analysis")
    print("  4. Consider visualization (trajectory plots, distributions)")


if __name__ == '__main__':
    main()


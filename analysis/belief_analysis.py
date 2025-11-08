"""
Belief trajectory analysis for Hope vs Fear campaign comparison.

Analyzes environmental_concern evolution at T0 (baseline), T1 (immediate), T2 (sustained)
for directly-targeted agents, with cascade depth analysis.
"""
import asyncio
from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import defaultdict
from database.db import Database
import config


async def extract_belief_trajectories(
    db: Database,
    attribute: str = 'environmental_concern'
) -> Dict[str, List[Dict]]:
    """
    Extract belief trajectories for all agents.
    
    Args:
        db: Database connection
        attribute: Belief attribute to extract
    
    Returns:
        Dict mapping agent_id to list of belief measurements
    """
    trajectories = defaultdict(list)
    
    for step in config.BELIEF_MEASUREMENT_STEPS:
        measurements = await db.get_beliefs_at_step(step, attribute)
        for m in measurements:
            trajectories[m['agent_id']].append({
                'step': m['step'],
                'value': m['value'],
                'reasoning': m['reasoning']
            })
    
    return dict(trajectories)


async def compare_hope_vs_fear(
    db: Database,
    attribute: str = 'environmental_concern'
) -> Dict[str, any]:
    """
    Compare Hope vs Fear campaign effects on belief change.
    
    Primary analysis: Δbelief = belief(T2) - belief(T0) for directly-targeted agents
    
    Args:
        db: Database connection
        attribute: Belief attribute to analyze
    
    Returns:
        Dict with comparison statistics
    """
    # Get directly targeted agents by campaign type
    hope_agents = await db.get_directly_targeted_agents('hope')
    fear_agents = await db.get_directly_targeted_agents('fear')
    
    # Extract trajectories
    trajectories = await extract_belief_trajectories(db, attribute)
    
    # Calculate Δbelief for each group
    hope_deltas = []
    fear_deltas = []
    
    for agent_id in hope_agents:
        traj = trajectories.get(agent_id, [])
        if len(traj) >= 2:
            t0_value = next((t['value'] for t in traj if t['step'] == config.BELIEF_MEASUREMENT_STEPS[0]), None)
            t2_value = next((t['value'] for t in traj if t['step'] == config.BELIEF_MEASUREMENT_STEPS[-1]), None)
            if t0_value is not None and t2_value is not None:
                hope_deltas.append(t2_value - t0_value)
    
    for agent_id in fear_agents:
        traj = trajectories.get(agent_id, [])
        if len(traj) >= 2:
            t0_value = next((t['value'] for t in traj if t['step'] == config.BELIEF_MEASUREMENT_STEPS[0]), None)
            t2_value = next((t['value'] for t in traj if t['step'] == config.BELIEF_MEASUREMENT_STEPS[-1]), None)
            if t0_value is not None and t2_value is not None:
                fear_deltas.append(t2_value - t0_value)
    
    # Calculate statistics
    hope_mean = np.mean(hope_deltas) if hope_deltas else 0.0
    hope_std = np.std(hope_deltas) if hope_deltas else 0.0
    fear_mean = np.mean(fear_deltas) if fear_deltas else 0.0
    fear_std = np.std(fear_deltas) if fear_deltas else 0.0
    
    # Effect size (Cohen's d)
    pooled_std = np.sqrt((hope_std**2 + fear_std**2) / 2) if (hope_std > 0 or fear_std > 0) else 1e-10
    cohens_d = (hope_mean - fear_mean) / pooled_std
    
    # Statistical test (independent t-test)
    from scipy import stats
    if len(hope_deltas) > 1 and len(fear_deltas) > 1:
        t_stat, p_value = stats.ttest_ind(hope_deltas, fear_deltas)
    else:
        t_stat, p_value = None, None
    
    return {
        'hope': {
            'n': len(hope_deltas),
            'mean_delta': hope_mean,
            'std_delta': hope_std,
            'deltas': hope_deltas
        },
        'fear': {
            'n': len(fear_deltas),
            'mean_delta': fear_mean,
            'std_delta': fear_std,
            'deltas': fear_deltas
        },
        'effect_size': cohens_d,
        't_statistic': t_stat,
        'p_value': p_value
    }


async def analyze_by_cascade_depth(
    db: Database,
    attribute: str = 'environmental_concern'
) -> Dict[int, Dict]:
    """
    Analyze belief change by exposure route (cascade depth).
    
    Groups agents by their primary exposure depth:
    - Depth 0: Direct campaign exposure
    - Depth 1: Saw 1st-degree reshare
    - Depth 2+: Saw 2nd+ degree reshare
    
    Args:
        db: Database connection
        attribute: Belief attribute
    
    Returns:
        Dict mapping cascade_depth to belief change statistics
    """
    # Get all campaign exposures
    async with db.conn.execute("""
        SELECT agent_id, MIN(cascade_depth) as primary_depth
        FROM campaign_exposures
        GROUP BY agent_id
    """) as cursor:
        rows = await cursor.fetchall()
        agent_depths = {row['agent_id']: row['primary_depth'] for row in rows}
    
    # Extract trajectories
    trajectories = await extract_belief_trajectories(db, attribute)
    
    # Group by depth
    depth_deltas = defaultdict(list)
    
    for agent_id, primary_depth in agent_depths.items():
        traj = trajectories.get(agent_id, [])
        if len(traj) >= 2:
            t0_value = next((t['value'] for t in traj if t['step'] == config.BELIEF_MEASUREMENT_STEPS[0]), None)
            t2_value = next((t['value'] for t in traj if t['step'] == config.BELIEF_MEASUREMENT_STEPS[-1]), None)
            if t0_value is not None and t2_value is not None:
                delta = t2_value - t0_value
                depth_deltas[primary_depth].append(delta)
    
    # Calculate statistics for each depth
    results = {}
    for depth, deltas in depth_deltas.items():
        results[depth] = {
            'n': len(deltas),
            'mean_delta': np.mean(deltas) if deltas else 0.0,
            'std_delta': np.std(deltas) if deltas else 0.0,
            'deltas': deltas
        }
    
    return results


async def dose_response_analysis(
    db: Database,
    attribute: str = 'environmental_concern'
) -> Dict[int, Dict]:
    """
    Analyze belief change as a function of exposure dose (number of exposures).
    
    Args:
        db: Database connection
        attribute: Belief attribute
    
    Returns:
        Dict mapping exposure_count to belief change statistics
    """
    # Count exposures per agent
    async with db.conn.execute("""
        SELECT agent_id, COUNT(*) as exposure_count
        FROM campaign_exposures
        GROUP BY agent_id
    """) as cursor:
        rows = await cursor.fetchall()
        agent_exposure_counts = {row['agent_id']: row['exposure_count'] for row in rows}
    
    # Extract trajectories
    trajectories = await extract_belief_trajectories(db, attribute)
    
    # Group by exposure count
    dose_deltas = defaultdict(list)
    
    for agent_id, exposure_count in agent_exposure_counts.items():
        traj = trajectories.get(agent_id, [])
        if len(traj) >= 2:
            t0_value = next((t['value'] for t in traj if t['step'] == config.BELIEF_MEASUREMENT_STEPS[0]), None)
            t2_value = next((t['value'] for t in traj if t['step'] == config.BELIEF_MEASUREMENT_STEPS[-1]), None)
            if t0_value is not None and t2_value is not None:
                delta = t2_value - t0_value
                # Bin exposure counts (0, 1, 2-3, 4-5, 6+)
                if exposure_count == 0:
                    bin_key = 0
                elif exposure_count == 1:
                    bin_key = 1
                elif exposure_count <= 3:
                    bin_key = 2
                elif exposure_count <= 5:
                    bin_key = 3
                else:
                    bin_key = 4
                
                dose_deltas[bin_key].append(delta)
    
    # Calculate statistics for each dose level
    results = {}
    dose_labels = {0: '0', 1: '1', 2: '2-3', 3: '4-5', 4: '6+'}
    
    for dose_bin, deltas in dose_deltas.items():
        results[dose_labels[dose_bin]] = {
            'n': len(deltas),
            'mean_delta': np.mean(deltas) if deltas else 0.0,
            'std_delta': np.std(deltas) if deltas else 0.0,
            'deltas': deltas
        }
    
    return results


async def generate_summary_report(
    db: Database,
    attribute: str = 'environmental_concern'
) -> str:
    """
    Generate a comprehensive text summary of belief change analysis.
    
    Args:
        db: Database connection
        attribute: Belief attribute
    
    Returns:
        Formatted text report
    """
    report = []
    report.append("=" * 70)
    report.append("BELIEF CHANGE ANALYSIS REPORT")
    report.append(f"Attribute: {attribute}")
    report.append("=" * 70)
    report.append("")
    
    # Primary analysis: Hope vs Fear
    report.append("PRIMARY ANALYSIS: Hope vs Fear Comparison")
    report.append("-" * 70)
    comparison = await compare_hope_vs_fear(db, attribute)
    
    hope_stats = comparison['hope']
    fear_stats = comparison['fear']
    
    report.append(f"Hope Campaign (n={hope_stats['n']})")
    report.append(f"  Mean Δ{attribute}: {hope_stats['mean_delta']:+.4f} ± {hope_stats['std_delta']:.4f}")
    report.append("")
    report.append(f"Fear Campaign (n={fear_stats['n']})")
    report.append(f"  Mean Δ{attribute}: {fear_stats['mean_delta']:+.4f} ± {fear_stats['std_delta']:.4f}")
    report.append("")
    report.append(f"Effect Size (Cohen's d): {comparison['effect_size']:.3f}")
    
    if comparison['p_value'] is not None:
        significance = "***" if comparison['p_value'] < 0.001 else "**" if comparison['p_value'] < 0.01 else "*" if comparison['p_value'] < 0.05 else "n.s."
        report.append(f"Statistical Test: t={comparison['t_statistic']:.3f}, p={comparison['p_value']:.4f} {significance}")
    report.append("")
    
    # Cascade depth analysis
    report.append("SECONDARY ANALYSIS: Cascade Depth Effects")
    report.append("-" * 70)
    depth_results = await analyze_by_cascade_depth(db, attribute)
    
    for depth in sorted(depth_results.keys()):
        stats = depth_results[depth]
        depth_label = f"Direct (depth=0)" if depth == 0 else f"Depth {depth} reshare"
        report.append(f"{depth_label} (n={stats['n']})")
        report.append(f"  Mean Δ{attribute}: {stats['mean_delta']:+.4f} ± {stats['std_delta']:.4f}")
    
    report.append("")
    report.append("=" * 70)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Quick test
    async def test():
        db = Database()
        await db.connect()
        
        report = await generate_summary_report(db)
        print(report)
        
        await db.close()
    
    asyncio.run(test())


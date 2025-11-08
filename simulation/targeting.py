"""
Stratified campaign target selection.

Ensures balanced assignment across Activity and network position to prevent
confounding variables in Hope vs Fear comparisons.
"""
from typing import List, Tuple
from collections import defaultdict
import random


def stratified_campaign_assignment(
    agents: List,
    network_graph,
    frac_hope: float = 0.1,
    frac_fear: float = 0.1,
    seed: int = 42
) -> Tuple[List[str], List[str]]:
    """
    Assign agents to Hope/Fear campaigns using stratified random sampling.
    
    Stratifies by Activity deciles × In-degree deciles to ensure:
    - Hope and Fear groups have matched Activity distributions
    - Hope and Fear groups have matched network centrality
    
    This prevents confounds where engagement differences could be attributed
    to baseline activity levels or network position rather than message framing.
    
    Args:
        agents: List of Agent objects with .agent_id and .activity attributes
        network_graph: NetworkX graph (directed) for in-degree calculation
        frac_hope: Fraction of agents to assign Hope (default 0.1 = 10%)
        frac_fear: Fraction of agents to assign Fear (default 0.1 = 10%)
        seed: Random seed for reproducible assignment
    
    Returns:
        Tuple of (hope_target_ids, fear_target_ids)
    
    Example:
        >>> hope_ids, fear_ids = stratified_campaign_assignment(
        ...     agents, graph, frac_hope=0.1, frac_fear=0.1, seed=42
        ... )
        >>> # Hope and Fear groups now have similar Activity/degree distributions
    
    Notes:
        - Remaining agents (80% by default) serve as control/indirect exposure group
        - Stratification ensures internal validity of Hope vs Fear comparison
        - Each Activity×Degree bin contributes proportionally to both conditions
    """
    rng = random.Random(seed)
    
    # Calculate degrees (BA graph is undirected, so degree = connections)
    degrees = dict(network_graph.degree())
    max_degree = max(degrees.values()) if degrees else 1
    
    # Bin agents by Activity decile × Degree decile
    bins = defaultdict(list)
    
    for agent in agents:
        # Activity decile: 0-9 (0.0-0.1 → 0, 0.1-0.2 → 1, ..., 0.9-1.0 → 9)
        act_bin = min(9, int(agent.activity * 10))
        
        # Degree decile: 0-9 (normalized by max degree)
        agent_degree = degrees.get(agent.agent_id, 0)
        deg_bin = min(9, int(agent_degree / max_degree * 10)) if max_degree > 0 else 0
        
        bins[(act_bin, deg_bin)].append(agent)
    
    # Sample from each bin proportionally
    hope_targets = []
    fear_targets = []
    
    for bin_key, bucket in bins.items():
        rng.shuffle(bucket)
        n = len(bucket)
        
        # Calculate samples per bin
        n_hope = int(n * frac_hope)
        n_fear = int(n * frac_fear)
        
        # Assign agents from this bin
        hope_targets.extend(bucket[:n_hope])
        fear_targets.extend(bucket[n_hope:n_hope + n_fear])
        # Remaining go to control (not directly targeted)
    
    return (
        [a.agent_id for a in hope_targets],
        [a.agent_id for a in fear_targets]
    )


def validate_assignment_balance(
    agents: List,
    hope_ids: List[str],
    fear_ids: List[str],
    network_graph,
    verbose: bool = True
) -> dict:
    """
    Validate that Hope and Fear groups have balanced distributions.
    
    Compares:
    - Activity distributions (should be nearly identical)
    - In-degree distributions (should be nearly identical)
    - Network centrality (should be nearly identical)
    
    Args:
        agents: All agents
        hope_ids: Agent IDs assigned to Hope
        fear_ids: Agent IDs assigned to Fear
        network_graph: NetworkX graph
        verbose: Print comparison statistics
    
    Returns:
        Dictionary with comparison metrics and pass/fail status
    """
    import numpy as np
    
    # Build agent lookup
    agent_dict = {a.agent_id: a for a in agents}
    
    # Get Activity values
    hope_activities = [agent_dict[aid].activity for aid in hope_ids]
    fear_activities = [agent_dict[aid].activity for aid in fear_ids]
    
    # Get in-degrees
    degrees = dict(network_graph.degree())
    hope_degrees = [degrees.get(aid, 0) for aid in hope_ids]
    fear_degrees = [degrees.get(aid, 0) for aid in fear_ids]
    
    # Statistical comparison
    activity_diff = abs(np.mean(hope_activities) - np.mean(fear_activities))
    degree_diff = abs(np.mean(hope_degrees) - np.mean(fear_degrees))
    
    # Acceptable thresholds
    activity_balanced = activity_diff < 0.05  # Within 5% of each other
    degree_balanced = degree_diff < (np.mean(hope_degrees) * 0.2)  # Within 20%
    
    if verbose:
        print("=" * 60)
        print("STRATIFIED ASSIGNMENT VALIDATION")
        print("=" * 60)
        print(f"\nActivity Distribution:")
        print(f"  Hope: mean={np.mean(hope_activities):.3f}, std={np.std(hope_activities):.3f}")
        print(f"  Fear: mean={np.mean(fear_activities):.3f}, std={np.std(fear_activities):.3f}")
        print(f"  Difference: {activity_diff:.3f}")
        print(f"  Status: {'✓ BALANCED' if activity_balanced else '✗ IMBALANCED'}")
        
        print(f"\nIn-Degree Distribution:")
        print(f"  Hope: mean={np.mean(hope_degrees):.1f}, std={np.std(hope_degrees):.1f}")
        print(f"  Fear: mean={np.mean(fear_degrees):.1f}, std={np.std(fear_degrees):.1f}")
        print(f"  Difference: {degree_diff:.1f}")
        print(f"  Status: {'✓ BALANCED' if degree_balanced else '✗ IMBALANCED'}")
        
        print("\n" + "=" * 60)
    
    return {
        'activity_diff': activity_diff,
        'activity_balanced': activity_balanced,
        'degree_diff': degree_diff,
        'degree_balanced': degree_balanced,
        'balanced': activity_balanced and degree_balanced,
        'hope_n': len(hope_ids),
        'fear_n': len(fear_ids)
    }


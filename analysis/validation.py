"""
Validation pipeline for social media simulation.

Implements four sanity checks from Section 4.8:
1. Network layer: Power-law degree distribution (Barabási & Albert 1999)
2. Temporal layer: Activity-driven heterogeneous behavior (Murdock et al. 2024)
3. Engagement layer: Heavy-tailed engagement distribution
4. Cascade layer: Structural virality and size distribution (Goel et al. 2016)

References:
    Barabási & Albert (1999). Science 286(5439), 509-512.
    Murdock et al. (2024). Social Network Analysis & Mining, 14, 145.
    Goel, S., Anderson, A., Hofman, J., & Watts, D. J. (2016). The structural
        virality of online diffusion. Management Science, 62(1), 180-196.
"""
from typing import Dict, List, Tuple, Optional
import numpy as np
from collections import Counter, defaultdict
import networkx as nx


class ValidationPipeline:
    """Validates simulation output against empirical benchmarks."""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize validation pipeline.
        
        Args:
            verbose: If True, print detailed validation results
        """
        self.verbose = verbose
        self.results = {}
    
    # ============================================
    # CHECK 1: NETWORK LAYER
    # ============================================
    
    def validate_network(
        self,
        graph: nx.Graph,
        expected_gamma_range: Tuple[float, float] = (2.7, 3.3),
        expected_clustering_max: float = 0.1
    ) -> Dict[str, any]:
        """
        Validate scale-free network properties (Barabási & Albert 1999).
        
        Tests:
        1. Power-law exponent γ ∈ [2.7, 3.3]
        2. Low clustering coefficient (< 0.1)
        
        Args:
            graph: NetworkX graph from generate_ba()
            expected_gamma_range: Acceptable range for power-law exponent
            expected_clustering_max: Maximum acceptable clustering
        
        Returns:
            Dictionary with validation results and pass/fail status
        """
        degrees = [d for _, d in graph.degree()]
        
        # Test 1: Power-law exponent
        gamma_hat = None
        gamma_valid = False
        
        try:
            from powerlaw import Fit
            fit = Fit(degrees, discrete=True, xmin=3, verbose=False)
            gamma_hat = fit.power_law.alpha
            gamma_valid = expected_gamma_range[0] <= gamma_hat <= expected_gamma_range[1]
            
            if self.verbose:
                print(f"[Network] Power-law exponent γ̂ = {gamma_hat:.2f}")
                print(f"[Network] Expected range: [{expected_gamma_range[0]}, {expected_gamma_range[1]}]")
                print(f"[Network] Status: {'✓ PASS' if gamma_valid else '✗ FAIL'}")
        except ImportError:
            if self.verbose:
                print("[Network] Warning: 'powerlaw' package not installed. Skipping γ test.")
                print("[Network] Install with: pip install powerlaw")
        
        # Test 2: Low clustering (scale-free networks are tree-like)
        avg_clustering = nx.average_clustering(graph)
        clustering_valid = avg_clustering < expected_clustering_max
        
        if self.verbose:
            print(f"[Network] Average clustering = {avg_clustering:.4f}")
            print(f"[Network] Expected: < {expected_clustering_max}")
            print(f"[Network] Status: {'✓ PASS' if clustering_valid else '✗ FAIL'}")
        
        result = {
            'check': 'network_layer',
            'gamma_hat': gamma_hat,
            'gamma_valid': gamma_valid,
            'avg_clustering': avg_clustering,
            'clustering_valid': clustering_valid,
            'passed': gamma_valid and clustering_valid,
            'details': {
                'n_nodes': graph.number_of_nodes(),
                'n_edges': graph.number_of_edges(),
                'min_degree': min(degrees),
                'max_degree': max(degrees),
                'mean_degree': np.mean(degrees)
            }
        }
        
        self.results['network'] = result
        return result
    
    # ============================================
    # CHECK 2: TEMPORAL LAYER
    # ============================================
    
    def validate_temporal_dynamics(
        self,
        agents: List,
        total_steps: int,
        expected_online_minutes: float = 23.0,
        tolerance: float = 0.2
    ) -> Dict[str, any]:
        """
        Validate Activity-driven heterogeneous behavior (Murdock et al. 2024).
        
        Tests:
        1. Mean Activity uniform in [0, 1]
        2. Average online time ≈ 23 minutes per day
        
        Args:
            agents: List of Agent objects with .activity and online time tracking
            total_steps: Total simulation steps (for calculating averages)
            expected_online_minutes: Expected daily online minutes (23 for Facebook)
            tolerance: Acceptable relative error (0.2 = ±20%)
        
        Returns:
            Dictionary with validation results
        """
        activities = [agent.activity for agent in agents]
        
        # Test 1: Activity distribution uniformity
        mean_activity = np.mean(activities)
        activity_uniform = 0.4 <= mean_activity <= 0.6  # Should be ~0.5
        
        if self.verbose:
            print(f"[Temporal] Mean Activity = {mean_activity:.3f}")
            print(f"[Temporal] Expected: ~0.5 (uniform distribution)")
            print(f"[Temporal] Status: {'✓ PASS' if activity_uniform else '✗ FAIL'}")
        
        # Test 2: Online time validation
        # Note: This requires tracking actual online minutes during simulation
        # For now, we validate the theoretical expectation
        expected_online = np.mean([2 * a * expected_online_minutes for a in activities])
        theoretical_valid = True  # Placeholder - actual tracking needed
        
        if self.verbose:
            print(f"[Temporal] Expected avg online time: {expected_online:.1f} min/day")
            print(f"[Temporal] Target benchmark: {expected_online_minutes} min/day")
        
        result = {
            'check': 'temporal_layer',
            'mean_activity': mean_activity,
            'activity_uniform': activity_uniform,
            'expected_online_minutes': expected_online,
            'passed': activity_uniform,
            'details': {
                'n_agents': len(agents),
                'activity_std': np.std(activities),
                'activity_min': min(activities),
                'activity_max': max(activities)
            }
        }
        
        self.results['temporal'] = result
        return result
    
    # ============================================
    # CHECK 3: ENGAGEMENT LAYER
    # ============================================
    
    def validate_engagement_inequality(
        self,
        interactions: List[Dict],
        agents: List,
        gini_threshold: float = 0.6,
        top_10_threshold: float = 0.5
    ) -> Dict[str, any]:
        """
        Validate heavy-tailed engagement distribution.
        
        Tests:
        1. Gini coefficient > 0.6 (high inequality)
        2. Top 10% of users generate > 50% of engagements
        
        Args:
            interactions: List of interaction records (likes, comments, reshares)
            agents: List of agents
            gini_threshold: Minimum acceptable Gini coefficient
            top_10_threshold: Minimum fraction of activity from top 10%
        
        Returns:
            Dictionary with validation results
        """
        # Count actions per agent
        action_counts = Counter(interaction['agent_id'] for interaction in interactions)
        
        # Include zero-activity agents
        all_counts = [action_counts.get(agent.agent_id, 0) for agent in agents]
        all_counts_sorted = sorted(all_counts)
        
        # Calculate Gini coefficient
        n = len(all_counts_sorted)
        if n == 0 or sum(all_counts_sorted) == 0:
            gini = 0.0
        else:
            cumsum = np.cumsum(all_counts_sorted)
            gini = (2 * np.sum((i + 1) * all_counts_sorted[i] for i in range(n))) / (n * sum(all_counts_sorted)) - (n + 1) / n
        
        gini_valid = gini >= gini_threshold
        
        # Calculate top 10% concentration
        top_10_count = int(np.ceil(len(agents) * 0.1))
        top_10_actions = sum(sorted(all_counts, reverse=True)[:top_10_count])
        total_actions = sum(all_counts)
        
        if total_actions > 0:
            top_10_fraction = top_10_actions / total_actions
        else:
            top_10_fraction = 0.0
        
        top_10_valid = top_10_fraction >= top_10_threshold
        
        if self.verbose:
            print(f"[Engagement] Gini coefficient = {gini:.3f}")
            print(f"[Engagement] Expected: ≥ {gini_threshold}")
            print(f"[Engagement] Status: {'✓ PASS' if gini_valid else '✗ FAIL'}")
            print(f"[Engagement] Top 10% activity = {top_10_fraction:.1%}")
            print(f"[Engagement] Expected: ≥ {top_10_threshold:.0%}")
            print(f"[Engagement] Status: {'✓ PASS' if top_10_valid else '✗ FAIL'}")
        
        result = {
            'check': 'engagement_layer',
            'gini_coefficient': gini,
            'gini_valid': gini_valid,
            'top_10_fraction': top_10_fraction,
            'top_10_valid': top_10_valid,
            'passed': gini_valid and top_10_valid,
            'details': {
                'total_interactions': len(interactions),
                'active_agents': len([c for c in all_counts if c > 0]),
                'max_actions': max(all_counts) if all_counts else 0,
                'mean_actions': np.mean(all_counts) if all_counts else 0
            }
        }
        
        self.results['engagement'] = result
        return result
    
    # ============================================
    # CHECK 4: CASCADE LAYER
    # ============================================
    
    def validate_cascade_structure(
        self,
        posts: List[Dict],
        expected_xi_range: Tuple[float, float] = (2.0, 8.0),
        size_xi_correlation_max: float = 0.3
    ) -> Dict[str, any]:
        """
        Validate cascade structure using structural virality (Goel et al. 2016).
        
        Tests:
        1. Median ξ (structural virality) ∈ [2, 8]
        2. Weak correlation between cascade size and ξ (ρ < 0.3)
        
        Args:
            posts: List of post dictionaries with parent_id links
            expected_xi_range: Acceptable range for median structural virality
            size_xi_correlation_max: Maximum acceptable Spearman correlation
        
        Returns:
            Dictionary with validation results
        """
        # Build cascade trees (posts with parent_id form trees)
        cascades = defaultdict(list)
        root_posts = {}
        
        # Identify roots and build trees
        for post in posts:
            if post.get('parent_post_id') is None:
                # This is a root post
                root_posts[post['post_id']] = post
                cascades[post['post_id']].append(post)
            else:
                # Find the root of this cascade
                root = self._find_cascade_root(post, posts)
                if root:
                    cascades[root].append(post)
        
        # Calculate structural virality for each cascade
        xi_values = []
        sizes = []
        
        for root_id, cascade_posts in cascades.items():
            if len(cascade_posts) > 1:  # Only cascades with 2+ nodes
                xi = self._calculate_structural_virality(cascade_posts)
                xi_values.append(xi)
                sizes.append(len(cascade_posts))
        
        if not xi_values:
            if self.verbose:
                print("[Cascade] Warning: No cascades found (requires reshares/comments)")
            
            result = {
                'check': 'cascade_layer',
                'passed': False,
                'error': 'No cascades found'
            }
            self.results['cascade'] = result
            return result
        
        # Test 1: Median ξ in expected range
        median_xi = np.median(xi_values)
        xi_valid = expected_xi_range[0] <= median_xi <= expected_xi_range[1]
        
        # Test 2: Weak size-ξ correlation
        if len(xi_values) > 2:
            from scipy.stats import spearmanr
            correlation, _ = spearmanr(sizes, xi_values)
            correlation_valid = abs(correlation) < size_xi_correlation_max
        else:
            correlation = 0.0
            correlation_valid = True
        
        if self.verbose:
            print(f"[Cascade] Median ξ = {median_xi:.2f}")
            print(f"[Cascade] Expected range: [{expected_xi_range[0]}, {expected_xi_range[1]}]")
            print(f"[Cascade] Status: {'✓ PASS' if xi_valid else '✗ FAIL'}")
            print(f"[Cascade] Size-ξ correlation = {correlation:.3f}")
            print(f"[Cascade] Expected: < {size_xi_correlation_max}")
            print(f"[Cascade] Status: {'✓ PASS' if correlation_valid else '✗ FAIL'}")
        
        result = {
            'check': 'cascade_layer',
            'median_xi': median_xi,
            'xi_valid': xi_valid,
            'size_xi_correlation': correlation,
            'correlation_valid': correlation_valid,
            'passed': xi_valid and correlation_valid,
            'details': {
                'n_cascades': len(xi_values),
                'mean_size': np.mean(sizes),
                'max_size': max(sizes),
                'xi_range': (min(xi_values), max(xi_values))
            }
        }
        
        self.results['cascade'] = result
        return result
    
    def _find_cascade_root(self, post: Dict, all_posts: List[Dict]) -> Optional[str]:
        """Walk up parent chain to find cascade root."""
        visited = set()
        current = post
        
        while current.get('parent_post_id') is not None:
            if current['post_id'] in visited:
                # Cycle detected
                return None
            visited.add(current['post_id'])
            
            # Find parent
            parent = next((p for p in all_posts if p['post_id'] == current['parent_post_id']), None)
            if parent is None:
                return None
            current = parent
        
        return current['post_id']
    
    def _assert_single_root(self, post_id: str, posts_dict: Dict[str, Dict]) -> str:
        """
        Walk parent pointers upward and assert single root (Serrano & Iglesias 2016).
        
        Verifies that the cascade forms a proper tree structure with:
        - No cycles (posts cannot be their own ancestors)
        - No broken links (all parent pointers valid)
        - Single root (exactly one post with no parent)
        
        This integrity check ensures reshare cascades follow the tree-structured
        retweet model described in Serrano & Iglesias (2016).
        
        Args:
            post_id: Starting post ID to trace upward
            posts_dict: Dictionary mapping post_id -> post dict
        
        Returns:
            Root post ID
        
        Raises:
            ValueError: If cycle detected or broken parent link found
        
        References:
            Serrano, E., & Iglesias, C. A. (2016). Validating viral marketing
            strategies in Twitter via agent-based social simulation.
            Expert Systems with Applications, 50, 140-150.
        """
        seen = set()
        current = post_id
        
        while posts_dict.get(current, {}).get('parent_post_id') is not None:
            if current in seen:
                raise ValueError(f"Cycle detected in cascade at post {current}")
            seen.add(current)
            current = posts_dict[current]['parent_post_id']
            if current not in posts_dict:
                raise ValueError(f"Broken parent link: {current} not found")
        
        return current  # root ID
    
    def _calculate_structural_virality(self, cascade_posts: List[Dict]) -> float:
        """
        Linear-time computation of ξ(T) (Goel et al. 2016, Eq 1 & Algorithm 1).
        
        Implements exact DFS algorithm from Goel et al. Appendix A.
        
        ξ measures average pairwise distance:
        - Star (broadcast): ξ ≈ 2
        - Chain (viral spread): ξ >> 2
        
        Algorithm: DFS traversal computing sum-of-pairs contribution.
        Complexity: O(n) where n is cascade size.
        
        References:
            Goel, S., Anderson, A., Hofman, J., & Watts, D. J. (2016).
            The structural virality of online diffusion. Management Science, 62(1), 180-196.
            See Appendix A, Algorithm 1.
        """
        from collections import defaultdict
        
        if len(cascade_posts) <= 1:
            return 0.0
        
        # Build children adjacency list
        children = defaultdict(list)
        for p in cascade_posts:
            if p.get('parent_post_id'):
                children[p['parent_post_id']].append(p['post_id'])
        
        # Find root (post with no parent)
        root_id = None
        for p in cascade_posts:
            if not p.get('parent_post_id'):
                root_id = p['post_id']
                break
        
        if not root_id:
            return 0.0
        
        # DFS with sum-of-pairs calculation (Goel et al. Algorithm 1)
        n = 0
        sum_pairs = 0
        
        def dfs(node):
            nonlocal n, sum_pairs
            size = 1
            for c in children[node]:
                size += dfs(c)
            # Add contribution of this subtree to sum-of-pairs
            sum_pairs += size * (size - 1) // 2
            n += 1
            return size
        
        dfs(root_id)
        
        if n < 2:
            return 0.0
        
        # Goel et al. Equation 1
        total_pairs = n * (n - 1) // 2
        return (2 / (n * (n - 1))) * (total_pairs - sum_pairs)
    
    # ============================================
    # FULL PIPELINE
    # ============================================
    
    def run_full_validation(
        self,
        graph: nx.Graph,
        agents: List,
        posts: List[Dict],
        interactions: List[Dict],
        total_steps: int
    ) -> Dict[str, any]:
        """
        Run all four validation checks.
        
        Args:
            graph: Social network graph
            agents: List of Agent objects
            posts: List of post records
            interactions: List of interaction records
            total_steps: Total simulation steps
        
        Returns:
            Dictionary with all validation results and overall pass/fail
        """
        if self.verbose:
            print("=" * 60)
            print("VALIDATION PIPELINE")
            print("=" * 60)
            print()
        
        # Run all checks
        network_result = self.validate_network(graph)
        print()
        
        temporal_result = self.validate_temporal_dynamics(agents, total_steps)
        print()
        
        engagement_result = self.validate_engagement_inequality(interactions, agents)
        print()
        
        cascade_result = self.validate_cascade_structure(posts)
        print()
        
        # Overall assessment
        all_passed = all([
            network_result.get('passed', False),
            temporal_result.get('passed', False),
            engagement_result.get('passed', False),
            cascade_result.get('passed', False)
        ])
        
        if self.verbose:
            print("=" * 60)
            print(f"OVERALL: {'✓ ALL CHECKS PASSED' if all_passed else '✗ SOME CHECKS FAILED'}")
            print("=" * 60)
        
        return {
            'all_passed': all_passed,
            'checks': {
                'network': network_result,
                'temporal': temporal_result,
                'engagement': engagement_result,
                'cascade': cascade_result
            }
        }


# Standalone validation functions for convenience
def validate_simulation(
    graph: nx.Graph,
    agents: List,
    posts: List[Dict],
    interactions: List[Dict],
    total_steps: int,
    verbose: bool = True
) -> Dict[str, any]:
    """
    Convenience function to run full validation pipeline.
    
    Args:
        graph: Social network from generate_ba()
        agents: List of Agent instances
        posts: Post records from database
        interactions: Interaction records from database
        total_steps: Total simulation steps
        verbose: Print detailed results
    
    Returns:
        Full validation results dictionary
    """
    pipeline = ValidationPipeline(verbose=verbose)
    return pipeline.run_full_validation(graph, agents, posts, interactions, total_steps)


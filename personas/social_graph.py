"""
Social graph generation using Barabási-Albert preferential attachment.

Implementation based on:
Barabási, A.-L., & Albert, R. (1999). Emergence of scaling in random networks.
Science, 286(5439), 509-512. https://doi.org/10.1126/science.286.5439.509
"""
import networkx as nx
import random
from typing import List, Tuple
from collections import Counter


def generate_ba(n: int, m0: int = 5, m: int = 8, seed: int = 42) -> nx.Graph:
    """
    Barabási–Albert preferential attachment generator.
    
    Implements the canonical scale-free network generation algorithm
    (Barabási & Albert, 1999). The network grows by adding one node per step;
    each new node attaches to m existing nodes with probability proportional
    to their current degree (P(i) ∝ k_i).
    
    This process produces a scale-free degree distribution with exponent γ ≈ 3,
    matching the structure observed in real social networks including Twitter,
    Facebook, and scientific collaboration networks.
    
    Parameters
    ----------
    n : int
        Final number of nodes (agents) in the network.
    m0 : int, optional
        Size of the fully connected seed clique (must satisfy m0 ≥ m).
        Default is 5.
    m : int, optional
        Number of edges added by each new node. Controls network density
        and average degree. Default is 8 (typical for social media).
    seed : int, optional
        Random number generator seed for reproducibility. Default is 42.
    
    Returns
    -------
    G : networkx.Graph
        Undirected scale-free network where nodes represent agents and
        edges represent follower relationships. Node attributes include
        'join_step' indicating when the node was added to the network.
    
    Notes
    -----
    The resulting degree distribution follows P(k) ∼ k^(-γ) where γ ≈ 3.
    This can be validated using power-law fitting (see validate_ba_network).
    
    Examples
    --------
    >>> G = generate_ba(n=1000, m=8, seed=42)
    >>> degrees = [d for _, d in G.degree()]
    >>> max(degrees)  # Should see hub nodes with high degree
    
    References
    ----------
    Barabási, A.-L., & Albert, R. (1999). Emergence of scaling in random networks.
    Science, 286(5439), 509-512.
    """
    if m0 < m:
        raise ValueError(f"Seed size m0={m0} must be at least m={m}")
    if n < m0:
        raise ValueError(f"Network size n={n} must be at least seed size m0={m0}")
    
    rng = random.Random(seed)
    
    # Step 1: Create fully connected seed clique
    G = nx.complete_graph(m0)
    for node in G.nodes():
        G.nodes[node]['join_step'] = node
    
    # Step 2: Track all nodes available for attachment
    targets = list(G.nodes())
    
    # Step 3: Growth phase - add nodes one at a time
    for new_node in range(m0, n):
        # Preferential attachment: P(i) ∝ degree(i)
        weights = [G.degree(target) for target in targets]
        
        # Select m targets with replacement (following BA paper)
        # Note: Using choices() allows the same node to be picked multiple times,
        # but we only create one edge per unique target
        chosen = rng.choices(targets, weights=weights, k=m)
        chosen_unique = list(set(chosen))  # Remove duplicates
        
        # Add new node
        G.add_node(new_node, join_step=new_node)
        
        # Create edges to chosen targets
        G.add_edges_from((new_node, target) for target in chosen_unique)
        
        # Add new node to pool of potential targets
        targets.append(new_node)
    
    return G


def validate_ba_network(G: nx.Graph, verbose: bool = True) -> dict:
    """
    Validate that generated network exhibits scale-free properties.
    
    Performs two statistical tests described in Barabási & Albert (1999):
    1. Power-law exponent γ should be close to 3 (between 2.7 and 3.3)
    2. Network should have low clustering (scale-free networks lack triangles)
    
    Parameters
    ----------
    G : networkx.Graph
        Network to validate (output of generate_ba)
    verbose : bool, optional
        If True, print validation results. Default is True.
    
    Returns
    -------
    results : dict
        Dictionary containing:
        - 'gamma_hat': Estimated power-law exponent
        - 'gamma_valid': Whether γ is in acceptable range [2.7, 3.3]
        - 'avg_clustering': Average clustering coefficient
        - 'clustering_valid': Whether clustering < 0.1 (scale-free criterion)
        - 'max_degree': Maximum degree (identifies hub nodes)
        - 'avg_degree': Average degree
    
    Notes
    -----
    Requires the 'powerlaw' package for maximum-likelihood fitting:
        pip install powerlaw
    
    If powerlaw is not installed, gamma estimation will be skipped.
    
    Examples
    --------
    >>> G = generate_ba(10000, m=8, seed=42)
    >>> results = validate_ba_network(G)
    >>> assert results['gamma_valid'], "Network does not exhibit scale-free properties"
    
    References
    ----------
    Barabási & Albert (1999), Science 286(5439), 509-512.
    Clauset, A., Shalizi, C. R., & Newman, M. E. (2009). Power-law distributions
    in empirical data. SIAM Review, 51(4), 661-703.
    """
    degrees = [d for _, d in G.degree()]
    
    # Test 1: Power-law exponent
    gamma_hat = None
    gamma_valid = False
    
    try:
        from powerlaw import Fit
        fit = Fit(degrees, discrete=True, xmin=3, verbose=False)
        gamma_hat = fit.power_law.alpha
        gamma_valid = 2.7 <= gamma_hat <= 3.3
        
        if verbose:
            print(f"Power-law exponent γ̂ = {gamma_hat:.2f} (expected ≈ 3.0)")
            if gamma_valid:
                print("✓ Exponent within acceptable range [2.7, 3.3]")
            else:
                print("✗ Exponent outside expected range")
    except ImportError:
        if verbose:
            print("Warning: 'powerlaw' package not installed. Skipping γ estimation.")
            print("Install with: pip install powerlaw")
    
    # Test 2: Low clustering (scale-free networks are tree-like)
    avg_clustering = nx.average_clustering(G)
    clustering_valid = avg_clustering < 0.1
    
    if verbose:
        print(f"Average clustering = {avg_clustering:.4f} (expected < 0.1)")
        if clustering_valid:
            print("✓ Low clustering confirms scale-free structure")
        else:
            print("✗ High clustering suggests non-scale-free structure")
    
    # Additional statistics
    max_degree = max(degrees)
    avg_degree = sum(degrees) / len(degrees)
    
    if verbose:
        print(f"Network size: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
        print(f"Degree range: [{min(degrees)}, {max_degree}], average = {avg_degree:.2f}")
    
    return {
        'gamma_hat': gamma_hat,
        'gamma_valid': gamma_valid,
        'avg_clustering': avg_clustering,
        'clustering_valid': clustering_valid,
        'max_degree': max_degree,
        'avg_degree': avg_degree,
        'n_nodes': G.number_of_nodes(),
        'n_edges': G.number_of_edges()
    }


def convert_to_directed_follows(G: nx.Graph, agent_ids: List[str]) -> List[Tuple[str, str]]:
    """
    Convert undirected BA graph to directed follower relationships.
    
    In social media, follower relationships are directed (A follows B ≠ B follows A).
    This function converts the undirected BA graph to directed edges by randomly
    orienting each edge, maintaining the degree distribution while creating
    realistic asymmetric follower patterns.
    
    Parameters
    ----------
    G : networkx.Graph
        Undirected graph from generate_ba()
    agent_ids : List[str]
        List of agent ID strings to map to graph nodes
    
    Returns
    -------
    follows : List[Tuple[str, str]]
        List of (follower_id, followee_id) tuples representing directed
        follower relationships
    
    Notes
    -----
    Each undirected edge is converted to a directed edge with 50% probability
    in each direction. This preserves the scale-free in-degree distribution
    while creating realistic social network asymmetry.
    """
    if len(agent_ids) != G.number_of_nodes():
        raise ValueError(f"Number of agent IDs ({len(agent_ids)}) must match "
                        f"graph nodes ({G.number_of_nodes()})")
    
    follows = []
    node_to_agent = {i: agent_ids[i] for i in range(len(agent_ids))}
    
    for u, v in G.edges():
        # Randomly orient each edge
        if random.random() < 0.5:
            follows.append((node_to_agent[u], node_to_agent[v]))
        else:
            follows.append((node_to_agent[v], node_to_agent[u]))
    
    return follows


def get_graph_statistics(G: nx.Graph) -> dict:
    """
    Calculate comprehensive statistics about the social graph.
    
    Parameters
    ----------
    G : networkx.Graph
        Social network graph
    
    Returns
    -------
    stats : dict
        Dictionary containing network statistics:
        - Basic counts (nodes, edges)
        - Degree statistics (min, max, mean, median)
        - Structural properties (clustering, connected components)
    """
    degrees = [d for _, d in G.degree()]
    
    return {
        'n_nodes': G.number_of_nodes(),
        'n_edges': G.number_of_edges(),
        'min_degree': min(degrees) if degrees else 0,
        'max_degree': max(degrees) if degrees else 0,
        'mean_degree': sum(degrees) / len(degrees) if degrees else 0,
        'median_degree': sorted(degrees)[len(degrees) // 2] if degrees else 0,
        'avg_clustering': nx.average_clustering(G),
        'n_components': nx.number_connected_components(G)
    }


# Quick validation script
if __name__ == "__main__":
    print("=" * 60)
    print("Barabási-Albert Network Generator Validation")
    print("=" * 60)
    
    # Generate network
    print("\nGenerating network with n=10,000 nodes, m=8 edges per node...")
    G = generate_ba(n=10_000, m0=8, m=8, seed=42)
    
    print("\nValidation Results:")
    print("-" * 60)
    results = validate_ba_network(G, verbose=True)
    
    print("\n" + "=" * 60)
    if results['gamma_valid'] and results['clustering_valid']:
        print("✓ All validation checks passed")
        print("Network exhibits canonical scale-free properties")
    else:
        print("✗ Some validation checks failed")
        print("Review parameter settings or regenerate network")
    print("=" * 60)

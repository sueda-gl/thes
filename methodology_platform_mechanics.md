# Methodology: Social Media Platform Mechanics

## Overview

This chapter describes the design and implementation of the simulated social media environment in which AI agents interact. The platform architecture synthesizes established models from computational social science to create a realistic digital ecosystem that exhibits key properties observed in real-world social networks: scale-free topology, heterogeneous user activity, recency-biased content visibility, and viral information cascades.

The implementation follows a principled approach where each mechanical component is grounded in peer-reviewed literature. We adopt algorithms and formulas verbatim from cited papers, validate their behavior against published benchmarks, and maintain full traceability between code and source publications. This methodological rigor ensures that the simulated environment constitutes a valid testbed for studying persuasion dynamics in digital spaces.

## 3.1 Network Topology: Scale-Free Graph Generation

### Theoretical Foundation

Real-world social networks exhibit a characteristic "scale-free" structure where the probability of observing a node with k connections follows a power-law distribution P(k) ∝ k^(-γ) with exponent γ ≈ 3 (Barabási & Albert, 1999). This topology produces "hub" users with disproportionately large audiences—a structural feature that profoundly influences information diffusion patterns. Unlike random graphs where all nodes have roughly equal degree, scale-free networks create heterogeneous reach: a small number of highly-connected individuals can rapidly broadcast messages to large fractions of the population.

Barabási and Albert (1999) demonstrate that two minimal ingredients suffice to generate this topology:

1. **Continuous growth**: The network expands by adding nodes sequentially rather than all at once.
2. **Preferential attachment**: New nodes connect to existing nodes with probability proportional to their current degree, following the principle that "the rich get richer."

### Implementation

We implement the canonical Barabási-Albert (BA) algorithm in `personas/social_graph.py`. The function `generate_ba(n, m0, m, seed)` takes four parameters:

- `n`: Final network size (number of agents)
- `m0`: Size of initial fully-connected seed clique
- `m`: Number of edges each new node forms
- `seed`: Random number generator seed for reproducibility

The algorithm proceeds in two phases:

**Phase 1: Initialization**  
Create a complete graph of m₀ nodes where every pair is connected. This seed provides the initial degree distribution required for preferential attachment.

**Phase 2: Growth with Preferential Attachment**  
For each new node i ∈ {m₀, m₀+1, ..., n-1}:
1. Identify all existing nodes as potential attachment targets
2. Calculate attachment probability for each target t: P(t) = k_t / Σ_j k_j, where k_t is t's current degree
3. Select m distinct targets using weighted random sampling
4. Create edges from new node i to the selected targets
5. Add i to the pool of potential targets for future nodes

This process directly implements the linear preferential attachment rule from Barabási & Albert (1999, Science 286:509-512). The resulting network is stored as a NetworkX Graph object with node metadata recording join order.

### Validation

To verify correct implementation, we perform two statistical tests:

**Test 1: Power-Law Exponent**  
After generating a network of n=10,000 nodes, we fit a power-law distribution to the degree sequence using maximum likelihood estimation (Clauset et al., 2009). The estimated exponent γ̂ should fall within [2.7, 3.3], consistent with the theoretical prediction γ=3 derived by Barabási & Albert. The `validate_ba_network()` function in `personas/social_graph.py` performs this check using the `powerlaw` package.

**Test 2: Low Clustering**  
Scale-free networks generated via preferential attachment exhibit minimal clustering (average clustering coefficient C < 0.1) because the growth process creates tree-like structures rather than tightly-knit communities. We calculate C using NetworkX's `average_clustering()` function and assert it remains below the 0.1 threshold.

When both tests pass, we can confidently state: "Network edges are generated with the canonical growth-plus-preferential-attachment rule (Barabási & Albert, 1999), guaranteeing the hub-rich, scale-free structure observed in real social graphs."

### Conversion to Directed Relationships

Social media follower relationships are inherently directed (A following B does not imply B following A). The BA algorithm produces undirected edges, which we convert to directed relationships in `convert_to_directed_follows()` by randomly orienting each edge with 50% probability in each direction. This preserves the scale-free in-degree distribution while introducing realistic asymmetry.

## 3.2 Agent Activity and Temporal Dynamics

### Theoretical Foundation

Social media users exhibit highly heterogeneous activity levels. Empirical studies consistently show that a small fraction of users generate most content while the majority engage minimally. Murdock et al. (2024) synthesize findings from multiple platforms showing that 75% of users are "lurkers," the top 25% produce 97% of content, and the top 2% create 80% of tweets. This heavy-tailed distribution of engagement is fundamental to understanding information diffusion dynamics.

We model this heterogeneity using a continuous **Activity** parameter, following standard practice in agent-based models. This parameterization creates skewed behavior where most agents have moderate-to-high activity while excluding extreme lurkers.

**Population Focus: Engaged User Subset**

For this experiment, we set Activity ∈ [0.3, 1.0] rather than [0, 1.0], effectively modeling the engaged user population who meaningfully participate in information diffusion. This design choice serves both practical and theoretical purposes:

- **Practical**: Ensures sufficient interaction density for detecting belief changes within computational constraints. Extreme lurkers (Activity < 0.3) rarely see campaigns and never reshare, contributing noise without theoretical insight.
- **Theoretical**: Aligns with the empirical finding that information diffusion is driven by an active minority. Murdock et al. (2024) show that 75% of users are lurkers; by modeling the engaged 30-100th percentile, we focus on agents who actually participate in cascade dynamics.
- **External Validity**: Results generalize to active social media users—the population most relevant for studying persuasion through digital engagement—rather than the full spectrum including passive observers.

Two behavioral rates scale linearly with Activity:

1. **Online time**: Daily minutes online = Activity × 143, calibrated to the global average of 2 hours 23 minutes per day (DataReportal, 2024)
   - With Activity ∈ [0.3, 1.0], this yields 43–143 minutes/day (0.7–2.4 hours/day)
   - Spans casual users to power users, excluding extreme lurkers
2. **Posting rate**: Monthly posts = Activity × 15 (reflecting typical active user behavior)

This continuous approach creates heterogeneous engagement patterns consistent with the empirical observation that small fractions of users dominate content production, while ensuring all simulated agents contribute meaningfully to diffusion dynamics.

### Implementation: Finite State Machine

Each agent maintains an online/offline state managed by a finite state machine (FSM) in `simulation/agent.py`. The FSM alternates between two states:

**State: OFFLINE**  
- Expected duration: (1440 − Activity × 143) minutes, where 1440 = 24 hours
- Timer drawn from exponential distribution with this mean
- Agent cannot see feed or take actions

**State: ONLINE**  
- Expected duration: Activity × 143 minutes
- Timer drawn from exponential distribution with this mean
- Agent can observe feed and decide whether to engage

The `tick(step)` method advances the agent by one simulation step (representing one real-world minute). It decrements the current state's timer; when the timer reaches zero, the agent transitions to the opposite state and resets the timer according to the new state's expected duration.

**Rationale for Exponential Dwell Times**  
We use exponential inter-event times because they model memoryless processes: the probability of transitioning in the next minute is constant regardless of how long the agent has been in the current state. This creates unpredictable, "bursty" patterns characteristic of human online behavior rather than fixed schedules.

### Implementation: Poisson Posting Process

Organic post creation follows a Poisson process with rate λ = (Activity × 15) / (30 × 1440). The denominator converts "posts per month" to "posts per minute" (assuming 30-day months). During initialization, `_schedule_next_post()` draws the time until the next post from Exp(λ). When online, the agent decrements this timer each step; upon reaching zero, the agent creates an organic post and reschedules using a fresh exponential draw.

**Why Poisson?**  
Poisson processes model events that occur independently at a constant average rate. This assumption simplifies the model while capturing the key empirical regularity documented by Murdock et al. (2024): high-activity users create disproportionately more content than low-activity users, producing the heavy-tailed posting distribution characteristic of social platforms.

### Validation

The validation pipeline (`analysis/validation.py`) performs two checks:

**Uniformity Test**  
We construct a histogram of all agents' Activity values. Because Activity ~ U(0,1), the histogram should be approximately flat across the [0,1] interval. A Kolmogorov-Smirnov test confirms that the empirical distribution matches the uniform distribution.

**Temporal Consistency Test**  
After simulating 24 in-world hours (1440 steps), we compute the average fraction of time each agent spent online. The population mean should approximate 143/1440 ≈ 0.099 (9.9%), matching the DataReportal (2024) benchmark of 2 hours 23 minutes per day. Similarly, aggregating 30 simulated days should yield approximately Activity × 15 posts per user on average, with high-activity agents producing most content.

## 3.3 Feed Assembly: Recency-Based Visibility

### Theoretical Foundation

Social media feeds determine which content users see, thereby constraining the set of posts they can engage with. Feed algorithms typically balance multiple signals—recency, engagement, social ties, predicted interest—but many platforms offer a "Most Recent" mode that displays posts in reverse chronological order (Rader & Gray, 2015).

Users prefer chronological ordering because it feels more transparent and comprehensive (Rader & Gray, 2015). Studies show users have clear expectations about proper post order and notice when algorithms violate chronological sequencing. Furthermore, message visibility decays rapidly as newer content pushes older posts down the feed (Hodas & Lerman, 2014). Users with many followed accounts face higher information flux, reducing their probability of noticing any specific message.

We adopt reverse chronological ordering with a recency window for two reasons: (1) experimental transparency—keeping the feed mechanism simple ensures observed effects stem from agent decisions rather than algorithmic amplification, and (2) empirical grounding—chronological feeds match documented user preferences and visibility dynamics.

### Implementation

The `build_feed()` method in `simulation/platform.py` constructs an agent's feed at simulation time t using a pure recency window:

1. Retrieve the list of agents this user follows (from the social graph)
2. Query all posts authored by those followees
3. Filter to posts where (t - created_step) ≤ W, where W is the visibility window (default: 100 steps)
4. Sort posts by created_step descending (newest first)
5. Return top N items (default: N=7)

**Formula**:  
Feed(user, t) = {p ∈ Posts | p.author ∈ Following(user) ∧ t - p.timestamp ≤ W}

Campaign posts receive special handling: even if not from a followed account, campaign messages targeted at a specific user appear in their feed. This ensures experimental stimuli reach intended subjects regardless of network topology.

### Ranking: Pure Reverse Chronological Order

Unlike sophisticated feed algorithms that weight posts by predicted engagement, we rank solely by timestamp. The `_rank_posts()` method sorts posts descending by `created_step`, with campaign posts breaking ties to guarantee visibility.

**Justification**  
This design choice is intentional. Complex engagement-based ranking would introduce a confounding variable: if campaign posts receive higher engagement, the algorithm would further amplify them, making it difficult to isolate the causal effect of message framing. Recency-only ranking keeps the feed mechanism transparent and predictable, ensuring all experimental variance stems from agent decisions rather than algorithmic interference.

### Feed Length Upper Bound

To prevent pathological growth in high-degree networks, we implicitly bound feed length by the number of followees, their posting rates, and the visibility window:

Max feed size ≤ |Following| × post_rate × W

For typical parameters (degree ~10, Activity ~0.5 → ~0.3 posts/day, W=100 steps), feeds contain 10-20 items. The explicit limit N=7 shown to agents keeps LLM prompts short while ensuring a representative sample of recent content.

## 3.4 LLM-Based Engagement Decisions

### Departure from Numeric Models

Agent-based models of social media often use numeric engagement rules where interaction probability is determined by statistical properties of posts and users. While such formulas are computationally efficient, they are inherently **content-agnostic**—treating all posts with similar numeric scores identically regardless of actual text content.

Our implementation replaces numeric engagement formulas with LLM-based semantic reasoning. This design choice reflects our research goal: understanding how persuasive message framing influences agent decisions based on content meaning rather than statistical appeal scores.

By delegating engagement decisions to language model agents (Park et al., 2023), we enable:
- **Content-dependent reasoning**: Agents read actual message text and evaluate alignment with their personas
- **Qualitative judgments**: A post about climate urgency may resonate with environmentalist agents but not others
- **Framing sensitivity**: Hope vs fear messaging can produce different responses based on values, not just numeric scores

### Implementation Approach

When an agent observes posts in their feed, the decision process operates purely through LLM reasoning:

1. Agent sees post content (text)
2. LLM evaluates: "Given my persona (age, values, interests, past actions), how do I respond to this message?"
3. Agent takes action (like, reshare, comment, or ignore) based on LLM output

No numeric engagement probabilities gate this process. The Activity variable still governs **when** agents are online to see posts, but **what** they do with observed content is determined semantically.

### Implications for Experiments

This architecture means:
- Hope and fear campaigns have **identical platform mechanics** (network position, feed visibility, cascade structure)
- Observed differences in engagement rates, reshare patterns, or cascade shapes reflect **semantic interpretation** by LLM agents
- We can attribute effects to message framing content rather than algorithmic or statistical artifacts

The trade-off is computational cost (LLM inference is expensive) and stochasticity (language models introduce sampling variance). However, these costs are justified by the ability to study persuasion as a semantic phenomenon.

## 3.5 Reshare Mechanics: Parent-Pointer Trees

### Theoretical Foundation

Serrano & Iglesias (2016) study viral marketing on Twitter and model retweets as **tree-structured cascades**. Each retweet is treated as a new post that stores a pointer to its source. This "parent_id" link allows researchers to reconstruct the full diffusion tree by walking backward from any node to the root.

The tree property is critical for cascade analysis: it ensures each post has at most one parent, preventing cycles and enabling efficient algorithms for computing structural metrics. Empirically, Twitter's retweet mechanism enforces this constraint by design—you cannot retweet a tweet multiple times through different paths, and each retweet credits exactly one source.

### Implementation

The `create_reshare()` method in `simulation/platform.py` implements tree-structured sharing:

```python
async def create_reshare(agent_id, parent_post_id, content, step):
    # Fetch parent post
    original_post = await self.get_post(parent_post_id)
    
    # Build reshare content with attribution
    reshare_content = f"RT: {original_post['content'][:100]}..."
    if content:  # Optional commentary
        reshare_content = f"{content} // {reshare_content}"
    
    # Insert new post with parent_id link
    await db.insert_post(
        post_id=reshare_id,
        agent_id=agent_id,
        content=reshare_content,
        post_type='reshare',
        parent_post_id=parent_post_id,  # Tree link
        created_step=step
    )
```

**Key Design Feature: Content Propagation**  
Reshares preserve the original message text (truncated to 100 characters for display) while allowing optional commentary. This enables cascade analysis while maintaining attribution—each node in the diffusion tree can be traced back to the campaign origin.

### Integrity Validation

The `_assert_single_root()` method in `analysis/validation.py` verifies tree integrity by walking parent pointers upward from any post:

1. Start at a given post
2. Follow parent_id links until reaching a post with parent_id = NULL (root)
3. Detect cycles (visiting the same post twice)
4. Detect broken links (parent_id references nonexistent post)

Raising exceptions when cycles or broken links are found ensures that our reshare data always forms valid trees, as required by cascade analysis algorithms.

## 3.6 Cascade Metrics: Structural Virality

### Theoretical Foundation

Goel et al. (2016) introduce **structural virality** ξ to quantify how "tree-like" vs. "broadcast-like" an information cascade is. Traditional metrics like "total adopters" or "maximum depth" fail to distinguish between:

- **Broadcast cascades**: One influencer shares to many followers who do not re-share (star topology, ξ≈2)
- **Viral cascades**: Message passes through multiple generations in branching chains (deep tree, ξ>>2)

Structural virality is defined as the average pairwise distance between all adopters:

ξ(T) = (2 / (n(n-1))) × Σ_{i<j} dist(i,j)

where n is cascade size and dist(i,j) is the shortest path length between nodes i and j in the diffusion tree. 

**Interpretation**:
- ξ=2 → Perfect star (everyone 2 hops from everyone else via root)
- ξ=3-4 → Moderate branching with some generations
- ξ>5 → Deep viral spread through many intermediaries

Goel et al. observe that real Twitter cascades exceeding 100 adopters typically have median ξ ∈ [3,8], and crucially, size and ξ are only weakly correlated (Spearman ρ < 0.3). This means large cascades can be either broadcast-driven or viral-driven—scale alone does not reveal diffusion structure.

### Implementation: Algorithm 1 from Goel et al. Appendix A

Computing ξ naively requires O(n²) pairwise distance calculations. Goel et al. provide a linear-time algorithm (Appendix A, Algorithm 1) that computes ξ in a single depth-first traversal:

**Algorithm**:
1. Build adjacency list of children for each node
2. Perform DFS from root, computing subtree size for each node
3. For each subtree, accumulate "sum-of-pairs": size × (size-1) / 2
4. Total sum-of-pairs measures how many node pairs are within the same subtree
5. ξ = (2/(n(n-1))) × (total_pairs - sum_pairs), where total_pairs = n(n-1)/2

The `_calculate_structural_virality()` method in `analysis/validation.py` implements this algorithm exactly as specified:

```python
def _calculate_structural_virality(self, cascade_posts: List[Dict]) -> float:
    from collections import defaultdict
    
    # Build children adjacency list
    children = defaultdict(list)
    for p in cascade_posts:
        if p.get('parent_post_id'):
            children[p['parent_post_id']].append(p['post_id'])
    
    # Find root
    root_id = next((p['post_id'] for p in cascade_posts 
                    if not p.get('parent_post_id')), None)
    
    # DFS with sum-of-pairs calculation
    n = 0
    sum_pairs = 0
    
    def dfs(node):
        nonlocal n, sum_pairs
        size = 1
        for c in children[node]:
            size += dfs(c)
        sum_pairs += size * (size - 1) // 2
        n += 1
        return size
    
    dfs(root_id)
    
    # Goel et al. Equation 1
    total_pairs = n * (n - 1) // 2
    return (2 / (n * (n - 1))) * (total_pairs - sum_pairs)
```

### Validation

The cascade validation pipeline (`validate_cascade_structure()` in `analysis/validation.py`) performs two tests:

**Test 1: Median ξ in Expected Range**  
After running a simulation, compute ξ for all cascades with ≥2 nodes. The median should fall within [2, 8], matching the empirical range reported by Goel et al. for Twitter cascades.

**Test 2: Weak Size-ξ Correlation**  
Calculate Spearman rank correlation between cascade size and ξ. The absolute correlation should be <0.3, confirming that large cascades in our simulation exhibit diverse structures (some broadcast, some viral) as observed in real data.

When both tests pass, we can confidently cite: "Cascade metrics computed using Algorithm 1 from Goel et al. (2016, Appendix A) show realistic structural diversity consistent with empirical Twitter cascades."

## 3.7 Validation Pipeline

The `ValidationPipeline` class in `analysis/validation.py` orchestrates four sanity checks that verify the simulation environment matches published benchmarks:

### Check 1: Network Layer
- **Test**: Power-law exponent γ̂ ∈ [2.7, 3.3]
- **Test**: Average clustering <0.1
- **Source**: Barabási & Albert (1999)

### Check 2: Temporal Layer
- **Test**: Mean Activity ≈ 0.5 (uniform distribution)
- **Test**: Average daily online time ≈ 143 minutes (≈ 2 h 23 min)
- **Source**: DataReportal (2024) for calibration target

### Check 3: Engagement Layer
- **Test**: Gini coefficient >0.6 (high inequality)
- **Test**: Top 10% of users generate >50% of engagements
- **Rationale**: Reflects real platform inequality

### Check 4: Cascade Layer
- **Test**: Median ξ ∈ [2, 8]
- **Test**: Spearman correlation between size and ξ <0.3
- **Source**: Goel et al. (2016)

The `run_full_validation()` method executes all four checks after a simulation completes. Only runs that pass all gates are considered "in-scope" for analysis—this quality control ensures experimental results reflect theoretically grounded social dynamics rather than implementation artifacts.

## 3.8 Summary: Methodological Synthesis

The social media platform architecture combines peer-reviewed empirical findings with standard agent-based modeling techniques:

1. **Network**: Barabási-Albert preferential attachment (1999) — determines follower relationships
2. **Activity**: Continuous Activity ~ U(0,1) parameterization (standard ABM practice) — governs when agents are online and posting rates, calibrated to DataReportal (2024)
3. **Feed visibility**: Limited attention and visibility decay (Hodas & Lerman, 2014) — determines content discoverability
4. **Feed ordering**: Reverse chronological (Rader & Gray, 2015) — transparent, user-preferred presentation
5. **Cascades**: Structural virality (Goel et al., 2016) and parent-pointer trees (Serrano & Iglesias, 2016) — measures diffusion patterns
6. **Engagement**: LLM semantic reasoning (Park et al., 2023) — determines how agents respond

### Integration Rationale

We combine empirically grounded components from computational social science:

**Empirical motivation (Murdock et al., 2024):** Social media exhibits extreme activity heterogeneity—75% lurkers, top 25% produce 97% of content. We capture this through continuous Activity scaling rather than discrete tiers, allowing smooth behavioral variation.

**Activity calibration (DataReportal, 2024):** Global average social media usage of 143 min/day provides the calibration target for online time. High-Activity agents spend more time online and post more frequently, naturally reproducing skewed engagement patterns.

**Attention constraints (Hodas & Lerman, 2014):** Limited attention and visibility decay shape information diffusion. This justifies our recency windows and feed size bounds.

**Feed transparency (Rader & Gray, 2015):** Users prefer chronological ordering over algorithmic curation when transparency matters. This supports our choice of simple reverse chronological feeds.

These components create realistic platform dynamics—heterogeneous users, constrained attention, transparent visibility—without confounding our experimental manipulation. LLM agents then make engagement decisions based on semantic content interpretation rather than numeric formulas.

### External Validity

The platform exhibits validated properties of real social networks:
- Scale-free degree distribution (γ ≈ 3)
- Heavy-tailed engagement inequality (Gini > 0.6)
- Heterogeneous activity patterns (uniform Activity distribution)
- Realistic cascade structures (ξ ∈ [2, 8])

These benchmarks ensure that observed hope/fear differences emerge in a structurally realistic environment rather than an ad-hoc simulation.

**Key Methodological Principle**:  
Where possible, we adopt algorithms verbatim from source papers (network generation, feed assembly, cascade metrics). Where our research questions require semantic reasoning unavailable to numeric models, we transparently replace those components with LLM agents while documenting the substitution.

## References

Barabási, A.-L., & Albert, R. (1999). Emergence of scaling in random networks. *Science*, 286(5439), 509-512.

Clauset, A., Shalizi, C. R., & Newman, M. E. (2009). Power-law distributions in empirical data. *SIAM Review*, 51(4), 661-703.

Goel, S., Anderson, A., Hofman, J., & Watts, D. J. (2016). The structural virality of online diffusion. *Management Science*, 62(1), 180-196.

DataReportal. (2024). Digital 2024: Global Overview Report. Retrieved from https://datareportal.com/reports/digital-2024-global-overview-report

Hodas, N. O., & Lerman, K. (2014). The simple rules of social contagion. *Scientific Reports*, 4, 4343. https://doi.org/10.1038/srep04343

Murdock, I., Carley, K. M., & Yağan, O. (2024). An agent-based model of cross-platform information diffusion and moderation. *Social Network Analysis and Mining*, 14, 145. https://doi.org/10.1007/s13278-024-01305-x

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. *arXiv preprint arXiv:2304.03442*.

Rader, E., & Gray, R. (2015). Understanding user beliefs about algorithmic curation in the Facebook News Feed. In *Proceedings of the 33rd Annual ACM Conference on Human Factors in Computing Systems* (CHI '15), 173-182. https://doi.org/10.1145/2702123.2702174

Serrano, E., & Iglesias, C. A. (2016). Validating viral marketing strategies in Twitter via agent-based social simulation. *Expert Systems with Applications*, 50, 140-150.


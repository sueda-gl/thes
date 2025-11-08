# Experiment Design: Hope vs. Fear Campaign Belief Change

## Research Question

**Primary:** Do hope-framed and fear-framed environmental campaigns produce different longitudinal belief changes in social media agents?

**Secondary:** How do cascade dynamics (direct vs. secondary exposure) moderate belief change effects?

---

## Experimental Design

### Design Type
- **Between-subjects factor:** Campaign Type (Hope, Fear, Control)
- **Within-subjects factor:** Time (T0, T1, T2)
- **Dependent variable:** `environmental_concern` (continuous, 0-1 scale)
- **Design:** 3 × 3 Mixed ANOVA with repeated measures

### Hypotheses

**H1 (Main Effect):** Campaign exposure increases environmental concern relative to control  
**H2 (Framing Effect):** Hope and Fear campaigns produce different magnitudes of belief change  
**H3 (Temporal Dynamics):** Belief changes persist from T1 (immediate) to T2 (sustained)  
**H4 (Cascade Effect):** Direct exposure produces stronger belief change than secondary exposure

---

## Sample Size Justification

### Power Analysis

**Target effect size:** d = 0.3–0.5 (small-to-medium)  
- Justification: Meta-analysis of fear appeal interventions (Tannenbaum et al., 2015) reports median d = 0.29 for attitude change
- Hope-framed messaging shows comparable effects (Chadwick, 2015)

**Required sample size:**  
- Repeated measures ANOVA (3 time points, between-subjects)
- Power = 0.80, α = 0.05 (two-tailed)
- **n ≥ 52 per condition** for d = 0.4 (G*Power calculation)

**Selected sample sizes:**
- Hope condition: **60 agents** (10% buffer for robustness)
- Fear condition: **60 agents**
- Control group: **80 agents** (may receive secondary exposures via cascades)
- **Total: 200 agents**

### Why 30% Targeting (Not 10%)?

**Statistical necessity:**  
- 10% targeting = 20 agents/condition → Power ≈ 0.40 (underpowered)
- 30% targeting = 60 agents/condition → Power ≈ 0.82 (adequately powered)

**Theoretical justification:**  
- Real campaigns often target 20-40% of network (Seeman et al., 2023)
- Still leaves 40% control group for organic diffusion analysis
- Balances experimental control with ecological validity

---

## Population Definition: Engaged User Subset

### Rationale

We model **engaged social media users** rather than the full population including lurkers.

**Empirical basis (Murdock et al., 2024):**
- 75% of social media users are "lurkers" with minimal activity
- Top 25% produce 97% of content
- Top 2% create 80% of tweets

**Implementation:**  
- `Activity ∈ [0.3, 1.0]` (excludes extreme lurkers)
- `AVG_LOGIN = 429 min/day` (3× population baseline of 143 min/day)
- **Result:** Online time: 129–429 minutes/day (2.1–7.2 hours/day)
- **Steady-state:** ~35-40 agents online concurrently (19% of population)

### Justification

**Statistical power:** Lurkers rarely see campaigns and never reshare them. Including them dilutes treatment effects and reduces statistical power without adding theoretical insight.

**Practical constraints:** With limited computational budget, we prioritize agents who actually participate in information diffusion.

**Theoretical consistency:** Our research question concerns belief evolution through social media engagement. Engaged users are the relevant population for studying cascade-mediated persuasion.

**Limitation acknowledged:** Results generalize to active users, not the full social media population. We note this in limitations and recommend future work examining lurker populations separately.

### Citations Supporting Population Choice

- Murdock, I., Carley, K. M., & Yağan, O. (2024). *Social Network Analysis & Mining*, 14, 145.
- Van Mierlo, T. (2014). The 1% rule in four digital health social networks. *Journal of Medical Internet Research*, 16(2), e33.

---

## Timeline Design

### Total Duration: 2,000 Steps (~33 Hours Simulated Time)

| Phase | Steps | Duration | Purpose |
|-------|-------|----------|---------|
| **Burn-in** | 1–399 | ~7 hours | Establish organic social timeline |
| **T0 Measurement** | 399 | — | Baseline belief assessment (all 200 agents) |
| **Campaign Launch** | 400 | — | Inject Hope & Fear campaigns (stratified assignment) |
| **Immediate Response** | 400–799 | ~7 hours | Observe direct reactions, reshares |
| **T1 Measurement** | 800 | — | Immediate effect (120 targeted agents) |
| **Sustained Observation** | 800–2000 | ~20 hours | Track cascade propagation, sustained effects |
| **T2 Measurement** | 2000 | — | Sustained effect (120 targeted agents) |

### Why These Time Points?

**T0 (step 399):** Baseline immediately before intervention
- Ensures no pre-intervention differences between groups
- All 200 agents measured for representative baseline

**T1 (step 800, +7 hours):** Immediate effect
- Captures initial reactions to campaign exposure
- Time window allows multiple observations for most agents (Activity ∈ [0.3,1.0] → ~30% online at any time)

**T2 (step 2000, +27 hours):** Sustained effect
- Tests whether belief changes persist beyond immediate exposure
- Allows cascades to propagate (reshares → secondary exposures)
- Long enough for consolidation, short enough for computational feasibility

### Why 2,000 Steps (Not 7,200)?

**Statistical sufficiency:** 27 hours post-campaign allows:
- Multiple exposures per agent (avg 3-5 observations/agent)
- Cascade formation (median cascade completes in ~12 hours)
- Belief consolidation (immediate + sustained measurement)

**Computational efficiency:**
- Runtime: ~45-60 minutes (vs. 3-4 hours for 7,200 steps)
- Cost: ~$20-25 (vs. ~$60-80)
- Faster iteration for validation and debugging

**Precedent:** Many ABM studies use 24-48 hour windows (e.g., Centola, 2010; Hodas & Lerman, 2014)

---

## Stratified Assignment

### Assignment Method

**Stratified random sampling** by Activity × Network Degree (Seeman et al., 2023)

**Procedure:**
1. Calculate composite score: `score = Activity × log(Degree + 1)`
2. Sort agents by score, divide into quintiles
3. Within each quintile, randomly assign to Hope or Fear (equal probability)
4. Control group = all unassigned agents

**Why stratify?**
- Prevents confounding: Ensures Hope and Fear groups have equal Activity and Degree distributions
- High-Activity agents are more likely to engage with campaigns
- High-Degree agents have more followers → larger potential cascade
- Without stratification, random imbalance could bias results

**Validation check:**
- Kolmogorov-Smirnov test: Hope vs. Fear Activity distributions (p > 0.05)
- Mann-Whitney U test: Hope vs. Fear Degree distributions (p > 0.05)
- Implemented in `simulation/targeting.py::validate_assignment_balance()`

---

## Measurement Protocol

### Belief Measurement

**Attribute:** `environmental_concern` (0-1 continuous scale)

**Method:** LLM-based belief assessment (Park et al., 2023)
- Agent persona + memory stream → LLM extracts current belief level
- Temperature = 0.3 (reduced variance for consistency)
- Prompt: "Based on this agent's characteristics and recent experiences, rate their environmental concern on a 0-1 scale."

**Why LLM measurement?**
- Agents have no explicit belief variables (beliefs are latent in LLM reasoning)
- Belief emerges from persona traits + experiences
- LLM can assess qualitative shifts in rhetoric/priorities

**Measurement schedule:**
- **T0:** All 200 agents (baseline, pre-campaign)
- **T1, T2:** 120 targeted agents only (reduces cost, focuses on treated population)
- Rationale: Control group belief change expected to be small (no direct exposure)

**Concurrency:** 30 parallel LLM calls (balances speed vs. rate limits)

---

## Cascade Depth Tracking

### Definition

**Cascade depth** = Number of reshare steps from original campaign post

- Depth 0: Direct campaign exposure (agent sees brand post)
- Depth 1: First-order reshare (agent sees friend's reshare of campaign)
- Depth 2: Second-order reshare (friend-of-friend reshare)
- Depth n: n-th order reshare

### Implementation

- `posts.cascade_depth` column tracks depth in database
- Reshare inherits parent depth and increments: `child.depth = parent.depth + 1`
- `campaign_exposures` table logs each exposure with depth

### Analysis Plan

**Dose-response analysis:**  
Compare belief change by exposure profile:
- Never exposed (control)
- Direct only (depth 0)
- Direct + secondary (depth 0 + depth ≥1)
- Secondary only (depth ≥1, no direct exposure)

**Expected pattern (if cascades matter):**  
Δbelief: Direct > Direct+Secondary > Secondary > Control

---

## Campaign Messages

### Hope Campaign
```
🔔 SPONSORED POST

Together we're building a cleaner planet. Every choice you make 
creates positive change. Join thousands making a difference. 
Small actions lead to big impact. The future is bright when we 
act together.
```

**Framing elements:**
- Collective efficacy ("together," "we")
- Positive outcome focus ("cleaner planet," "bright future")
- Social proof ("thousands")
- Empowerment ("every choice you make")

### Fear Campaign
```
🔔 SPONSORED POST

Time is running out. Environmental damage is accelerating. 
Without immediate action, consequences will be severe. 
Don't wait until it's too late. Act now before the window closes.
```

**Framing elements:**
- Urgency ("running out," "accelerating")
- Threat focus ("damage," "severe consequences")
- Scarcity ("window closes")
- Loss aversion ("too late")

### Message Design Rationale

**Equivalent structure:** Both messages have similar length, "SPONSORED POST" marker, and call-to-action structure

**Theoretically grounded:** 
- Hope: Positive reinforcement, collective efficacy (Chadwick, 2015)
- Fear: Threat + urgency (Witte & Allen, 2000)

**Content-identical baseline:** Both discuss environmental action; only emotional framing differs

---

## Statistical Analysis Plan

### Primary Analysis

**Repeated Measures ANOVA:**
- DV: `environmental_concern`
- Within-subjects: Time (T0, T1, T2)
- Between-subjects: Condition (Hope, Fear)
- Interaction term: **Time × Condition** (primary test)

**Post-hoc tests (if interaction significant):**
- Hope: T1-T0, T2-T0 (paired t-tests)
- Fear: T1-T0, T2-T0 (paired t-tests)
- Between: (T1-T0)_Hope vs. (T1-T0)_Fear (independent t-test)

**Multiple comparison correction:** Bonferroni adjustment

### Secondary Analyses

**Cascade depth moderation:**
- ANCOVA with cascade depth as continuous covariate
- Tests whether exposure intensity moderates belief change

**Individual differences:**
- Activity level as moderator (do high-activity agents respond differently?)
- Persona traits as moderators (openness, neuroticism, etc.)

**Network effects:**
- Degree centrality as moderator (do hubs respond differently?)
- Clustering coefficient as moderator (do community-embedded agents differ?)

---

## Expected Outcomes

### If Framing Matters (H2 Supported)

**Hope campaign:**
- Moderate belief increase (d ≈ 0.3-0.4)
- Sustained effect (T2 ≈ T1)
- More reshares (positive content spreads more; Berger & Milkman, 2012)

**Fear campaign:**
- Smaller immediate increase OR no change (reactance possible)
- Decay from T1 to T2 (fear wears off without sustained threat)
- Fewer reshares (negative content less viral)

### If Framing Doesn't Matter (H2 Not Supported)

Both campaigns produce similar belief changes → content (environmental action) matters more than frame

**Interpretation:** LLM agents weight semantic content over emotional tone, OR environmental concern driven by information (not emotion)

---

## Limitations & Mitigation

### 1. LLM Belief Measurement Reliability

**Limitation:** Beliefs are latent constructs; LLM extracts subjective estimates  
**Mitigation:** 
- Low temperature (0.3) for consistency
- Multiple exposures per agent improve signal
- Validate with synthetic checks (agents with known beliefs)

### 2. Engaged User Subset Generalization

**Limitation:** Results apply to active users, not full population  
**Mitigation:**
- Explicitly state scope in discussion
- Frame as "studying engaged users who drive diffusion"
- Recommend future work on lurker populations

### 3. Short Timeline (33 Hours)

**Limitation:** Can't observe long-term belief persistence (weeks/months)  
**Mitigation:**
- Focused on immediate + short-term sustained effects (theoretically relevant)
- Real campaigns have short attention windows anyway
- Acknowledge as limitation; recommend extended runs as future work

### 4. Single Campaign per Agent

**Limitation:** Real users see multiple competing messages  
**Mitigation:**
- Single-message design isolates framing effect
- Controls for message fatigue / interference
- Acknowledge as controlled experimental design

---

## Implementation Validation

### Pre-Run Checks

**Network validation:**
- Power-law exponent γ̂ ∈ [2.7, 3.3]
- Average clustering < 0.1

**Activity validation:**
- Mean Activity ≈ 0.65 (midpoint of [0.3, 1.0])
- ~25-35 agents online at any step

**Assignment validation:**
- Hope and Fear groups balanced on Activity and Degree (K-S test p > 0.05)

### Post-Run Checks

**Treatment delivery:**
- ≥90% of targeted agents saw campaign at least once
- Median exposures per targeted agent ≥ 2

**Cascade formation:**
- ≥5 reshares per campaign (evidence of diffusion)
- Structural virality ξ ∈ [2, 8] (realistic cascade shapes)

**Belief measurement:**
- ≥95% of measurement attempts successful (LLM reliability)
- T0 beliefs roughly uniform across groups (no pre-intervention bias)

---

## References

Berger, J., & Milkman, K. L. (2012). What makes online content viral? *Journal of Marketing Research*, 49(2), 192-205.

Centola, D. (2010). The spread of behavior in an online social network experiment. *Science*, 329(5996), 1194-1197.

Chadwick, A. E. (2015). Toward a theory of persuasive hope. *Social and Personality Psychology Compass*, 9(5), 208-223.

Hodas, N. O., & Lerman, K. (2014). The simple rules of social contagion. *Scientific Reports*, 4, 4343.

Murdock, I., Carley, K. M., & Yağan, O. (2024). An agent-based model of cross-platform information diffusion and moderation. *Social Network Analysis and Mining*, 14, 145.

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. *arXiv preprint arXiv:2304.03442*.

Seeman, L., Rosen, Y., Apanovitch, E., & Lev, O. (2023). Planning the behavior of agents for influence maximization. *Journal of Artificial Intelligence Research*, 78, 1-50.

Tannenbaum, M. B., Hepler, J., Zimmerman, R. S., Saul, L., Jacobs, S., Wilson, K., & Albarracín, D. (2015). Appealing to fear: A meta-analysis of fear appeal effectiveness and theories. *Psychological Bulletin*, 141(6), 1178-1204.

Van Mierlo, T. (2014). The 1% rule in four digital health social networks: An observational study. *Journal of Medical Internet Research*, 16(2), e33.

Witte, K., & Allen, M. (2000). A meta-analysis of fear appeals. *Health Education & Behavior*, 27(5), 591-615.


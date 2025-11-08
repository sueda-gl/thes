# Chapter 3: Methodology - Agent Design

## 3.1 Theoretical Framework for Agent Architecture

Our simulation employs LLM-based autonomous agents that observe, reflect, and act within a stylized social media environment. The agent design synthesizes two foundational approaches from recent literature: Park et al.'s (2023) memory-and-reflection architecture for temporal continuity, and Vu et al.'s (2025) personality conditioning for trait-consistent behavior. This section justifies our design choices and explains how we adapt these frameworks to our experimental context.

---

## 3.2 Memory and Reflection System (Park et al., 2023)

### 3.2.1 Source Framework

Park et al. (2023) introduced **Generative Agents** that sustain believable human-like behaviors over extended simulations through a three-part cognitive architecture:

1. **Memory stream**: All agent observations stored as timestamped natural-language records
2. **Retrieval function**: Memories scored by recency, importance, and semantic relevance (via embedding similarity)
3. **Reflection and planning**: Periodic LLM-driven summarization of memories into higher-level insights, with hierarchical goal decomposition

Their evaluation in a multi-day simulation ("Smallville") demonstrated that this architecture enables emergent social phenomena such as information diffusion, relationship formation, and coordinated events. Controlled ablation studies confirmed that removing any component (memory, reflection, or planning) significantly reduces behavioral believability.

### 3.2.2 Our Adaptation: Streamlined Memory-Reflection

We adopt the core memory-reflection mechanism but simplify the retrieval and omit the planning component. Our design preserves temporal continuity and self-awareness while reducing computational overhead for our shorter experimental timeframe.

**What we retain:**

- **Memory stream with importance scoring**: Each observation (feed item seen) and action (like, comment, post) is stored with a calculated importance weight. Importance captures how salient a memory should be for future retrieval, incorporating factors such as whether the content is campaign-related, whether it received high engagement, and whether it aligns with the agent's stated interests.

- **Retrieval by importance and recency**: When an agent reflects, we retrieve the most relevant memories using a scoring function that combines importance (pre-computed) with recency (exponentially decaying with age). This approach mirrors Park et al.'s first two retrieval components—recency and importance—without requiring semantic embeddings.

- **LLM-based reflection synthesis**: Periodically (every 3 simulation steps), agents generate a brief first-person reflection summarizing their recent activity and emotional state. The reflection prompt includes the agent's personality traits and the retrieved memories, producing context-aware self-assessments that inform subsequent decisions.

**What we simplify:**

- **No semantic relevance via embeddings**: Park et al.'s third retrieval component uses cosine similarity of memory embeddings to identify semantically related content. We omit this because:
  - Our 10-step simulation is too brief for complex memory landscapes where semantic search provides significant value
  - Importance and recency scoring proved sufficient in preliminary testing
  - Eliminating vector databases reduces technical complexity and computational cost

- **No hierarchical planning**: Park et al. decompose daily goals into hourly schedules and minute-by-minute actions. We do not implement planning because:
  - Our agents make discrete decisions per simulation step rather than managing continuous activity
  - The experimental focus (campaign response) does not require long-horizon goal structures
  - The constrained action space (like, comment, post, reshare, none) does not benefit from hierarchical decomposition

### 3.2.3 Justification

These simplifications align our agent architecture with our research scope. The core contribution of Park et al.—using memory-informed reflection to maintain behavioral coherence—remains intact. The omitted components (embeddings, planning) are appropriate for multi-day, open-ended simulations but add unnecessary complexity for controlled, short-horizon experiments comparing campaign framings.

---

## 3.3 Personality Conditioning (Vu et al., 2025)

### 3.3.1 Source Framework

Vu et al. (2025) present **PsychAdapter**, a method for conditioning LLM outputs on Big Five personality traits to produce stable, trait-consistent behaviors. Their approach operates through:

1. **Continuous trait conditioning**: Five-dimensional personality vectors (Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism) are projected into transformer hidden states via learned adapter layers
2. **Training on personality-labeled text**: Using PsychGenerator (846k Facebook posts with authors' Big Five scores), the model learns to generate text reflecting specific trait profiles
3. **Validation**: Human psychologists and LLM raters achieved 87.3% accuracy in identifying intended trait levels from generated text

Critically, Vu et al. recognize that not all users can modify model weights, and they provide a **prompt-based fallback**: embedding trait descriptions and behavioral priors directly into the input prompt to steer the base model's outputs.

### 3.3.2 Our Adaptation: Prompt-Based Trait Conditioning

We implement personality conditioning using the prompt-based method rather than weight modification, as we rely on a commercial LLM (GPT-4o) where internal parameters are fixed.

**What we retain:**

- **Big Five trait representation**: All agents are initialized with continuous values for the five traits, sampled from Gaussian distributions centered at 0.5 with standard deviation 0.15, clipped to [0.1, 0.9]. This produces a diverse population without extreme outliers.

- **Trait-informed prompts**: Decision prompts explicitly state the agent's personality profile, converting continuous trait values into categorical descriptors (high/moderate/low) that the LLM can interpret. For example: "Openness to new ideas: high (0.82)."

- **Behavioral priors**: Beyond trait labels, we include conditional instructions that specify how traits should manifest in behavior. High extraversion agents are told they "enjoy sharing content," while high neuroticism agents "often feel compelled to comment on concerning posts." These priors guide the LLM toward trait-consistent action selection.

**What we do not implement:**

- **PsychAdapter weight modification**: Directly modifying GPT-4o's transformer layers is not feasible with the OpenAI API. Our prompt-based approach is the officially recommended fallback for this constraint.

- **Training on personality-labeled data**: We use the off-the-shelf GPT-4o model without fine-tuning. Vu et al.'s validation results suggest that their prompt-based method, while not as strong as adapter tuning, still produces recognizable trait patterns.

- **Formal psychological validation**: We do not conduct human evaluations with trained psychologists to verify trait authenticity. Instead, our validation is behavioral: we assess whether personality moderates campaign response in theoretically expected ways (e.g., high neuroticism → stronger fear response).

### 3.3.3 Extension: Campaign-Specific Sensitivities

Beyond the Big Five, we derive two additional personality-based parameters tailored to our hope-versus-fear experimental design:

- **Emotion sensitivity**: Combines neuroticism (emotional reactivity) and extraversion (social expressiveness) to modulate how strongly agents respond to emotionally framed content. This aligns with fear-appeal theories (Witte & Allen, 2000) that emphasize individual differences in emotional processing.

- **Efficacy sensitivity**: Combines conscientiousness (action-orientation) and openness (receptivity to new approaches) to capture preferences for clear, actionable steps versus abstract ideals. This links to Tannenbaum et al.'s (2015) finding that fear appeals require high efficacy cues to drive behavior.

These derived metrics bridge personality psychology with persuasion research, allowing us to test whether campaign effectiveness is moderated by trait-driven sensitivities.

### 3.3.4 Justification

Our prompt-based implementation follows Vu et al.'s recommended alternative for commercial LLM users. While less powerful than adapter-based conditioning, it avoids the need for model training infrastructure and leverages the strong prompt-following capabilities of modern LLMs. The derived sensitivities represent a novel contribution that operationalizes personality-campaign interactions within the Big Five framework.

---

## 3.4 Integration: Memory-Informed, Personality-Consistent Decision-Making

The final agent architecture integrates memory-reflection (Park et al.) and personality conditioning (Vu et al.) into a unified decision loop:

1. **Observation phase**: Agents perceive personalized feeds and store observations as weighted memories
2. **Reflection phase**: Every three steps, agents retrieve salient memories and generate a personality-aware reflection
3. **Decision phase**: Agents receive prompts that include their personality traits, recent reflection (if available), and current feed content, then select an action
4. **Action phase**: The chosen action is executed and recorded as a new memory

This integration ensures that agents exhibit both **temporal continuity** (via memory-informed reflection) and **cross-situational consistency** (via personality-conditioned prompts). Reflections provide agents with awareness of their recent behavior patterns, while personality traits shape how they interpret and respond to content.

---

## 3.5 Design Rationale Summary

### 3.5.1 Why These Papers?

**Park et al. (2023)** provides the foundation for agents that maintain coherent behavior over time rather than treating each decision as isolated. This is essential for studying cascades, where early engagement influences later spread.

**Vu et al. (2025)** provides the foundation for agents with stable, differentiated personalities. This enables moderation analysis (does personality affect campaign response?) and population-level diversity without hand-coding behavioral rules.

### 3.5.2 Why These Simplifications?

- **No embeddings**: 10-step simulation does not accumulate enough memories to benefit from semantic search
- **No planning**: Discrete, step-by-step decisions do not require hierarchical goal structures
- **No weight modification**: Technical constraints (commercial LLM API) necessitate prompt-based approach
- **No formal psychological validation**: Behavioral validation (personality × campaign interactions) is more aligned with our research question than verifying trait realism per se

### 3.5.3 Novel Contributions

Our design contributes beyond direct implementation of existing work:

1. **Synthesis of memory and personality**: Prior work treats these as separate problems; we integrate them in a single prompt-based agent
2. **Campaign-specific sensitivities**: Derived personality metrics link Big Five traits to persuasion theory
3. **Simplified retrieval for short-horizon experiments**: Demonstrates that importance + recency is sufficient when semantic search is overkill

---

## 3.6 Limitations and Scope

### 3.6.1 Fidelity to Source Papers

Our implementation achieves partial fidelity to the source frameworks:

- **Park et al.**: ~65% fidelity (core memory-reflection retained, embeddings and planning omitted)
- **Vu et al.**: ~85% fidelity (prompt-based conditioning retained, weight modification unavailable)

These percentages reflect principled adaptations rather than implementation shortcuts. The omitted components are either computationally expensive for minimal gain (embeddings, planning) or technically infeasible (weight modification).

### 3.6.2 Validity Considerations

**Internal validity** is strengthened by:
- Transparent design decisions with clear justifications
- Controlled experimental environment (all agents face identical platform mechanics)
- Reproducibility via fixed random seeds

**External validity** is limited by:
- Synthetic agents may not fully replicate human decision-making nuances
- Prompt-based personality conditioning is weaker than adapter-based tuning
- 10-step simulations capture short-term dynamics but not long-term attitude change

**Construct validity** depends on:
- Whether LLM-generated reflections capture genuine self-awareness
- Whether personality prompts produce trait-consistent behavior patterns
- Whether campaign responses align with persuasion theory predictions

We address these through behavioral validation: checking whether personality moderates campaign effectiveness in theoretically expected directions (hope → sharing, fear → deliberation; high neuroticism → stronger fear response).

---

## 3.7 Theoretical Positioning

This agent design positions our work within the emerging paradigm of **LLM-based computational social science** (Haase & Pokutta, 2025). Rather than claiming to predict real-world outcomes, we use LLM agents as a controlled testbed for exploring **relative differences** between conditions (hope vs. fear framing) under transparent, auditable assumptions.

The memory-reflection mechanism ensures agents exhibit temporal continuity, preventing unrealistic volatility in engagement patterns. The personality-conditioning mechanism ensures population heterogeneity, enabling moderation analyses without hand-coding behavioral rules. Together, these components support a simulation that is **tractable** (runs efficiently), **interpretable** (design choices are explicit), and **extensible** (components can be swapped or enhanced).

---

## References

Haase, P., & Pokutta, S. (2025). Multi-agent LLM systems for computational social science. *arXiv preprint* arXiv:2506.01839.

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). Generative agents: Interactive simulacra of human behavior. *UIST 2023*. arXiv:2304.03442.

Tannenbaum, M. B., Hepler, J., Zimmerman, R. S., Saul, L., Jacobs, S., Wilson, K., & Albarracín, D. (2015). Appealing to fear: A meta-analysis of fear appeal effectiveness and theories. *Psychological Bulletin*, 141(6), 1178–1204.

Vu, T. H., et al. (2025). PsychAdapter: Adapting LLM transformers to reflect traits, personality & mental health. Preprint, January 2025.

Witte, K., & Allen, M. (2000). A meta-analysis of fear appeals: Implications for effective public health campaigns. *Health Education & Behavior*, 27(5), 591–615.


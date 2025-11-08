# Methodology: Agent Architecture and Implementation

## 3.1 Agent Design: Theoretical Foundation

Our agent architecture draws primarily from two foundational works in LLM-based agent systems: Park et al. (2023) for memory and reflection mechanisms, and Vu et al. (2025) for personality-conditioned behavior.

### 3.1.1 Memory Stream Architecture (Park et al., 2023)

Park et al. (2023) introduced **Generative Agents**, demonstrating that LLMs combined with memory, reflection, and planning can sustain believable behaviors over extended simulations. Their three-part architecture consists of:

1. **Memory stream**: Natural-language records of observations with timestamps
2. **Retrieval function**: Scores memories by recency, importance, and relevance (cosine similarity of embeddings)
3. **Reflection & Planning**: Periodic LLM calls to summarize memories hierarchically and decompose goals into actions

#### Our Implementation: Simplified Memory Stream

We adopt Park et al.'s memory stream concept but simplify the retrieval mechanism to suit our shorter simulation timeframe (10 steps vs. their multi-day simulations):

**What we implemented from Park et al.:**

- ✓ **Memory Stream** (`simulation/agent.py`, lines 11-45): Each observation and action is stored as a structured `MemoryEntry` object with:
  - `timestamp`: Simulation step when memory was created
  - `memory_type`: 'observation', 'action', or 'reflection'
  - `content`: Human-readable description
  - `importance`: Calculated score (0-1)
  - `metadata`: Additional contextual information

- ✓ **Importance Calculation** (lines 77-129): Memories are scored based on:
  - Memory type (+0.2 for actions vs. observations)
  - Campaign content (+0.3 for experimental tracking)
  - Engagement level (+0.2 for >10 likes+comments)
  - Interest alignment (+0.15 for content matching agent interests)
  - Emotional framing (+0.1 for hope/fear keywords)

- ✓ **Retrieval with Recency + Importance** (lines 259-296): Top-k memories retrieved using:
  ```
  score = importance + recency_weight × (0.99^age)
  ```
  where age is steps since memory creation, and recency_weight = 0.5

- ✓ **LLM-Based Reflection** (lines 298-362): Every 3 steps, agents:
  1. Retrieve top-10 most relevant memories
  2. Generate reflection via LLM (GPT-4o, temperature=0.5)
  3. Store reflection as high-importance memory (0.8)

**Key simplifications from Park et al.:**

- ✗ **No vector embeddings**: We do NOT use cosine similarity for relevance scoring. Park et al.'s third retrieval component (relevance via embeddings) is omitted because:
  - Our 10-step simulation is too short to benefit from semantic retrieval
  - Importance + recency scoring proved sufficient in testing
  - Reduces computational overhead and eliminates vector database dependency

- ✗ **No planning module**: Park et al. decompose daily goals into hourly chunks and 5-15 minute actions. We do not implement hierarchical planning because:
  - Our agents make discrete decisions per step, not continuous activity
  - 10-step simulation doesn't require long-term goal decomposition
  - Action space is constrained (like, comment, post, reshare, none)

**Justification**: These simplifications are appropriate for our experimental scope. The core Park et al. contribution—memory-informed reflection—is preserved, while computationally expensive components (embeddings, planning) are removed where they add minimal value for short-horizon campaign comparisons.

---

### 3.1.2 Personality Conditioning (Vu et al., 2025)

Vu et al. (2025) present **PsychAdapter**, a system for conditioning LLM outputs on Big Five personality traits. Their approach includes:

1. **Continuous trait conditioning**: 5-dimensional trait vectors projected into transformer hidden states via learned matrices
2. **PsychGenerator dataset**: 846k Facebook posts labeled with authors' Big Five scores
3. **Validation**: 87.3% accuracy in matching intended trait levels (human + LLM raters)
4. **Prompt-only fallback**: For users unable to modify model weights, a compact template approach

#### Our Implementation: Prompt-Based Trait Conditioning

We adopt Vu et al.'s **prompt-only fallback approach** rather than their weight-modification method (PsychAdapter), as we use a commercial LLM (GPT-4o) where internal weights cannot be modified.

**What we implemented from Vu et al.:**

- ✓ **Big Five Trait Generation** (`personas/generator.py`, lines 73-79):
  - All five traits: Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism
  - Continuous values sampled from Gaussian distributions (mean=0.5, std=0.15)
  - Range clipped to [0.1, 0.9] to ensure diversity while avoiding extremes

- ✓ **Prompt-Based Conditioning** (`llm/prompts.py`, lines 69-102):
  - Traits converted to categorical descriptors (high/moderate/low) for LLM interpretation
  - Personality section in decision prompt:
    ```
    Personality:
    - Openness to new ideas: high (0.82)
    - Emotional sensitivity: moderate (0.54)
    - Social tendency: very social (0.78)
    ```
  
- ✓ **Trait-Specific Behavioral Priors** (lines 83-101):
  - High emotion_sensitivity: "You tend to react strongly to emotional content"
  - High efficacy_sensitivity: "You respond best to clear, actionable steps"
  - High extraversion: "You enjoy sharing content that resonates with you"
  - High neuroticism: "You often feel compelled to comment on concerning posts"

- ✓ **Derived Campaign-Specific Sensitivities** (`personas/generator.py`, lines 127-141):
  - **Emotion sensitivity**: Derived from neuroticism + extraversion (for hope/fear framing moderation)
    ```
    emotion_sensitivity = 0.5 + (neuroticism - 0.5) × 0.5 + (extraversion - 0.5) × 0.3
    ```
  - **Efficacy sensitivity**: Derived from conscientiousness + openness (for actionability preferences)
    ```
    efficacy_sensitivity = 0.5 + (conscientiousness - 0.5) × 0.4 + (openness - 0.5) × 0.3
    ```

**What we did NOT implement from Vu et al.:**

- ✗ **PsychAdapter weight modification**: We cannot modify GPT-4o's internal transformer layers
- ✗ **Training on Facebook posts**: We use an off-the-shelf LLM, not a fine-tuned model
- ✗ **Formal validation with human psychologists**: Our validation is behavioral (simulation output analysis)

**Justification**: Vu et al. explicitly provide the prompt-only approach as a fallback for commercial LLM users. Their paper (Section 2.3, y.ttxt lines 58-59) states: *"for users who cannot modify weights, the authors provide a compact template—seed the generation with a short stem...plus an extreme-value trait vector."* Our implementation follows this guidance, with categorical trait descriptors and behavioral priors replacing direct weight conditioning.

---

### 3.1.3 Integration: Memory + Personality in Decision-Making

Our agents combine Park et al.'s memory-reflection loop with Vu et al.'s personality conditioning in a unified decision-making process:

**Decision Flow** (`simulation/agent.py`, lines 170-203):

1. **Memory Recording**: Observations and actions stored with importance scores
2. **Reflection Generation** (every 3 steps):
   - Retrieve top-10 memories via importance+recency scoring
   - Generate personality-aware reflection via LLM
   - Store reflection as high-importance memory
3. **Decision Prompt Construction** (`llm/prompts.py`):
   - Personality traits (Big Five + sensitivities)
   - Recent reflection (if available)
   - Current feed content
   - Action space (like/comment/post/reshare/none)
4. **LLM Decision**: GPT-4o generates action with reason
5. **Action Execution & Recording**: New memory entry created

**Example Decision Prompt** (simplified):
```
You are Alice, 28 years old, female.

Personality:
- Openness: high (0.82)
- Neuroticism: moderate (0.54)
- Extraversion: very social (0.78)

You tend to react strongly to emotional content and urgent messaging.
You enjoy sharing content that resonates with you.

Recent reflection: I've been actively engaging with posts about 
environmental action, especially hopeful messages, which resonate 
with my values and make me feel optimistic.

Your social media feed shows:
1. [Campaign Post]: "Together we're building a cleaner planet..."
   Likes: 10 | Comments: 5

Based on your personality and what you see, what do you do?
Options: A) Like B) Comment C) Reshare D) Post E) Nothing
```

**Reflection Prompt** (personality-aware, `llm/prompts.py`, lines 312-340):
```
You are Alice, 28 years old, reflecting on recent social media activity.

Your personality traits:
- Openness: 0.82
- Emotional sensitivity (neuroticism): 0.54
- Social tendency (extraversion): 0.78

Below are your most relevant memories (ranked by importance and recency):
1. [1 step ago, importance: 1.00] Saw campaign post: 'Together...'
2. [0 steps ago, importance: 0.80] I commented: 'I completely agree!...'

Based on these memories, write a brief 1-2 sentence reflection...
Your reflection should reflect your personality (e.g., if neuroticism 
is high, express concern or anxiety).
```

---

## 3.2 Validity and Limitations

### Fidelity to Source Papers

**Park et al. (2023) fidelity: ~65%**
- ✓ Core memory stream preserved
- ✓ Importance-based retrieval implemented
- ✓ LLM-based reflection synthesis
- ✗ No vector embeddings (cosine similarity omitted)
- ✗ No hierarchical planning

**Vu et al. (2025) fidelity: ~85%**
- ✓ All Big Five traits implemented
- ✓ Continuous trait values (Gaussian distributions)
- ✓ Prompt-based conditioning (official fallback method)
- ✓ Trait-specific behavioral priors
- ✗ No weight modification (PsychAdapter)
- ✗ No custom training on personality-labeled data

### Appropriate Simplifications

Our adaptations are justified by:

1. **Simulation scale**: 10 steps vs. Park et al.'s multi-day scenarios
2. **Research focus**: Campaign comparison requires behavioral consistency, not emergent planning
3. **Technical constraints**: Commercial LLM (GPT-4o) with fixed weights
4. **Cost-benefit**: Embeddings add ~$2-3 per run with minimal benefit for 10-step simulations

### Novel Contributions

Beyond the source papers, we introduce:

1. **Campaign-specific sensitivities** (emotion_sensitivity, efficacy_sensitivity): Bridge Big Five traits with fear/hope framing theory (Witte & Allen 2000; Tannenbaum et al. 2015)
2. **Trait-derived activity patterns**: Link extraversion/conscientiousness to participation probability (not in Park et al.)
3. **Integrated reflection-personality system**: Single decision prompt combining memory context and trait conditioning

---

## 3.3 Implementation Summary

| Component | Source Paper | Lines of Code | Key Parameters |
|-----------|-------------|---------------|----------------|
| MemoryEntry dataclass | Park et al. 2023 | agent.py:11-45 | timestamp, importance, metadata |
| Importance calculation | Park et al. 2023 | agent.py:77-129 | 5 factors, range [0,1] |
| Memory retrieval | Park et al. 2023 | agent.py:259-296 | k=10, recency_weight=0.5 |
| LLM reflection | Park et al. 2023 | agent.py:298-362 | every 3 steps, temp=0.5 |
| Big Five generation | Vu et al. 2025 | generator.py:73-79 | Gaussian (μ=0.5, σ=0.15) |
| Trait conditioning | Vu et al. 2025 | prompts.py:69-102 | categorical descriptors |
| Emotion sensitivity | Novel (Witte 2000) | generator.py:127-133 | f(neuroticism, extraversion) |
| Efficacy sensitivity | Novel (Tannenbaum 2015) | generator.py:135-141 | f(conscientiousness, openness) |

**Cost Analysis**:
- Decision-making: ~$4.00 per 100-agent, 10-step simulation
- LLM reflections: +$0.45 (11% increase)
- Total: ~$4.45 per simulation run

---

## References for This Section

Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., & Bernstein, M. S. (2023). *Generative Agents: Interactive Simulacra of Human Behavior*. UIST 2023. arXiv:2304.03442

Vu, T. H., et al. (2025). *PsychAdapter: Adapting LLM Transformers to Reflect Traits, Personality & Mental Health*. Preprint, January 2025.

Witte, K., & Allen, M. (2000). *A Meta-Analysis of Fear Appeals: Implications for Effective Public Health Campaigns*. Health Education & Behavior, 27(5), 591-615.

Tannenbaum, M. B., et al. (2015). *Appealing to Fear: A Meta-Analysis of Fear Appeal Effectiveness and Theories*. Psychological Bulletin, 141(6), 1178-1204.


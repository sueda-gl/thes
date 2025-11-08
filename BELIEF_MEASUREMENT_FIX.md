# Fix for Median Collapse in Belief Measurement

## Problem
Current belief assessment prompt only includes name and age, creating high risk of median collapse where all agents cluster around 5/10 regardless of persona or experiences.

## Solution: Persona-Informed Belief Assessment

### Updated Prompt Structure

```python
def create_belief_assessment_prompt(
    persona: Dict[str, Any],
    attribute: str,
    memory_context: Optional[str] = None  # NEW: Include recent memories
) -> str:
    """
    Create prompt for belief assessment with full persona context.
    
    CRITICAL: Include personality, interests, and memory to prevent median collapse
    (Argyle et al., 2023; Hagendorff et al., 2023)
    """
    name = persona.get('name', 'User')
    age = persona.get('age', 30)
    
    # NEW: Extract personality and interests
    personality = persona.get('personality', {})
    interests = persona.get('interests', [])
    initial_env_concern = persona.get('environmental_concern', 0.5)
    
    # NEW: Personality descriptors
    openness = personality.get('openness', 0.5)
    neuroticism = personality.get('neuroticism', 0.5)
    
    openness_desc = "high" if openness > 0.7 else "moderate" if openness > 0.4 else "low"
    neuro_desc = "high" if neuroticism > 0.7 else "moderate" if neuroticism > 0.4 else "low"
    
    if attribute == 'environmental_concern':
        # NEW: Frame initial concern level
        if initial_env_concern > 0.8:
            concern_baseline = "You've always been deeply committed to environmental protection"
        elif initial_env_concern > 0.6:
            concern_baseline = "You care about the environment and try to make sustainable choices"
        elif initial_env_concern > 0.4:
            concern_baseline = "You're aware of environmental issues but they're not your top priority"
        else:
            concern_baseline = "You're somewhat skeptical about environmental activism"
        
        prompt = f"""You are {name}, a {age}-year-old person.

Your personality:
- You have {openness_desc} openness to new ideas
- You have {neuro_desc} emotional sensitivity
- Your interests include: {', '.join(interests[:3]) if len(interests) >= 3 else ', '.join(interests)}

Your environmental stance:
- {concern_baseline}"""

        # NEW: Add memory context if provided
        if memory_context:
            prompt += f"""

Recent experiences:
{memory_context}"""

        prompt += """

Please reflect honestly on your CURRENT views about environmental issues and climate change, 
considering both your background and any recent experiences.

On a scale from 0 to 10:
- 0 = Not concerned at all about environmental issues
- 5 = Moderately concerned
- 10 = Extremely concerned and committed to environmental action

How would you currently rate your level of environmental concern?

Respond in this exact format:
RATING: [your number from 0-10]
REASONING: [1-2 sentences explaining your current stance, mentioning any recent influences]

Your response:"""
    
    return prompt
```

### Updated `measure_belief` Method

```python
async def measure_belief(
    self,
    attribute: str,
    step: int,
    db: Any
) -> float:
    """
    Measure agent's current belief with full persona + memory context.
    """
    from llm.prompts import create_belief_assessment_prompt, parse_belief_response
    
    # NEW: Build memory context for belief assessment
    recent_memories = self.retrieve_memories(
        current_step=step,
        k=5,  # Top 5 most relevant memories
        recency_weight=0.7  # Emphasize recent experiences
    )
    
    memory_context = None
    if recent_memories:
        memory_lines = []
        for mem in recent_memories:
            age = step - mem.timestamp
            memory_lines.append(f"- {mem.content} ({age} steps ago)")
        memory_context = "\n".join(memory_lines)
    
    # Generate belief assessment prompt with full context
    prompt = create_belief_assessment_prompt(
        persona=self.persona,
        attribute=attribute,
        memory_context=memory_context  # NEW: Include memories
    )
    
    # Get LLM response with slightly higher temperature
    response = await self.llm_client.generate(
        prompt,
        temperature=0.4,  # INCREASED from 0.3 for more variance
        max_tokens=200    # INCREASED for longer reasoning
    )
    
    if not response:
        # Fallback to current persona value
        current_value = self.persona.get(attribute, 0.5)
        reasoning = "Failed to generate belief assessment"
    else:
        # Parse response
        current_value, reasoning = parse_belief_response(response)
    
    # Log to database
    await db.insert_belief_measurement(
        agent_id=self.agent_id,
        attribute=attribute,
        value=current_value,
        step=step,
        reasoning=reasoning
    )
    
    # Update persona with measured value
    self.persona[attribute] = current_value
    
    return current_value
```

## Validation Checks

After implementing, validate median collapse mitigation:

### Check 1: T0 Distribution Should Match Persona
```python
# Expected: T0 measurements ~ persona environmental_concern (0.59-0.89)
# If median collapse: T0 measurements cluster around 0.5
```

### Check 2: Variance Should NOT Compress
```python
# Expected: σ(T0) ≈ 0.08 (similar to persona variance)
# If median collapse: σ(T0) << 0.05 (compressed)
```

### Check 3: Belief Changes Should Be Detectable
```python
# Expected: Hope agents show ΔT1-T0 > 0, Fear agents may vary
# If median collapse: All Δ ≈ 0 (no change detected)
```

## References

Argyle, L. P., et al. (2023). Out of one, many: Using language models to simulate human samples. 
*Political Analysis*, 31(3), 337-351.

Hagendorff, T., et al. (2023). Human-like intuitive behavior and reasoning biases emerged in 
language models—and disappeared in GPT-4. *arXiv preprint arXiv:2306.07622*.

Törnberg, P. (2023). ChatGPT-4 outperforms experts and crowd workers in annotating political 
Twitter messages with zero-shot learning. *arXiv preprint arXiv:2304.06588*.


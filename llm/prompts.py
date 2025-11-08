"""
Prompt templates for agent decision-making and reflection.
"""
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from simulation.agent import MemoryEntry


def create_decision_prompt(
    persona: Dict[str, Any],
    feed_items: List[Dict[str, Any]],
    step: int,
    reflection: Optional[str] = None
) -> str:
    """
    Create a prompt for agent decision-making.
    
    Args:
        persona: Agent's persona dict
        feed_items: List of posts/comments in the feed
        step: Current simulation step
    
    Returns:
        Formatted prompt string
    """
    
    # Extract persona details
    name = persona.get('name', 'User')
    age = persona.get('age', 30)
    gender = persona.get('gender', 'person')
    personality = persona.get('personality', {})
    interests = persona.get('interests', [])
    social_behavior = persona.get('social_behavior', 'casual')
    backstory = persona.get('backstory', None)  # NEW: Rich personal narrative
    
    openness = personality.get('openness', 0.5)
    neuroticism = personality.get('neuroticism', 0.5)
    extraversion = personality.get('extraversion', 0.5)
    
    # Domain-specific attitudes
    env_concern = persona.get('environmental_concern', 0.5)
    brand_trust = persona.get('brand_trust', 0.5)
    
    # Personality descriptions
    openness_desc = "high" if openness > 0.7 else "moderate" if openness > 0.4 else "low"
    neuro_desc = "high" if neuroticism > 0.7 else "moderate" if neuroticism > 0.4 else "low"
    extra_desc = "very social" if extraversion > 0.7 else "moderately social" if extraversion > 0.4 else "reserved"
    
    # Environmental stance (natural language)
    if env_concern > 0.8:
        env_stance = "You are deeply committed to environmental protection and climate action"
    elif env_concern > 0.6:
        env_stance = "You care about the environment and try to make sustainable choices"
    elif env_concern > 0.4:
        env_stance = "You're aware of environmental issues but they're not a top priority for you"
    elif env_concern > 0.2:
        env_stance = "You're somewhat skeptical about environmental activism and climate concerns"
    else:
        env_stance = "You're highly skeptical of environmental movements and climate messaging"
    
    # Build feed display
    feed_text = ""
    for idx, item in enumerate(feed_items, 1):
        post_type = item.get('post_type', 'organic')
        content = item.get('content', '')
        likes = item.get('like_count', 0)
        comments = item.get('comment_count', 0)
        author = item.get('agent_id', 'Unknown')
        
        if post_type == 'campaign':
            feed_text += f"{idx}. [Campaign Post]: \"{content}\"\n"
        else:
            feed_text += f"{idx}. [Post by {author}]: \"{content}\"\n"
        
        feed_text += f"   Likes: {likes} | Comments: {comments}\n\n"
    
    if not feed_text:
        feed_text = "(Your feed is empty right now)\n"
    
    # Build prompt with reflection
    # NEW V2: Use rich backstory if available, fall back to traits if not
    if backstory:
        prompt = f"""You are {name}. {backstory}

Your interests include {', '.join(interests[:3]) if len(interests) >= 3 else ', '.join(interests)}."""
    else:
        # Fallback to old format if no backstory (backward compatible)
        prompt = f"""You are {name}, a {age}-year-old {gender}.

Your personality:
- You have {openness_desc} openness to new ideas
- You have {neuro_desc} emotional sensitivity  
- You are {extra_desc}
- Your social media behavior is typically {social_behavior}

Your interests include {', '.join(interests[:3]) if len(interests) >= 3 else ', '.join(interests)}.

Your values and attitudes:
- {env_stance}
- You have {f'high trust' if brand_trust > 0.7 else f'moderate trust' if brand_trust > 0.5 else f'low trust'} in brands and sponsored content"""
    
    # Add reflection if available (Park et al. 2023 memory→reflection)
    if reflection:
        prompt += f"\n\nYour recent thoughts: {reflection}"
    
    prompt += f"""

Your social media feed shows:

{feed_text}

What do you do? Respond authentically based on who you are and how you actually think and speak.

Options:
A) Like one of these posts
B) Comment on a post (say what you're really thinking - be yourself, not corporate)
C) Share/repost with your own take
D) Create your own post about something on your mind
E) Just scroll (not feeling it right now)

Respond in this format:

ACTION: [A/B/C/D/E]
POST_NUMBER: [if A, B, or C]
CONTENT: [your actual words - be honest, be you, don't be fake]
REASON: [why this matters to you]

Your response:"""
    
    return prompt


def parse_action_response(response_text: str, feed_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Parse LLM response into structured action.
    
    Args:
        response_text: Raw LLM response
        feed_items: Feed items (to map post numbers to IDs)
    
    Returns:
        Dict with action type and parameters
    """
    if not response_text:
        return {'type': 'none'}
    
    lines = response_text.strip().split('\n')
    
    action_type = None
    post_number = None
    content = None
    reason = None
    
    # Parse each line with error handling
    for i, line in enumerate(lines):
        line = line.strip()
        
        if line.startswith('ACTION:'):
            try:
                action_letter = line.split(':', 1)[1].strip().upper()
                # Extract just the letter (A, B, C, D, or E)
                if action_letter and action_letter[0] in ['A', 'B', 'C', 'D', 'E']:
                    action_type = action_letter[0]
            except (IndexError, AttributeError):
                pass
        
        elif line.startswith('POST_NUMBER:'):
            try:
                num_str = line.split(':', 1)[1].strip()
                post_number = int(num_str)
            except (ValueError, IndexError, AttributeError):
                pass
        
        elif line.startswith('CONTENT:'):
            try:
                content = line.split(':', 1)[1].strip()
                # Continue reading if content spans multiple lines
                # Use index i to get subsequent lines
                for j in range(i + 1, len(lines)):
                    next_stripped = lines[j].strip()
                    if next_stripped.startswith(('REASON:', 'ACTION:', 'POST_NUMBER:')):
                        break
                    if next_stripped:  # Only add non-empty lines
                        content += ' ' + next_stripped
            except (IndexError, AttributeError):
                pass
        
        elif line.startswith('REASON:'):
            try:
                reason = line.split(':', 1)[1].strip()
            except (IndexError, AttributeError):
                pass
    
    # Fallback: if no ACTION found, try to infer from content
    if not action_type and content:
        # If we have content but no action, assume it's a post
        action_type = 'D'
    
    # Convert to action object with validation
    if action_type == 'A':  # Like
        if post_number and feed_items and 1 <= post_number <= len(feed_items):
            return {
                'type': 'like',
                'post_id': feed_items[post_number - 1]['post_id'],
                'reason': reason  # Ferraro et al. Choice-Reason-Content
            }
    
    elif action_type == 'B':  # Comment
        if post_number and content and feed_items and 1 <= post_number <= len(feed_items):
            # Truncate if too long
            if len(content) > 280:
                content = content[:277] + '...'
            return {
                'type': 'comment',
                'parent_post_id': feed_items[post_number - 1]['post_id'],
                'content': content,
                'reason': reason
            }
    
    elif action_type == 'C':  # Reshare
        if post_number and feed_items and 1 <= post_number <= len(feed_items):
            # Optional share comment
            if content and len(content) > 280:
                content = content[:277] + '...'
            return {
                'type': 'reshare',
                'parent_post_id': feed_items[post_number - 1]['post_id'],
                'content': content if content else None,
                'reason': reason
            }
    
    elif action_type == 'D':  # Post
        if content:
            # Truncate if too long
            if len(content) > 280:
                content = content[:277] + '...'
            return {
                'type': 'post',
                'content': content,
                'reason': reason
            }
    
    elif action_type == 'E':  # No action
        return {'type': 'none', 'reason': reason}
    
    # Default to no action if parsing fails or validation fails
    return {'type': 'none'}


def create_reflection_prompt(
    persona: Dict[str, Any],
    memories: List[Any],  # List[MemoryEntry] but avoid circular import
    current_step: int
) -> str:
    """
    Create prompt for LLM to generate reflection.
    Implements Park et al. 2023 reflection generation.
    
    Args:
        persona: Agent's persona dict
        memories: Retrieved memory entries
        current_step: Current simulation step
    
    Returns:
        Prompt string for reflection generation
    """
    name = persona.get('name', 'User')
    age = persona.get('age', 30)
    personality = persona.get('personality', {})
    
    # Get key personality traits for context
    openness = personality.get('openness', 0.5)
    neuroticism = personality.get('neuroticism', 0.5)
    extraversion = personality.get('extraversion', 0.5)
    
    # Build memory list with importance and recency
    memory_text = ""
    for i, memory in enumerate(memories, 1):
        age = current_step - memory.timestamp
        memory_text += f"{i}. [{age} steps ago, importance: {memory.importance:.2f}] {memory.content}\n"
    
    if not memory_text:
        memory_text = "(No memories to reflect on)\n"
    
    prompt = f"""You are {name}, {age} years old, reflecting on your recent social media activity.

Your personality traits:
- Openness: {openness:.2f}
- Emotional sensitivity (neuroticism): {neuroticism:.2f}
- Social tendency (extraversion): {extraversion:.2f}

Below are your most relevant memories from the past few steps (ranked by importance and recency):

{memory_text}

Based on these memories, write a brief 1-2 sentence reflection that captures:
- Your recent behavior patterns (active/inactive, what you engaged with)
- Any themes or topics you've been noticing
- Your current emotional state or thoughts about the content

Your reflection should:
- Be in first person and conversational
- Reflect your personality (e.g., if neuroticism is high, you might express concern or anxiety)
- Be specific about what you saw or did, not generic
- Be honest about your feelings

Examples of good reflections:
- "I've been really engaged with environmental content lately, especially hopeful messages about climate action, which align with my values and make me feel optimistic."
- "I've noticed a lot of alarming posts about environmental damage recently, which has made me more concerned and anxious, compelling me to comment more than usual."
- "I've been relatively quiet, mostly observing rather than posting, though I did like a few posts about sustainability that resonated with me."
- "The hope campaign really inspired me to share positive environmental content because I believe optimistic messaging drives real change in my network."

Your reflection (1-2 sentences):"""
    
    return prompt


def create_belief_assessment_prompt(
    persona: Dict[str, Any],
    attribute: str,
    memory_context: Optional[str] = None
) -> str:
    """
    Create prompt for belief assessment measurement with full persona context.
    
    CRITICAL FIX FOR MEDIAN COLLAPSE:
    Includes personality, interests, and baseline beliefs to prevent LLM from
    defaulting to median responses (Argyle et al., 2023; Hagendorff et al., 2023).
    Without persona context, all agents cluster around 5/10 regardless of traits.
    
    Used at T0/T1/T2 checkpoints to measure environmental_concern or brand_trust.
    
    Args:
        persona: Agent's persona dict
        attribute: 'environmental_concern' or 'brand_trust'
        memory_context: Optional string summarizing recent memories (for T1/T2)
    
    Returns:
        Prompt string for belief assessment
    
    References:
        Argyle et al. (2023). Out of one, many: Using LLMs to simulate human samples.
        Hagendorff et al. (2023). AI models collapse toward the mean in opinion simulations.
    """
    name = persona.get('name', 'User')
    age = persona.get('age', 30)
    
    # Extract personality traits and backstory
    personality = persona.get('personality', {})
    interests = persona.get('interests', [])
    backstory = persona.get('backstory', None)  # V2: Rich narrative
    
    openness = personality.get('openness', 0.5)
    neuroticism = personality.get('neuroticism', 0.5)
    
    # Convert numeric traits to categorical descriptors
    openness_desc = "high" if openness > 0.7 else "moderate" if openness > 0.4 else "low"
    neuro_desc = "high" if neuroticism > 0.7 else "moderate" if neuroticism > 0.4 else "low"
    
    if attribute == 'environmental_concern':
        # Extract baseline concern level
        initial_env_concern = persona.get('environmental_concern', 0.5)
        
        # Convert to natural language baseline
        if initial_env_concern > 0.7:
            concern_baseline = "You've always been deeply committed to environmental protection and climate action"
        elif initial_env_concern > 0.5:
            concern_baseline = "You care about the environment and try to make sustainable choices"
        elif initial_env_concern > 0.3:
            concern_baseline = "You're aware of environmental issues but they're not a top priority for you"
        elif initial_env_concern > 0.15:
            concern_baseline = "You're somewhat skeptical about environmental activism and climate concerns"
        else:
            concern_baseline = "You're highly skeptical of environmental movements and climate messaging"
        
        # Build prompt - USE BACKSTORY if available (V2), else traits (V1 fallback)
        if backstory:
            prompt = f"""You are {name}. {backstory}

Your current environmental stance based on your background and experiences:
- {concern_baseline}"""
        else:
            # Fallback to trait-based description
            prompt = f"""You are {name}, a {age}-year-old person.

Your personality:
- You have {openness_desc} openness to new ideas
- You have {neuro_desc} emotional sensitivity
- Your interests include: {', '.join(interests[:3]) if len(interests) >= 3 else ', '.join(interests)}

Your environmental stance:
- {concern_baseline}"""

        # Add memory context if provided (for T1/T2 measurements)
        if memory_context:
            prompt += f"""

Recent experiences on social media:
{memory_context}"""

        prompt += """

Please describe your current thoughts and feelings about environmental issues and 
climate change, considering both your background and any recent experiences.

Be specific about:
- How important these issues are to you right now
- Whether you feel motivated to take action
- How you've been thinking about this recently
- Any influences (posts, campaigns, discussions) that shaped your views

After your description, provide a summary rating from 0-10 that reflects your 
overall level of environmental concern.

Respond in this exact format:
THOUGHTS: [2-3 sentences describing your current stance and feelings]
RATING: [0-10]

Example responses:
THOUGHTS: I'm deeply concerned about climate change and it motivates me to act daily. 
The hopeful campaign I saw recently reinforced my belief that collective action works. 
I feel optimistic but also urgent about the need for change.
RATING: 8

THOUGHTS: I'm aware of environmental issues but I don't think about them much. 
I haven't seen anything recently that really caught my attention. There are other 
priorities that feel more immediate to me right now.
RATING: 3

Your response:"""
    
    elif attribute == 'brand_trust':
        prompt = f"""You are {name}, {age} years old.

Please reflect honestly on your current trust in brands and sponsored content on social media.

On a scale from 0 to 10:
- 0 = No trust in brands or sponsored content at all
- 5 = Moderate trust, depends on the brand
- 10 = High trust in brands and believe sponsored content is valuable

How would you currently rate your trust in brands and sponsored content?

Respond in this exact format:
RATING: [your number from 0-10]
REASONING: [1-2 sentences explaining your current stance]

Your response:"""
    
    else:
        # Generic belief prompt for other attributes
        prompt = f"""You are {name}, {age} years old.

Please reflect on your current attitude toward {attribute}.

On a scale from 0 to 10 (0 = very negative, 10 = very positive), how would you rate your current stance?

Respond in this exact format:
RATING: [your number from 0-10]
REASONING: [1-2 sentences explaining your current stance]

Your response:"""
    
    return prompt


def parse_belief_response(response: str) -> tuple[float, str]:
    """
    Parse belief assessment response in THOUGHTS + RATING format.
    
    UPDATED FOR HYBRID APPROACH:
    Now extracts qualitative thoughts (primary) and numeric rating (summary).
    This prevents numeric anchoring while maintaining quantitative measurement.
    
    Args:
        response: LLM response with THOUGHTS and RATING fields
    
    Returns:
        Tuple of (normalized_value [0,1], thoughts_text)
    
    Example input:
        "THOUGHTS: I'm deeply concerned about climate change...
         RATING: 8"
    
    Returns: (0.8, "I'm deeply concerned about climate change...")
    """
    lines = [line.strip() for line in response.split('\n') if line.strip()]
    
    rating = None
    thoughts = ""
    
    for i, line in enumerate(lines):
        if line.startswith('THOUGHTS:'):
            try:
                thoughts = line.split(':', 1)[1].strip()
                # Continue reading if thoughts span multiple lines
                # (until we hit RATING: or end of response)
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    if next_line.startswith('RATING:'):
                        break
                    thoughts += ' ' + next_line
            except (IndexError, ValueError):
                pass
        
        elif line.startswith('RATING:'):
            try:
                rating_str = line.split(':', 1)[1].strip()
                # Extract first number found
                import re
                match = re.search(r'\d+(\.\d+)?', rating_str)
                if match:
                    rating = float(match.group())
            except (IndexError, ValueError):
                pass
    
    # Normalize rating to [0, 1]
    if rating is not None:
        normalized = max(0.0, min(10.0, rating)) / 10.0
    else:
        # Fallback: try to infer from thoughts if no rating provided
        if thoughts:
            # Simple sentiment-based fallback
            thoughts_lower = thoughts.lower()
            if any(word in thoughts_lower for word in ['deeply', 'extremely', 'very concerned', 'committed']):
                normalized = 0.8
            elif any(word in thoughts_lower for word in ['concerned', 'care about', 'important']):
                normalized = 0.6
            elif any(word in thoughts_lower for word in ['somewhat', 'aware', 'moderately']):
                normalized = 0.5
            elif any(word in thoughts_lower for word in ['not really', 'skeptical', 'not concerned']):
                normalized = 0.3
            else:
                normalized = 0.5
        else:
            normalized = 0.5
            thoughts = "Failed to parse belief assessment"
    
    return normalized, thoughts


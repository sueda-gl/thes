"""
AI Agent with LLM-powered decision-making.

Combines two architectural approaches:
1. Park et al. (2023): Memory stream with importance-weighted retrieval
2. Activity-driven temporal dynamics: Heterogeneous user engagement

Social media users exhibit highly skewed activity patterns, with most being
"lurkers" and a small fraction creating most content (Murdock et al., 2024).
We model this via an Activity parameter that scales online time and posting rates.

References:
    Park, J. S., O'Brien, J. C., Cai, C. J., Morris, M. R., Liang, P., &
    Bernstein, M. S. (2023). Generative agents: Interactive simulacra of
    human behavior. arXiv preprint arXiv:2304.03442.
    
    Murdock, I., Carley, K. M., & Yağan, O. (2024). An agent-based model of
    cross-platform information diffusion and moderation. Social Network
    Analysis and Mining, 14, 145.
"""
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from llm.prompts import create_decision_prompt, parse_action_response
from llm.client import LLMClient
import config


@dataclass
class MemoryEntry:
    """
    Single memory entry with metadata for retrieval.
    Based on Park et al. 2023 memory stream structure.
    """
    timestamp: int  # simulation step
    memory_type: str  # 'observation', 'action', or 'reflection'
    content: str  # human-readable description
    importance: float  # 0-1 score
    metadata: Dict[str, Any]  # additional context
    
    def get_age(self, current_step: int) -> int:
        """Calculate how old this memory is."""
        return current_step - self.timestamp
    
    def get_retrieval_score(
        self, 
        current_step: int, 
        recency_weight: float = 0.5
    ) -> float:
        """
        Calculate retrieval score combining importance and recency.
        Park et al. 2023 formula: score = importance + recency_decay
        
        Args:
            current_step: Current simulation step
            recency_weight: Weight for recency component (0-1)
        
        Returns:
            Retrieval score (higher = more relevant)
        """
        age = self.get_age(current_step)
        recency_decay = recency_weight * (0.99 ** age)  # exponential decay
        return self.importance + recency_decay


class Agent:
    """
    AI agent that observes, decides, and acts on social media.
    
    Combines:
    - Park et al. (2023): Memory stream and reflection-based decision making
    - Activity-driven temporal behavior based on empirical social media patterns
      (Murdock et al., 2024: heterogeneous activity tiers)
    """
    
    def __init__(
        self,
        agent_id: str,
        persona: Dict[str, Any],
        llm_client: LLMClient,
        rng: Any = None
    ):
        """
        Initialize agent with Activity-driven behavior.
        
        Activity ~ U(0,1) creates heterogeneous users following empirical
        distributions where most are lurkers and few are highly active
        (Murdock et al., 2024).
        
        Args:
            agent_id: Unique agent identifier
            persona: Persona dictionary (includes demographics, interests)
            llm_client: Shared LLM client for decision-making
            rng: Random number generator for Activity mechanics
        """
        import random as _random
        if rng is None:
            rng = _random.Random()
        self.rng = rng
        
        self.agent_id = agent_id
        self.persona = persona
        self.llm_client = llm_client
        
        # ============================================
        # ACTIVITY MECHANICS (Murdock et al. 2024)
        # ============================================
        # Activity represents user engagement heterogeneity.
        # 
        # ENGAGED USER SUBSET MODELING:
        # We model the active/engaged user population by setting an activity floor.
        # Activity ∈ [0.3, 1.0] excludes the lowest-activity 30% (extreme lurkers)
        # and focuses on users who meaningfully participate in information diffusion.
        # 
        # Justification: Murdock et al. (2024) show that 75% of users are "lurkers"
        # who contribute minimally to cascades. By modeling engaged users, we ensure
        # sufficient interaction density for statistical power while remaining
        # consistent with the empirical finding that most diffusion is driven by
        # a minority of active users.
        # 
        # Activity ∈ [0.3, 1.0] → Online time ∈ [43, 143] min/day
        # This range spans casual-to-power users, excluding pure lurkers.
        self.activity = 0.3 + (rng.random() * 0.7)  # Engaged user subset
        
        # Online/offline finite state machine
        # Randomize initial state: higher-activity users more likely to start online
        # Steady-state: ~20-60% of agents online at any time (activity-dependent)
        online_probability = 0.2 + (0.4 * self.activity)  # 20% (low) to 60% (high)
        self.online = rng.random() < online_probability
        self.timer = 0  # Steps until state flip
        self._reset_timer()
        
        # Posting schedule (Poisson process)
        self.next_post_timer = 0  # Steps until next organic post
        self._schedule_next_post()
        
        # ============================================
        # MEMORY SYSTEM (Park et al. 2023)
        # ============================================
        self.memory_stream: List[MemoryEntry] = []  # All memories
        self.reflections: List[MemoryEntry] = []    # Generated reflections
        
        # Tracking
        self.actions_taken = []  # Keep for compatibility
        self.last_reflection_step = 0
        self.content_filter_hits = 0  # Track how many times this agent triggered filter
    
    def _reset_timer(self):
        """
        Reset online/offline timer based on Activity level.
        
        Higher-Activity users spend more time online, scaled linearly.
        Exponential dwell times create memoryless state transitions.
        
        Online duration: Activity × AVG_LOGIN (143 min/day average)
        Offline duration: DAY_MINUTES - online_minutes
        
        References:
            Murdock et al. (2024) for heterogeneous activity levels
            DataReportal (2024) for 143 min/day calibration
        """
        online_minutes = self.activity * config.AVG_LOGIN
        offline_minutes = config.DAY_MINUTES - online_minutes
        
        mean = online_minutes if self.online else offline_minutes
        # Exponential dwell time (in simulation steps = minutes)
        self.timer = max(1, int(self.rng.expovariate(1 / mean) if mean > 0 else 1))
    
    def _schedule_next_post(self):
        """
        Schedule next organic post using Poisson process.
        
        Posting rate scales with Activity, reflecting that high-activity users
        create most content (Murdock et al., 2024 show top 25% produce 97% of posts).
        
        Monthly post rate: Activity × AVG_POSTRATE
        Converts to per-step rate and draws exponential inter-arrival time.
        
        References:
            Murdock et al. (2024) for activity-scaled posting behavior
        """
        rate_per_month = self.activity * config.AVG_POSTRATE
        rate_per_step = rate_per_month / config.MONTH_STEPS
        
        if rate_per_step > 0:
            self.next_post_timer = max(1, int(self.rng.expovariate(rate_per_step)))
        else:
            self.next_post_timer = float('inf')  # Never post
    
    def tick(self, step: int):
        """
        Advance agent by one simulation step (1 minute).
        
        Manages:
        - Online/offline state transitions
        - Organic posting schedule
        
        Args:
            step: Current simulation step
        """
        # Decrement state timer
        self.timer -= 1
        if self.timer <= 0:
            # Flip state
            self.online = not self.online
            self._reset_timer()
        
        # If online, decrement posting timer
        if self.online:
            self.next_post_timer -= 1
    
    def should_create_organic_post(self) -> bool:
        """
        Check if it's time for an organic post.
        
        Returns:
            True if agent is online and posting timer expired
        """
        return self.online and self.next_post_timer <= 0
    
    def reset_post_timer(self):
        """Reset the posting timer after creating an organic post."""
        self._schedule_next_post()
    
    def calculate_importance(
        self,
        memory_type: str,
        content: Dict[str, Any]
    ) -> float:
        """
        Calculate importance score (0-1) for a memory.
        
        Importance factors (Park et al. 2023):
        - Campaign posts are highly important
        - High-engagement content is important
        - Own actions are more important than observations
        - Content matching agent interests is important
        
        Args:
            memory_type: 'observation' or 'action'
            content: Memory content dict
        
        Returns:
            Importance score 0-1
        """
        importance = 0.5  # baseline
        
        # Factor 1: Memory type - own actions are more important
        if memory_type == 'action':
            importance += 0.2
        
        # Factor 2: Campaign content - critical for experimental tracking
        if content.get('post_type') == 'campaign':
            importance += 0.3
        
        # Factor 3: Engagement level - popular content is important
        engagement = content.get('like_count', 0) + content.get('comment_count', 0)
        if engagement > 10:
            importance += 0.2
        elif engagement > 5:
            importance += 0.1
        
        # Factor 4: Interest alignment - relevant content is important
        post_content = str(content.get('content', '')).lower()
        agent_interests = [i.lower() for i in self.persona.get('interests', [])]
        
        if any(interest in post_content for interest in agent_interests):
            importance += 0.15
        
        # Factor 5: Emotional content - hope/fear framing (study-specific)
        if any(word in post_content for word in ['hope', 'bright', 'positive', 'together']):
            importance += 0.1  # Hope framing
        if any(word in post_content for word in ['fear', 'damage', 'severe', 'crisis', 'urgent']):
            importance += 0.1  # Fear framing
        
        # Clip to [0, 1]
        return min(1.0, max(0.0, importance))
    
    def observe(self, feed_items: List[Dict[str, Any]], step: int):
        """
        Observe feed items and store as memories with importance.
        Enhanced with Park et al. 2023 memory stream approach.
        
        Args:
            feed_items: List of posts/comments in feed
            step: Current simulation step
        """
        for item in feed_items:
            # Calculate importance for this observation
            importance = self.calculate_importance('observation', item)
            
            # Create human-readable content description
            author = item.get('agent_id', 'Unknown')
            post_type = item.get('post_type', 'organic')
            content_preview = item.get('content', '')[:80]  # First 80 chars
            
            if post_type == 'campaign':
                description = f"Saw campaign post: '{content_preview}'"
            else:
                description = f"Saw post by {author}: '{content_preview}'"
            
            # Create memory entry
            memory = MemoryEntry(
                timestamp=step,
                memory_type='observation',
                content=description,
                importance=importance,
                metadata={
                    'post_id': item.get('post_id'),
                    'post_type': post_type,
                    'engagement': item.get('like_count', 0) + item.get('comment_count', 0),
                    'full_content': item.get('content', '')
                }
            )
            
            self.memory_stream.append(memory)
    
    async def decide_action(self, feed_items: List[Dict[str, Any]], step: int) -> Dict[str, Any]:
        """
        Decide what action to take based on current feed.
        Includes LLM-based reflection if applicable (Park et al. 2023).
        
        V2 UPDATE: Content filter fallback - if rich backstory triggers Azure filter,
        retry with simplified trait-based prompt to ensure agent can still participate.
        
        Args:
            feed_items: Current feed items
            step: Current simulation step
        
        Returns:
            Action dict with type, parameters, and reason
        """
        # Generate LLM-based reflection if it's time
        reflection = await self.generate_reflection(step)
        
        # Try with full persona (backstory if available)
        prompt = create_decision_prompt(
            persona=self.persona,
            feed_items=feed_items,
            step=step,
            reflection=reflection
        )
        
        # Get LLM response
        response = await self.llm_client.generate(prompt)
        
        # FALLBACK: If content filter blocked, try simplified prompt without backstory
        if response is None and 'backstory' in self.persona:
            self.content_filter_hits += 1  # Track filter trigger
            
            # Create temporary persona without backstory for fallback
            persona_simple = self.persona.copy()
            persona_simple.pop('backstory', None)
            
            prompt_simple = create_decision_prompt(
                persona=persona_simple,
                feed_items=feed_items,
                step=step,
                reflection=reflection
            )
            
            response = await self.llm_client.generate(prompt_simple)
        
        if response is None:
            # Both attempts failed, default to no action
            return {'type': 'none', 'reason': 'LLM generation failed'}
        
        # Parse response into action
        action = parse_action_response(response, feed_items)
        
        return action
    
    def record_action(self, action: Dict[str, Any], step: int):
        """
        Record an action taken as a memory with reason.
        Enhanced with Park et al. 2023 memory stream approach.
        
        Args:
            action: Action dict with type, content, and reason
            step: Current simulation step
        """
        # Store in actions list (for compatibility)
        self.actions_taken.append({
            'step': step,
            'action': action
        })
        
        action_type = action.get('type')
        
        # Don't store "do nothing" as memory
        if action_type == 'none':
            return
        
        # Create human-readable description
        reason = action.get('reason', 'N/A')
        
        if action_type == 'like':
            description = f"I liked a post (reason: {reason})"
        elif action_type == 'comment':
            content = action.get('content', '')[:60]  # First 60 chars
            description = f"I commented: '{content}' (reason: {reason})"
        elif action_type == 'post':
            content = action.get('content', '')[:60]
            description = f"I created post: '{content}' (reason: {reason})"
        elif action_type == 'reshare':
            description = f"I reshared a post (reason: {reason})"
        else:
            description = f"I took action: {action_type}"
        
        # Calculate importance (actions have higher baseline)
        importance = self.calculate_importance('action', action)
        
        # Create memory entry
        memory = MemoryEntry(
            timestamp=step,
            memory_type='action',
            content=description,
            importance=importance,
            metadata={
                'action_type': action_type,
                'action_details': action.copy()
            }
        )
        
        self.memory_stream.append(memory)
    
    def retrieve_memories(
        self,
        current_step: int,
        k: int = None,
        recency_weight: float = None
    ) -> List[MemoryEntry]:
        """
        Retrieve top-k most relevant memories.
        
        Uses importance + recency scoring (Park et al. 2023).
        No vector embeddings needed - relies on importance scores.
        
        Args:
            current_step: Current simulation step
            k: Number of memories to retrieve (defaults to config)
            recency_weight: Weight for recency decay 0-1 (defaults to config)
        
        Returns:
            List of most relevant memory entries
        """
        if not self.memory_stream:
            return []
        
        # Use config defaults if not specified
        k = k or config.MEMORY_SUMMARY_K
        recency_weight = recency_weight or config.RETRIEVAL_RECENCY_WEIGHT
        
        # Calculate retrieval scores for all memories
        scored_memories = [
            (memory, memory.get_retrieval_score(current_step, recency_weight))
            for memory in self.memory_stream
        ]
        
        # Sort by score (highest first)
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k memories
        return [memory for memory, score in scored_memories[:k]]
    
    async def generate_reflection(self, current_step: int, force: bool = False) -> Optional[str]:
        """
        Generate LLM-based reflection from retrieved memories.
        Implements Park et al. 2023 memory→reflection with LLM synthesis.
        
        V2 UPDATE: Can be force-triggered at measurement points for focused reflection.
        
        Args:
            current_step: Current simulation step
            force: If True, generate reflection regardless of schedule
            
        Returns:
            Reflection string or None if not time to reflect
        """
        # If forced (e.g., before belief measurement), skip schedule checks
        if force:
            if len(self.memory_stream) < 3:
                return None  # Need minimum memories to reflect
        else:
            # Normal scheduled reflection
            if current_step % config.REFLECT_EVERY != 0 or len(self.memory_stream) < 3:
                return None
            
            # Don't reflect too soon after last reflection
            if current_step - self.last_reflection_step < config.REFLECT_EVERY:
                return None
        
        # Retrieve relevant memories using importance + recency
        relevant_memories = self.retrieve_memories(
            current_step=current_step,
            k=config.MEMORY_SUMMARY_K,
            recency_weight=config.RETRIEVAL_RECENCY_WEIGHT
        )
        
        if not relevant_memories:
            return None
        
        # Generate reflection using LLM
        from llm.prompts import create_reflection_prompt
        
        reflection_prompt = create_reflection_prompt(
            persona=self.persona,
            memories=relevant_memories,
            current_step=current_step
        )
        
        # Call LLM with lower temperature for consistent reflections
        reflection_text = await self.llm_client.generate(
            reflection_prompt,
            temperature=config.REFLECTION_TEMPERATURE,
            max_tokens=config.REFLECTION_MAX_TOKENS
        )
        
        if not reflection_text:
            return None
        
        # Clean up reflection text
        reflection_text = reflection_text.strip()
        
        # Store reflection as a memory itself (Park et al. 2023)
        reflection_memory = MemoryEntry(
            timestamp=current_step,
            memory_type='reflection',
            content=reflection_text,
            importance=0.8,  # Reflections are high importance
            metadata={'source_memories': [m.content for m in relevant_memories]}
        )
        
        self.reflections.append(reflection_memory)
        self.memory_stream.append(reflection_memory)
        self.last_reflection_step = current_step
        
        return reflection_text
    
    def get_behavior_style(self) -> str:
        """Get agent's social behavior style."""
        return self.persona.get('social_behavior', 'casual')
    
    async def measure_belief(
        self,
        attribute: str,
        step: int,
        db: Any
    ) -> float:
        """
        Measure agent's current belief on an attribute using LLM assessment.
        
        MEDIAN COLLAPSE FIX:
        Includes full persona context (personality, interests, baseline beliefs) and
        recent memory context to prevent LLM from defaulting to median responses.
        
        Used at T0/T1/T2 checkpoints to track belief evolution over time.
        The LLM responds as the agent reflecting on their current stance.
        
        Args:
            attribute: Belief attribute ('environmental_concern', 'brand_trust', etc.)
            step: Current simulation step
            db: Database connection for logging
        
        Returns:
            Normalized belief value [0, 1]
        
        References:
            Argyle et al. (2023). Out of one, many: Using LLMs to simulate human samples.
            Hagendorff et al. (2023). AI models collapse toward the mean in opinion simulations.
        """
        from llm.prompts import create_belief_assessment_prompt, parse_belief_response
        
        # Build memory context from recent experiences (if any memories exist)
        memory_context = None
        if len(self.memory_stream) > 0:
            # Retrieve top-5 most relevant memories (importance + recency)
            recent_memories = self.retrieve_memories(
                current_step=step,
                k=5,
                recency_weight=0.7  # Emphasize recent experiences
            )
            
            if recent_memories:
                memory_lines = []
                for mem in recent_memories:
                    age_steps = step - mem.timestamp
                    # Format: "- [Memory content] (X steps ago)"
                    memory_lines.append(f"- {mem.content} ({age_steps} steps ago)")
                memory_context = "\n".join(memory_lines)
        
        # Generate belief assessment prompt with full persona + memory context
        prompt = create_belief_assessment_prompt(
            persona=self.persona,
            attribute=attribute,
            memory_context=memory_context  # NEW: Include recent experiences
        )
        
        # Get LLM response with slightly higher temperature for variance
        response = await self.llm_client.generate(
            prompt,
            temperature=0.4,  # INCREASED from 0.3 to allow more individual variation
            max_tokens=250    # INCREASED from 200 to accommodate 2-3 sentence thoughts
        )
        
        # FALLBACK: If content filter blocked backstory prompt, try trait-based prompt
        if not response and 'backstory' in self.persona and self.persona['backstory']:
            self.content_filter_hits += 1  # Track filter trigger
            from llm.prompts import create_belief_assessment_prompt
            
            # Retry with persona without backstory
            persona_simple = self.persona.copy()
            persona_simple.pop('backstory', None)
            
            prompt_simple = create_belief_assessment_prompt(
                persona=persona_simple,
                attribute=attribute,
                memory_context=memory_context
            )
            
            response = await self.llm_client.generate(
                prompt_simple,
                temperature=0.4,
                max_tokens=250
            )
        
        if not response:
            # All attempts failed, use current persona baseline
            current_value = self.persona.get(attribute, 0.5)
            thoughts = "Failed to generate belief assessment (content filter or API error)"
        else:
            # Parse response (returns normalized_value, thoughts_text)
            # UPDATED: Now extracts THOUGHTS (qualitative) + RATING (quantitative)
            current_value, thoughts = parse_belief_response(response)
        
        # Log to database (reasoning field stores qualitative thoughts)
        await db.insert_belief_measurement(
            agent_id=self.agent_id,
            attribute=attribute,
            value=current_value,
            step=step,
            reasoning=thoughts  # Stores qualitative thoughts for rich data
        )
        
        # Update persona with measured value (allows belief to influence future decisions)
        self.persona[attribute] = current_value
        
        return current_value
    
    def __repr__(self):
        """String representation."""
        return (
            f"Agent({self.agent_id}, {self.persona.get('name')}, "
            f"age={self.persona.get('age')}, "
            f"behavior={self.get_behavior_style()})"
        )


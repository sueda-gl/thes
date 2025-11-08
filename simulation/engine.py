"""
Simulation engine orchestrating the entire experiment.
"""
import asyncio
import json
import random
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from database.db import Database
from simulation.agent import Agent
from simulation.platform import Platform
from llm.client import LLMClient
from personas.generator import load_personas
from personas.social_graph import generate_ba, convert_to_directed_follows, validate_ba_network
import config


class SimulationEngine:
    """Main simulation orchestrator."""
    
    def __init__(
        self,
        db_path: str = None,
        seed: int = None,
        n_steps: int = None,
        n_agents: int = None
    ):
        """
        Initialize simulation engine.
        
        Args:
            db_path: Path to database (defaults to config)
            seed: Random seed (defaults to config)
            n_steps: Number of simulation steps (defaults to config)
            n_agents: Number of agents to use (defaults to config)
        """
        self.db_path = db_path or config.DATABASE_PATH
        self.seed = seed if seed is not None else config.RANDOM_SEED
        self.n_steps = n_steps or config.SIMULATION_STEPS
        self.n_agents = n_agents or config.NUM_AGENTS
        
        # Set random seed
        random.seed(self.seed)
        
        # Components (initialized in setup)
        self.db: Optional[Database] = None
        self.platform: Optional[Platform] = None
        self.llm_client: Optional[LLMClient] = None
        self.agents: List[Agent] = []
        self.network_graph = None  # Store for stratified assignment
        
        # Tracking
        self.run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.step_metrics: List[Dict] = []
        self.campaign_assignments: Dict[str, str] = {}  # agent_id -> campaign_type
        self.directly_targeted_agents: List[str] = []  # Agents who received campaigns directly
        self.start_time = None  # Set when simulation starts
    
    async def initialize(self):
        """Initialize all components."""
        print(f"Initializing simulation (Run ID: {self.run_id})...")
        
        # Connect to database
        self.db = Database(self.db_path)
        await self.db.connect()
        print("✓ Database connected")
        
        # Clear previous data (for clean runs)
        await self.db.clear_all_data()
        print("✓ Database cleared")
        
        # Initialize platform
        self.platform = Platform(self.db)
        print("✓ Platform initialized")
        
        # Initialize LLM client
        self.llm_client = LLMClient()
        print("✓ LLM client initialized")
        
        # Load personas (use config.PERSONA_FILE if set, else default)
        persona_file = getattr(config, 'PERSONA_FILE', None)
        if persona_file and os.path.exists(persona_file):
            personas = load_personas(persona_file)[:self.n_agents]
            print(f"✓ Loaded {len(personas)} personas from {persona_file}")
        else:
            personas = load_personas()[:self.n_agents]
            print(f"✓ Loaded {len(personas)} personas")
        
        # Insert agents into database
        agent_data = [(p['agent_id'], p) for p in personas]
        await self.db.insert_agents_batch(agent_data)
        print(f"✓ Inserted {len(personas)} agents into database")
        
        # Create agent objects with individual RNGs
        for i, persona in enumerate(personas):
            # Each agent gets seeded RNG for reproducibility
            agent_rng = random.Random(self.seed + i)
            
            agent = Agent(
                agent_id=persona['agent_id'],
                persona=persona,
                llm_client=self.llm_client,
                rng=agent_rng
            )
            self.agents.append(agent)
        print(f"✓ Created {len(self.agents)} agent objects")
        
        # Build social graph using Barabási-Albert model
        print(f"  Generating scale-free network (BA model)...")
        agent_ids = [a.agent_id for a in self.agents]
        
        # Generate BA graph
        self.network_graph = generate_ba(
            n=len(agent_ids),
            m0=config.BA_M0,
            m=config.BA_M,
            seed=self.seed
        )
        
        # Validate network properties
        validation = validate_ba_network(self.network_graph, verbose=False)
        print(f"    γ̂ = {validation.get('gamma_hat', 'N/A')}, "
              f"clustering = {validation['avg_clustering']:.4f}")
        
        # Convert to directed follows
        follows = convert_to_directed_follows(self.network_graph, agent_ids)
        await self.db.insert_follows_batch(follows)
        
        # Calculate statistics
        from collections import Counter
        followee_counts = Counter(followee for _, followee in follows)
        most_followed = followee_counts.most_common(1)[0] if followee_counts else (None, 0)
        avg_degree = len(follows) / len(agent_ids) if agent_ids else 0
        
        print(f"  ✓ Created {len(follows)} follower relationships")
        print(f"✓ Social graph created:")
        print(f"  - {len(follows)} follow relationships")
        print(f"  - Avg {avg_degree:.1f} following per agent")
        print(f"  - Most popular agent: {most_followed[0]} ({most_followed[1]} followers)")
        
        # Record simulation run
        config_dict = {
            'n_agents': self.n_agents,
            'n_steps': self.n_steps,
            'seed': self.seed,
            'campaign_launch_step': config.CAMPAIGN_LAUNCH_STEP
        }
        await self.db.insert_simulation_run(
            run_id=self.run_id,
            config_dict=config_dict,
            total_steps=self.n_steps,
            total_agents=self.n_agents,
            seed=self.seed
        )
        print(f"✓ Simulation run recorded\n")
    
    async def run(self, progress_callback=None):
        """
        Run the complete simulation.
        
        Args:
            progress_callback: Optional callback function(step, total_steps, metrics)
        
        Returns:
            Final metrics dictionary
        """
        print(f"Starting simulation: {self.n_steps} steps with {self.n_agents} agents\n")
        print("=" * 60)
        
        self.start_time = datetime.utcnow()
        
        for step in range(1, self.n_steps + 1):
            print(f"\nSTEP {step}/{self.n_steps}")
            print("-" * 60)
            
            # Execute step
            step_metrics = await self.execute_step(step)
            self.step_metrics.append(step_metrics)
            
            # Progress callback
            if progress_callback:
                progress_callback(step, self.n_steps, step_metrics)
            
            # Token usage report every 10 steps
            if step % 10 == 0:
                usage = self.llm_client.get_usage_stats()
                print(f"\n💰 Token Usage (Step {step}):")
                print(f"   Requests: {usage['total_requests']:,} | "
                      f"Input: {usage['total_input_tokens']:,} | "
                      f"Output: {usage['total_output_tokens']:,} | "
                      f"Cost: ${usage['estimated_cost_usd']:.2f}")
            
            print(f"✓ Step {step} complete")
        
        # Finalize
        await self.finalize()
        
        print("\n" + "=" * 60)
        print("Simulation complete!")
        print("=" * 60)
        
        return self.get_summary()
    
    async def execute_step(self, step: int) -> Dict[str, Any]:
        """
        Execute one simulation step.
        
        Args:
            step: Current step number
        
        Returns:
            Step metrics
        """
        # 0. Belief measurement checkpoint (if applicable)
        if step in config.BELIEF_MEASUREMENT_STEPS:
            await self.belief_measurement_checkpoint(step)
        
        # 1. Advance agent temporal state (Activity-driven FSM)
        for agent in self.agents:
            agent.tick(step)
        
        # 2. Handle organic posting
        await self.organic_posting_phase(step)
        
        # 3. Campaign injection (if applicable)
        if step == config.CAMPAIGN_LAUNCH_STEP:
            await self.inject_campaigns(step)
        
        # 4. Observation phase
        await self.observation_phase(step)
        
        # 5. Decision phase
        agent_actions = await self.decision_phase(step)
        
        # 6. Action execution phase
        await self.action_phase(agent_actions, step)
        
        # 7. Calculate step metrics
        metrics = await self.calculate_step_metrics(step)
        
        return metrics
    
    async def belief_measurement_checkpoint(self, step: int):
        """
        Measure beliefs at T0/T1/T2 checkpoints for longitudinal analysis.
        
        V2 UPDATE: Triggers reflection before measurement for focused self-assessment.
        Agents reflect on recent experiences, then immediately assess beliefs.
        This creates coherent reflection→measurement sequence.
        
        Checkpoint timing (configurable via config.BELIEF_MEASUREMENT_STEPS):
        - T0: Baseline measurement (all agents, before campaign)
        - T1: Immediate effect (targeted agents only, shortly after campaign)
        - T2: Sustained effect (targeted agents only, end of simulation)
        
        Args:
            step: Current simulation step
        """
        print(f"\n  📊 BELIEF MEASUREMENT CHECKPOINT (T{config.BELIEF_MEASUREMENT_STEPS.index(step)})")
        
        # Determine which agents to measure
        if step == config.BELIEF_MEASUREMENT_STEPS[0]:
            # T0: Measure all agents (baseline)
            agents_to_measure = self.agents
            print(f"  - Measuring all {len(agents_to_measure)} agents (baseline)")
        else:
            # T1/T2: Measure only directly targeted agents
            agents_to_measure = [
                agent for agent in self.agents
                if agent.agent_id in self.directly_targeted_agents
            ]
            print(f"  - Measuring {len(agents_to_measure)} directly-targeted agents")
        
        # STEP 1: Generate reflections for all agents being measured
        print(f"  - Step 1: Generating reflections before measurement...")
        reflection_count = 0
        for agent in agents_to_measure:
            reflection = await agent.generate_reflection(step, force=True)
            if reflection:
                reflection_count += 1
        print(f"    ✓ {reflection_count}/{len(agents_to_measure)} agents reflected")
        
        # STEP 2: Measure beliefs in batches with concurrency limit
        print(f"  - Step 2: Measuring beliefs...")
        semaphore = asyncio.Semaphore(config.BELIEF_CONCURRENCY_LIMIT)
        
        async def measure_with_semaphore(agent):
            async with semaphore:
                try:
                    value = await agent.measure_belief(
                        attribute=config.BELIEF_ATTRIBUTE,
                        step=step,
                        db=self.db
                    )
                    return value
                except Exception as e:
                    print(f"  ⚠️  Error measuring belief for {agent.agent_id}: {e}")
                    return None
        
        # Execute measurements in parallel (respecting concurrency limit)
        results = await asyncio.gather(*[
            measure_with_semaphore(agent)
            for agent in agents_to_measure
        ])
        
        # Calculate statistics
        valid_results = [r for r in results if r is not None]
        if valid_results:
            avg_belief = sum(valid_results) / len(valid_results)
            print(f"  ✓ Measured {len(valid_results)}/{len(agents_to_measure)} agents")
            print(f"  ✓ Average {config.BELIEF_ATTRIBUTE}: {avg_belief:.3f}")
        else:
            print(f"  ⚠️  No valid measurements collected")
    
    async def inject_campaigns(self, step: int):
        """
        Inject hope and fear campaigns using stratified assignment.
        
        Uses stratified random sampling to balance Activity and network
        centrality across Hope and Fear groups, preventing confounds.
        """
        print(f"\n  🎯 CAMPAIGN INJECTION (Stratified Assignment)")
        
        # Import stratified assignment
        from simulation.targeting import (
            stratified_campaign_assignment,
            validate_assignment_balance
        )
        
        # Stratified assignment by Activity × Degree
        hope_ids, fear_ids = stratified_campaign_assignment(
            agents=self.agents,
            network_graph=self.network_graph,
            frac_hope=config.CAMPAIGN_FRAC_HOPE,
            frac_fear=config.CAMPAIGN_FRAC_FEAR,
            seed=self.seed
        )
        
        # Validate balance
        balance = validate_assignment_balance(
            self.agents,
            hope_ids,
            fear_ids,
            self.network_graph,
            verbose=True
        )
        
        if not balance['balanced']:
            print("  ⚠️  Warning: Assignment not fully balanced - may introduce bias")
        
        # Record assignments
        for aid in hope_ids:
            self.campaign_assignments[aid] = 'hope'
        for aid in fear_ids:
            self.campaign_assignments[aid] = 'fear'
        
        # Track all directly targeted agents for belief measurement
        self.directly_targeted_agents = hope_ids + fear_ids
        
        # Inject hope campaign
        hope_config = config.CAMPAIGNS['hope']
        targeted_hope = await self.platform.inject_campaign(
            campaign_id='campaign_hope',
            campaign_type=hope_config['type'],
            message=hope_config['message'],
            target_agents=hope_ids,
            step=step
        )
        print(f"  ✓ Hope campaign → {len(targeted_hope)} agents (stratified)")
        
        # Inject fear campaign
        fear_config = config.CAMPAIGNS['fear']
        targeted_fear = await self.platform.inject_campaign(
            campaign_id='campaign_fear',
            campaign_type=fear_config['type'],
            message=fear_config['message'],
            target_agents=fear_ids,
            step=step
        )
        print(f"  ✓ Fear campaign → {len(targeted_fear)} agents (stratified)")
        print(f"  ✓ Total directly targeted: {len(self.directly_targeted_agents)} agents")
    
    async def organic_posting_phase(self, step: int):
        """
        Handle organic posting based on Activity-driven Poisson schedule.
        
        V2 UPDATE: Uses LLM to generate personality-driven organic content.
        Each agent checks if their posting timer expired; if so, creates
        an organic post and reschedules.
        """
        posts_created = 0
        
        for agent in self.agents:
            if agent.should_create_organic_post():
                # Generate LLM-driven organic content (V2: async)
                content = await self._generate_organic_content(agent)
                
                await self.platform.create_post(
                    agent_id=agent.agent_id,
                    content=content,
                    post_type='organic',
                    step=step
                )
                
                agent.reset_post_timer()
                posts_created += 1
        
        if posts_created > 0 and step % 100 == 0:
            print(f"  📝 {posts_created} organic posts created")
    
    async def _generate_organic_content(self, agent: Agent) -> str:
        """
        Generate organic post content using LLM for personality-driven realism.
        
        V2 UPDATE: Uses LLM instead of templates to create authentic posts
        that reflect agent's personality, backstory, and recent experiences.
        """
        # Get recent memories for context
        recent_memories = []
        if len(agent.memory_stream) > 0:
            recent_memories = agent.retrieve_memories(
                current_step=self.platform.current_step,
                k=3,
                recency_weight=0.8
            )
        
        # Build memory context
        memory_text = ""
        if recent_memories:
            memory_lines = [f"- {mem.content}" for mem in recent_memories[:2]]
            memory_text = "\n".join(memory_lines)
        
        # Get backstory if available
        backstory = agent.persona.get('backstory', '')
        name = agent.persona.get('name', 'User')
        interests = agent.persona.get('interests', ['life'])
        
        # Build prompt
        if backstory:
            context = f"You are {name}. {backstory[:200]}..."  # Truncate for brevity
        else:
            context = f"You are {name}, interested in {', '.join(interests[:2])}."
        
        prompt = f"""{context}

You want to share something on social media. Write a brief post (1-2 sentences) about 
something you're thinking about, experiencing, or reacting to.

Be authentic - write how you actually think and speak, not how a brand would post.

Your post:"""
        
        try:
            content = await agent.llm_client.generate(
                prompt,
                temperature=0.7,  # Higher for creative variation
                max_tokens=100
            )
            
            # If content filter blocked and backstory was used, try without backstory
            if content is None and backstory:
                prompt_simple = f"""You want to share something on social media about {random.choice(interests)}.

Write a brief post (1-2 sentences).

Your post:"""
                content = await agent.llm_client.generate(
                    prompt_simple,
                    temperature=0.7,
                    max_tokens=100
                )
            
            return content.strip() if content else f"Thinking about {random.choice(interests)}..."
        except Exception as e:
            # Fallback to template if all LLM attempts fail
            return f"Thinking about {random.choice(interests)}..."
    
    async def observation_phase(self, step: int):
        """Online agents observe their feeds."""
        print(f"\n  👀 OBSERVATION PHASE")
        
        observation_count = 0
        secondary_exposures_this_step = 0
        online_agents = 0
        
        for agent in self.agents:
            # Only online agents can observe feeds (Activity FSM)
            if not agent.online:
                continue
            
            online_agents += 1
            
            # Build personalized feed
            feed = await self.platform.build_feed(agent.agent_id, step)
            
            # Agent observes
            agent.observe(feed, step)
            
            # Record observations
            post_ids = [item['post_id'] for item in feed]
            await self.platform.record_observations(agent.agent_id, post_ids, step)
            
            observation_count += len(post_ids)
            
            # Track campaign exposures with cascade depth
            for item in feed:
                post_id = item.get('post_id', '')
                cascade_depth = item.get('cascade_depth', 0)
                
                # Check if this post is part of a campaign cascade
                campaign_id = await self.platform.get_campaign_origin(post_id)
                if campaign_id:
                    # Log exposure with cascade depth tracking
                    await self.db.log_campaign_exposure(
                        agent_id=agent.agent_id,
                        post_id=post_id,
                        campaign_id=campaign_id,
                        cascade_depth=cascade_depth,
                        exposure_step=step,
                        responded=False,
                        action_type=None
                    )
                    
                    # Count non-direct exposures as secondary
                    if cascade_depth > 0:
                        secondary_exposures_this_step += 1
        
        print(f"  ✓ {online_agents}/{len(self.agents)} agents online")
        print(f"  ✓ {observation_count} total observations")
        if secondary_exposures_this_step > 0:
            print(f"  ✓ {secondary_exposures_this_step} secondary exposure events this step")
    
    async def decision_phase(self, step: int) -> List[tuple]:
        """
        Online agents decide actions in parallel batches.
        
        Only agents currently online (Activity FSM) make decisions.
        
        Returns:
            List of (agent, action) tuples
        """
        print(f"\n  🧠 DECISION PHASE")
        
        decisions = []
        batch_size = config.LLM_MAX_CONCURRENT
        
        # Filter to online agents only (Activity FSM)
        active_agents = [a for a in self.agents if a.online]
        print(f"  - {len(active_agents)}/{len(self.agents)} agents online and deciding")
        
        # Process in batches
        for i in range(0, len(active_agents), batch_size):
            batch = active_agents[i:i + batch_size]
            
            # Get feeds and make decisions in parallel
            batch_decisions = await asyncio.gather(*[
                self._agent_decision(agent, step)
                for agent in batch
            ])
            
            decisions.extend(batch_decisions)
            
            print(f"  ✓ Batch {i//batch_size + 1}: {len(batch)} agents decided")
        
        # Count action types
        action_counts = {}
        for agent, action in decisions:
            action_type = action['type']
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        print(f"  Actions: {dict(action_counts)}")
        
        return decisions
    
    async def _agent_decision(self, agent: Agent, step: int) -> tuple:
        """Helper: Single agent decision."""
        # Build feed
        feed = await self.platform.build_feed(agent.agent_id, step)
        
        # Decide action
        action = await agent.decide_action(feed, step)
        
        return (agent, action)
    
    async def action_phase(self, agent_actions: List[tuple], step: int):
        """Execute all agent actions."""
        print(f"\n  ⚡ ACTION EXECUTION")
        
        counts = {'like': 0, 'comment': 0, 'post': 0, 'reshare': 0, 'none': 0}
        
        for agent, action in agent_actions:
            action_type = action['type']
            counts[action_type] += 1
            
            try:
                if action_type == 'like':
                    await self.platform.create_like(
                        agent_id=agent.agent_id,
                        post_id=action['post_id'],
                        step=step
                    )
                    # Check if it's a campaign post
                    await self._check_campaign_response(agent.agent_id, action['post_id'], 'like')
                
                elif action_type == 'comment':
                    await self.platform.create_comment(
                        agent_id=agent.agent_id,
                        parent_post_id=action['parent_post_id'],
                        content=action['content'],
                        step=step
                    )
                    await self._check_campaign_response(agent.agent_id, action['parent_post_id'], 'comment')
                
                elif action_type == 'reshare':
                    post_id = await self.platform.create_reshare(
                        agent_id=agent.agent_id,
                        parent_post_id=action['parent_post_id'],
                        content=action.get('content'),  # Optional share comment
                        step=step
                    )
                    await self._check_campaign_response(agent.agent_id, action['parent_post_id'], 'post')
                
                elif action_type == 'post':
                    await self.platform.create_post(
                        agent_id=agent.agent_id,
                        content=action['content'],
                        post_type='organic',
                        step=step
                    )
                    # Note: Organic posts aren't direct campaign responses
                    # Campaign response tracking happens via _check_campaign_response for likes/comments/reshares
                
                # Record action
                agent.record_action(action, step)
            
            except Exception as e:
                print(f"  ⚠️  Error executing action for {agent.agent_id}: {e}")
        
        print(f"  ✓ Executed: {counts['like']} likes, {counts['comment']} comments, {counts['post']} posts, {counts['reshare']} reshares")
    
    async def _check_campaign_response(self, agent_id: str, post_id: str, action_type: str):
        """Check if action is a response to a campaign post."""
        # Get post
        post = await self.platform.get_post(post_id)
        
        if post and post.get('post_type') == 'campaign':
            # Mark as responded (post_id is the campaign post they interacted with)
            await self.platform.track_campaign_response(
                agent_id=agent_id,
                post_id=post_id,
                action_type=action_type
            )
    
    async def calculate_step_metrics(self, step: int) -> Dict[str, Any]:
        """Calculate metrics for this step."""
        # Get posts from this step
        posts = await self.db.get_posts_by_step(step)
        
        # Count by type
        campaign_posts = sum(1 for p in posts if p['post_type'] == 'campaign')
        organic_posts = sum(1 for p in posts if p['post_type'] != 'campaign')
        
        # Get total likes and comments this step
        # (This is a simplified version; full metrics calculated later)
        total_likes = sum(p['like_count'] for p in posts)
        total_comments = sum(p['comment_count'] for p in posts)
        
        return {
            'step': step,
            'campaign_posts': campaign_posts,
            'organic_posts': organic_posts,
            'total_likes': total_likes,
            'total_comments': total_comments
        }
    
    async def finalize(self):
        """Finalize simulation."""
        # Update simulation status
        await self.db.update_simulation_status(self.run_id, 'completed')
        
        # Print LLM usage
        usage = self.llm_client.get_usage_stats()
        print(f"\nLLM Usage:")
        print(f"  - Total requests: {usage['total_requests']}")
        print(f"  - Failed requests: {usage['failed_requests']}")
        print(f"  - Total tokens: {usage['total_tokens']:,}")
        print(f"  - Estimated cost: ${usage['estimated_cost_usd']:.4f}")
        
        # Check for content filter issues
        filtered_agents = [(a.agent_id, a.content_filter_hits) for a in self.agents if a.content_filter_hits > 0]
        if filtered_agents:
            print(f"\n⚠️  Content Filter Report:")
            print(f"  - {len(filtered_agents)}/{len(self.agents)} agents triggered content filters")
            print(f"  - These agents used simplified prompts (backstory removed)")
            print(f"  - Total filter hits: {sum(hits for _, hits in filtered_agents)}")
            if len(filtered_agents) <= 10:
                print(f"\n  Affected agents:")
                for agent_id, hits in sorted(filtered_agents, key=lambda x: x[1], reverse=True):
                    print(f"    {agent_id}: {hits} filter triggers")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get simulation summary."""
        return {
            'run_id': self.run_id,
            'n_agents': self.n_agents,
            'n_steps': self.n_steps,
            'seed': self.seed,
            'step_metrics': self.step_metrics,
            'llm_usage': self.llm_client.get_usage_stats(),
            'campaign_assignments': self.campaign_assignments
        }
    
    async def close(self):
        """Close all connections."""
        if self.llm_client:
            await self.llm_client.close()
        if self.db:
            await self.db.close()


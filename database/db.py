"""
Database operations for the AI Social Media Simulation.
"""
import aiosqlite
import json
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import config


class Database:
    """Async SQLite database manager."""
    
    def __init__(self, db_path: str = None):
        """Initialize database connection."""
        self.db_path = db_path or config.DATABASE_PATH
        self.conn: Optional[aiosqlite.Connection] = None
    
    async def connect(self):
        """Establish database connection and create tables."""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Connect to database
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row
        
        # Load and execute schema
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_path, 'r') as f:
            schema = f.read()
        
        await self.conn.executescript(schema)
        await self.conn.commit()
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # ============================================
    # AGENTS
    # ============================================
    
    async def insert_agent(self, agent_id: str, persona: Dict[str, Any]):
        """Insert a new agent."""
        await self.conn.execute(
            "INSERT INTO agents (agent_id, persona) VALUES (?, ?)",
            (agent_id, json.dumps(persona))
        )
        await self.conn.commit()
    
    async def insert_agents_batch(self, agents: List[tuple]):
        """Insert multiple agents at once."""
        await self.conn.executemany(
            "INSERT INTO agents (agent_id, persona) VALUES (?, ?)",
            [(aid, json.dumps(persona)) for aid, persona in agents]
        )
        await self.conn.commit()
    
    async def get_agent(self, agent_id: str) -> Optional[Dict]:
        """Get agent by ID."""
        async with self.conn.execute(
            "SELECT * FROM agents WHERE agent_id = ?", (agent_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return {
                    'agent_id': row['agent_id'],
                    'persona': json.loads(row['persona']),
                    'created_at': row['created_at']
                }
            return None
    
    async def get_all_agents(self) -> List[Dict]:
        """Get all agents."""
        async with self.conn.execute("SELECT * FROM agents") as cursor:
            rows = await cursor.fetchall()
            return [
                {
                    'agent_id': row['agent_id'],
                    'persona': json.loads(row['persona']),
                    'created_at': row['created_at']
                }
                for row in rows
            ]
    
    # ============================================
    # POSTS
    # ============================================
    
    async def insert_post(
        self,
        post_id: str,
        agent_id: str,
        content: str,
        post_type: str,
        created_step: int,
        parent_post_id: Optional[str] = None,
        cascade_depth: int = 0
    ) -> str:
        """
        Insert a new post or comment.
        
        Args:
            post_id: Unique post identifier
            agent_id: Author's agent ID
            content: Post text content
            post_type: 'campaign', 'organic', 'response', or 'reshare'
            created_step: Simulation step when created
            parent_post_id: Parent post ID if this is a comment/reshare
            cascade_depth: Cascade depth (0=original, 1=1st reshare, etc.)
        
        Returns:
            post_id
        """
        await self.conn.execute(
            """INSERT INTO posts 
               (post_id, agent_id, content, post_type, parent_post_id, created_step, cascade_depth)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (post_id, agent_id, content, post_type, parent_post_id, created_step, cascade_depth)
        )
        await self.conn.commit()
        
        # If this is a comment, increment parent's comment count
        if parent_post_id:
            await self.increment_comment_count(parent_post_id)
        
        return post_id
    
    async def get_post(self, post_id: str) -> Optional[Dict]:
        """Get post by ID."""
        async with self.conn.execute(
            "SELECT * FROM posts WHERE post_id = ?", (post_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    async def get_posts_by_step(self, step: int) -> List[Dict]:
        """Get all posts created in a specific step."""
        async with self.conn.execute(
            "SELECT * FROM posts WHERE created_step = ? ORDER BY created_at",
            (step,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_posts_by_agent(self, agent_id: str, limit: int = None) -> List[Dict]:
        """Get posts by a specific agent."""
        query = "SELECT * FROM posts WHERE agent_id = ? ORDER BY created_step DESC"
        params = [agent_id]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_posts_for_feed(
        self,
        agent_ids: List[str],
        max_step: int,
        min_step: int = 0,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get posts from specific agents within a step range.
        
        Includes:
        - Original posts (parent_post_id IS NULL)
        - Reshares (post_type = 'reshare')
        
        Excludes:
        - Comments (post_type = 'response' with parent_id)
        
        This allows reshares to propagate through the network while keeping
        comment threads separate from main feed.
        """
        placeholders = ','.join('?' * len(agent_ids))
        query = f"""
            SELECT * FROM posts 
            WHERE agent_id IN ({placeholders})
            AND created_step <= ?
            AND created_step >= ?
            AND (parent_post_id IS NULL OR post_type = 'reshare')
            ORDER BY created_step DESC
            LIMIT ?
        """
        params = agent_ids + [max_step, min_step, limit]
        
        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_comments_for_post(self, post_id: str) -> List[Dict]:
        """Get all comments for a post."""
        async with self.conn.execute(
            """SELECT * FROM posts 
               WHERE parent_post_id = ? 
               ORDER BY created_at""",
            (post_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def increment_like_count(self, post_id: str):
        """Increment like count for a post."""
        await self.conn.execute(
            "UPDATE posts SET like_count = like_count + 1 WHERE post_id = ?",
            (post_id,)
        )
        await self.conn.commit()
    
    async def increment_comment_count(self, post_id: str):
        """Increment comment count for a post."""
        await self.conn.execute(
            "UPDATE posts SET comment_count = comment_count + 1 WHERE post_id = ?",
            (post_id,)
        )
        await self.conn.commit()
    
    # ============================================
    # FOLLOWS (Social Graph)
    # ============================================
    
    async def insert_follow(self, follower_id: str, followee_id: str):
        """Create a follow relationship."""
        await self.conn.execute(
            "INSERT OR IGNORE INTO follows (follower_id, followee_id) VALUES (?, ?)",
            (follower_id, followee_id)
        )
        await self.conn.commit()
    
    async def insert_follows_batch(self, follows: List[tuple]):
        """Insert multiple follow relationships."""
        await self.conn.executemany(
            "INSERT OR IGNORE INTO follows (follower_id, followee_id) VALUES (?, ?)",
            follows
        )
        await self.conn.commit()
    
    async def get_following(self, agent_id: str) -> List[str]:
        """Get list of agents this agent follows."""
        async with self.conn.execute(
            "SELECT followee_id FROM follows WHERE follower_id = ?",
            (agent_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row['followee_id'] for row in rows]
    
    async def get_followers(self, agent_id: str) -> List[str]:
        """Get list of agents following this agent."""
        async with self.conn.execute(
            "SELECT follower_id FROM follows WHERE followee_id = ?",
            (agent_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [row['follower_id'] for row in rows]
    
    # ============================================
    # INTERACTIONS
    # ============================================
    
    async def insert_interaction(
        self,
        agent_id: str,
        post_id: str,
        interaction_type: str,
        created_step: int
    ):
        """Record an interaction (like)."""
        try:
            await self.conn.execute(
                """INSERT INTO interactions 
                   (agent_id, post_id, interaction_type, created_step)
                   VALUES (?, ?, ?, ?)""",
                (agent_id, post_id, interaction_type, created_step)
            )
            await self.conn.commit()
            
            # Increment post like count if it's a like
            if interaction_type == 'like':
                await self.increment_like_count(post_id)
        except aiosqlite.IntegrityError:
            # Already liked this post
            pass
    
    async def get_interactions_by_post(self, post_id: str) -> List[Dict]:
        """Get all interactions for a post."""
        async with self.conn.execute(
            "SELECT * FROM interactions WHERE post_id = ?",
            (post_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_interactions_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all interactions by an agent."""
        async with self.conn.execute(
            "SELECT * FROM interactions WHERE agent_id = ?",
            (agent_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ============================================
    # OBSERVATIONS
    # ============================================
    
    async def insert_observation(
        self,
        agent_id: str,
        post_id: str,
        seen_step: int
    ):
        """Record that an agent saw a post."""
        await self.conn.execute(
            "INSERT INTO observations (agent_id, post_id, seen_step) VALUES (?, ?, ?)",
            (agent_id, post_id, seen_step)
        )
        await self.conn.commit()
    
    async def insert_observations_batch(self, observations: List[tuple]):
        """Insert multiple observations."""
        await self.conn.executemany(
            "INSERT INTO observations (agent_id, post_id, seen_step) VALUES (?, ?, ?)",
            observations
        )
        await self.conn.commit()
    
    async def get_observations_by_agent(self, agent_id: str, step: int = None) -> List[Dict]:
        """Get what an agent has observed."""
        if step is not None:
            query = "SELECT * FROM observations WHERE agent_id = ? AND seen_step = ?"
            params = (agent_id, step)
        else:
            query = "SELECT * FROM observations WHERE agent_id = ?"
            params = (agent_id,)
        
        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ============================================
    # CAMPAIGNS
    # ============================================
    
    async def insert_campaign(
        self,
        campaign_id: str,
        campaign_type: str,
        message: str,
        launch_step: int
    ):
        """Insert a campaign."""
        await self.conn.execute(
            """INSERT INTO campaigns 
               (campaign_id, campaign_type, message, launch_step)
               VALUES (?, ?, ?, ?)""",
            (campaign_id, campaign_type, message, launch_step)
        )
        await self.conn.commit()
    
    async def get_campaign(self, campaign_id: str) -> Optional[Dict]:
        """Get campaign by ID."""
        async with self.conn.execute(
            "SELECT * FROM campaigns WHERE campaign_id = ?",
            (campaign_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    # ============================================
    # CAMPAIGN EXPOSURES
    # ============================================
    
    async def log_campaign_exposure(
        self,
        agent_id: str,
        post_id: str,
        campaign_id: str,
        cascade_depth: int,
        exposure_step: int,
        responded: bool = False,
        action_type: Optional[str] = None
    ):
        """
        Record a campaign exposure with cascade depth tracking.
        
        Args:
            agent_id: Agent who saw the post
            post_id: Specific post seen
            campaign_id: Campaign identifier
            cascade_depth: 0=direct campaign, 1=1st reshare, etc.
            exposure_step: When exposed
            responded: Whether agent took action
            action_type: Type of action ('like', 'comment', 'reshare')
        """
        try:
            await self.conn.execute(
                """INSERT INTO campaign_exposures 
                       (agent_id, post_id, campaign_id, cascade_depth, exposure_step, responded, action_type)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (agent_id, post_id, campaign_id, cascade_depth, exposure_step, responded, action_type)
            )
            await self.conn.commit()
        except aiosqlite.IntegrityError:
            # Already logged this exposure (agent saw this specific post before)
            pass
    
    async def update_exposure_response(
        self,
        agent_id: str,
        post_id: str,
        action_type: str
    ):
        """Update exposure to mark as responded."""
        await self.conn.execute(
            """UPDATE campaign_exposures 
               SET responded = TRUE, action_type = ?
               WHERE agent_id = ? AND post_id = ?""",
            (action_type, agent_id, post_id)
        )
        await self.conn.commit()
    
    async def get_exposures_by_campaign(self, campaign_id: str) -> List[Dict]:
        """Get all exposures for a campaign."""
        async with self.conn.execute(
            "SELECT * FROM campaign_exposures WHERE campaign_id = ?",
            (campaign_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_exposures_by_agent(self, agent_id: str) -> List[Dict]:
        """Get all exposures for an agent."""
        async with self.conn.execute(
            "SELECT * FROM campaign_exposures WHERE agent_id = ?",
            (agent_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ============================================
    # SIMULATION RUNS
    # ============================================
    
    async def insert_simulation_run(
        self,
        run_id: str,
        config_dict: Dict[str, Any],
        total_steps: int,
        total_agents: int,
        seed: int
    ):
        """Record a simulation run."""
        await self.conn.execute(
            """INSERT INTO simulation_runs 
               (run_id, config, status, total_steps, total_agents, seed)
               VALUES (?, ?, 'running', ?, ?, ?)""",
            (run_id, json.dumps(config_dict), total_steps, total_agents, seed)
        )
        await self.conn.commit()
    
    async def update_simulation_status(
        self,
        run_id: str,
        status: str,
        completed_at: str = None
    ):
        """Update simulation run status."""
        if completed_at is None:
            completed_at = datetime.utcnow().isoformat()
        
        await self.conn.execute(
            """UPDATE simulation_runs 
               SET status = ?, completed_at = ?
               WHERE run_id = ?""",
            (status, completed_at, run_id)
        )
        await self.conn.commit()
    
    # ============================================
    # BELIEF MEASUREMENTS
    # ============================================
    
    async def insert_belief_measurement(
        self,
        agent_id: str,
        attribute: str,
        value: float,
        step: int,
        reasoning: Optional[str] = None
    ):
        """
        Record a belief measurement.
        
        Args:
            agent_id: Agent ID
            attribute: Belief attribute ('environmental_concern', 'brand_trust', etc.)
            value: Normalized value [0, 1]
            step: Measurement step
            reasoning: LLM's explanation for the value
        """
        await self.conn.execute(
            """INSERT OR REPLACE INTO belief_measurements 
               (agent_id, attribute, value, step, reasoning)
               VALUES (?, ?, ?, ?, ?)""",
            (agent_id, attribute, value, step, reasoning)
        )
        await self.conn.commit()
    
    async def get_belief_history(
        self,
        agent_id: str,
        attribute: str
    ) -> List[Dict]:
        """
        Get belief history for an agent.
        
        Args:
            agent_id: Agent ID
            attribute: Belief attribute
        
        Returns:
            List of measurements ordered by step
        """
        async with self.conn.execute(
            """SELECT * FROM belief_measurements 
               WHERE agent_id = ? AND attribute = ?
               ORDER BY step""",
            (agent_id, attribute)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_beliefs_at_step(
        self,
        step: int,
        attribute: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all belief measurements at a specific step.
        
        Args:
            step: Measurement step
            attribute: Optional filter by attribute
        
        Returns:
            List of belief measurements
        """
        if attribute:
            query = "SELECT * FROM belief_measurements WHERE step = ? AND attribute = ?"
            params = (step, attribute)
        else:
            query = "SELECT * FROM belief_measurements WHERE step = ?"
            params = (step,)
        
        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_directly_targeted_agents(
        self,
        campaign_type: Optional[str] = None
    ) -> List[str]:
        """
        Get list of agents who were directly targeted by campaigns (cascade_depth=0).
        
        Args:
            campaign_type: Optional filter by 'hope' or 'fear'
        
        Returns:
            List of agent IDs
        """
        if campaign_type:
            query = """
                SELECT DISTINCT ce.agent_id 
                FROM campaign_exposures ce
                JOIN campaigns c ON ce.campaign_id = c.campaign_id
                WHERE ce.cascade_depth = 0 AND c.campaign_type = ?
            """
            params = (campaign_type,)
        else:
            query = """
                SELECT DISTINCT agent_id 
                FROM campaign_exposures 
                WHERE cascade_depth = 0
            """
            params = ()
        
        async with self.conn.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [row['agent_id'] for row in rows]
    
    # ============================================
    # UTILITY QUERIES
    # ============================================
    
    async def clear_all_data(self):
        """Clear all data from all tables (for testing)."""
        tables = [
            'belief_measurements',
            'campaign_exposures',
            'observations',
            'interactions',
            'posts',
            'follows',
            'campaigns',
            'agents',
            'simulation_runs'
        ]
        
        for table in tables:
            await self.conn.execute(f"DELETE FROM {table}")
        
        await self.conn.commit()
    
    async def get_stats(self) -> Dict[str, int]:
        """Get counts of all major entities."""
        stats = {}
        
        tables = ['agents', 'posts', 'follows', 'interactions', 'observations', 
                  'campaigns', 'campaign_exposures', 'belief_measurements', 'simulation_runs']
        
        for table in tables:
            async with self.conn.execute(f"SELECT COUNT(*) as count FROM {table}") as cursor:
                row = await cursor.fetchone()
                stats[table] = row['count']
        
        return stats
    
    async def get_sample_posts_with_engagement(self, limit: int = 10) -> List[Dict]:
        """Get sample posts with high engagement (likes + comments)."""
        query = """
            SELECT * FROM posts 
            WHERE parent_post_id IS NULL
            ORDER BY (like_count + comment_count) DESC, created_step DESC
            LIMIT ?
        """
        async with self.conn.execute(query, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_campaign_posts(self, limit: int = 4) -> List[Dict]:
        """Get sample campaign posts."""
        query = """
            SELECT * FROM posts 
            WHERE post_type = 'campaign'
            ORDER BY created_step
            LIMIT ?
        """
        async with self.conn.execute(query, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_posts_with_threads(self, limit: int = 5) -> List[Dict]:
        """Get posts that have comment threads."""
        query = """
            SELECT * FROM posts 
            WHERE parent_post_id IS NULL 
            AND comment_count > 0
            ORDER BY comment_count DESC, created_step DESC
            LIMIT ?
        """
        async with self.conn.execute(query, (limit,)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


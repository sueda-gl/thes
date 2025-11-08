"""
Social media platform state management.

Implements core platform mechanics following:
- Barabási & Albert (1999): Scale-free social graph
- Hodas & Lerman (2014): Feed visibility and limited attention
- Rader & Gray (2015): Reverse chronological ordering
- Serrano & Iglesias (2016): Tree-structured reshare mechanics
- Goel et al. (2016): Structural virality metrics
"""
from typing import List, Dict, Optional, Any
import uuid
from database.db import Database
import config


class Platform:
    """Virtual social media platform."""
    
    def __init__(self, db: Database):
        """
        Initialize platform.
        
        Args:
            db: Database connection
        """
        self.db = db
        self.current_step = 0
    
    # ============================================
    # SOCIAL GRAPH
    # ============================================
    
    async def get_following(self, agent_id: str) -> List[str]:
        """Get list of agents this agent follows."""
        return await self.db.get_following(agent_id)
    
    async def get_followers(self, agent_id: str) -> List[str]:
        """Get list of agents following this agent."""
        return await self.db.get_followers(agent_id)
    
    # ============================================
    # FEED GENERATION
    # ============================================
    
    async def build_feed(
        self,
        agent_id: str,
        current_step: int,
        n_items: int = None
    ) -> List[Dict[str, Any]]:
        """
        Build personalized feed for an agent.
        
        Args:
            agent_id: Agent ID
            current_step: Current simulation step
            n_items: Number of items to include (default: config.FEED_SIZE)
        
        Returns:
            List of feed items (posts with engagement data)
        """
        n_items = n_items or config.FEED_SIZE
        
        # Get who this agent follows
        following = await self.get_following(agent_id)
        
        # Get recent posts from followed agents within visibility window
        min_step = max(0, current_step - config.VISIBILITY_WINDOW)
        posts = []
        
        if following:
            posts = await self.db.get_posts_for_feed(
                agent_ids=following,
                max_step=current_step,
                min_step=min_step,
                limit=50  # Get more than needed for ranking
            )
        
        # CRITICAL: Add campaign posts targeted at this agent
        # Campaign posts should always appear even if not from followed accounts
        async with self.db.conn.execute(
            """SELECT * FROM posts 
               WHERE post_type = 'campaign'
               AND post_id LIKE ?
               AND created_step <= ?""",
            (f"%_{agent_id}", current_step)
        ) as cursor:
            campaign_posts = await cursor.fetchall()
            # Add to posts list
            for cp in campaign_posts:
                posts.append(dict(cp))
        
        if not posts:
            return []
        
        # Rank posts
        ranked_posts = self._rank_posts(posts, current_step)
        
        # Return top N
        return ranked_posts[:n_items]
    
    def _rank_posts(
        self,
        posts: List[Dict],
        current_step: int
    ) -> List[Dict]:
        """
        Rank posts by pure recency (reverse chronological).
        
        Users prefer chronological ordering for transparency and completeness
        (Rader & Gray, 2015). Message visibility decays as newer posts displace
        older ones in the feed, reducing discoverability (Hodas & Lerman, 2014).
        
        We intentionally avoid engagement-based ranking to maintain experimental
        transparency. This ensures observed differences between Hope and Fear
        campaigns reflect agent decisions rather than algorithmic amplification.
        
        Args:
            posts: List of post dictionaries
            current_step: Current simulation step (unused but kept for API consistency)
        
        Returns:
            List of posts sorted by created_step descending (newest first)
        
        References:
            Rader, E., & Gray, R. (2015). Understanding user beliefs about
            algorithmic curation in the Facebook News Feed. CHI '15, 173-182.
            
            Hodas, N. O., & Lerman, K. (2014). The simple rules of social
            contagion. Scientific Reports, 4, 4343.
        """
        # Sort by timestamp (newest first), with campaign posts breaking ties
        sorted_posts = sorted(
            posts,
            key=lambda p: (p['created_step'], 1 if p['post_type'] == 'campaign' else 0),
            reverse=True
        )
        
        return sorted_posts
    
    # ============================================
    # CONTENT MANAGEMENT
    # ============================================
    
    async def create_post(
        self,
        agent_id: str,
        content: str,
        post_type: str,
        step: int
    ) -> str:
        """
        Create a new post.
        
        Args:
            agent_id: Author's ID
            content: Post content
            post_type: 'campaign', 'organic', or 'response'
            step: Current step
        
        Returns:
            Post ID
        """
        post_id = f"post_{uuid.uuid4().hex[:12]}"
        
        await self.db.insert_post(
            post_id=post_id,
            agent_id=agent_id,
            content=content,
            post_type=post_type,
            created_step=step,
            parent_post_id=None
        )
        
        return post_id
    
    async def create_comment(
        self,
        agent_id: str,
        parent_post_id: str,
        content: str,
        step: int
    ) -> str:
        """
        Create a comment on a post.
        
        Args:
            agent_id: Commenter's ID
            parent_post_id: Parent post ID
            content: Comment content
            step: Current step
        
        Returns:
            Comment ID
        """
        comment_id = f"comment_{uuid.uuid4().hex[:12]}"
        
        await self.db.insert_post(
            post_id=comment_id,
            agent_id=agent_id,
            content=content,
            post_type='response',
            created_step=step,
            parent_post_id=parent_post_id
        )
        
        return comment_id
    
    async def create_reshare(
        self,
        agent_id: str,
        parent_post_id: str,
        content: Optional[str],
        step: int
    ) -> str:
        """
        Create a reshare/repost following Serrano & Iglesias (2016).
        
        Implements tree-structured retweets: each reshare is a new post
        that stores a pointer to its source, allowing cascade reconstruction.
        Cascade depth is inherited and incremented from parent.
        
        Args:
            agent_id: Agent resharing
            parent_post_id: Original post ID
            content: Optional share comment
            step: Current step
        
        Returns:
            Reshare post ID
            
        References:
            Serrano, E., & Iglesias, C. A. (2016). Validating viral marketing
            strategies in Twitter via agent-based social simulation.
            Expert Systems with Applications, 50, 140-150.
        """
        reshare_id = f"reshare_{uuid.uuid4().hex[:12]}"
        
        # Get original post to reference it and inherit cascade depth
        original_post = await self.get_post(parent_post_id)
        if not original_post:
            return None
        
        # Inherit and increment cascade depth
        parent_depth = original_post.get('cascade_depth', 0)
        reshare_depth = parent_depth + 1
        
        # Build reshare content with attribution
        reshare_content = f"RT: {original_post['content'][:100]}..."
        if content:
            reshare_content = f"{content} // {reshare_content}"
        
        await self.db.insert_post(
            post_id=reshare_id,
            agent_id=agent_id,
            content=reshare_content,
            post_type='reshare',
            created_step=step,
            parent_post_id=parent_post_id,
            cascade_depth=reshare_depth
        )
        
        # Update comment count on parent (reshares count as engagement)
        await self.db.increment_comment_count(parent_post_id)
        
        return reshare_id
    
    async def get_campaign_origin(self, post_id: str) -> Optional[str]:
        """
        Trace a post back to its campaign origin if it exists.
        
        Args:
            post_id: Post to trace
            
        Returns:
            Campaign ID if post is part of a campaign cascade, None otherwise
        """
        post = await self.get_post(post_id)
        if not post:
            return None
        
        # Direct campaign post
        if post['post_type'] == 'campaign' and 'campaign_' in post['post_id']:
            # Extract campaign ID from post_id format: campaign_hope_agent123
            parts = post['post_id'].split('_')
            if len(parts) >= 2:
                return f"campaign_{parts[1]}"  # campaign_hope or campaign_fear
        
        # Check parent recursively (for comments and reshares)
        if post['parent_post_id']:
            return await self.get_campaign_origin(post['parent_post_id'])
        
        return None
    
    async def create_like(
        self,
        agent_id: str,
        post_id: str,
        step: int
    ):
        """
        Create a like on a post.
        
        Args:
            agent_id: Liker's ID
            post_id: Post ID
            step: Current step
        """
        await self.db.insert_interaction(
            agent_id=agent_id,
            post_id=post_id,
            interaction_type='like',
            created_step=step
        )
    
    async def get_post(self, post_id: str) -> Optional[Dict]:
        """Get a post by ID."""
        return await self.db.get_post(post_id)
    
    # ============================================
    # CAMPAIGN MANAGEMENT
    # ============================================
    
    async def inject_campaign(
        self,
        campaign_id: str,
        campaign_type: str,
        message: str,
        target_agents: List[str],
        step: int
    ) -> List[str]:
        """
        Inject campaign to target agents with cascade depth tracking.
        
        Args:
            campaign_id: Campaign identifier
            campaign_type: 'hope' or 'fear'
            message: Campaign message
            target_agents: List of agent IDs to target
            step: Current step
        
        Returns:
            List of targeted agent IDs (for tracking)
        """
        # Record campaign
        await self.db.insert_campaign(
            campaign_id=campaign_id,
            campaign_type=campaign_type,
            message=message,
            launch_step=step
        )
        
        # Create campaign post for each target agent
        # (appears in their feed as if from a brand account)
        for agent_id in target_agents:
            post_id = f"campaign_{campaign_id}_{agent_id}"
            
            # Campaign posts have cascade_depth=0 (direct exposure)
            await self.db.insert_post(
                post_id=post_id,
                agent_id='CAMPAIGN_BRAND',  # Special brand account
                content=message,
                post_type='campaign',
                created_step=step,
                parent_post_id=None,
                cascade_depth=0
            )
            
            # Record direct exposure with cascade depth
            await self.db.log_campaign_exposure(
                agent_id=agent_id,
                post_id=post_id,
                campaign_id=campaign_id,
                cascade_depth=0,
                exposure_step=step,
                responded=False,
                action_type=None
            )
            
            # Record observation
            await self.db.insert_observation(
                agent_id=agent_id,
                post_id=post_id,
                seen_step=step
            )
        
        return target_agents
    
    async def track_campaign_response(
        self,
        agent_id: str,
        post_id: str,
        action_type: str
    ):
        """
        Mark that an agent responded to a campaign post.
        
        Args:
            agent_id: Agent ID
            post_id: Campaign post ID
            action_type: 'like', 'comment', or 'reshare'
        """
        await self.db.update_exposure_response(
            agent_id=agent_id,
            post_id=post_id,
            action_type=action_type
        )
    
    # ============================================
    # OBSERVATIONS
    # ============================================
    
    async def record_observations(
        self,
        agent_id: str,
        post_ids: List[str],
        step: int
    ):
        """
        Record that an agent observed posts.
        
        Args:
            agent_id: Agent ID
            post_ids: List of post IDs seen
            step: Current step
        """
        observations = [
            (agent_id, post_id, step)
            for post_id in post_ids
        ]
        
        if observations:
            await self.db.insert_observations_batch(observations)
    
    # ============================================
    # UTILITIES
    # ============================================
    
    async def get_post_engagement(self, post_id: str) -> Dict[str, int]:
        """
        Get engagement metrics for a post.
        
        Args:
            post_id: Post ID
        
        Returns:
            Dict with likes and comments counts
        """
        post = await self.get_post(post_id)
        if post:
            return {
                'likes': post['like_count'],
                'comments': post['comment_count']
            }
        return {'likes': 0, 'comments': 0}


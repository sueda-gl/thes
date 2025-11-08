"""
Thread depth and conversation analysis.
"""
from typing import Dict, List
from database.db import Database


class ThreadAnalyzer:
    """Analyze discussion threads and conversation patterns."""
    
    def __init__(self, db: Database):
        """Initialize with database connection."""
        self.db = db
    
    async def get_thread_depth(self, post_id: str) -> int:
        """
        Calculate maximum depth of a comment thread.
        
        Args:
            post_id: Root post ID
        
        Returns:
            Maximum thread depth
        """
        comments = await self.db.get_comments_for_post(post_id)
        
        if not comments:
            return 0
        
        # For simplicity, since our schema has parent_post_id,
        # we consider direct comments = depth 1
        return 1 if comments else 0
    
    async def get_thread_statistics(self, campaign_id: str) -> Dict:
        """
        Get statistics about discussion threads.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Dict with thread statistics
        """
        # Get all posts related to campaign
        all_posts = await self.db.conn.execute(
            "SELECT * FROM posts WHERE post_type = 'campaign' OR agent_id IN (SELECT agent_id FROM campaign_exposures WHERE campaign_id = ?)",
            (campaign_id,)
        )
        posts = await all_posts.fetchall()
        
        # Calculate statistics
        total_threads = 0
        total_comments = 0
        threads_with_comments = 0
        
        for post in posts:
            if post['parent_post_id'] is None:  # Root post
                total_threads += 1
                comment_count = post['comment_count']
                total_comments += comment_count
                if comment_count > 0:
                    threads_with_comments += 1
        
        avg_comments = total_comments / total_threads if total_threads > 0 else 0
        
        return {
            'total_threads': total_threads,
            'threads_with_comments': threads_with_comments,
            'total_comments': total_comments,
            'avg_comments_per_thread': round(avg_comments, 2),
            'engagement_rate': round(threads_with_comments / total_threads * 100, 1) if total_threads > 0 else 0
        }


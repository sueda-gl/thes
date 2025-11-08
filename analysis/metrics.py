"""
Comprehensive metrics calculation and statistical analysis.
"""
from typing import Dict, List, Any, Optional
from database.db import Database
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
import json


class MetricsCalculator:
    """Calculate all simulation metrics."""
    
    def __init__(self, db: Database):
        """Initialize with database connection."""
        self.db = db
    
    # ===================================
    # ENGAGEMENT METRICS
    # ===================================
    
    async def calculate_total_engagements(self, campaign_id: str) -> Dict[str, int]:
        """
        Calculate total engagements for a campaign.
        
        Returns:
            Dict with likes, comments, posts counts
        """
        exposures = await self.db.get_exposures_by_campaign(campaign_id)
        
        # Count by action type
        likes = sum(1 for e in exposures if e['action_type'] == 'like')
        comments = sum(1 for e in exposures if e['action_type'] == 'comment')
        posts = sum(1 for e in exposures if e['action_type'] == 'post')
        
        return {
            'likes': likes,
            'comments': comments,
            'posts': posts,
            'total': likes + comments + posts
        }
    
    async def calculate_engagement_rate(self, campaign_id: str) -> float:
        """
        Calculate engagement rate (% of exposed agents who engaged).
        
        Returns:
            Engagement rate (0-1)
        """
        exposures = await self.db.get_exposures_by_campaign(campaign_id)
        
        if not exposures:
            return 0.0
        
        # Count direct exposures (the target audience)
        direct_exposures = [e for e in exposures if e['exposure_type'] == 'direct']
        responded = sum(1 for e in direct_exposures if e['responded'])
        
        return responded / len(direct_exposures) if direct_exposures else 0.0
    
    async def get_engagement_breakdown(self, campaign_id: str) -> Dict[str, float]:
        """
        Get percentage breakdown of engagement types.
        
        Returns:
            Dict with percentages of likes, comments, posts
        """
        engagements = await self.calculate_total_engagements(campaign_id)
        total = engagements['total']
        
        if total == 0:
            return {'likes_pct': 0, 'comments_pct': 0, 'posts_pct': 0}
        
        return {
            'likes_pct': round(engagements['likes'] / total * 100, 1),
            'comments_pct': round(engagements['comments'] / total * 100, 1),
            'posts_pct': round(engagements['posts'] / total * 100, 1)
        }
    
    # ===================================
    # REACH METRICS
    # ===================================
    
    async def calculate_reach(self, campaign_id: str) -> Dict[str, int]:
        """
        Calculate reach metrics.
        
        Returns:
            Dict with direct, secondary, tertiary, and total reach
        """
        exposures = await self.db.get_exposures_by_campaign(campaign_id)
        
        direct = len([e for e in exposures if e['exposure_type'] == 'direct'])
        secondary = len([e for e in exposures if e['exposure_type'] == 'secondary'])
        tertiary = len([e for e in exposures if e['exposure_type'] == 'tertiary'])
        
        # Get unique agents reached
        unique_agents = set(e['agent_id'] for e in exposures)
        
        return {
            'direct': direct,
            'secondary': secondary,
            'tertiary': tertiary,
            'total_unique': len(unique_agents)
        }
    
    async def calculate_reach_percentage(self, campaign_id: str, total_agents: int) -> float:
        """
        Calculate what percentage of the network was reached.
        
        Args:
            campaign_id: Campaign ID
            total_agents: Total number of agents in simulation
        
        Returns:
            Percentage (0-100)
        """
        reach = await self.calculate_reach(campaign_id)
        return round(reach['total_unique'] / total_agents * 100, 1)
    
    # ===================================
    # VIRALITY METRICS
    # ===================================
    
    async def calculate_virality_coefficient(self, campaign_id: str) -> float:
        """
        Calculate virality coefficient (secondary reach / direct reach).
        
        Returns:
            Virality coefficient
        """
        reach = await self.calculate_reach(campaign_id)
        
        if reach['direct'] == 0:
            return 0.0
        
        return round(reach['secondary'] / reach['direct'], 2)
    
    async def calculate_amplification_rate(self, campaign_id: str) -> float:
        """
        Calculate amplification rate (% who created posts).
        
        Returns:
            Amplification rate (0-1)
        """
        exposures = await self.db.get_exposures_by_campaign(campaign_id)
        direct_exposures = [e for e in exposures if e['exposure_type'] == 'direct']
        
        if not direct_exposures:
            return 0.0
        
        posted = sum(1 for e in direct_exposures if e['action_type'] == 'post')
        return round(posted / len(direct_exposures), 2)
    
    # ===================================
    # DISCUSSION METRICS
    # ===================================
    
    async def calculate_comment_density(self, campaign_id: str) -> float:
        """
        Calculate average comments per post about campaign.
        
        Returns:
            Average comments per post
        """
        # Get all posts related to campaign
        # This is simplified - in full implementation would track campaign-related posts
        engagements = await self.calculate_total_engagements(campaign_id)
        
        if engagements['posts'] == 0:
            return 0.0
        
        return round(engagements['comments'] / engagements['posts'], 1)
    
    async def calculate_comment_share(self, campaign_id: str) -> float:
        """
        Calculate comment share (proportion of engagements that are comments).
        
        Returns:
            Comment share (0-1)
        """
        engagements = await self.calculate_total_engagements(campaign_id)
        
        if engagements['total'] == 0:
            return 0.0
        
        return round(engagements['comments'] / engagements['total'], 3)
    
    # ===================================
    # TEMPORAL METRICS
    # ===================================
    
    async def get_engagement_over_time(self, campaign_id: str) -> List[Dict]:
        """
        Get engagement metrics by step.
        
        Returns:
            List of dicts with step and engagement counts
        """
        # Get campaign type (hope or fear)
        campaign_type = campaign_id.replace('campaign_', '')
        
        # Initialize step data structure
        step_data = {}
        
        # 1. Get likes on campaign posts, grouped by step
        async with self.db.conn.execute(
            """SELECT i.created_step, COUNT(*) as count
               FROM interactions i
               JOIN posts p ON i.post_id = p.post_id
               WHERE p.post_type = 'campaign'
               AND p.post_id LIKE ?
               GROUP BY i.created_step""",
            (f"%{campaign_type}%",)
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                step = row['created_step']
                if step not in step_data:
                    step_data[step] = {'likes': 0, 'comments': 0, 'posts': 0}
                step_data[step]['likes'] = row['count']
        
        # 2. Get comments on campaign posts, grouped by step
        async with self.db.conn.execute(
            """SELECT p2.created_step, COUNT(*) as count
               FROM posts p2
               WHERE p2.parent_post_id IN (
                   SELECT post_id FROM posts 
                   WHERE post_type = 'campaign' AND post_id LIKE ?
               )
               GROUP BY p2.created_step""",
            (f"%{campaign_type}%",)
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                step = row['created_step']
                if step not in step_data:
                    step_data[step] = {'likes': 0, 'comments': 0, 'posts': 0}
                step_data[step]['comments'] = row['count']
        
        # 3. Get organic posts from agents exposed to this campaign
        # (Posts created by agents after being exposed to the campaign)
        async with self.db.conn.execute(
            """SELECT p.created_step, COUNT(*) as count
               FROM posts p
               JOIN campaign_exposures ce ON p.agent_id = ce.agent_id
               WHERE ce.campaign_id = ?
               AND p.post_type = 'organic'
               AND p.created_step >= ce.exposure_step
               AND p.parent_post_id IS NULL
               GROUP BY p.created_step""",
            (campaign_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                step = row['created_step']
                if step not in step_data:
                    step_data[step] = {'likes': 0, 'comments': 0, 'posts': 0}
                step_data[step]['posts'] = row['count']
        
        # Convert to list and sort by step
        timeline = []
        for step in sorted(step_data.keys()):
            data = step_data[step]
            timeline.append({
                'step': step,
                'likes': data['likes'],
                'comments': data['comments'],
                'posts': data['posts'],
                'total': data['likes'] + data['comments'] + data['posts']
            })
        
        return timeline
    
    async def calculate_time_to_peak(self, campaign_id: str) -> Dict[str, Any]:
        """
        Calculate the step at which engagement peaked.
        
        Returns:
            Dict with peak_step and peak_engagement
        """
        timeline = await self.get_engagement_over_time(campaign_id)
        
        if not timeline:
            return {'peak_step': None, 'peak_engagement': 0}
        
        # Find step with maximum total engagement
        peak_step = 0
        peak_engagement = 0
        
        for entry in timeline:
            if entry['total'] > peak_engagement:
                peak_engagement = entry['total']
                peak_step = entry['step']
        
        return {
            'peak_step': peak_step,
            'peak_engagement': peak_engagement
        }
    
    async def calculate_half_life(self, campaign_id: str) -> Dict[str, Any]:
        """
        Calculate when cumulative engagement reaches 50% of final total.
        
        Returns:
            Dict with half_life_step and cumulative metrics
        """
        timeline = await self.get_engagement_over_time(campaign_id)
        
        if not timeline:
            return {'half_life_step': None, 'total_engagement': 0}
        
        # Calculate total engagement across all steps
        total_engagement = sum(entry['total'] for entry in timeline)
        
        if total_engagement == 0:
            return {'half_life_step': None, 'total_engagement': 0}
        
        # Find when cumulative engagement reaches 50%
        half_point = total_engagement / 2
        cumulative = 0
        half_life_step = None
        
        for entry in timeline:
            cumulative += entry['total']
            if cumulative >= half_point and half_life_step is None:
                half_life_step = entry['step']
                break
        
        return {
            'half_life_step': half_life_step,
            'total_engagement': total_engagement,
            'half_point_engagement': int(half_point)
        }
    
    # ===================================
    # COMPARATIVE ANALYSIS
    # ===================================
    
    async def compare_campaigns(self) -> Dict[str, Any]:
        """
        Compare hope vs fear campaigns across all metrics.
        
        Returns:
            Comprehensive comparison dict
        """
        # Get all agents to calculate percentages
        all_agents = await self.db.get_all_agents()
        total_agents = len(all_agents)
        
        # Hope campaign metrics
        hope_engagement = await self.calculate_total_engagements('campaign_hope')
        hope_reach = await self.calculate_reach('campaign_hope')
        hope_rate = await self.calculate_engagement_rate('campaign_hope')
        hope_virality = await self.calculate_virality_coefficient('campaign_hope')
        hope_amplification = await self.calculate_amplification_rate('campaign_hope')
        
        # Fear campaign metrics
        fear_engagement = await self.calculate_total_engagements('campaign_fear')
        fear_reach = await self.calculate_reach('campaign_fear')
        fear_rate = await self.calculate_engagement_rate('campaign_fear')
        fear_virality = await self.calculate_virality_coefficient('campaign_fear')
        fear_amplification = await self.calculate_amplification_rate('campaign_fear')
        
        return {
            'hope': {
                'engagement': hope_engagement,
                'engagement_rate': round(hope_rate, 3),
                'reach': hope_reach,
                'reach_pct': round(hope_reach['total_unique'] / total_agents * 100, 1),
                'virality': hope_virality,
                'amplification': hope_amplification
            },
            'fear': {
                'engagement': fear_engagement,
                'engagement_rate': round(fear_rate, 3),
                'reach': fear_reach,
                'reach_pct': round(fear_reach['total_unique'] / total_agents * 100, 1),
                'virality': fear_virality,
                'amplification': fear_amplification
            }
        }
    
    # ===================================
    # STATISTICAL TESTS
    # ===================================
    
    async def chi_square_test(self) -> Dict[str, Any]:
        """
        Chi-square test for engagement type distribution.
        
        Returns:
            Test results with statistic and p-value
        """
        hope_eng = await self.calculate_total_engagements('campaign_hope')
        fear_eng = await self.calculate_total_engagements('campaign_fear')
        
        # Create contingency table
        observed = np.array([
            [hope_eng['likes'], hope_eng['comments'], hope_eng['posts']],
            [fear_eng['likes'], fear_eng['comments'], fear_eng['posts']]
        ])
        
        # Check if we have enough data for chi-square test
        # Need at least 5 expected frequency in each cell
        total = observed.sum()
        if total < 10:  # Very low engagement
            return {
                'test': 'chi_square',
                'statistic': None,
                'p_value': None,
                'degrees_of_freedom': None,
                'significant': False,
                'error': 'Insufficient data for chi-square test (need more engagement)'
            }
        
        # Check for zero columns
        col_sums = observed.sum(axis=0)
        if any(col_sums == 0):
            # Remove zero columns
            non_zero_cols = col_sums > 0
            observed = observed[:, non_zero_cols]
        
        # Check if we still have valid data
        if observed.shape[1] < 2:
            return {
                'test': 'chi_square',
                'statistic': None,
                'p_value': None,
                'degrees_of_freedom': None,
                'significant': False,
                'error': 'Not enough variation in engagement types'
            }
        
        try:
            # Perform chi-square test
            chi2, p, dof, expected = stats.chi2_contingency(observed)
            
            return {
                'test': 'chi_square',
                'statistic': round(chi2, 3),
                'p_value': round(p, 4),
                'degrees_of_freedom': dof,
                'significant': p < 0.05
            }
        except ValueError as e:
            return {
                'test': 'chi_square',
                'statistic': None,
                'p_value': None,
                'degrees_of_freedom': None,
                'significant': False,
                'error': f'Chi-square test failed: {str(e)}'
            }
    
    async def proportion_test_reach(self) -> Dict[str, Any]:
        """
        Proportion test comparing reach percentages.
        
        Returns:
            Test results with z-statistic and p-value
        """
        all_agents = await self.db.get_all_agents()
        total = len(all_agents)
        
        hope_reach = await self.calculate_reach('campaign_hope')
        fear_reach = await self.calculate_reach('campaign_fear')
        
        # Check if we have enough data
        if hope_reach['total_unique'] == 0 and fear_reach['total_unique'] == 0:
            return {
                'test': 'proportion_z_test',
                'statistic': None,
                'p_value': None,
                'hope_reach': 0,
                'fear_reach': 0,
                'significant': False,
                'error': 'No reach data available'
            }
        
        try:
            # Two-proportion z-test
            count = np.array([hope_reach['total_unique'], fear_reach['total_unique']])
            nobs = np.array([total, total])
            
            # Use statsmodels for proportion test
            from statsmodels.stats.proportion import proportions_ztest
            z_stat, p_value = proportions_ztest(count, nobs)
            
            return {
                'test': 'proportion_z_test',
                'statistic': round(z_stat, 3),
                'p_value': round(p_value, 4),
                'hope_reach': hope_reach['total_unique'],
                'fear_reach': fear_reach['total_unique'],
                'significant': p_value < 0.05
            }
        except Exception as e:
            return {
                'test': 'proportion_z_test',
                'statistic': None,
                'p_value': None,
                'hope_reach': hope_reach['total_unique'],
                'fear_reach': fear_reach['total_unique'],
                'significant': False,
                'error': f'Test failed: {str(e)}'
            }
    
    async def fishers_exact_test(self) -> Dict[str, Any]:
        """
        Fisher's exact test for amplification rate.
        
        Returns:
            Test results with odds ratio and p-value
        """
        hope_exp = await self.db.get_exposures_by_campaign('campaign_hope')
        fear_exp = await self.db.get_exposures_by_campaign('campaign_fear')
        
        # Direct exposures only
        hope_direct = [e for e in hope_exp if e['exposure_type'] == 'direct']
        fear_direct = [e for e in fear_exp if e['exposure_type'] == 'direct']
        
        # Count who posted
        hope_posted = sum(1 for e in hope_direct if e['action_type'] == 'post')
        hope_not_posted = len(hope_direct) - hope_posted
        
        fear_posted = sum(1 for e in fear_direct if e['action_type'] == 'post')
        fear_not_posted = len(fear_direct) - fear_posted
        
        # Check if we have enough data
        if len(hope_direct) == 0 or len(fear_direct) == 0:
            return {
                'test': 'fishers_exact',
                'odds_ratio': None,
                'p_value': None,
                'hope_posted': hope_posted,
                'hope_total': len(hope_direct),
                'fear_posted': fear_posted,
                'fear_total': len(fear_direct),
                'significant': False,
                'error': 'Insufficient exposure data'
            }
        
        try:
            # 2x2 contingency table
            table = [[hope_posted, hope_not_posted],
                     [fear_posted, fear_not_posted]]
            
            odds_ratio, p_value = stats.fisher_exact(table)
            
            return {
                'test': 'fishers_exact',
                'odds_ratio': round(odds_ratio, 3),
                'p_value': round(p_value, 4),
                'hope_posted': hope_posted,
                'hope_total': len(hope_direct),
                'fear_posted': fear_posted,
                'fear_total': len(fear_direct),
                'significant': p_value < 0.05
            }
        except Exception as e:
            return {
                'test': 'fishers_exact',
                'odds_ratio': None,
                'p_value': None,
                'hope_posted': hope_posted,
                'hope_total': len(hope_direct),
                'fear_posted': fear_posted,
                'fear_total': len(fear_direct),
                'significant': False,
                'error': f'Test failed: {str(e)}'
            }
    
    async def personality_moderation_analysis(self) -> Dict[str, Any]:
        """
        Analyze how personality traits moderate campaign response.
        
        Returns:
            Analysis results by trait
        """
        # Get all agents and their responses
        all_agents = await self.db.get_all_agents()
        hope_exp = await self.db.get_exposures_by_campaign('campaign_hope')
        fear_exp = await self.db.get_exposures_by_campaign('campaign_fear')
        
        # Build dataset for all Big Five traits
        traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        results = {
            trait: {'hope': {'high': [], 'low': []}, 'fear': {'high': [], 'low': []}}
            for trait in traits
        }
        
        # Create mapping of agent_id to persona
        agent_map = {a['agent_id']: a['persona'] for a in all_agents}
        
        # Analyze all traits for Hope campaign
        for exp in hope_exp:
            if exp['exposure_type'] == 'direct':
                agent_id = exp['agent_id']
                persona = agent_map.get(agent_id, {})
                personality = persona.get('personality', {})
                engaged = 1 if exp['responded'] else 0
                
                for trait in traits:
                    trait_value = personality.get(trait, 0.5)
                    category = 'high' if trait_value > 0.7 else 'low'
                    results[trait]['hope'][category].append(engaged)
        
        # Analyze all traits for Fear campaign
        for exp in fear_exp:
            if exp['exposure_type'] == 'direct':
                agent_id = exp['agent_id']
                persona = agent_map.get(agent_id, {})
                personality = persona.get('personality', {})
                engaged = 1 if exp['responded'] else 0
                
                for trait in traits:
                    trait_value = personality.get(trait, 0.5)
                    category = 'high' if trait_value > 0.7 else 'low'
                    results[trait]['fear'][category].append(engaged)
        
        # Calculate engagement rates
        analysis = {}
        
        for trait in traits:
            hope_high_rate = np.mean(results[trait]['hope']['high']) if results[trait]['hope']['high'] else 0
            hope_low_rate = np.mean(results[trait]['hope']['low']) if results[trait]['hope']['low'] else 0
            fear_high_rate = np.mean(results[trait]['fear']['high']) if results[trait]['fear']['high'] else 0
            fear_low_rate = np.mean(results[trait]['fear']['low']) if results[trait]['fear']['low'] else 0
            
            analysis[trait] = {
                'hope_high_engagement': round(hope_high_rate, 3),
                'hope_low_engagement': round(hope_low_rate, 3),
                'fear_high_engagement': round(fear_high_rate, 3),
                'fear_low_engagement': round(fear_low_rate, 3),
                'hope_high_count': len(results[trait]['hope']['high']),
                'hope_low_count': len(results[trait]['hope']['low']),
                'fear_high_count': len(results[trait]['fear']['high']),
                'fear_low_count': len(results[trait]['fear']['low'])
            }
        
        return analysis
    
    # ===================================
    # VALIDATION METRICS
    # ===================================
    
    async def check_heavy_tailed_distribution(self) -> Dict[str, Any]:
        """
        Check if engagement follows heavy-tailed distribution (Clauset et al. 2009).
        
        Returns:
            Dict with distribution analysis
        """
        # Get engagement counts per post
        async with self.db.conn.execute(
            """SELECT p.post_id, p.like_count, p.comment_count,
                      (p.like_count + p.comment_count) as total_engagement
               FROM posts p
               WHERE p.post_type IN ('organic', 'reshare')
               ORDER BY total_engagement DESC"""
        ) as cursor:
            posts = await cursor.fetchall()
        
        if not posts:
            return {'error': 'No posts found'}
        
        # Extract engagement values
        engagements = [p['total_engagement'] for p in posts if p['total_engagement'] > 0]
        
        if len(engagements) < 10:
            return {'error': 'Insufficient data for analysis'}
        
        # Calculate rank-frequency distribution
        sorted_eng = sorted(engagements, reverse=True)
        ranks = list(range(1, len(sorted_eng) + 1))
        
        # Check power law: frequency ~ rank^(-α)
        # In log-log plot, should be approximately linear
        import math
        log_ranks = [math.log(r) for r in ranks[:20]]  # Top 20
        log_values = [math.log(v + 1) for v in sorted_eng[:20]]  # Add 1 to avoid log(0)
        
        # Simple linear regression for slope
        n = len(log_ranks)
        if n > 1:
            sum_x = sum(log_ranks)
            sum_y = sum(log_values)
            sum_xy = sum(x * y for x, y in zip(log_ranks, log_values))
            sum_x2 = sum(x * x for x in log_ranks)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Heavy-tailed if slope is negative and steep (typically < -1)
            is_heavy_tailed = slope < -0.5
        else:
            slope = 0
            is_heavy_tailed = False
        
        # Calculate concentration metrics
        top_10_pct_posts = max(1, len(engagements) // 10)
        top_10_pct_engagement = sum(sorted_eng[:top_10_pct_posts])
        total_engagement = sum(engagements)
        concentration = top_10_pct_engagement / total_engagement if total_engagement > 0 else 0
        
        return {
            'is_heavy_tailed': is_heavy_tailed,
            'power_law_slope': round(slope, 3),
            'total_posts': len(posts),
            'posts_with_engagement': len(engagements),
            'top_post_engagement': sorted_eng[0] if sorted_eng else 0,
            'median_engagement': sorted_eng[len(sorted_eng)//2] if sorted_eng else 0,
            'concentration_top_10pct': round(concentration, 3),
            'interpretation': 'Heavy-tailed' if is_heavy_tailed else 'Not heavy-tailed'
        }
    
    async def analyze_temporal_decay(self, campaign_id: str) -> Dict[str, Any]:
        """
        Analyze temporal decay pattern after peak (Wu & Huberman 2007; Crane & Sornette 2008).
        
        Returns:
            Dict with decay analysis
        """
        # Get time to peak first
        peak_info = await self.calculate_time_to_peak(campaign_id)
        peak_step = peak_info['peak_step']
        
        if peak_step is None:
            return {'error': 'No peak found'}
        
        # Get engagement timeline
        timeline = await self.get_engagement_over_time(campaign_id)
        
        # Extract post-peak data
        post_peak_data = [entry for entry in timeline if entry['step'] > peak_step]
        
        if len(post_peak_data) < 3:
            return {'error': 'Insufficient post-peak data'}
        
        # Normalize by peak engagement
        peak_engagement = peak_info['peak_engagement']
        if peak_engagement == 0:
            return {'error': 'Peak engagement is zero'}
        
        # Calculate decay metrics
        decay_steps = []
        decay_values = []
        
        for entry in post_peak_data:
            steps_from_peak = entry['step'] - peak_step
            normalized_engagement = entry['total'] / peak_engagement
            decay_steps.append(steps_from_peak)
            decay_values.append(normalized_engagement)
        
        # Fit exponential decay: y = exp(-λt)
        # log(y) = -λt, so slope of log(y) vs t gives -λ
        import math
        log_values = []
        valid_steps = []
        
        for i, val in enumerate(decay_values):
            if val > 0:
                log_values.append(math.log(val))
                valid_steps.append(decay_steps[i])
        
        # Simple linear regression for decay rate
        if len(valid_steps) > 1:
            n = len(valid_steps)
            sum_t = sum(valid_steps)
            sum_log_y = sum(log_values)
            sum_t_log_y = sum(t * log_y for t, log_y in zip(valid_steps, log_values))
            sum_t2 = sum(t * t for t in valid_steps)
            
            if n * sum_t2 - sum_t * sum_t != 0:
                decay_rate = -(n * sum_t_log_y - sum_t * sum_log_y) / (n * sum_t2 - sum_t * sum_t)
            else:
                decay_rate = 0
            
            # Calculate half-life from decay rate (t where e^(-λt) = 0.5)
            if decay_rate > 0:
                decay_half_life = math.log(2) / decay_rate
            else:
                decay_half_life = float('inf')
        else:
            decay_rate = 0
            decay_half_life = float('inf')
        
        # Check if decay follows expected pattern
        # Good decay: steady decrease after peak
        steady_decay = sum(1 for i in range(1, len(decay_values)) if decay_values[i] <= decay_values[i-1])
        decay_quality = steady_decay / (len(decay_values) - 1) if len(decay_values) > 1 else 0
        
        return {
            'peak_step': peak_step,
            'peak_engagement': peak_engagement,
            'decay_rate': round(decay_rate, 4),
            'decay_half_life': round(decay_half_life, 2) if decay_half_life < 1000 else 'inf',
            'post_peak_steps': len(post_peak_data),
            'decay_quality': round(decay_quality, 3),
            'follows_exponential': decay_rate > 0 and decay_quality > 0.7,
            'interpretation': 'Exponential decay' if decay_rate > 0 and decay_quality > 0.7 else 'Irregular decay'
        }
    
    async def analyze_homophily(self) -> Dict[str, Any]:
        """
        Analyze homophily in interactions (McPherson et al. 2001).
        Measures if agents interact more with similar agents than expected by chance.
        
        Returns:
            Dict with homophily analysis
        """
        # Get all agents and their personas
        agents = await self.db.get_all_agents()
        agent_map = {a['agent_id']: a['persona'] for a in agents}
        
        # Analyze follow relationships
        follow_homophily = await self._analyze_follow_homophily(agent_map)
        
        # Analyze interaction homophily (likes and comments)
        interaction_homophily = await self._analyze_interaction_homophily(agent_map)
        
        return {
            'follow_homophily': follow_homophily,
            'interaction_homophily': interaction_homophily,
            'interpretation': self._interpret_homophily(follow_homophily, interaction_homophily)
        }
    
    async def _analyze_follow_homophily(self, agent_map: Dict) -> Dict[str, Any]:
        """Analyze homophily in follow relationships."""
        # Get all follow relationships
        async with self.db.conn.execute(
            "SELECT follower_id, followee_id FROM follows"
        ) as cursor:
            follows = await cursor.fetchall()
        
        if not follows:
            return {'error': 'No follow relationships found'}
        
        # Calculate similarity for actual follows
        actual_similarities = {
            'personality': [],
            'age': [],
            'interests': []
        }
        
        for follow in follows:
            follower = agent_map.get(follow['follower_id'])
            followee = agent_map.get(follow['followee_id'])
            
            if follower and followee:
                # Personality similarity (Big Five)
                pers_sim = self._calculate_personality_similarity(follower, followee)
                actual_similarities['personality'].append(pers_sim)
                
                # Age similarity
                age_sim = 1.0 - abs(follower['age'] - followee['age']) / 50.0
                actual_similarities['age'].append(age_sim)
                
                # Interest similarity
                int_sim = self._calculate_interest_similarity(follower, followee)
                actual_similarities['interests'].append(int_sim)
        
        # Calculate random baseline (sample random pairs)
        n_samples = min(len(follows), 1000)
        random_similarities = {
            'personality': [],
            'age': [],
            'interests': []
        }
        
        agent_ids = list(agent_map.keys())
        import random
        
        for _ in range(n_samples):
            id1, id2 = random.sample(agent_ids, 2)
            agent1 = agent_map[id1]
            agent2 = agent_map[id2]
            
            pers_sim = self._calculate_personality_similarity(agent1, agent2)
            random_similarities['personality'].append(pers_sim)
            
            age_sim = 1.0 - abs(agent1['age'] - agent2['age']) / 50.0
            random_similarities['age'].append(age_sim)
            
            int_sim = self._calculate_interest_similarity(agent1, agent2)
            random_similarities['interests'].append(int_sim)
        
        # Calculate homophily scores
        results = {}
        for dimension in ['personality', 'age', 'interests']:
            if actual_similarities[dimension] and random_similarities[dimension]:
                actual_mean = sum(actual_similarities[dimension]) / len(actual_similarities[dimension])
                random_mean = sum(random_similarities[dimension]) / len(random_similarities[dimension])
                homophily_score = (actual_mean - random_mean) / random_mean if random_mean > 0 else 0
                
                results[dimension] = {
                    'actual_similarity': round(actual_mean, 3),
                    'random_similarity': round(random_mean, 3),
                    'homophily_score': round(homophily_score, 3),
                    'is_homophilic': homophily_score > 0.1
                }
            else:
                results[dimension] = {'error': 'Insufficient data'}
        
        results['total_follows'] = len(follows)
        return results
    
    async def _analyze_interaction_homophily(self, agent_map: Dict) -> Dict[str, Any]:
        """Analyze homophily in likes and comments."""
        # Get interactions with post authors
        async with self.db.conn.execute(
            """SELECT i.agent_id as interactor, p.agent_id as author, i.interaction_type
               FROM interactions i
               JOIN posts p ON i.post_id = p.post_id
               WHERE i.agent_id != p.agent_id"""
        ) as cursor:
            interactions = await cursor.fetchall()
        
        if not interactions:
            return {'error': 'No interactions found'}
        
        # Similar analysis as follows
        actual_similarities = {
            'personality': [],
            'age': [],
            'interests': []
        }
        
        for interaction in interactions:
            interactor = agent_map.get(interaction['interactor'])
            author = agent_map.get(interaction['author'])
            
            if interactor and author:
                pers_sim = self._calculate_personality_similarity(interactor, author)
                actual_similarities['personality'].append(pers_sim)
                
                age_sim = 1.0 - abs(interactor['age'] - author['age']) / 50.0
                actual_similarities['age'].append(age_sim)
                
                int_sim = self._calculate_interest_similarity(interactor, author)
                actual_similarities['interests'].append(int_sim)
        
        # Random baseline
        n_samples = min(len(interactions), 1000)
        random_similarities = {
            'personality': [],
            'age': [],
            'interests': []
        }
        
        agent_ids = list(agent_map.keys())
        import random
        
        for _ in range(n_samples):
            id1, id2 = random.sample(agent_ids, 2)
            agent1 = agent_map[id1]
            agent2 = agent_map[id2]
            
            pers_sim = self._calculate_personality_similarity(agent1, agent2)
            random_similarities['personality'].append(pers_sim)
            
            age_sim = 1.0 - abs(agent1['age'] - agent2['age']) / 50.0
            random_similarities['age'].append(age_sim)
            
            int_sim = self._calculate_interest_similarity(agent1, agent2)
            random_similarities['interests'].append(int_sim)
        
        # Calculate homophily scores
        results = {}
        for dimension in ['personality', 'age', 'interests']:
            if actual_similarities[dimension] and random_similarities[dimension]:
                actual_mean = sum(actual_similarities[dimension]) / len(actual_similarities[dimension])
                random_mean = sum(random_similarities[dimension]) / len(random_similarities[dimension])
                homophily_score = (actual_mean - random_mean) / random_mean if random_mean > 0 else 0
                
                results[dimension] = {
                    'actual_similarity': round(actual_mean, 3),
                    'random_similarity': round(random_mean, 3),
                    'homophily_score': round(homophily_score, 3),
                    'is_homophilic': homophily_score > 0.1
                }
            else:
                results[dimension] = {'error': 'Insufficient data'}
        
        results['total_interactions'] = len(interactions)
        return results
    
    def _calculate_personality_similarity(self, agent1: Dict, agent2: Dict) -> float:
        """Calculate Big Five personality similarity (0-1)."""
        traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
        
        pers1 = agent1.get('personality', {})
        pers2 = agent2.get('personality', {})
        
        if not pers1 or not pers2:
            return 0.5
        
        # Euclidean distance in 5D personality space
        squared_diffs = [(pers1.get(t, 0.5) - pers2.get(t, 0.5))**2 for t in traits]
        distance = (sum(squared_diffs) / len(traits)) ** 0.5
        
        # Convert to similarity (0-1), max distance is ~0.7 for [0,1] traits
        similarity = 1.0 - distance / 0.7
        return max(0, min(1, similarity))
    
    def _calculate_interest_similarity(self, agent1: Dict, agent2: Dict) -> float:
        """Calculate interest overlap (Jaccard similarity)."""
        interests1 = set(agent1.get('interests', []))
        interests2 = set(agent2.get('interests', []))
        
        if not interests1 and not interests2:
            return 0.0
        
        intersection = len(interests1 & interests2)
        union = len(interests1 | interests2)
        
        return intersection / union if union > 0 else 0.0
    
    def _interpret_homophily(self, follow_hom: Dict, interact_hom: Dict) -> str:
        """Interpret homophily results."""
        homophilic_dimensions = []
        
        # Check follows
        if 'personality' in follow_hom and follow_hom['personality'].get('is_homophilic'):
            homophilic_dimensions.append('personality (follows)')
        if 'age' in follow_hom and follow_hom['age'].get('is_homophilic'):
            homophilic_dimensions.append('age (follows)')
        if 'interests' in follow_hom and follow_hom['interests'].get('is_homophilic'):
            homophilic_dimensions.append('interests (follows)')
        
        # Check interactions
        if 'personality' in interact_hom and interact_hom['personality'].get('is_homophilic'):
            homophilic_dimensions.append('personality (interactions)')
        if 'age' in interact_hom and interact_hom['age'].get('is_homophilic'):
            homophilic_dimensions.append('age (interactions)')
        if 'interests' in interact_hom and interact_hom['interests'].get('is_homophilic'):
            homophilic_dimensions.append('interests (interactions)')
        
        if not homophilic_dimensions:
            return "No significant homophily detected"
        elif len(homophilic_dimensions) <= 2:
            return f"Weak homophily in: {', '.join(homophilic_dimensions)}"
        else:
            return f"Strong homophily across: {', '.join(homophilic_dimensions[:3])}"
    
    # ===================================
    # SUMMARY REPORT
    # ===================================
    
    async def generate_full_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive analysis report.
        
        Returns:
            Complete report with all metrics and tests
        """
        comparison = await self.compare_campaigns()
        chi_square = await self.chi_square_test()
        proportion = await self.proportion_test_reach()
        fishers = await self.fishers_exact_test()
        personality = await self.personality_moderation_analysis()
        
        hope_timeline = await self.get_engagement_over_time('campaign_hope')
        fear_timeline = await self.get_engagement_over_time('campaign_fear')
        
        # Temporal metrics
        hope_peak = await self.calculate_time_to_peak('campaign_hope')
        fear_peak = await self.calculate_time_to_peak('campaign_fear')
        hope_half_life = await self.calculate_half_life('campaign_hope')
        fear_half_life = await self.calculate_half_life('campaign_fear')
        
        # Validation metrics
        heavy_tail = await self.check_heavy_tailed_distribution()
        hope_decay = await self.analyze_temporal_decay('campaign_hope')
        fear_decay = await self.analyze_temporal_decay('campaign_fear')
        homophily = await self.analyze_homophily()
        
        # Import cascade analyzer for structural virality
        from .cascade import CascadeAnalyzer
        cascade_analyzer = CascadeAnalyzer(self.db)
        hope_virality = await cascade_analyzer.calculate_structural_virality('campaign_hope')
        fear_virality = await cascade_analyzer.calculate_structural_virality('campaign_fear')
        
        return {
            'campaign_comparison': comparison,
            'statistical_tests': {
                'chi_square': chi_square,
                'proportion_test': proportion,
                'fishers_exact': fishers
            },
            'personality_moderation': personality,
            'temporal_dynamics': {
                'hope': hope_timeline,
                'fear': fear_timeline,
                'hope_peak': hope_peak,
                'fear_peak': fear_peak,
                'hope_half_life': hope_half_life,
                'fear_half_life': fear_half_life
            },
            'validation_metrics': {
                'heavy_tailed_distribution': heavy_tail,
                'temporal_decay': {
                    'hope': hope_decay,
                    'fear': fear_decay
                },
                'homophily': homophily,
                'structural_virality': {
                    'hope': hope_virality,
                    'fear': fear_virality
                }
            },
            'key_findings': self._summarize_findings(comparison, chi_square, proportion, fishers)
        }
    
    def _summarize_findings(
        self,
        comparison: Dict,
        chi_square: Dict,
        proportion: Dict,
        fishers: Dict
    ) -> List[str]:
        """Generate list of key findings."""
        findings = []
        
        # Engagement comparison
        hope_total = comparison['hope']['engagement']['total']
        fear_total = comparison['fear']['engagement']['total']
        
        if hope_total == 0 and fear_total == 0:
            findings.append("No engagement recorded for either campaign (possible tracking issue)")
        elif hope_total == 0:
            findings.append(f"Fear campaign generated {fear_total} engagements, Hope had no recorded engagement")
        elif fear_total == 0:
            findings.append(f"Hope campaign generated {hope_total} engagements, Fear had no recorded engagement")
        elif hope_total > fear_total:
            pct_diff = round((hope_total - fear_total) / fear_total * 100, 1)
            findings.append(f"Hope campaign generated {pct_diff}% more total engagement than fear campaign")
        else:
            pct_diff = round((fear_total - hope_total) / hope_total * 100, 1)
            findings.append(f"Fear campaign generated {pct_diff}% more total engagement than hope campaign")
        
        # Reach comparison
        hope_reach = comparison['hope']['reach']['total_unique']
        fear_reach = comparison['fear']['reach']['total_unique']
        if hope_reach > 0 and fear_reach > 0:
            if hope_reach > fear_reach:
                pct_diff = round((hope_reach - fear_reach) / fear_reach * 100, 1)
                findings.append(f"Hope campaign reached {pct_diff}% more agents than fear campaign")
            elif fear_reach > hope_reach:
                pct_diff = round((fear_reach - hope_reach) / hope_reach * 100, 1)
                findings.append(f"Fear campaign reached {pct_diff}% more agents than hope campaign")
        
        # Virality
        hope_viral = comparison['hope']['virality']
        fear_viral = comparison['fear']['virality']
        if hope_viral > 0 and fear_viral > 0:
            if hope_viral > fear_viral:
                pct_diff = round((hope_viral - fear_viral) / fear_viral * 100, 1)
                findings.append(f"Hope campaign was {pct_diff}% more viral (higher secondary spread)")
            elif fear_viral > hope_viral:
                pct_diff = round((fear_viral - hope_viral) / hope_viral * 100, 1)
                findings.append(f"Fear campaign was {pct_diff}% more viral (higher secondary spread)")
        
        # Statistical significance
        if proportion['significant']:
            findings.append(f"Reach difference is statistically significant (p={proportion['p_value']:.4f})")
        
        if fishers['significant']:
            findings.append(f"Amplification rate difference is statistically significant (p={fishers['p_value']:.4f})")
        
        return findings


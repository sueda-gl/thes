"""
Network cascade and information spread analysis.
"""
from typing import Dict, List, Set
from database.db import Database


class CascadeAnalyzer:
    """Analyze how campaigns cascade through the network."""
    
    def __init__(self, db: Database):
        """Initialize with database connection."""
        self.db = db
    
    async def trace_cascade(self, campaign_id: str) -> Dict:
        """
        Trace how a campaign spread through the network.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Cascade flow data
        """
        exposures = await self.db.get_exposures_by_campaign(campaign_id)
        
        # Group by exposure type
        direct_agents = set(e['agent_id'] for e in exposures if e['exposure_type'] == 'direct')
        secondary_agents = set(e['agent_id'] for e in exposures if e['exposure_type'] == 'secondary')
        tertiary_agents = set(e['agent_id'] for e in exposures if e['exposure_type'] == 'tertiary')
        
        # Calculate cascade metrics
        direct_count = len(direct_agents)
        secondary_count = len(secondary_agents)
        tertiary_count = len(tertiary_agents)
        
        # Amplification at each level
        primary_amplification = secondary_count / direct_count if direct_count > 0 else 0
        secondary_amplification = tertiary_count / secondary_count if secondary_count > 0 else 0
        
        return {
            'direct': direct_count,
            'secondary': secondary_count,
            'tertiary': tertiary_count,
            'total_reached': direct_count + secondary_count + tertiary_count,
            'primary_amplification': round(primary_amplification, 2),
            'secondary_amplification': round(secondary_amplification, 2),
            'cascade_levels': 3 if tertiary_count > 0 else (2 if secondary_count > 0 else 1)
        }
    
    async def get_cascade_flow(self, campaign_id: str) -> Dict:
        """
        Get data for Sankey diagram visualization.
        
        Args:
            campaign_id: Campaign ID
        
        Returns:
            Flow data for visualization
        """
        cascade = await self.trace_cascade(campaign_id)
        
        # Create flow data
        flows = [
            {
                'source': 'Direct Exposure',
                'target': 'Secondary Exposure',
                'value': cascade['secondary']
            },
            {
                'source': 'Secondary Exposure',
                'target': 'Tertiary Exposure',
                'value': cascade['tertiary']
            },
            {
                'source': 'Direct Exposure',
                'target': 'No Further Spread',
                'value': cascade['direct'] - cascade['secondary']
            }
        ]
        
        return {
            'nodes': [
                'Direct Exposure',
                'Secondary Exposure',
                'Tertiary Exposure',
                'No Further Spread'
            ],
            'flows': flows
        }
    
    async def verify_cascade_consistency(self, campaign_id: str) -> Dict[str, Any]:
        """
        Verify cascade accounting is consistent.
        Checks that reshares have proper parent links and exposure levels.
        
        Returns:
            Dict with consistency check results
        """
        issues = []
        
        # Get all campaign posts and their descendants
        campaign_type = campaign_id.replace('campaign_', '')
        
        # Check 1: All reshares have valid parent_post_id
        async with self.db.conn.execute(
            """SELECT post_id, parent_post_id, post_type, agent_id 
               FROM posts 
               WHERE post_type = 'reshare'"""
        ) as cursor:
            reshares = await cursor.fetchall()
            
            for reshare in reshares:
                # Verify parent exists
                parent = await self.db.get_post(reshare['parent_post_id'])
                if not parent:
                    issues.append(f"Reshare {reshare['post_id']} has invalid parent {reshare['parent_post_id']}")
        
        # Check 2: Exposure levels are consistent
        exposures = await self.db.get_exposures_by_campaign(campaign_id)
        
        # Group by agent to check consistency
        agent_exposures = {}
        for exp in exposures:
            agent_id = exp['agent_id']
            if agent_id not in agent_exposures:
                agent_exposures[agent_id] = []
            agent_exposures[agent_id].append(exp)
        
        for agent_id, exps in agent_exposures.items():
            exp_types = [e['exposure_type'] for e in exps]
            
            # Check logical progression
            if 'tertiary' in exp_types and 'secondary' not in exp_types:
                issues.append(f"Agent {agent_id} has tertiary exposure without secondary")
            
            # Check no duplicates at same level
            if len(exp_types) != len(set(exp_types)):
                issues.append(f"Agent {agent_id} has duplicate exposure levels")
        
        return {
            'is_consistent': len(issues) == 0,
            'issues': issues,
            'total_reshares': len(reshares),
            'agents_with_exposures': len(agent_exposures)
        }
    
    async def calculate_structural_virality(self, campaign_id: str) -> Dict[str, Any]:
        """
        Calculate structural virality (Goel et al. 2016).
        Measures average distance from root in cascade tree.
        Low values = broadcast-like, High values = viral spread.
        
        Returns:
            Dict with structural virality metrics
        """
        # Get all exposures for this campaign
        exposures = await self.db.get_exposures_by_campaign(campaign_id)
        
        if not exposures:
            return {'error': 'No exposures found'}
        
        # Build exposure tree
        direct_agents = set()
        secondary_agents = set()
        tertiary_agents = set()
        
        for exp in exposures:
            agent_id = exp['agent_id']
            exp_type = exp['exposure_type']
            
            if exp_type == 'direct':
                direct_agents.add(agent_id)
            elif exp_type == 'secondary':
                secondary_agents.add(agent_id)
            elif exp_type == 'tertiary':
                tertiary_agents.add(agent_id)
        
        # Calculate total nodes in cascade
        total_nodes = len(direct_agents) + len(secondary_agents) + len(tertiary_agents)
        
        if total_nodes <= 1:
            return {
                'structural_virality': 0,
                'total_nodes': total_nodes,
                'interpretation': 'No cascade (single node)'
            }
        
        # Calculate average pairwise distance
        # For our three-level model, we use a simplified calculation
        # Direct agents are at distance 0 from root
        # Secondary agents are at distance 1
        # Tertiary agents are at distance 2
        
        n_direct = len(direct_agents)
        n_secondary = len(secondary_agents)
        n_tertiary = len(tertiary_agents)
        
        # Sum of all pairwise distances from root
        # Direct nodes: distance 0
        # Secondary nodes: distance 1 each
        # Tertiary nodes: distance 2 each
        total_distance = 0 * n_direct + 1 * n_secondary + 2 * n_tertiary
        
        # Average distance (structural virality)
        avg_distance = total_distance / total_nodes
        
        # Calculate cascade depth and breadth
        cascade_depth = 0
        if n_tertiary > 0:
            cascade_depth = 2
        elif n_secondary > 0:
            cascade_depth = 1
        else:
            cascade_depth = 0
        
        # Breadth at each level
        breadth_metrics = {
            'level_0_breadth': n_direct,
            'level_1_breadth': n_secondary,
            'level_2_breadth': n_tertiary,
            'max_breadth': max(n_direct, n_secondary, n_tertiary)
        }
        
        # Interpretation based on structural virality
        if avg_distance < 0.5:
            interpretation = "Broadcast-like (most nodes directly exposed)"
        elif avg_distance < 1.0:
            interpretation = "Moderate virality (mix of direct and secondary)"
        else:
            interpretation = "High virality (significant cascade depth)"
        
        return {
            'structural_virality': round(avg_distance, 3),
            'total_nodes': total_nodes,
            'cascade_depth': cascade_depth,
            'nodes_by_level': {
                'direct': n_direct,
                'secondary': n_secondary,
                'tertiary': n_tertiary
            },
            'breadth_metrics': breadth_metrics,
            'interpretation': interpretation
        }


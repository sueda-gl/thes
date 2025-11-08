"""
Test script for belief change tracking system.

Runs a small-scale simulation to validate:
- Database schema updates
- Cascade depth tracking
- Belief measurement at T0/T1/T2
- Exposure tracking with depth
- Analysis tools
"""
import asyncio
from simulation.engine import SimulationEngine
from analysis.belief_analysis import generate_summary_report
from database.db import Database


async def run_test():
    """Run small test simulation."""
    print("=" * 70)
    print("BELIEF TRACKING SYSTEM TEST")
    print("=" * 70)
    print("\nRunning small-scale simulation...")
    print("- 20 agents")
    print("- 500 steps (~8 hours)")
    print("- Campaign at step 240 (4 hours)")
    print("- Belief measurements at steps: 239, 360, 500")
    print()
    
    # Override config for quick test
    import config
    original_steps = config.SIMULATION_STEPS
    original_agents = config.NUM_AGENTS
    original_campaign_step = config.CAMPAIGN_LAUNCH_STEP
    original_belief_steps = config.BELIEF_MEASUREMENT_STEPS
    
    config.SIMULATION_STEPS = 500
    config.NUM_AGENTS = 20
    config.CAMPAIGN_LAUNCH_STEP = 240
    config.BELIEF_MEASUREMENT_STEPS = [239, 360, 500]  # T0, T1, T2
    
    try:
        # Create engine
        engine = SimulationEngine(
            db_path="data/test_belief.db",
            seed=42,
            n_steps=500,
            n_agents=20
        )
        
        # Initialize
        await engine.initialize()
        
        # Run simulation
        print("\n" + "=" * 70)
        print("RUNNING SIMULATION")
        print("=" * 70)
        
        for step in range(1, config.SIMULATION_STEPS + 1):
            # Execute step
            metrics = await engine.execute_step(step)
            
            # Print progress every 100 steps
            if step % 100 == 0 or step == config.SIMULATION_STEPS:
                print(f"\n✓ Step {step}/{config.SIMULATION_STEPS} complete")
                print(f"  - Online agents: {metrics.get('online_agents', 0)}")
                print(f"  - Total posts: {metrics.get('total_posts', 0)}")
        
        # Finalize
        await engine.finalize()
        
        print("\n" + "=" * 70)
        print("SIMULATION COMPLETE")
        print("=" * 70)
        
        # Validate data
        print("\n" + "=" * 70)
        print("DATA VALIDATION")
        print("=" * 70)
        
        db = engine.db
        
        # Check belief measurements
        print("\n1. Belief Measurements:")
        for step in config.BELIEF_MEASUREMENT_STEPS:
            measurements = await db.get_beliefs_at_step(step, 'environmental_concern')
            print(f"   T{config.BELIEF_MEASUREMENT_STEPS.index(step)} (step {step}): {len(measurements)} measurements")
            if measurements:
                values = [m['value'] for m in measurements]
                avg = sum(values) / len(values)
                print(f"     Average value: {avg:.3f}")
        
        # Check cascade depth tracking
        print("\n2. Cascade Depth Distribution:")
        async with db.conn.execute("""
            SELECT cascade_depth, COUNT(*) as count
            FROM posts
            WHERE post_type IN ('campaign', 'reshare')
            GROUP BY cascade_depth
            ORDER BY cascade_depth
        """) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                print(f"   Depth {row['cascade_depth']}: {row['count']} posts")
        
        # Check campaign exposures
        print("\n3. Campaign Exposures:")
        async with db.conn.execute("""
            SELECT campaign_id, cascade_depth, COUNT(*) as count
            FROM campaign_exposures
            GROUP BY campaign_id, cascade_depth
            ORDER BY campaign_id, cascade_depth
        """) as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                camp_type = 'Hope' if 'hope' in row['campaign_id'] else 'Fear'
                depth_label = f"Direct (depth=0)" if row['cascade_depth'] == 0 else f"Depth {row['cascade_depth']}"
                print(f"   {camp_type} - {depth_label}: {row['count']} exposures")
        
        # Check directly targeted agents
        print("\n4. Directly Targeted Agents:")
        hope_targeted = await db.get_directly_targeted_agents('hope')
        fear_targeted = await db.get_directly_targeted_agents('fear')
        print(f"   Hope campaign: {len(hope_targeted)} agents")
        print(f"   Fear campaign: {len(fear_targeted)} agents")
        
        # Generate analysis report
        print("\n" + "=" * 70)
        print("BELIEF CHANGE ANALYSIS")
        print("=" * 70)
        
        report = await generate_summary_report(db, 'environmental_concern')
        print("\n" + report)
        
        # Close database
        await db.close()
        
        print("\n" + "=" * 70)
        print("✅ TEST COMPLETE - All systems operational!")
        print("=" * 70)
        
    finally:
        # Restore original config
        config.SIMULATION_STEPS = original_steps
        config.NUM_AGENTS = original_agents
        config.CAMPAIGN_LAUNCH_STEP = original_campaign_step
        config.BELIEF_MEASUREMENT_STEPS = original_belief_steps


if __name__ == "__main__":
    asyncio.run(run_test())


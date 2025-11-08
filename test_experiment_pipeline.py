"""
Ultra-fast pipeline test: Validates full experiment works with LLM agents.
Should complete in 2-3 minutes.
"""
import asyncio
from simulation.engine import SimulationEngine
from analysis.belief_analysis import generate_summary_report
import config

# Override for ultra-fast test
config.SIMULATION_STEPS = 100  # Just 100 minutes
config.NUM_AGENTS = 100  # Good sample size for testing
config.CAMPAIGN_LAUNCH_STEP = 40  # Launch early
config.BELIEF_MEASUREMENT_STEPS = [39, 60, 100]  # T0, T1, T2
config.LLM_MODEL = "gpt-3.5-turbo"  # Fast and cheap
config.LLM_MAX_CONCURRENT = 50  # High concurrency
config.BELIEF_CONCURRENCY_LIMIT = 50


async def main():
    print("=" * 70)
    print("ULTRA-FAST EXPERIMENT PIPELINE TEST")
    print("=" * 70)
    print("\nConfiguration:")
    print(f"  - 100 agents (10 Hope, 10 Fear, 80 control)")
    print(f"  - 100 steps (~1.5 hours simulated time)")
    print(f"  - Campaign at step 40")
    print(f"  - Using gpt-3.5-turbo for speed")
    print(f"  - Expected runtime: 5-10 minutes")
    print()
    
    engine = SimulationEngine(
        db_path="data/pipeline_test.db",
        seed=42,
        n_steps=100,
        n_agents=100
    )
    
    await engine.initialize()
    
    print("\n" + "=" * 70)
    print("RUNNING SIMULATION")
    print("=" * 70)
    
    for step in range(1, 101):
        await engine.execute_step(step)
        
        # Show progress every 20 steps
        if step % 20 == 0:
            print(f"\n[Step {step}/100] ✓")
    
    await engine.finalize()
    
    print("\n" + "=" * 70)
    print("VALIDATION")
    print("=" * 70)
    
    db = engine.db
    
    # Check campaigns were injected
    async with db.conn.execute("SELECT COUNT(*) as count FROM campaigns") as cursor:
        row = await cursor.fetchone()
        print(f"\n✓ Campaigns injected: {row['count']}")
    
    # Check belief measurements at all 3 timepoints
    print(f"\n✓ Belief measurements:")
    for step in config.BELIEF_MEASUREMENT_STEPS:
        beliefs = await db.get_beliefs_at_step(step, 'environmental_concern')
        print(f"   T{config.BELIEF_MEASUREMENT_STEPS.index(step)} (step {step}): {len(beliefs)} measurements")
    
    # Check exposures
    async with db.conn.execute("""
        SELECT campaign_id, COUNT(DISTINCT agent_id) as agents
        FROM campaign_exposures
        WHERE cascade_depth = 0
        GROUP BY campaign_id
    """) as cursor:
        rows = await cursor.fetchall()
        print(f"\n✓ Direct campaign exposures:")
        for row in rows:
            camp_type = 'Hope' if 'hope' in row['campaign_id'] else 'Fear'
            print(f"   {camp_type}: {row['agents']} agents")
    
    # Generate analysis
    print("\n" + "=" * 70)
    print("BELIEF CHANGE ANALYSIS")
    print("=" * 70)
    
    report = await generate_summary_report(db, 'environmental_concern')
    print("\n" + report)
    
    await db.close()
    
    print("\n" + "=" * 70)
    print("✅ PIPELINE TEST COMPLETE!")
    print("=" * 70)
    print("\nIf you see belief measurements and campaign analysis above,")
    print("your full experiment pipeline is working correctly.")
    print("\nYou can now scale up to full experiments with confidence.")
    print()


if __name__ == "__main__":
    asyncio.run(main())


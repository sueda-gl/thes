"""
Bachelor's Thesis Experiment V2: Hope vs. Fear Campaign Belief Change

CORRECTED VERSION - Fixes reflection frequency confound from V1

Changes from V1:
    - REFLECT_EVERY = 100 (was 3) → Reduces reflections from 133k to 4k
    - Prevents psychological repetition artifact
    - Allows clean test of Hope vs Fear framing hypothesis

Expected Runtime: 30-45 minutes
Expected Cost: $35-45 (down from $284 due to fewer reflections)
"""
import asyncio
from simulation.engine import SimulationEngine
from analysis.belief_analysis import generate_summary_report
import config
from datetime import datetime
import os


# ============================================
# EXPERIMENT CONFIGURATION V2
# ============================================

# Population: 200 agents (engaged user subset)
config.NUM_AGENTS = 200

# Timeline: 2000 steps = ~33 hours simulated time
config.SIMULATION_STEPS = 2000
config.CAMPAIGN_LAUNCH_STEP = 400

# Belief measurement checkpoints
config.BELIEF_MEASUREMENT_STEPS = [399, 800, 2000]

# Campaign targeting: 30% each for Hope and Fear (stratified assignment)
config.CAMPAIGN_FRAC_HOPE = 0.30  # 60 agents
config.CAMPAIGN_FRAC_FEAR = 0.30  # 60 agents

# LLM Configuration
config.LLM_MODEL = "gpt-4o"
config.LLM_TEMPERATURE = 0.8  # HIGH for authentic, diverse voices (was 0.4 in V1, 0.6 in V2-draft)
config.LLM_MAX_CONCURRENT = 50
config.BELIEF_CONCURRENCY_LIMIT = 30

# Persona configuration - V2 uses Beta(2.5, 3.75) + rich biographical narratives
config.PERSONA_FILE = "personas/personas_v2_final.json"

# CRITICAL FIX 1: Reflection timing
# V1 had REFLECT_EVERY = 3 (too frequent) → 133k reflections → psychological repetition
# V2 uses measurement-triggered reflections → Only 3 per agent → zero repetition
# Agents reflect ONLY at T0/T1/T2 (right before belief measurement)
# This creates coherent reflection→belief assessment sequence
config.REFLECT_EVERY = 9999  # Disable scheduled reflections (use triggered instead)

# CRITICAL FIX 2: Remove sponsored marker
# V1 had "🔔 SPONSORED POST" → triggered reactance regardless of framing
# V2 removes marker → tests pure Hope vs Fear message content
# V2.1: Added efficacy to both messages for theory-aligned comparison
config.CAMPAIGNS = {
    "hope": {
        "type": "hope",
        "message": (
            "The great reversal has begun. "
            "For the first time in history, renewables are outpacing fossil fuels. "
            "Entire regions once smothered in smoke now glow with wind-powered light. "
            "Coral reefs once declared dead are flickering back to life. "
            "Air once toxic has turned blue again. "
            "And your choice matters. "
            "A five-minute switch to clean power adds your share to the comeback — "
            "cutting pollution that sends thousands to hospitals each year and keeping warming below 1.5 °C. "
            "The process is verified, quick, and confirmed within a day. "
            "Be the reason your family breathes cleaner air and the planet wins its fight."
        )
    },
    "fear": {
        "type": "fear",
        "message": (
            "This is how civilisation collapses — quietly, degree by degree. "
            "We're on track to cross 1.5 °C by 2030. Once that line is crossed, the world we know unravels: "
            "Cities suffocate under heat so intense the human body can't survive outdoors. "
            "Rivers that feed billions run dry. "
            "Entire coastlines disappear under rising seas. "
            "Food prices skyrocket as harvests fail across continents. "
            "This isn't distant — it's your world, your future. "
            "But you can still push back. "
            "A five-minute switch to verified clean energy keeps about a tonne of CO₂ out of the air each year — "
            "enough to power your home for two months or cool a neighbourhood for days. "
            "The window to act is closing. Every day of delay locks in another disaster. "
            "Act before the tipping point becomes permanent."
        )
    }
}

# Engaged user calibration (3× baseline)
config.AVG_LOGIN = 429  # 3× baseline for power user modeling


async def main():
    """Run the corrected thesis experiment."""
    
    print("=" * 80)
    print("BACHELOR'S THESIS EXPERIMENT V2 (CORRECTED)")
    print("Hope vs. Fear Campaign Belief Change on Social Media")
    print("=" * 80)
    
    start_timestamp = datetime.now()
    print(f"\nStarted: {start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "─" * 80)
    print("CONFIGURATION SUMMARY (V2 - Corrected)")
    print("─" * 80)
    print(f"  Population:")
    print(f"    • 200 agents (engaged user subset: Activity ∈ [0.3, 1.0])")
    print(f"    • Online time range: 129-429 min/day (3× baseline, power users)")
    print(f"    • Expected concurrent online: ~35-40 agents at steady-state")
    print()
    print(f"  Experimental Assignment:")
    print(f"    • 60 agents → Hope campaign (30%)")
    print(f"    • 60 agents → Fear campaign (30%)")
    print(f"    • 80 agents → Control (40%, may see via cascades)")
    print(f"    • Stratified by Activity × Network Degree")
    print()
    print(f"  Timeline:")
    print(f"    • Total: 2000 steps (~33 hours simulated time)")
    print(f"    • Burn-in: Steps 1-399 (organic baseline)")
    print(f"    • Campaign: Step 400")
    print(f"    • Belief measurements: T0=399, T1=800, T2=2000")
    print()
    print(f"  ⚠️  CRITICAL FIXES FROM V1:")
    print(f"    • FIX 1: Measurement-triggered reflections (was scheduled every 3 steps)")
    print(f"      - Reflections: 3 per agent, ONLY before T0/T1/T2 measurements")
    print(f"      - Reduces from 133,000 to 600 total reflections (99.5% reduction)")
    print(f"      - Campaign mentioned max 3 times (was 133 times)")
    print(f"      - Zero psychological repetition artifact")
    print(f"    • FIX 2: Removed '🔔 SPONSORED POST' marker")
    print(f"      - Tests pure Hope vs Fear framing")
    print(f"      - Eliminates advertising reactance confound")
    print()
    print(f"  Persona Quality:")
    print(f"    • Environmental concern: 0.10-0.72 (mean 0.40, SD 0.14)")
    print(f"    • Wide variance: Activists to skeptics to apolitical")
    print(f"    • Rich backstories: Politics, trauma, conspiracies, family drama")
    print()
    print(f"  Computational Resources:")
    print(f"    • LLM: {config.LLM_MODEL}")
    print(f"    • Temperature: 0.8 (HIGH for authentic, diverse voices)")
    print(f"    • Max concurrent calls: {config.LLM_MAX_CONCURRENT}")
    print(f"    • Expected LLM calls: ~38,500 total")
    print(f"      - Decisions: ~18,000 (personality-driven)")
    print(f"      - Organic posts: ~20,000 (LLM-generated, not templates)")
    print(f"      - Reflections: ~600 (ONLY at T0/T1/T2, before measurement)")
    print(f"      - Belief measurements: ~440")
    print(f"    • Expected runtime: 40-50 minutes")
    print(f"    • Expected cost: $130-150")
    print("─" * 80)
    print()
    
    print("📋 Complete V2 Improvements:")
    print("  ✅ Measurement-triggered reflections (3 per agent vs 666 in V1)")
    print("  ✅ Sponsored marker removed (pure framing test)")
    print("  ✅ Beta(2.5, 3.75) environmental concern (theoretically justified)")
    print("  ✅ Lower baseline (mean 0.40 vs 0.74 - avoids ceiling effect)")
    print("  ✅ WIDE variance (0.05-0.90 range, SD 0.18 vs 0.10)")
    print("  ✅ Rich biographical narratives (politics, family, trauma, conspiracies)")
    print("  ✅ LLM-generated organic posts (personality-driven vs templates)")
    print("  ✅ Higher temperature (0.8 vs 0.4 - authentic voices)")
    print("  ✅ Unconstrained prompts ('be yourself, not corporate')")
    print("  ✅ Environmentally-engaged subsample (interests = advocacy OR critique)")
    print(f"  ✅ Same experimental design (stratified, 3 timepoints, power user model)")
    print()
    
    response = input("Proceed with corrected experiment? [y/N]: ")
    if response.lower() != 'y':
        print("Experiment cancelled.")
        return
    
    print("\n" + "=" * 80)
    print("STARTING SIMULATION V2")
    print("=" * 80)
    
    # Create timestamped database path
    db_filename = f"thesis_experiment_v2_{start_timestamp.strftime('%Y%m%d_%H%M%S')}.db"
    db_path = os.path.join("data", db_filename)
    
    # Initialize engine
    engine = SimulationEngine(
        db_path=db_path,
        seed=42,
        n_steps=2000,
        n_agents=200
    )
    
    # Initialize components
    await engine.initialize()
    
    # Run simulation
    try:
        print("\n" + "=" * 80)
        print("RUNNING SIMULATION")
        print("=" * 80)
        print("This will take approximately 30-45 minutes.")
        print("Progress will be displayed every 100 steps.")
        print()
        
        final_metrics = await engine.run()
        
        print("\n" + "=" * 80)
        print("SIMULATION COMPLETE")
        print("=" * 80)
        
        # Print summary statistics
        end_timestamp = datetime.now()
        duration = end_timestamp - start_timestamp
        
        print(f"\nCompleted: {end_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Duration: {duration}")
        print(f"Database: {db_path}")
        
        # LLM usage
        usage = engine.llm_client.get_usage_stats()
        print(f"\nLLM Usage:")
        print(f"  • Total requests: {usage['total_requests']:,}")
        print(f"  • Failed requests: {usage['failed_requests']:,}")
        print(f"  • Total tokens: {usage['total_tokens']:,}")
        print(f"  • Input tokens: {usage['total_input_tokens']:,}")
        print(f"  • Output tokens: {usage['total_output_tokens']:,}")
        print(f"  • Estimated cost: ${usage['estimated_cost_usd']:.2f}")
        
        print("\n" + "=" * 80)
        print("COMPARISON: V1 vs V2")
        print("=" * 80)
        print(f"\nV1 (Confounded):")
        print(f"  • Reflections: ~133,000")
        print(f"  • Total calls: 117,728")
        print(f"  • Cost: $284.59")
        print(f"  • Result: Both decreased (confounded by psychological repetition)")
        print(f"\nV2 (Corrected):")
        print(f"  • Reflections: ~4,000")
        print(f"  • Total calls: {usage['total_requests']:,}")
        print(f"  • Cost: ${usage['estimated_cost_usd']:.2f}")
        print(f"  • Result: TBD (clean test of Hope vs Fear)")
        
        print("\n" + "=" * 80)
        print("EXPERIMENT V2 COMPLETE")
        print("=" * 80)
        print(f"\nDatabase saved: {db_path}")
        print("Ready for analysis with run_thesis_experiment_v2_analysis.py")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Experiment interrupted by user")
        print(f"Partial data saved to: {db_path}")
    except Exception as e:
        print(f"\n\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Close connections
        await engine.close()
        print("\n✓ Connections closed")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("EXPERIMENT V2: CORRECTED REFLECTION FREQUENCY")
    print("=" * 80)
    print("""
V1 Issue Identified:
    • REFLECT_EVERY = 3 caused ~133,000 reflections
    • Campaign memory retrieved 133 times per agent
    • Created psychological repetition → fatigue → decreased concern
    • Confounded Hope vs Fear comparison

V2 Fix:
    • REFLECT_EVERY = 100 → ~4,000 reflections (33× reduction)
    • Agents reflect every ~1.7 hours (reasonable frequency)
    • Campaign memory still considered, but not overwhelming
    • Clean test of Hope vs Fear framing hypothesis

Expected Outcome:
    • If Hope/Fear differ: Will detect it (no confound)
    • If sponsored marker matters: May still see decrease (but smaller)
    • If no effects: Genuine null result (not artifact)

Cost: ~$35-45 (much lower than V1's $284)
    """)
    print("=" * 80)
    
    # Run experiment
    asyncio.run(main())


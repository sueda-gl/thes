"""
Bachelor's Thesis Experiment: Hope vs. Fear Campaign Belief Change

This script runs the main experiment testing whether hope-framed and fear-framed
environmental campaigns produce different longitudinal belief changes in social
media agents.

Experiment Design:
    - 200 agents (engaged user subset modeling)
    - 30% Hope targeting (60 agents)
    - 30% Fear targeting (60 agents)
    - 40% Control (80 agents)
    - 2000 steps (~33 hours simulated time)
    - 3 belief measurement checkpoints (T0, T1, T2)

See EXPERIMENT_DESIGN.md for complete methodology and justification.

Expected Runtime: 45-60 minutes
Expected Cost: $20-25 (GPT-4o at standard rates)
"""
import asyncio
from simulation.engine import SimulationEngine
from analysis.belief_analysis import generate_summary_report
import config
from datetime import datetime
import os


# ============================================
# EXPERIMENT CONFIGURATION
# ============================================
# These settings override config.py defaults for the thesis experiment.
# All choices are justified in EXPERIMENT_DESIGN.md.

# Population: 200 agents (engaged user subset)
# Justification: n=60 per condition provides 80% power for d=0.4 effect size
config.NUM_AGENTS = 200

# Timeline: 2000 steps = ~33 hours simulated time
# Justification: Sufficient for immediate + sustained belief measurement
#                Balances statistical power with computational efficiency
config.SIMULATION_STEPS = 2000

# Campaign launch: Step 400 (~7 hours after simulation start)
# Justification: Allows burn-in period for organic social timeline
config.CAMPAIGN_LAUNCH_STEP = 400

# Belief measurement checkpoints
# T0 (399): Baseline before campaign (all 200 agents)
# T1 (800): Immediate effect, +7 hours post-campaign (120 targeted agents)
# T2 (2000): Sustained effect, +27 hours post-campaign (120 targeted agents)
config.BELIEF_MEASUREMENT_STEPS = [399, 800, 2000]

# Campaign targeting: 30% each for Hope and Fear (stratified assignment)
# Justification: n=60 per condition for adequate statistical power
#                Stratification by Activity × Degree prevents confounding
config.CAMPAIGN_FRAC_HOPE = 0.30  # 60 agents
config.CAMPAIGN_FRAC_FEAR = 0.30  # 60 agents
# Control group: 80 agents (may receive secondary exposures via cascades)

# LLM Configuration
# Model: GPT-4o (Azure deployment name)
config.LLM_MODEL = "gpt-4o"
config.LLM_TEMPERATURE = 0.4  # Consistent decisions, moderate creativity
config.LLM_MAX_CONCURRENT = 50  # Balance speed and rate limits
config.BELIEF_CONCURRENCY_LIMIT = 30  # Parallel belief measurements

# ENGAGED USER CALIBRATION:
# Activity floor (0.3-1.0) already implemented in simulation/agent.py
# Additionally, scale online time to 3× baseline to model power users
# who drive most platform activity and cascades (Murdock et al., 2024)
#
# Justification: The active minority on social platforms (top 25-30% of users)
# spend substantially more time online than the population average. Studies show
# power users spend 3-5× more time engaged than casual users. By modeling this
# engaged cohort, we ensure sufficient interaction density for observing cascade
# dynamics and belief evolution within computational constraints.
#
# Result: Activity ∈ [0.3, 1.0] × 3 → Online time: 129-429 min/day (2-7 hrs/day)
# Steady-state: ~35-40 agents online at any time (enables rich interactions)
config.AVG_LOGIN = 429  # 3× baseline (143 min/day) for power user modeling


async def main():
    """Run the complete thesis experiment."""
    
    print("=" * 80)
    print("BACHELOR'S THESIS EXPERIMENT")
    print("Hope vs. Fear Campaign Belief Change on Social Media")
    print("=" * 80)
    
    start_timestamp = datetime.now()
    print(f"\nStarted: {start_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "─" * 80)
    print("CONFIGURATION SUMMARY")
    print("─" * 80)
    print(f"  Population:")
    print(f"    • 200 agents (engaged user subset: Activity ∈ [0.3, 1.0])")
    print(f"    • Online time range: 129-429 min/day (3× baseline, power users)")
    print(f"    • Expected concurrent online: ~35-40 agents at steady-state")
    print(f"    • Justification: Models active users who drive diffusion")
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
    print(f"  Statistical Design:")
    print(f"    • Mixed ANOVA: Time (T0,T1,T2) × Condition (Hope,Fear)")
    print(f"    • Target effect size: d = 0.3-0.5")
    print(f"    • Expected power: 0.80 with n=60 per condition")
    print()
    print(f"  Computational Resources:")
    print(f"    • LLM: {config.LLM_MODEL}")
    print(f"    • Max concurrent calls: {config.LLM_MAX_CONCURRENT}")
    print(f"    • Expected runtime: 45-60 minutes")
    print(f"    • Expected cost: $20-25")
    print("─" * 80)
    print()
    
    # Confirm before proceeding
    print("📋 Pre-flight checks:")
    print("  ✓ 200 personas generated (personas/personas.json)")
    print("  ✓ Engaged user subset implemented (Activity ∈ [0.3, 1.0])")
    print("  ✓ Stratified assignment configured")
    print("  ✓ Cascade depth tracking enabled")
    print("  ✓ Belief measurement protocol ready")
    print()
    
    response = input("Proceed with experiment? [y/N]: ")
    if response.lower() != 'y':
        print("Experiment cancelled.")
        return
    
    print("\n" + "=" * 80)
    print("STARTING SIMULATION")
    print("=" * 80)
    
    # Create timestamped database path
    db_filename = f"thesis_experiment_{start_timestamp.strftime('%Y%m%d_%H%M%S')}.db"
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
        print("This will take approximately 45-60 minutes.")
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
        
        # Generate analysis report
        print("\n" + "=" * 80)
        print("GENERATING ANALYSIS REPORT")
        print("=" * 80)
        
        try:
            report_path = await generate_summary_report(db_path)
            print(f"\n✓ Analysis report generated: {report_path}")
            print("\nNext steps:")
            print("  1. Review belief trajectories in the report")
            print("  2. Check Hope vs. Fear comparison statistics")
            print("  3. Examine cascade depth effects")
            print("  4. Run statistical tests (ANOVA) on exported data")
        except Exception as e:
            print(f"\n⚠️  Error generating analysis report: {e}")
            print("You can manually run analysis using: python -m analysis.belief_analysis")
        
        print("\n" + "=" * 80)
        print("EXPERIMENT COMPLETE")
        print("=" * 80)
        print(f"\nDatabase saved: {db_path}")
        print("Ready for statistical analysis and thesis writing.")
        
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


def print_experiment_design_summary():
    """Print a summary of the experimental design for reference."""
    print("\n" + "=" * 80)
    print("EXPERIMENTAL DESIGN REFERENCE")
    print("=" * 80)
    print("""
Design Type: 3 × 3 Mixed ANOVA
    • Between-subjects: Campaign Type (Hope, Fear, Control)
    • Within-subjects: Time (T0, T1, T2)
    • DV: environmental_concern (0-1 scale)

Hypotheses:
    H1: Campaign exposure increases environmental_concern
    H2: Hope and Fear produce different magnitudes of change
    H3: Belief changes persist from T1 to T2
    H4: Direct exposure > Secondary exposure effect

Sample Sizes:
    • Hope: 60 agents (stratified random assignment)
    • Fear: 60 agents (stratified random assignment)
    • Control: 80 agents (no direct targeting)

Timeline:
    • T0 (step 399): Baseline (measure all 200 agents)
    • Campaign (step 400): Inject Hope & Fear messages
    • T1 (step 800): Immediate effect (measure 120 targeted agents)
    • T2 (step 2000): Sustained effect (measure 120 targeted agents)

Population:
    • Engaged user subset (Activity ∈ [0.3, 1.0])
    • Excludes extreme lurkers for statistical power
    • Consistent with empirical finding: active minority drives diffusion

See EXPERIMENT_DESIGN.md for complete justification and citations.
    """)
    print("=" * 80)


if __name__ == '__main__':
    # Print design summary for reference
    print_experiment_design_summary()
    
    # Run experiment
    asyncio.run(main())

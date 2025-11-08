"""Quick test to verify agents come online."""
import asyncio
from simulation.engine import SimulationEngine
import config

# Override for very short test
config.SIMULATION_STEPS = 50
config.NUM_AGENTS = 10
config.CAMPAIGN_LAUNCH_STEP = 25
config.BELIEF_MEASUREMENT_STEPS = [24, 35, 50]

async def main():
    engine = SimulationEngine(
        db_path="data/quick_test.db",
        seed=42,
        n_steps=50,
        n_agents=10
    )
    
    await engine.initialize()
    
    print("\nRunning 50 steps to check agent activity...")
    for step in range(1, 51):
        metrics = await engine.execute_step(step)
        
        if step % 10 == 0:
            online = metrics.get('online_agents', 0)
            print(f"Step {step}: {online}/10 agents online")
    
    await engine.finalize()
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(main())

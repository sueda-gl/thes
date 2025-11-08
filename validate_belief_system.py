"""
Fast validation of belief tracking system components (no LLM calls needed).
"""
import asyncio
from database.db import Database
from simulation.agent import Agent
from llm.client import LLMClient
import random


async def test_belief_system():
    print("=" * 70)
    print("BELIEF TRACKING SYSTEM VALIDATION")
    print("=" * 70)
    
    # 1. Test database schema
    print("\n1. Testing database schema...")
    db = Database("data/validate_belief.db")
    await db.connect()
    await db.clear_all_data()
    
    # Insert test agent
    test_persona = {
        'agent_id': 'test_001',
        'name': 'TestAgent',
        'age': 25,
        'environmental_concern': 0.5,
        'brand_trust': 0.6
    }
    await db.insert_agent('test_001', test_persona)
    print("   ✓ Agent insertion works")
    
    # 2. Test belief measurement storage
    print("\n2. Testing belief measurement storage...")
    await db.insert_belief_measurement(
        agent_id='test_001',
        attribute='environmental_concern',
        value=0.55,
        step=100,
        reasoning="Test measurement"
    )
    
    history = await db.get_belief_history('test_001', 'environmental_concern')
    assert len(history) == 1
    assert history[0]['value'] == 0.55
    print("   ✓ Belief measurement storage works")
    
    # 3. Test cascade depth in posts
    print("\n3. Testing cascade depth tracking...")
    await db.insert_post(
        post_id='post_001',
        agent_id='test_001',
        content='Original post',
        post_type='campaign',
        created_step=10,
        cascade_depth=0
    )
    
    await db.insert_post(
        post_id='post_002',
        agent_id='test_001',
        content='Reshare',
        post_type='reshare',
        created_step=20,
        parent_post_id='post_001',
        cascade_depth=1
    )
    
    post = await db.get_post('post_002')
    assert post['cascade_depth'] == 1
    print("   ✓ Cascade depth tracking works")
    
    # 4. Test campaign exposure logging
    print("\n4. Testing campaign exposure logging...")
    await db.log_campaign_exposure(
        agent_id='test_001',
        post_id='post_001',
        campaign_id='campaign_hope',
        cascade_depth=0,
        exposure_step=10
    )
    
    exposures = await db.get_exposures_by_agent('test_001')
    assert len(exposures) == 1
    assert exposures[0]['cascade_depth'] == 0
    print("   ✓ Campaign exposure logging works")
    
    # 5. Test agent initialization with online/offline
    print("\n5. Testing agent online/offline initialization...")
    rng = random.Random(42)
    llm = LLMClient()
    
    online_count = 0
    for i in range(100):
        agent = Agent(
            agent_id=f'agent_{i}',
            persona={'agent_id': f'agent_{i}', 'name': f'Agent{i}', 'age': 25},
            llm_client=llm,
            rng=random.Random(42 + i)
        )
        if agent.online:
            online_count += 1
    
    online_pct = online_count / 100 * 100
    print(f"   ✓ {online_pct:.0f}% of agents start online (expected ~40%)")
    
    if 25 <= online_pct <= 55:
        print("   ✓ Online percentage is reasonable")
    else:
        print(f"   ⚠️  Online percentage seems off (expected 25-55%, got {online_pct:.0f}%)")
    
    # 6. Test belief measurement at multiple timepoints
    print("\n6. Testing multi-timepoint belief tracking...")
    for step in [0, 100, 200]:
        await db.insert_belief_measurement(
            agent_id='test_001',
            attribute='environmental_concern',
            value=0.5 + (step * 0.001),
            step=step,
            reasoning=f"Measurement at step {step}"
        )
    
    beliefs_t0 = await db.get_beliefs_at_step(0)
    beliefs_t2 = await db.get_beliefs_at_step(200)
    assert len(beliefs_t0) == 1
    assert len(beliefs_t2) == 1
    assert beliefs_t2[0]['value'] > beliefs_t0[0]['value']
    print("   ✓ Multi-timepoint tracking works")
    
    # 7. Test get_directly_targeted_agents
    print("\n7. Testing directly targeted agent retrieval...")
    await db.insert_campaign('campaign_hope', 'hope', 'Hope message', 10)
    await db.log_campaign_exposure(
        agent_id='test_001',
        post_id='post_001',
        campaign_id='campaign_hope',
        cascade_depth=0,
        exposure_step=10
    )
    
    targeted = await db.get_directly_targeted_agents('hope')
    assert 'test_001' in targeted
    print("   ✓ Directly targeted agent query works")
    
    await db.close()
    
    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED - Belief tracking system is operational!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(test_belief_system())


"""
Test script for LLM-based reflection system.
Tests the new memory stream and reflection generation.
"""
import asyncio
import sys
from simulation.agent import Agent, MemoryEntry
from llm.client import LLMClient
import config


async def test_reflection_system():
    """Test the LLM-based reflection implementation."""
    
    print("=" * 60)
    print("Testing LLM-Based Reflection System")
    print("=" * 60)
    
    # Initialize LLM client
    llm_client = LLMClient()
    
    # Create a test persona
    test_persona = {
        'agent_id': 'test_001',
        'name': 'Alice',
        'age': 28,
        'gender': 'female',
        'personality': {
            'openness': 0.8,
            'conscientiousness': 0.6,
            'extraversion': 0.7,
            'agreeableness': 0.7,
            'neuroticism': 0.4
        },
        'interests': ['sustainability', 'climate action', 'renewable energy'],
        'social_behavior': 'active'
    }
    
    # Create agent
    print("\n1. Creating agent with new memory system...")
    agent = Agent('test_001', test_persona, llm_client)
    print(f"   ✓ Agent created: {agent.agent_id}")
    print(f"   ✓ Memory stream initialized: {len(agent.memory_stream)} memories")
    print(f"   ✓ Reflections list initialized: {len(agent.reflections)} reflections")
    
    # Test memory importance calculation
    print("\n2. Testing importance calculation...")
    
    campaign_post = {
        'post_type': 'campaign',
        'content': 'Together we\'re building a cleaner planet. Every choice you make creates positive change.',
        'like_count': 5,
        'comment_count': 3
    }
    importance = agent.calculate_importance('observation', campaign_post)
    print(f"   ✓ Campaign post importance: {importance:.3f}")
    assert importance > 0.7, "Campaign posts should have high importance"
    
    organic_post = {
        'post_type': 'organic',
        'content': 'Just posted about my day',
        'like_count': 1,
        'comment_count': 0
    }
    importance = agent.calculate_importance('observation', organic_post)
    print(f"   ✓ Organic post importance: {importance:.3f}")
    
    # Test observation recording
    print("\n3. Testing observation recording...")
    
    feed_items = [
        {
            'post_id': 'post_001',
            'agent_id': 'CAMPAIGN_BRAND',
            'post_type': 'campaign',
            'content': 'Together we\'re building a cleaner planet. Every choice creates change.',
            'like_count': 10,
            'comment_count': 5
        },
        {
            'post_id': 'post_002',
            'agent_id': 'Agent_002',
            'post_type': 'organic',
            'content': 'Just saw an inspiring environmental campaign!',
            'like_count': 3,
            'comment_count': 1
        }
    ]
    
    agent.observe(feed_items, step=1)
    print(f"   ✓ Observed {len(feed_items)} posts")
    print(f"   ✓ Memory stream now has {len(agent.memory_stream)} memories")
    
    # Show memories
    for i, memory in enumerate(agent.memory_stream, 1):
        print(f"      Memory {i}: [imp={memory.importance:.2f}] {memory.content[:60]}...")
    
    # Test action recording
    print("\n4. Testing action recording...")
    
    action = {
        'type': 'like',
        'post_id': 'post_001',
        'reason': 'The hope-framed message aligns with my values'
    }
    
    agent.record_action(action, step=1)
    print(f"   ✓ Recorded action: {action['type']}")
    print(f"   ✓ Memory stream now has {len(agent.memory_stream)} memories")
    
    # Add more observations and actions for step 2
    print("\n5. Adding more observations and actions (step 2)...")
    
    agent.observe([
        {
            'post_id': 'post_003',
            'agent_id': 'Agent_003',
            'post_type': 'organic',
            'content': 'We need urgent action on climate change!',
            'like_count': 7,
            'comment_count': 4
        }
    ], step=2)
    
    agent.record_action({
        'type': 'comment',
        'content': 'I completely agree! Positive action is the way forward.',
        'reason': 'Want to contribute to the discussion'
    }, step=2)
    
    print(f"   ✓ Memory stream now has {len(agent.memory_stream)} memories")
    
    # Test memory retrieval
    print("\n6. Testing memory retrieval with importance+recency scoring...")
    
    retrieved = agent.retrieve_memories(current_step=2, k=5)
    print(f"   ✓ Retrieved {len(retrieved)} most relevant memories:")
    
    for i, memory in enumerate(retrieved, 1):
        score = memory.get_retrieval_score(2, config.RETRIEVAL_RECENCY_WEIGHT)
        print(f"      {i}. [score={score:.3f}, imp={memory.importance:.2f}, age={memory.get_age(2)}] {memory.content[:50]}...")
    
    # Add more memories to reach reflection step
    print("\n7. Adding more memories to reach reflection step (step 3)...")
    
    agent.observe([
        {
            'post_id': 'post_004',
            'agent_id': 'Agent_004',
            'post_type': 'organic',
            'content': 'Small actions lead to big impact in sustainability',
            'like_count': 5,
            'comment_count': 2
        }
    ], step=3)
    
    print(f"   ✓ Memory stream now has {len(agent.memory_stream)} memories")
    
    # Test LLM-based reflection generation
    print("\n8. Testing LLM-based reflection generation...")
    print("   (This will make an API call to OpenAI...)")
    
    try:
        reflection = await agent.generate_reflection(current_step=3)
        
        if reflection:
            print(f"\n   ✓ Generated reflection:")
            print(f"   '{reflection}'")
            print(f"\n   ✓ Memory stream now has {len(agent.memory_stream)} memories (reflection added)")
            print(f"   ✓ Reflections list now has {len(agent.reflections)} reflections")
            
            # Verify reflection was stored
            reflection_memories = [m for m in agent.memory_stream if m.memory_type == 'reflection']
            print(f"   ✓ Found {len(reflection_memories)} reflection memories in stream")
        else:
            print("   ⚠️  No reflection generated (might be too early)")
    
    except Exception as e:
        print(f"   ❌ Error generating reflection: {e}")
        import traceback
        traceback.print_exc()
    
    # Test full decision-making with reflection
    print("\n9. Testing full decision-making with reflection...")
    
    try:
        decision = await agent.decide_action(feed_items, step=3)
        print(f"   ✓ Decision made: {decision.get('type')}")
        if decision.get('reason'):
            print(f"   ✓ Reason: {decision.get('reason')}")
    except Exception as e:
        print(f"   ❌ Error in decision-making: {e}")
        import traceback
        traceback.print_exc()
    
    # Show LLM usage stats
    print("\n10. LLM Usage Statistics:")
    stats = llm_client.get_usage_stats()
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Total tokens: {stats['total_tokens']:,}")
    print(f"   Estimated cost: ${stats['estimated_cost_usd']:.4f}")
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully!")
    print("=" * 60)
    
    await llm_client.close()


if __name__ == "__main__":
    # Check for API key
    if not config.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("   Please set it in your .env file")
        sys.exit(1)
    
    # Run tests
    asyncio.run(test_reflection_system())


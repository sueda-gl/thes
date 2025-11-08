"""
Generate V2 Personas: Lower Baseline + Rich Biographical Narratives

Combines:
1. Lower environmental concern baseline (0.3-0.65 instead of 0.59-0.89)
2. Rich personal backstories (family, politics, life events, conspiracies)
3. Numeric Big Five traits (for consistency)

Result: Realistic, diverse agents who sound like real people on social media
"""
import json
import random
import numpy as np
from typing import List, Dict, Any
import os
import sys

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personas.generator import (
    load_distributions,
    weighted_choice,
    generate_age,
    generate_personality_trait,
    select_interests
)
from personas.biographical_templates import (
    FAMILY_SITUATIONS, PETS, JOBS, POLITICAL_LEANINGS,
    CONSPIRACY_BELIEFS, RECENT_EVENTS, ENVIRONMENTAL_STANCES,
    SOCIAL_MEDIA_STYLES, generate_rich_backstory
)


def generate_v2_persona(agent_id: str, distributions: Dict, rng: random.Random) -> Dict[str, Any]:
    """Generate V2 persona with lower baseline and rich backstory."""
    
    # Demographics
    age = generate_age(distributions, rng)
    gender = weighted_choice(distributions['gender_distribution'], rng)
    location = weighted_choice(distributions['location_distribution'], rng)
    income = weighted_choice(distributions['income_distribution'], rng)
    
    # Personality traits (Big Five)
    traits = distributions['personality_traits']
    openness = generate_personality_trait(traits['openness'], rng)
    conscientiousness = generate_personality_trait(traits['conscientiousness'], rng)
    extraversion = generate_personality_trait(traits['extraversion'], rng)
    agreeableness = generate_personality_trait(traits['agreeableness'], rng)
    neuroticism = generate_personality_trait(traits['neuroticism'], rng)
    
    # Interests
    interests = select_interests(distributions, rng)
    
    # Social behavior
    social_behavior = weighted_choice(distributions['social_behavior'], rng)
    
    # Name
    name = rng.choice(distributions['names']['first_names'])
    
    # Environmental concern - LOWER BASELINE
    base_concern = 0.3  # Lower (was 0.5)
    age_factor = (65 - age) / 65 * 0.15  # Reduced (was 0.2)
    openness_factor = openness * 0.2      # Reduced (was 0.3)
    env_concern = base_concern + age_factor + openness_factor
    env_concern = max(0.1, min(0.75, env_concern))  # Cap at 0.75
    
    # Brand trust
    base_trust = 0.5
    agree_factor = agreeableness * 0.3
    neuro_factor = -neuroticism * 0.2
    brand_trust = base_trust + agree_factor + neuro_factor
    brand_trust = max(0.1, min(0.9, brand_trust))
    
    # Activity
    activity_base_prob = 0.5
    activity_base_prob += (extraversion - 0.5) * 0.4
    activity_base_prob += (conscientiousness - 0.5) * 0.2
    activity_base_prob -= (neuroticism - 0.5) * 0.2
    activity_base_prob = max(0.1, min(0.95, activity_base_prob))
    
    # Preferred activity window
    if conscientiousness > 0.7:
        if extraversion > 0.6:
            preferred_window = [8, 9, 10, 18, 19, 20]
        else:
            preferred_window = [9, 10, 11, 14, 15, 16]
    else:
        window_start = rng.randint(6, 20)
        preferred_window = [(window_start + i) % 24 for i in range(6)]
    
    # Emotion and efficacy sensitivity
    emotion_sensitivity = 0.5
    emotion_sensitivity += (neuroticism - 0.5) * 0.5
    emotion_sensitivity += (extraversion - 0.5) * 0.3
    emotion_sensitivity = max(0.1, min(0.9, emotion_sensitivity))
    
    efficacy_sensitivity = 0.5
    efficacy_sensitivity += (conscientiousness - 0.5) * 0.4
    efficacy_sensitivity += (openness - 0.5) * 0.3
    efficacy_sensitivity = max(0.1, min(0.9, efficacy_sensitivity))
    
    # NEW: Generate rich backstory
    backstory = generate_rich_backstory(
        env_concern=env_concern,
        personality={'openness': openness, 'neuroticism': neuroticism, 
                    'extraversion': extraversion, 'agreeableness': agreeableness,
                    'conscientiousness': conscientiousness},
        interests=interests,
        age=age,
        rng=rng
    )
    
    return {
        'agent_id': agent_id,
        'name': name,
        'age': age,
        'gender': gender,
        'location': location,
        'income': income,
        'personality': {
            'openness': openness,
            'conscientiousness': conscientiousness,
            'extraversion': extraversion,
            'agreeableness': agreeableness,
            'neuroticism': neuroticism
        },
        'interests': interests,
        'social_behavior': social_behavior,
        'environmental_concern': round(env_concern, 2),
        'brand_trust': round(brand_trust, 2),
        'activity_base_prob': round(activity_base_prob, 3),
        'preferred_activity_window': preferred_window,
        'emotion_sensitivity': round(emotion_sensitivity, 2),
        'efficacy_sensitivity': round(efficacy_sensitivity, 2),
        'backstory': backstory  # NEW: Rich personal narrative
    }


if __name__ == '__main__':
    """Generate 200 V2 personas."""
    
    print("=" * 80)
    print("GENERATING 200 V2 PERSONAS")
    print("Lower Baseline + Rich Biographical Narratives")
    print("=" * 80)
    print()
    
    # Load distributions
    dist_path = os.path.join(os.path.dirname(__file__), 'distributions.json')
    with open(dist_path, 'r') as f:
        distributions = json.load(f)
    
    # Generate
    rng = random.Random(42)
    np.random.seed(42)
    
    personas = []
    for i in range(200):
        agent_id = f"Agent_{i:03d}"
        persona = generate_v2_persona(agent_id, distributions, rng)
        personas.append(persona)
    
    # Statistics
    env_concerns = [p['environmental_concern'] for p in personas]
    
    print("Generated 200 personas with rich backstories")
    print()
    print("Environmental Concern Distribution:")
    print(f"  Min: {min(env_concerns):.2f}")
    print(f"  Max: {max(env_concerns):.2f}")
    print(f"  Mean: {np.mean(env_concerns):.2f}")
    print(f"  SD: {np.std(env_concerns):.2f}")
    print(f"  Range: {max(env_concerns) - min(env_concerns):.2f}")
    print()
    
    print("Sample Backstories:")
    print("-" * 80)
    for persona in personas[:5]:
        print(f"\n{persona['agent_id']}: {persona['name']}, env_concern={persona['environmental_concern']}")
        print(f"  {persona['backstory']}")
    
    # Save
    output_path = os.path.join(os.path.dirname(__file__), 'personas_v2.json')
    with open(output_path, 'w') as f:
        json.dump(personas, f, indent=2)
    
    print(f"\n✓ Saved 200 V2 personas to: {output_path}")
    print()
    print("Next steps:")
    print("  1. Update prompts.py to include backstory in decision prompts")
    print("  2. Update engine.py to use LLM for organic posts")
    print("  3. Update run_thesis_experiment_v2.py to load personas_v2.json")


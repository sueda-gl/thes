"""
Generate V2 Personas: REALISTIC Variance with Wide Range

Creates highly diverse population with:
- Environmental concern: 0.1-0.75 (mean ~0.42)
- Higher personality variance
- More extreme trait combinations
- Rich biographical narratives

Reflects real social media: mix of activists, skeptics, apolitical, conspiracy theorists
"""
import json
import random
import numpy as np
from typing import List, Dict, Any
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personas.generator import (
    load_distributions,
    weighted_choice,
    generate_age,
    select_interests
)
from personas.biographical_templates import (
    FAMILY_SITUATIONS, PETS, JOBS, POLITICAL_LEANINGS,
    CONSPIRACY_BELIEFS, RECENT_EVENTS, ENVIRONMENTAL_STANCES,
    SOCIAL_MEDIA_STYLES, generate_rich_backstory
)


def generate_personality_trait_wider(mean: float, std: float, rng: random.Random) -> float:
    """Generate personality trait with WIDER variance than original."""
    # Increase std from 0.15 to 0.25 for more extreme personalities
    value = rng.gauss(mean, 0.25)  # Wider (was 0.15 in original)
    return max(0.05, min(0.95, value))  # Allow more extreme values


def generate_v2_realistic_persona(agent_id: str, distributions: Dict, rng: random.Random) -> Dict[str, Any]:
    """Generate highly diverse V2 persona with wide variance."""
    
    # Demographics
    age = rng.randint(18, 75)  # Wider age range
    gender = weighted_choice(distributions['gender_distribution'], rng)
    location = weighted_choice(distributions['location_distribution'], rng)
    income = weighted_choice(distributions['income_distribution'], rng)
    
    # Personality traits with WIDER variance
    openness = generate_personality_trait_wider(0.5, 0.25, rng)
    conscientiousness = generate_personality_trait_wider(0.5, 0.25, rng)
    extraversion = generate_personality_trait_wider(0.5, 0.25, rng)
    agreeableness = generate_personality_trait_wider(0.5, 0.25, rng)
    neuroticism = generate_personality_trait_wider(0.5, 0.25, rng)
    
    # Interests
    interests = select_interests(distributions, rng)
    
    # Social behavior
    social_behavior = weighted_choice(distributions['social_behavior'], rng)
    
    # Name
    name = rng.choice(distributions['names']['first_names'])
    
    # Environmental concern - WIDE RANGE (0.1-0.75)
    # Use more randomization, less deterministic formula
    base_concern = rng.uniform(0.1, 0.5)  # Random base
    age_factor = (65 - age) / 65 * rng.uniform(0, 0.2)  # Variable influence
    openness_factor = openness * rng.uniform(0, 0.25)  # Variable influence
    
    env_concern = base_concern + age_factor + openness_factor
    
    # Add noise for even more variance
    noise = rng.gauss(0, 0.08)  # Random perturbation
    env_concern = env_concern + noise
    
    env_concern = max(0.1, min(0.75, env_concern))  # Wide range
    
    # Brand trust - also wider range
    base_trust = rng.uniform(0.2, 0.7)
    agree_factor = agreeableness * rng.uniform(-0.2, 0.3)
    neuro_factor = -neuroticism * rng.uniform(0, 0.2)
    brand_trust = base_trust + agree_factor + neuro_factor
    brand_trust = max(0.1, min(0.9, brand_trust))
    
    # Activity - wider variance
    activity_base_prob = rng.uniform(0.2, 0.8)  # More random
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
    
    # Emotion and efficacy sensitivity with more variance
    emotion_sensitivity = 0.5
    emotion_sensitivity += (neuroticism - 0.5) * rng.uniform(0.4, 0.6)
    emotion_sensitivity += (extraversion - 0.5) * rng.uniform(0.2, 0.4)
    emotion_sensitivity = max(0.1, min(0.9, emotion_sensitivity))
    
    efficacy_sensitivity = 0.5
    efficacy_sensitivity += (conscientiousness - 0.5) * rng.uniform(0.3, 0.5)
    efficacy_sensitivity += (openness - 0.5) * rng.uniform(0.2, 0.4)
    efficacy_sensitivity = max(0.1, min(0.9, efficacy_sensitivity))
    
    # Generate rich backstory
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
            'openness': round(openness, 2),
            'conscientiousness': round(conscientiousness, 2),
            'extraversion': round(extraversion, 2),
            'agreeableness': round(agreeableness, 2),
            'neuroticism': round(neuroticism, 2)
        },
        'interests': interests,
        'social_behavior': social_behavior,
        'environmental_concern': round(env_concern, 2),
        'brand_trust': round(brand_trust, 2),
        'activity_base_prob': round(activity_base_prob, 3),
        'preferred_activity_window': preferred_window,
        'emotion_sensitivity': round(emotion_sensitivity, 2),
        'efficacy_sensitivity': round(efficacy_sensitivity, 2),
        'backstory': backstory
    }


if __name__ == '__main__':
    """Generate 200 highly diverse V2 personas."""
    
    print("=" * 80)
    print("GENERATING 200 V2 PERSONAS - HIGH REALISM & VARIANCE")
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
        persona = generate_v2_realistic_persona(agent_id, distributions, rng)
        personas.append(persona)
    
    # Statistics
    env_concerns = [p['environmental_concern'] for p in personas]
    openness_vals = [p['personality']['openness'] for p in personas]
    neuroticism_vals = [p['personality']['neuroticism'] for p in personas]
    
    print("Generated 200 highly diverse personas")
    print()
    print("ENVIRONMENTAL CONCERN:")
    print(f"  Min: {min(env_concerns):.2f}")
    print(f"  Max: {max(env_concerns):.2f}")
    print(f"  Mean: {np.mean(env_concerns):.2f}")
    print(f"  SD: {np.std(env_concerns):.2f}")
    print(f"  Range: {max(env_concerns) - min(env_concerns):.2f}")
    print()
    print("PERSONALITY VARIANCE (Openness example):")
    print(f"  Min: {min(openness_vals):.2f}")
    print(f"  Max: {max(openness_vals):.2f}")
    print(f"  SD: {np.std(openness_vals):.2f}")
    print()
    print("PERSONALITY VARIANCE (Neuroticism example):")
    print(f"  Min: {min(neuroticism_vals):.2f}")
    print(f"  Max: {max(neuroticism_vals):.2f}")
    print(f"  SD: {np.std(neuroticism_vals):.2f}")
    print()
    
    # Show diversity
    print("Sample Diverse Personas:")
    print("-" * 80)
    
    # Get diverse sample (low, medium, high concern)
    sorted_personas = sorted(personas, key=lambda p: p['environmental_concern'])
    samples = [sorted_personas[0], sorted_personas[50], sorted_personas[100], 
               sorted_personas[150], sorted_personas[-1]]
    
    for persona in samples:
        print(f"\n{persona['agent_id']}: {persona['name']}, env={persona['environmental_concern']:.2f}")
        print(f"  Personality: O={persona['personality']['openness']:.2f}, "
              f"N={persona['personality']['neuroticism']:.2f}, "
              f"E={persona['personality']['extraversion']:.2f}")
        print(f"  {persona['backstory'][:150]}...")
    
    # Save
    output_path = os.path.join(os.path.dirname(__file__), 'personas_v2.json')
    with open(output_path, 'w') as f:
        json.dump(personas, f, indent=2)
    
    print(f"\n" + "=" * 80)
    print(f"✅ Saved 200 highly diverse personas to: {output_path}")
    print("=" * 80)
    print()
    print("V2 Improvements:")
    print("  ✅ Environmental concern: 0.1-0.75 (was 0.37-0.57)")
    print("  ✅ Mean: ~0.42 (was 0.74 in V1)")
    print("  ✅ Higher personality variance (SD ~0.25 vs 0.15)")
    print("  ✅ Rich biographical narratives")
    print("  ✅ Includes: politics, conspiracies, trauma, family drama")
    print()
    print("Ready for V2 experiment with realistic, diverse agents!")


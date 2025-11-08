"""
Generate 200 personas with LOWER environmental concern baseline.

Changes from original:
- Base concern: 0.3 (was 0.5)
- Age factor: 0.15× (was 0.2×)  
- Openness factor: 0.2× (was 0.3×)

Result: env_concern ∈ [0.3, 0.65] instead of [0.59, 0.89]
This creates more room for upward movement (avoids ceiling effect)
"""
import json
import random
import numpy as np
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personas.generator import (
    load_distributions, 
    weighted_choice, 
    generate_age,
    generate_personality_trait,
    select_interests
)


def generate_persona_lower_baseline(agent_id: str, distributions: Dict, rng: random.Random) -> Dict[str, Any]:
    """Generate persona with LOWER environmental concern baseline."""
    
    # Demographics (same as original)
    age = generate_age(distributions, rng)
    gender = weighted_choice(distributions['gender_distribution'], rng)
    location = weighted_choice(distributions['location_distribution'], rng)
    income = weighted_choice(distributions['income_distribution'], rng)
    
    # Personality traits (same as original)
    traits = distributions['personality_traits']
    openness = generate_personality_trait(traits['openness'], rng)
    conscientiousness = generate_personality_trait(traits['conscientiousness'], rng)
    extraversion = generate_personality_trait(traits['extraversion'], rng)
    agreeableness = generate_personality_trait(traits['agreeableness'], rng)
    neuroticism = generate_personality_trait(traits['neuroticism'], rng)
    
    # Interests (same as original)
    interests = select_interests(distributions, rng)
    
    # Social behavior (same as original)
    social_behavior = weighted_choice(distributions['social_behavior'], rng)
    
    # Name (same as original)
    name = rng.choice(distributions['names']['first_names'])
    
    # Environmental concern - MODIFIED FOR LOWER BASELINE
    # Original: base=0.5, age×0.2, openness×0.3 → 0.5-1.0 → clipped to 0.95
    # Modified: base=0.3, age×0.15, openness×0.2 → 0.3-0.65
    base_concern = 0.3  # LOWER base (was 0.5)
    age_factor = (65 - age) / 65 * 0.15  # REDUCED influence (was 0.2)
    openness_factor = openness * 0.2      # REDUCED influence (was 0.3)
    env_concern = base_concern + age_factor + openness_factor
    env_concern = max(0.1, min(0.75, env_concern))  # Cap at 0.75 (was 0.95)
    
    # Brand trust (same as original)
    base_trust = 0.5
    agree_factor = agreeableness * 0.3
    neuro_factor = -neuroticism * 0.2
    brand_trust = base_trust + agree_factor + neuro_factor
    brand_trust = max(0.1, min(0.9, brand_trust))
    
    # Activity, emotion sensitivity, efficacy sensitivity (same as original)
    activity_base_prob = 0.5
    activity_base_prob += (extraversion - 0.5) * 0.4
    activity_base_prob += (conscientiousness - 0.5) * 0.2
    activity_base_prob -= (neuroticism - 0.5) * 0.2
    activity_base_prob = max(0.1, min(0.95, activity_base_prob))
    
    if conscientiousness > 0.7:
        if extraversion > 0.6:
            preferred_window = [8, 9, 10, 18, 19, 20]
        else:
            preferred_window = [9, 10, 11, 14, 15, 16]
    else:
        window_start = rng.randint(6, 20)
        preferred_window = [(window_start + i) % 24 for i in range(6)]
    
    emotion_sensitivity = 0.5
    emotion_sensitivity += (neuroticism - 0.5) * 0.5
    emotion_sensitivity += (extraversion - 0.5) * 0.3
    emotion_sensitivity = max(0.1, min(0.9, emotion_sensitivity))
    
    efficacy_sensitivity = 0.5
    efficacy_sensitivity += (conscientiousness - 0.5) * 0.4
    efficacy_sensitivity += (openness - 0.5) * 0.3
    efficacy_sensitivity = max(0.1, min(0.9, efficacy_sensitivity))
    
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
        'efficacy_sensitivity': round(efficacy_sensitivity, 2)
    }


if __name__ == '__main__':
    """Generate and save 200 personas with lower environmental concern baseline."""
    
    print("=" * 80)
    print("GENERATING 200 PERSONAS - LOWER ENVIRONMENTAL CONCERN BASELINE")
    print("=" * 80)
    print()
    print("Changes from original:")
    print("  • Base concern: 0.3 (was 0.5)")
    print("  • Age factor: 0.15× (was 0.2×)")
    print("  • Openness factor: 0.2× (was 0.3×)")
    print("  • Expected range: 0.3-0.65 (was 0.59-0.89)")
    print("  • Expected mean: ~0.48 (was 0.74)")
    print()
    
    # Load distributions
    dist_path = os.path.join(os.path.dirname(__file__), 'distributions.json')
    with open(dist_path, 'r') as f:
        distributions = json.load(f)
    
    # Generate personas
    rng = random.Random(42)
    np.random.seed(42)
    
    personas = []
    for i in range(200):
        agent_id = f"Agent_{i:03d}"
        persona = generate_persona_lower_baseline(agent_id, distributions, rng)
        personas.append(persona)
    
    # Calculate statistics
    env_concerns = [p['environmental_concern'] for p in personas]
    
    print("Generated 200 personas")
    print()
    print("Environmental Concern Distribution:")
    print(f"  Min: {min(env_concerns):.2f}")
    print(f"  Max: {max(env_concerns):.2f}")
    print(f"  Mean: {np.mean(env_concerns):.2f}")
    print(f"  SD: {np.std(env_concerns):.2f}")
    print()
    
    # Save
    output_path = os.path.join(os.path.dirname(__file__), 'personas_lower_baseline.json')
    with open(output_path, 'w') as f:
        json.dump(personas, f, indent=2)
    
    print(f"✓ Saved to: {output_path}")
    print()
    print("To use for experiment:")
    print("  1. Backup current: mv personas/personas.json personas/personas_original.json")
    print("  2. Use new: cp personas/personas_lower_baseline.json personas/personas.json")
    print("  3. Or modify run script to load personas_lower_baseline.json directly")


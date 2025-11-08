"""
Generate V2 FINAL Personas: Beta Distribution + Rich Narratives

Uses Beta(α=2.5, β=3.75) for environmental concern:
- Mean: 0.40
- SD: ~0.19
- Range: 0.05-0.95 (naturally bounded)
- Right-skewed: More low-concern than high-concern (realistic)

Theoretically justified for bounded attitude variables.
"""
import json
import random
import numpy as np
from scipy.stats import beta as beta_dist
from typing import List, Dict, Any
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from personas.generator import (
    load_distributions,
    weighted_choice,
    select_interests
)
from personas.biographical_templates import generate_rich_backstory


def generate_personality_trait_wider(mean: float, std: float, rng: random.Random) -> float:
    """Generate personality trait with wider variance."""
    value = rng.gauss(mean, 0.25)  # SD=0.25 for more extreme personalities
    return max(0.05, min(0.95, value))


def generate_v2_final_persona(agent_id: str, distributions: Dict, rng: random.Random, np_rng) -> Dict[str, Any]:
    """Generate V2 FINAL persona with Beta-distributed environmental concern."""
    
    # Demographics
    age = rng.randint(18, 75)
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
    
    # Environmental concern - BETA DISTRIBUTION (THEORETICALLY JUSTIFIED)
    # Beta(α=2.5, β=3.75) produces:
    # - Mean = α/(α+β) = 2.5/6.25 = 0.40
    # - Right-skewed (more low-concern than high)
    # - Bounded [0,1] naturally
    # - Standard for modeling attitudes/proportions
    env_concern = beta_dist.rvs(a=2.5, b=3.75, random_state=np_rng)
    
    # Optional floor to exclude true zero (even skeptics acknowledge issues exist)
    env_concern = max(0.05, env_concern)
    
    # Brand trust - wider range with more variance
    base_trust = rng.uniform(0.2, 0.7)
    agree_factor = agreeableness * rng.uniform(-0.2, 0.3)
    neuro_factor = -neuroticism * rng.uniform(0, 0.2)
    brand_trust = base_trust + agree_factor + neuro_factor
    brand_trust = max(0.1, min(0.9, brand_trust))
    
    # Activity - wider variance
    activity_base_prob = rng.uniform(0.2, 0.8)
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
    """Generate 200 V2 FINAL personas with Beta distribution."""
    
    print("=" * 80)
    print("GENERATING 200 V2 FINAL PERSONAS")
    print("Beta(2.5, 3.75) + Rich Narratives + High Variance")
    print("=" * 80)
    print()
    
    # Load distributions
    dist_path = os.path.join(os.path.dirname(__file__), 'distributions.json')
    with open(dist_path, 'r') as f:
        distributions = json.load(f)
    
    # Generate with dual RNGs (Python random + numpy for scipy)
    rng = random.Random(42)
    np_rng = np.random.default_rng(42)
    
    personas = []
    for i in range(200):
        agent_id = f"Agent_{i:03d}"
        persona = generate_v2_final_persona(agent_id, distributions, rng, np_rng)
        personas.append(persona)
    
    # Statistics
    env_concerns = [p['environmental_concern'] for p in personas]
    openness_vals = [p['personality']['openness'] for p in personas]
    neuroticism_vals = [p['personality']['neuroticism'] for p in personas]
    
    print("Generated 200 FINAL V2 personas")
    print()
    print("ENVIRONMENTAL CONCERN (Beta(2.5, 3.75) with floor at 0.05):")
    print(f"  Min: {min(env_concerns):.2f}")
    print(f"  Max: {max(env_concerns):.2f}")
    print(f"  Mean: {np.mean(env_concerns):.2f}")
    print(f"  Median: {np.median(env_concerns):.2f}")
    print(f"  SD: {np.std(env_concerns):.2f}")
    print(f"  Range: {max(env_concerns) - min(env_concerns):.2f}")
    print()
    
    # Distribution breakdown
    bins = [(0.0, 0.2, "Very Low"), (0.2, 0.4, "Low"), (0.4, 0.6, "Moderate"), 
            (0.6, 0.8, "High"), (0.8, 1.0, "Very High")]
    
    print("Distribution by level:")
    for low, high, label in bins:
        count = len([x for x in env_concerns if low <= x < high])
        pct = count / len(env_concerns) * 100
        print(f"  {label:12s} [{low:.1f}-{high:.1f}): {count:3d} agents ({pct:5.1f}%)")
    
    print()
    print("PERSONALITY VARIANCE:")
    print(f"  Openness SD: {np.std(openness_vals):.2f}")
    print(f"  Neuroticism SD: {np.std(neuroticism_vals):.2f}")
    print()
    
    # Show diverse samples
    print("Sample Extreme Personas:")
    print("-" * 80)
    
    sorted_personas = sorted(personas, key=lambda p: p['environmental_concern'])
    samples = [sorted_personas[0], sorted_personas[50], sorted_personas[100], 
               sorted_personas[150], sorted_personas[-1]]
    
    for p in samples:
        print(f"\n{p['agent_id']}: env={p['environmental_concern']:.2f}")
        print(f"  {p['backstory'][:120]}...")
    
    # Save
    output_path = os.path.join(os.path.dirname(__file__), 'personas_v2_final.json')
    with open(output_path, 'w') as f:
        json.dump(personas, f, indent=2)
    
    print(f"\n" + "=" * 80)
    print(f"✅ Saved to: {output_path}")
    print("=" * 80)
    print()
    print("Theoretical Justification:")
    print("  • Beta(2.5, 3.75) is standard for bounded attitude variables")
    print("  • Produces realistic right-skewed distribution")
    print("  • Mean 0.40 allows detection of upward movement")
    print("  • Range 0.05-0.95 includes full spectrum (skeptics to activists)")
    print("  • Citable: Standard in survey research and ABM")
    print()
    print("Ready for final V2 experiment!")


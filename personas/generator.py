"""
Procedural persona generation for AI agents.
"""
import json
import random
import numpy as np
from typing import List, Dict, Any
import os


def load_distributions():
    """Load distribution configuration."""
    path = os.path.join(os.path.dirname(__file__), 'distributions.json')
    with open(path, 'r') as f:
        return json.load(f)


def weighted_choice(options: Dict[str, float], rng: random.Random) -> str:
    """Make a weighted random choice."""
    items = list(options.keys())
    weights = list(options.values())
    return rng.choices(items, weights=weights)[0]


def generate_age(distributions: Dict, rng: random.Random) -> int:
    """Generate age based on distribution."""
    age_ranges = distributions['age_distribution']['ranges']
    
    # Choose age range
    weights = [r['weight'] for r in age_ranges]
    chosen_range = rng.choices(age_ranges, weights=weights)[0]
    
    # Pick random age in range
    return rng.randint(chosen_range['min'], chosen_range['max'])


def generate_personality_trait(trait_config: Dict, rng: random.Random) -> float:
    """Generate a personality trait value using normal distribution."""
    value = rng.gauss(trait_config['mean'], trait_config['std'])
    # Clip to valid range
    value = max(trait_config['min'], min(trait_config['max'], value))
    return round(value, 2)


def select_interests(distributions: Dict, rng: random.Random, n_interests: int = 5) -> List[str]:
    """Select random interests from all categories."""
    all_interests = []
    for category, interests in distributions['interests'].items():
        all_interests.extend(interests)
    
    # Ensure environmental topics are well represented (at least 2)
    environmental = distributions['interests']['environmental']
    n_env = rng.randint(2, 3)
    selected_env = rng.sample(environmental, n_env)
    
    # Fill remaining with other interests
    other_interests = [i for i in all_interests if i not in environmental]
    n_other = n_interests - n_env
    selected_other = rng.sample(other_interests, min(n_other, len(other_interests)))
    
    return selected_env + selected_other


def generate_persona(agent_id: str, distributions: Dict, rng: random.Random) -> Dict[str, Any]:
    """Generate a complete persona for an agent."""
    
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
    
    # Environmental concern (influenced by openness and age)
    # Younger + higher openness = higher environmental concern
    base_concern = 0.5
    age_factor = (65 - age) / 65 * 0.2  # Younger = higher
    openness_factor = openness * 0.3
    env_concern = base_concern + age_factor + openness_factor
    env_concern = max(0.1, min(0.95, env_concern))
    
    # Brand trust (influenced by agreeableness and neuroticism)
    base_trust = 0.5
    agree_factor = agreeableness * 0.3
    neuro_factor = -neuroticism * 0.2  # Higher neuroticism = lower trust
    brand_trust = base_trust + agree_factor + neuro_factor
    brand_trust = max(0.1, min(0.9, brand_trust))
    
    # Activity level (trait-driven, replaces arbitrary categories)
    # Higher extraversion and conscientiousness, lower neuroticism = more active
    # Aligns with Park et al. 2023 agent routines
    activity_base_prob = 0.5  # baseline
    activity_base_prob += (extraversion - 0.5) * 0.4  # -0.2 to +0.2
    activity_base_prob += (conscientiousness - 0.5) * 0.2  # -0.1 to +0.1
    activity_base_prob -= (neuroticism - 0.5) * 0.2  # +0.1 to -0.1
    activity_base_prob = max(0.1, min(0.95, activity_base_prob))
    
    # Preferred activity window (when agent is most active during 24-step cycle)
    # Conscientiousness influences regularity, extraversion influences timing
    if conscientiousness > 0.7:
        # Highly conscientious = regular schedule
        if extraversion > 0.6:
            preferred_window = [8, 9, 10, 18, 19, 20]  # Morning and evening
        else:
            preferred_window = [9, 10, 11, 14, 15, 16]  # Daytime focused
    else:
        # Less conscientious = irregular
        window_start = rng.randint(6, 20)
        preferred_window = [(window_start + i) % 24 for i in range(6)]
    
    # Emotion sensitivity (how strongly they respond to emotional framing)
    # Higher neuroticism and extraversion = more emotionally responsive
    # Supports fear/hope framing moderation (Witte & Allen 2000)
    emotion_sensitivity = 0.5
    emotion_sensitivity += (neuroticism - 0.5) * 0.5  # -0.25 to +0.25
    emotion_sensitivity += (extraversion - 0.5) * 0.3  # -0.15 to +0.15
    emotion_sensitivity = max(0.1, min(0.9, emotion_sensitivity))
    
    # Efficacy sensitivity (how much they need clear actionable steps)
    # Higher conscientiousness and openness = more responsive to clear actions
    # Supports fear+efficacy theory (Tannenbaum et al. 2015)
    efficacy_sensitivity = 0.5
    efficacy_sensitivity += (conscientiousness - 0.5) * 0.4  # -0.2 to +0.2
    efficacy_sensitivity += (openness - 0.5) * 0.3  # -0.15 to +0.15
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
        'social_behavior': social_behavior,  # Kept for compatibility
        'environmental_concern': round(env_concern, 2),
        'brand_trust': round(brand_trust, 2),
        'activity_base_prob': round(activity_base_prob, 3),
        'preferred_activity_window': preferred_window,
        'emotion_sensitivity': round(emotion_sensitivity, 2),
        'efficacy_sensitivity': round(efficacy_sensitivity, 2)
    }


def generate_personas(n_agents: int = 100, seed: int = 42) -> List[Dict[str, Any]]:
    """Generate N personas with reproducible randomness."""
    rng = random.Random(seed)
    np.random.seed(seed)
    
    distributions = load_distributions()
    personas = []
    
    for i in range(n_agents):
        agent_id = f"Agent_{i:03d}"
        persona = generate_persona(agent_id, distributions, rng)
        personas.append(persona)
    
    return personas


def save_personas(personas: List[Dict[str, Any]], filepath: str = None):
    """Save personas to JSON file."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), 'personas.json')
    
    with open(filepath, 'w') as f:
        json.dump(personas, f, indent=2)
    
    print(f"Saved {len(personas)} personas to {filepath}")


def load_personas(filepath: str = None) -> List[Dict[str, Any]]:
    """Load personas from JSON file."""
    if filepath is None:
        filepath = os.path.join(os.path.dirname(__file__), 'personas.json')
    
    with open(filepath, 'r') as f:
        return json.load(f)


def get_persona_stats(personas: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get statistics about generated personas."""
    stats = {
        'total': len(personas),
        'age': {
            'mean': np.mean([p['age'] for p in personas]),
            'min': min(p['age'] for p in personas),
            'max': max(p['age'] for p in personas)
        },
        'gender': {},
        'social_behavior': {},
        'personality': {}
    }
    
    # Gender distribution
    for persona in personas:
        gender = persona['gender']
        stats['gender'][gender] = stats['gender'].get(gender, 0) + 1
    
    # Social behavior distribution
    for persona in personas:
        behavior = persona['social_behavior']
        stats['social_behavior'][behavior] = stats['social_behavior'].get(behavior, 0) + 1
    
    # Personality trait averages
    traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    for trait in traits:
        values = [p['personality'][trait] for p in personas]
        stats['personality'][trait] = {
            'mean': round(np.mean(values), 2),
            'std': round(np.std(values), 2)
        }
    
    return stats


if __name__ == '__main__':
    """Generate and save 100 personas."""
    print("Generating 100 AI agent personas...")
    personas = generate_personas(n_agents=100, seed=42)
    
    print("\nPersona Statistics:")
    stats = get_persona_stats(personas)
    print(json.dumps(stats, indent=2))
    
    print("\nSample Personas:")
    for i in [0, 25, 50, 75, 99]:
        p = personas[i]
        print(f"\n{p['agent_id']}: {p['name']}")
        print(f"  Age: {p['age']}, Gender: {p['gender']}, Location: {p['location']}")
        print(f"  Openness: {p['personality']['openness']}, Neuroticism: {p['personality']['neuroticism']}")
        print(f"  Behavior: {p['social_behavior']}")
        print(f"  Interests: {', '.join(p['interests'][:3])}")
    
    save_personas(personas)
    print("\n✓ Persona generation complete!")


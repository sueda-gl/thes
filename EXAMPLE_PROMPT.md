# Example LLM Prompt with Environmental Concern

## Agent Profile (from personas.json)
```json
{
  "name": "Alex",
  "age": 58,
  "gender": "male",
  "personality": {
    "openness": 0.5,
    "extraversion": 0.7,
    "neuroticism": 0.31
  },
  "interests": ["sustainability", "eco-friendly living", "fitness"],
  "environmental_concern": 0.67,
  "brand_trust": 0.63
}
```

## What LLM Now Sees (Complete Prompt)

```
You are Alex, a 58-year-old male.

Your personality:
- You have moderate openness to new ideas
- You have low emotional sensitivity  
- You are very social
- Your social media behavior is typically casual

Your interests include sustainability, eco-friendly living, fitness.

Your values and attitudes:
- You care about the environment and try to make sustainable choices
- You have moderate trust in brands and sponsored content

You enjoy sharing content that resonates with you and engaging with others' posts.

Your social media feed shows:

1. [Campaign Post]: "🔔 SPONSORED POST

Together we're building a cleaner planet. Every choice you make creates positive change. Join thousands making a difference. Small actions lead to big impact. The future is bright when we act together."
   Likes: 5 | Comments: 2

2. [Post by Agent_042]: "Thinking about sustainability today..."
   Likes: 1 | Comments: 0

3. [Post by Agent_091]: "Interesting perspective on eco-friendly living"
   Likes: 3 | Comments: 1

What would you like to do?
A) Like one of these posts (specify which number)
B) Reshare one of these posts (specify which)  
C) Comment on one of these posts (specify which and write your comment)
D) Do nothing

Respond with your choice and briefly explain why.
```

---

## How This Helps Your Experiment

### **Agent with HIGH environmental concern (0.9):**
```
Your values and attitudes:
- You are deeply committed to environmental protection and climate action
```
**Expected:** Likely to engage with BOTH Hope and Fear campaigns (cares about climate)

### **Agent with LOW environmental concern (0.2):**
```
Your values and attitudes:
- You're somewhat skeptical about environmental activism and climate concerns
```
**Expected:** Likely to IGNORE both campaigns (doesn't care about climate)

### **Agent with MODERATE concern (0.6):**
```
Your values and attitudes:
- You care about the environment and try to make sustainable choices
```
**Expected:** Selective engagement - might prefer Hope (aligns with values) over Fear (stressful)

---

## This Makes Your Results Interpretable

**Without env_concern:** Hope vs Fear effect size = small (only framing)

**With env_concern:** 
- Main effect: Framing (Hope vs Fear)
- Moderator: Pre-existing concern
- Interaction: Does Hope work better for concerned agents?

**More realistic, richer analysis, defensible design.**

---

## Updated Experiment Now Testable

Your simulation can now study:
1. **Direct framing effect:** Hope vs Fear (primary question)
2. **Concern moderator:** High vs low environmental_concern responses
3. **Interaction:** Does framing effectiveness depend on prior attitudes?

This is publication-quality experimental design for a bachelor's thesis.


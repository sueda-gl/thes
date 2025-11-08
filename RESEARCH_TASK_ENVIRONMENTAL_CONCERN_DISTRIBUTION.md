# Research Task: Justify Environmental Concern Distribution

## Context

I'm writing a bachelor's thesis using agent-based modeling (ABM) to simulate social media users' responses to environmental campaigns (Hope vs. Fear framing). Each of 200 agents has an `environmental_concern` parameter (continuous, 0-1 scale) that represents their baseline attitude toward environmental issues and climate change.

## Current Problem

I need a **defensible, non-arbitrary** way to initialize this parameter that:
1. Has **empirical or theoretical grounding** (citable sources)
2. Produces appropriate **mean (~0.35-0.45)** and **variance (SD ~0.15-0.20)**
3. Includes **wide range** (skeptics to activists, ideally 0.05-0.80)
4. Is **standard practice** in ABM or survey research

Currently using ad-hoc formulas that reviewers will question.

## Requirements

### Statistical Properties Needed
- **Mean:** 0.35-0.45 (moderate average concern)
- **Range:** Should include skeptics (0.05-0.15) to activists (0.70-0.85)
- **Variance:** SD ~0.15-0.20 (substantial individual differences)
- **Distribution shape:** Slightly right-skewed preferred (more low-concern than high-concern)

### Why These Properties?
- **Low mean (0.35-0.45):** Avoids ceiling effect - campaigns can increase concern
- **Wide range:** Enables testing personality × campaign interactions
- **High variance:** Reflects real population heterogeneity

### Academic Level
Bachelor's thesis in computational social science. Needs to be:
- Defensible to reviewers
- Citable (peer-reviewed sources preferred)
- Not overly complex (simple > complicated)

## Your Task

Find and justify the BEST approach for initializing environmental_concern. Consider:

### Option A: Named Probability Distribution
Examples: Beta(α, β), Truncated Normal(μ, σ), etc.
- ✅ Theoretically standard
- ✅ Easily citable
- Specify: Distribution name, parameters, justification

### Option B: Empirical Survey Data
Use actual population survey distributions (Pew, Gallup, Eurobarometer, etc.)
- ✅ Empirically grounded
- ✅ High external validity
- Specify: Source, year, sample, distribution

### Option C: Literature-Based
Follow distributions used in published ABM studies
- ✅ Follows precedent
- ✅ Directly citable
- Specify: Paper, distribution used, context

## Deliverables

Please provide:

### 1. Recommended Distribution
- **Name:** (e.g., "Beta(α=2, β=3)")
- **Parameters:** Specific values
- **Resulting properties:** Mean, SD, range
- **Code snippet:** How to implement in Python

### 2. Theoretical/Empirical Justification
- **Why this distribution?** (1-2 paragraphs)
- **What does it represent?** (real population? standard practice?)
- **Why is it defensible?** (not arbitrary)

### 3. Citations (Peer-Reviewed)
Provide 2-3 citations supporting this choice:
- Survey papers showing real distributions
- ABM papers using similar approaches
- Statistical methods papers on attitude measurement

### 4. Alternative Options
Briefly mention 1-2 alternatives with pros/cons

### 5. Implementation Code
Python code snippet ready to drop into persona generator

## Constraints

- Must be defendable at bachelor's thesis level
- Prefer simple over complex (Beta distribution > mixture models)
- Prefer published precedent over novel approaches
- Must produce mean ~0.35-0.45 and SD ~0.15-0.20
- Should include some extreme values (0.05-0.15 skeptics, 0.70-0.85 activists)

## Example Output Format

```markdown
## Recommendation: Beta(α, β) Distribution

### Choice: Beta(α=2.5, β=3.5)

**Resulting Properties:**
- Mean: 0.42
- Mode: 0.33
- SD: 0.19
- Range: ~0.05-0.90 (95% within 0.15-0.75)

### Justification

[2 paragraphs explaining why Beta distributions are appropriate for 
bounded attitude variables, with citations]

### Implementation

```python
from scipy.stats import beta
env_concern = beta.rvs(a=2.5, b=3.5, random_state=seed)
```

### Citations

1. [Full citation for why Beta is appropriate]
2. [Survey data showing real distributions]
3. [ABM paper using similar approach]

### Alternatives Considered

- Truncated Normal: [brief pro/con]
- Survey resampling: [brief pro/con]
```

## Start Your Research

Focus on:
1. **Environmental attitude measurement literature** (psychology, survey research)
2. **Agent-based modeling best practices** (how do others initialize attitudes?)
3. **Statistical distributions for bounded variables** (Beta, truncated normal, etc.)

Find the approach that is **simple, standard, and citable** for a bachelor's thesis.


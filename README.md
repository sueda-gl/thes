# AI Social Media Simulation - Hope vs. Fear Campaign Effectiveness

A bachelor thesis project that uses AI agents to simulate social media dynamics and test the effectiveness of hope-based vs. fear-based environmental marketing campaigns.

## Overview

This simulation platform creates a virtual social media environment with 100 AI agents (powered by GPT-3.5) that have unique personalities, social connections, and behavioral patterns. The agents interact over 10 time steps, and we measure how different emotional framings in campaigns affect engagement, network reach, and virality.

### Research Question

**Which type of campaign messaging is more effective: hopeful/optimistic or pessimistic/fear-based?**

### Key Metrics

- **Total Engagement**: Likes, comments, and posts
- **Network Reach**: How far campaigns spread through social connections
- **Virality**: Secondary and tertiary exposure rates
- **Content Amplification**: How often agents create their own posts about campaigns
- **Discussion Depth**: Comment threads and conversation patterns
- **Temporal Dynamics**: Sustained engagement vs. rapid decay

## Installation

### Prerequisites

- Python 3.9+ (Python 3.10 or 3.11 recommended)
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Quick Start

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

This will install all required packages:
- Streamlit (Web UI)
- OpenAI (GPT-3.5 integration)
- Pandas, NumPy (Data processing)
- SciPy, Scikit-learn, Statsmodels (Statistical analysis)
- Plotly, Matplotlib, Seaborn (Visualizations)
- aiohttp, aiosqlite (Async operations)

4. **Configure your OpenAI API key**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

Edit the `.env` file:
```
OPENAI_API_KEY=sk-your-actual-api-key-here
```

5. **Run the simulation**:
```bash
streamlit run main.py
```

This will open your browser automatically at `http://localhost:8501`

## Usage

### Running the Simulation

The Streamlit interface provides an intuitive way to run simulations:

1. **Configure Parameters** (left sidebar):
   - Number of agents (50-100)
   - Simulation steps (5-15)
   - Campaign launch step (2-5)
   - LLM temperature (0.5-1.0)
   - Random seed (for reproducibility)

2. **Click "RUN SIMULATION"** button

3. **Monitor Progress** in the "Progress" tab:
   - Real-time step counter
   - Live engagement metrics
   - Simulation logs

4. **View Results** across multiple tabs:
   - **Engagement**: Total engagement, breakdown by type, statistical tests
   - **Network Reach**: Spread visualization, virality coefficients
   - **Temporal**: Engagement over time, decay patterns
   - **Personality**: How traits moderate responses
   - **Sample Content**: Example posts and conversations
   - **Export**: Download results as JSON/CSV

### Configuration Options

Key parameters you can adjust:

- **Number of agents** (50-100, default: 100)
  - More agents = more realistic but slower and more expensive

- **Simulation steps** (5-15, default: 10)
  - More steps = longer observation period but higher cost

- **Campaign launch step** (2-5, default: 3)
  - When to inject the campaigns (after warm-up)

- **LLM temperature** (0.5-1.0, default: 0.7)
  - Lower = more predictable, Higher = more creative/variable

- **Random seed** (any integer, default: 42)
  - Same seed = reproducible results
  - Different seed = different social graph and outcomes

## Architecture

### Project Structure

```
thesis_simulation/
├── main.py                      # Streamlit UI entry point
├── config.py                    # Central configuration
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── .env                         # API keys (not in git)
├── .gitignore                   # Git ignore rules
│
├── simulation/                  # Core simulation logic
│   ├── __init__.py
│   ├── engine.py               # Main orchestrator
│   ├── agent.py                # AI agent with LLM
│   └── platform.py             # Social media platform state
│
├── llm/                         # LLM integration
│   ├── __init__.py
│   ├── client.py               # Async OpenAI client
│   └── prompts.py              # Prompt templates & parsing
│
├── database/                    # Data persistence
│   ├── __init__.py
│   ├── schema.sql              # SQLite schema
│   └── db.py                   # Database operations
│
├── personas/                    # Agent generation
│   ├── __init__.py
│   ├── generator.py            # Persona creation
│   ├── social_graph.py         # Network builder
│   ├── distributions.json      # Population distributions
│   └── personas.json           # 100 pre-generated personas
│
├── analysis/                    # Metrics & statistics
│   ├── __init__.py
│   ├── metrics.py              # All metrics calculations
│   ├── threads.py              # Discussion analysis
│   └── cascade.py              # Network spread tracking
│
├── ui/                          # Streamlit components
│   ├── __init__.py
│   ├── components.py           # UI widgets
│   └── visualizations.py       # Charts and graphs
│
└── data/                        # Runtime data (gitignored)
    ├── simulation.db           # SQLite database
    └── results/                # Exported results
```

### How It Works

The simulation follows this flow:

**1. Initialization**
- Load 100 pre-generated personas (age, gender, Big Five traits, interests)
- Create Agent objects with LLM decision-making capability
- Build social graph (each agent follows 8-15 others, power-law distribution)
- Initialize SQLite database

**2. Warm-up Phase (Steps 1-2)**
- Agents observe empty feeds or minimal content
- Establish baseline interaction patterns
- No campaigns yet

**3. Campaign Injection (Step 3)**
- Shuffle agents randomly
- 50 agents → Hope campaign (optimistic environmental message)
- 50 agents → Fear campaign (pessimistic environmental message)
- Record direct exposures in database

**4. Simulation Loop (Steps 3-10)**

Each step:
- **Observation**: Build personalized feed for each agent (posts from followed agents)
- **Decision**: Agent uses LLM to decide action based on personality + feed content
  - Options: Like a post, Comment, Create post, Do nothing
- **Execution**: Record actions in database, update engagement counts
- **Cascade Tracking**: Detect secondary/tertiary exposures to campaigns

**5. Analysis**
- Calculate comprehensive metrics (engagement, reach, virality)
- Run statistical tests (chi-square, proportion tests, Fisher's exact)
- Generate visualizations
- Export results

### Campaign Messages

**Hope Campaign (Optimistic)**:
> "Together we're building a cleaner planet. Every choice you make creates positive change. Join thousands making a difference. Small actions lead to big impact. The future is bright when we act together."

**Fear Campaign (Pessimistic)**:
> "Time is running out. Environmental damage is accelerating. Without immediate action, consequences will be severe. Don't wait until it's too late. Act now before the window closes."

## Cost Estimates

### Per Simulation Run (100 agents, 10 steps)

**Token Usage**:
- ~200 tokens per agent decision (prompt + response)
- ~100 active agents per step (some are "lurkers")
- 10 steps × 100 agents × 200 tokens = ~200,000 tokens total

**Costs** (GPT-3.5-turbo pricing):
- Input tokens: ~100K × $0.0015/1K = $0.15
- Output tokens: ~100K × $0.002/1K = $0.20
- **Total per run: ~$0.35-0.45**

### Full Thesis Budget

- 5 simulation runs (different seeds): ~$2.00
- Testing and debugging: ~$1.00
- Development iterations: ~$2.00

**Total estimated cost: $5-6**

*Note: Costs may vary based on OpenAI pricing updates and actual token usage.*

## Results & Metrics

### What You'll Get

After running a simulation, you'll receive:

**Engagement Metrics**:
- Total likes, comments, posts by campaign
- Engagement rate (% of exposed agents who engaged)
- Engagement breakdown (% likes vs comments vs posts)

**Network Reach**:
- Direct exposure: 50 agents each (by design)
- Secondary reach: Agents who saw friends' posts about campaign
- Tertiary reach: Third-degree exposure
- Total unique agents reached
- Reach percentage (of entire network)

**Virality**:
- Virality coefficient (secondary / direct)
- Amplification rate (% who created posts)
- Cascade depth (how many levels it spread)

**Temporal Dynamics**:
- Engagement by step (timeline)
- Peak engagement vs sustained engagement
- Decay rate from peak

**Statistical Tests**:
- Chi-square test (engagement type distribution)
- Proportion z-test (reach comparison)
- Fisher's exact test (amplification rate)
- Personality moderation analysis

**Key Findings** (example):
- "Hope campaign reached 31% more agents than fear campaign"
- "Hope campaign was 75% more viral (higher secondary spread)"
- "Hope inspires 92% more content creation"
- "Fear triggers more debate, hope more sharing"

### Sample Results Visualization

The UI provides interactive charts:
- Bar charts comparing engagement
- Stacked bars showing reach breakdown
- Line charts for temporal patterns
- Gauge charts for virality
- Grouped bars for personality effects

## Database Schema

The simulation uses SQLite with these tables:

- **agents**: Agent ID, persona (JSON with demographics/traits)
- **posts**: All content (posts + comments), with parent_post_id for threading
- **follows**: Social graph (follower_id, followee_id)
- **interactions**: Likes (agent_id, post_id, step)
- **observations**: What each agent saw (agent_id, post_id, step)
- **campaigns**: Campaign metadata (ID, type, message, launch_step)
- **campaign_exposures**: Exposure tracking (agent, campaign, type: direct/secondary/tertiary, responded, action_type)
- **simulation_runs**: Run metadata (ID, config, status, timestamps)

## Troubleshooting

**"Module not found" errors**:
- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt`

**"OpenAI API key not found"**:
- Check that `.env` file exists in project root
- Verify `OPENAI_API_KEY=sk-...` is set correctly
- Don't use quotes around the key

**Simulation runs slowly**:
- Reduce number of agents (try 50 instead of 100)
- Reduce number of steps (try 5 instead of 10)
- This is normal - LLM calls take time

**Database locked errors**:
- Make sure only one simulation is running at a time
- Delete `data/simulation.db` and restart if needed

**Dependency installation fails on Python 3.13**:
- Use Python 3.10 or 3.11 instead (more compatible)
- Some scientific packages may not support 3.13 yet

## Academic Context

### Research Contributions

This thesis demonstrates:

1. **Methodological Innovation**: Using AI agents as research participants
   - More cost-effective than human surveys
   - Better control over confounding variables
   - Ability to observe network dynamics

2. **Network Effects Discovery**: How emotional framing affects information spread
   - Hope creates amplification loops
   - Fear creates discussion without virality

3. **Practical Marketing Insights**: Evidence-based guidance
   - When to use hope vs fear messaging
   - How personality moderates response
   - Temporal dynamics of campaign effectiveness

### Thesis Structure

Recommended thesis chapters:

1. **Introduction**: Research question, motivation
2. **Literature Review**: Campaign effectiveness, social media dynamics, AI simulation
3. **Methodology**: Agent design, simulation architecture, metrics
4. **Results**: Comprehensive findings with visualizations
5. **Discussion**: Interpretation, limitations, implications
6. **Conclusion**: Key takeaways, future work

## License

This is an academic project developed for a bachelor thesis. The code is provided as-is for educational and research purposes.

## Author

Bachelor Thesis Project  
2025

## Acknowledgments

This project was built as part of a bachelor thesis exploring social media marketing effectiveness using AI agent simulation methods. Special thanks to the open-source community for the amazing tools and libraries that made this possible.

---

**Questions or Issues?**

If you encounter any problems or have questions about the simulation, please check the troubleshooting section above or review the code comments for detailed implementation notes.


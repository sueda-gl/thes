"""
AI Social Media Simulation - Streamlit UI
Hope vs Fear Campaign Effectiveness Research
"""
import streamlit as st
import asyncio
import json
import pandas as pd
import numpy as np
from datetime import datetime
import config
from simulation.engine import SimulationEngine
from database.db import Database
from analysis.metrics import MetricsCalculator
from analysis.threads import ThreadAnalyzer
from analysis.cascade import CascadeAnalyzer
from ui.visualizations import (
    create_engagement_comparison_chart,
    create_reach_visualization,
    create_temporal_chart,
    create_personality_chart,
    create_virality_comparison
)
from ui.components import (
    display_key_findings,
    display_statistical_test,
    display_campaign_comparison_table
)


# Page config
st.set_page_config(
    page_title="AI Social Media Simulation",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Title
st.title("🧪 AI Social Media Simulation")
st.markdown("### Hope vs Fear: Campaign Effectiveness Research")
st.markdown("---")


# Sidebar Configuration
st.sidebar.header("⚙️ Configuration")

n_agents = st.sidebar.slider(
    "Number of Agents",
    min_value=20,
    max_value=100,
    value=config.NUM_AGENTS,
    step=10,
    help="100 recommended for thesis (20-50 for quick tests)"
)

n_steps = st.sidebar.slider(
    "Simulation Steps",
    min_value=4,
    max_value=15,
    value=config.SIMULATION_STEPS,
    step=1,
    help="10 recommended for thesis (4-7 for quick tests)"
)

campaign_step = st.sidebar.slider(
    "Campaign Launch Step",
    min_value=2,
    max_value=5,
    value=config.CAMPAIGN_LAUNCH_STEP,
    step=1,
    help="3 recommended (2 for quick tests with fewer steps)"
)

temperature = st.sidebar.slider(
    "LLM Temperature",
    min_value=0.5,
    max_value=1.0,
    value=config.LLM_TEMPERATURE,
    step=0.1,
    help="Controls agent behavior variability"
)

seed = st.sidebar.number_input(
    "Random Seed",
    min_value=1,
    max_value=999,
    value=config.RANDOM_SEED,
    help="For reproducibility"
)

st.sidebar.markdown("---")

# Cost estimate
estimated_cost = (n_agents * n_steps * 200) / 1000 * 0.0125  # Rough estimate
st.sidebar.info(f"""
**Estimated Cost:** ~${estimated_cost:.2f}  
**Time:** ~{n_steps * 0.5:.0f}-{n_steps * 1:.0f} minutes

💡 **Testing Tip:**  
Start with 20 agents, 4 steps for quick tests (~$0.10)
""")

st.sidebar.markdown("---")

# Run button
run_button = st.sidebar.button("🚀 RUN SIMULATION", type="primary", use_container_width=True)


# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📋 Setup",
    "⏳ Progress",
    "📊 Engagement",
    "🌐 Network Reach",
    "📈 Temporal",
    "🧬 Personality",
    "💬 Sample Content",
    "📥 Export"
])


# Tab 1: Setup
with tab1:
    st.header("Campaign Messages")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🌟 Hope Campaign (Optimistic)")
        st.info(config.CAMPAIGNS['hope']['message'])
    
    with col2:
        st.subheader("⚠️ Fear Campaign (Pessimistic)")
        st.warning(config.CAMPAIGNS['fear']['message'])
    
    st.markdown("---")
    
    st.header("Agent Demographics")
    st.markdown(f"**Total Agents:** {n_agents}")
    st.markdown(f"**Simulation Steps:** {n_steps}")
    st.markdown(f"**Campaign Launch:** Step {campaign_step}")
    
    st.info("""
    **How it works:**
    1. 100 AI agents with unique personalities are created
    2. They form a social network (following each other)
    3. Agents interact naturally for 2-3 steps (warm-up)
    4. At step 3, half see the Hope campaign, half see Fear campaign
    5. Agents can like, comment, or post about what they see
    6. We track how campaigns spread through the network
    7. Comprehensive metrics measure effectiveness
    """)


# Tab 2: Progress (populated during simulation)
with tab2:
    st.header("Simulation Progress")
    progress_placeholder = st.empty()
    metrics_placeholder = st.empty()
    log_placeholder = st.empty()


# Initialize session state
if 'simulation_run' not in st.session_state:
    st.session_state.simulation_run = False
if 'results' not in st.session_state:
    st.session_state.results = None


# Run simulation
if run_button and not st.session_state.simulation_run:
    st.session_state.simulation_run = True
    
    # Use a synchronous wrapper for the async simulation
    def run_simulation_sync():
        """Synchronous wrapper that properly handles async code."""
        import nest_asyncio
        
        # Allow nested event loops
        nest_asyncio.apply()
        
        async def run_simulation():
            # Initialize engine
            engine = SimulationEngine(
                seed=seed,
                n_steps=n_steps,
                n_agents=n_agents
            )
            
            # Progress callback
            def progress_callback(step, total, metrics):
                with progress_placeholder.container():
                    progress = step / total
                    st.progress(progress)
                    st.caption(f"Step {step}/{total}")
                
                with metrics_placeholder.container():
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Hope Posts", metrics.get('organic_posts', 0))
                    with col2:
                        st.metric("Fear Posts", metrics.get('organic_posts', 0))
            
            # Initialize
            await engine.initialize()
            
            # Run
            summary = await engine.run(progress_callback=progress_callback)
            
            # Calculate metrics
            db = engine.db
            calculator = MetricsCalculator(db)
            
            report = await calculator.generate_full_report()
            
            # Close
            await engine.close()
            
            return report
        
        # Run with nest_asyncio enabled
        return asyncio.run(run_simulation())
    
    # Verify API key first
    if not config.OPENAI_API_KEY or config.OPENAI_API_KEY == "your_openai_api_key_here":
        st.error("❌ OpenAI API key not configured! Please edit the .env file and add your API key.")
        st.code("OPENAI_API_KEY=sk-your-actual-key-here")
        st.session_state.simulation_run = False
    else:
        # Run simulation
        try:
            with st.spinner("Running simulation... This may take 10-20 minutes."):
                results = run_simulation_sync()
                st.session_state.results = results
                st.session_state.simulation_run = False
            
            st.success("✅ Simulation complete!")
            st.balloons()
        
        except Exception as e:
            st.error(f"❌ Error running simulation: {e}")
            st.session_state.simulation_run = False
            import traceback
            with st.expander("Show Full Error Details"):
                st.code(traceback.format_exc())


# Display results if available
if st.session_state.results:
    results = st.session_state.results
    comparison = results['campaign_comparison']
    stats_tests = results['statistical_tests']
    personality = results['personality_moderation']
    temporal = results['temporal_dynamics']
    findings = results['key_findings']
    
    # Tab 3: Engagement
    with tab3:
        st.header("Engagement Metrics")
        
        # Key findings
        display_key_findings(findings)
        
        st.markdown("---")
        
        # Comparison table
        st.subheader("Detailed Comparison")
        display_campaign_comparison_table(comparison)
        
        st.markdown("---")
        
        # Visualizations
        st.subheader("Engagement Breakdown")
        fig = create_engagement_comparison_chart(comparison)
        st.plotly_chart(fig, use_container_width=True)
        
        # Statistical test
        st.markdown("---")
        st.subheader("Statistical Significance")
        if 'chi_square' in stats_tests:
            display_statistical_test(stats_tests['chi_square'])
    
    # Tab 4: Network Reach
    with tab4:
        st.header("Network Reach & Virality")
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Hope Reach",
                f"{comparison['hope']['reach']['total_unique']} agents",
                f"{comparison['hope']['reach_pct']}%"
            )
        
        with col2:
            st.metric(
                "Fear Reach",
                f"{comparison['fear']['reach']['total_unique']} agents",
                f"{comparison['fear']['reach_pct']}%"
            )
        
        with col3:
            reach_diff = comparison['hope']['reach']['total_unique'] - comparison['fear']['reach']['total_unique']
            st.metric(
                "Difference",
                f"{reach_diff} agents",
                delta_color="normal"
            )
        
        st.markdown("---")
        
        # Reach visualization
        st.subheader("Reach Breakdown")
        fig = create_reach_visualization(comparison)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Virality
        st.subheader("Virality Coefficients")
        fig = create_virality_comparison(comparison)
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Hope Virality", comparison['hope']['virality'])
            st.caption("How many people each exposed person reached")
        
        with col2:
            st.metric("Fear Virality", comparison['fear']['virality'])
            st.caption("How many people each exposed person reached")
        
        # Statistical test
        st.markdown("---")
        st.subheader("Statistical Significance")
        if 'proportion_test' in stats_tests:
            display_statistical_test(stats_tests['proportion_test'])
    
    # Tab 5: Temporal
    with tab5:
        st.header("Engagement Over Time")
        
        # Timeline chart
        hope_timeline = temporal.get('hope', [])
        fear_timeline = temporal.get('fear', [])
        
        if hope_timeline and fear_timeline:
            fig = create_temporal_chart(hope_timeline, fear_timeline)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Decay analysis
            st.subheader("Engagement Dynamics")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if hope_timeline:
                    peak = max(item['total'] for item in hope_timeline)
                    final = hope_timeline[-1]['total'] if hope_timeline else 0
                    retention = (final / peak * 100) if peak > 0 else 0
                    
                    st.metric("Hope Peak Engagement", peak)
                    st.metric("Hope Retention", f"{retention:.1f}%")
            
            with col2:
                if fear_timeline:
                    peak = max(item['total'] for item in fear_timeline)
                    final = fear_timeline[-1]['total'] if fear_timeline else 0
                    retention = (final / peak * 100) if peak > 0 else 0
                    
                    st.metric("Fear Peak Engagement", peak)
                    st.metric("Fear Retention", f"{retention:.1f}%")
        else:
            st.info("No temporal data available yet. Run a simulation first.")
    
    # Tab 6: Personality
    with tab6:
        st.header("Personality Moderation")
        
        if personality:
            st.markdown("""
            This analysis shows how Big Five personality traits moderate response to campaigns.
            
            **Trait Interpretations:**
            - **Openness:** Curiosity, creativity, openness to new experiences
            - **Conscientiousness:** Organization, responsibility, self-discipline
            - **Extraversion:** Sociability, assertiveness, energy
            - **Agreeableness:** Compassion, cooperation, trust
            - **Neuroticism:** Emotional instability, anxiety, mood swings
            """)
            
            st.markdown("---")
            
            # Chart
            fig = create_personality_chart(personality)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # Interpretation
            st.subheader("Key Findings")
            
            trait_labels = {
                'openness': 'Openness',
                'conscientiousness': 'Conscientiousness',
                'extraversion': 'Extraversion',
                'agreeableness': 'Agreeableness',
                'neuroticism': 'Neuroticism'
            }
            
            for trait_key, trait_name in trait_labels.items():
                if trait_key in personality:
                    trait_data = personality[trait_key]
                    hope_diff = trait_data['hope_high_engagement'] - trait_data['hope_low_engagement']
                    fear_diff = trait_data['fear_high_engagement'] - trait_data['fear_low_engagement']
                    
                    st.markdown(f"**{trait_name}:**")
                    st.markdown(f"""
                    - Hope Campaign: High {trait_name.lower()} agents engage {hope_diff*100:.1f}% {'more' if hope_diff > 0 else 'less'} than low {trait_name.lower()} ({trait_data['hope_high_count']} high vs {trait_data['hope_low_count']} low agents)
                    - Fear Campaign: High {trait_name.lower()} agents engage {fear_diff*100:.1f}% {'more' if fear_diff > 0 else 'less'} than low {trait_name.lower()} ({trait_data['fear_high_count']} high vs {trait_data['fear_low_count']} low agents)
                    """)
        else:
            st.info("No personality data available yet. Run a simulation first.")
    
    # Tab 7: Sample Content
    with tab7:
        st.header("Sample Agent Posts & Conversations")
        
        # Helper function to fetch sample content
        async def fetch_sample_content():
            """Fetch sample posts and conversations from database."""
            db = Database()
            await db.connect()
            
            # Get different types of sample content
            campaign_posts = await db.get_campaign_posts(limit=4)
            posts_with_threads = await db.get_posts_with_threads(limit=5)
            high_engagement_posts = await db.get_sample_posts_with_engagement(limit=8)
            
            # Get agents for displaying names
            agents = await db.get_all_agents()
            agent_map = {a['agent_id']: a['persona'] for a in agents}
            
            # Get comments for threaded posts
            threads = {}
            for post in posts_with_threads:
                comments = await db.get_comments_for_post(post['post_id'])
                threads[post['post_id']] = comments
            
            await db.close()
            
            return {
                'campaign_posts': campaign_posts,
                'posts_with_threads': posts_with_threads,
                'high_engagement_posts': high_engagement_posts,
                'agent_map': agent_map,
                'threads': threads
            }
        
        # Helper function to display a post
        def display_post(post, agent_map, show_stats=True):
            """Display a single post."""
            agent_id = post['agent_id']
            persona = agent_map.get(agent_id, {})
            name = persona.get('name', agent_id)
            
            # Determine post type styling
            if post['post_type'] == 'campaign':
                # Extract campaign type from post_id (format: campaign_hope_agent123 or campaign_fear_agent123)
                campaign_type = 'hope' if 'hope' in post['post_id'] else 'fear'
                icon = "🌟" if campaign_type == 'hope' else "⚠️"
                border_color = "#4CAF50" if campaign_type == 'hope' else "#FF9800"
            else:
                icon = "💬"
                border_color = "#2196F3"
            
            # Post container with custom styling
            st.markdown(f"""
                <div style="border-left: 4px solid {border_color}; padding-left: 12px; margin-bottom: 16px;">
                    <p style="margin: 0; font-weight: bold; font-size: 14px;">{icon} {name}</p>
                    <p style="margin: 4px 0 0 0; color: #888; font-size: 12px;">Step {post['created_step']} • {post['post_type'].title()}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"_{post['content']}_")
            
            if show_stats and (post['like_count'] > 0 or post['comment_count'] > 0):
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.caption(f"👍 {post['like_count']} likes")
                with col2:
                    st.caption(f"💬 {post['comment_count']} comments")
        
        # Helper function to display a thread
        def display_thread(post, comments, agent_map):
            """Display a post with its comment thread."""
            display_post(post, agent_map, show_stats=True)
            
            if comments:
                st.markdown("**Replies:**")
                for comment in comments:
                    with st.container():
                        st.markdown("---")
                        persona = agent_map.get(comment['agent_id'], {})
                        name = persona.get('name', comment['agent_id'])
                        st.markdown(f"**↳ {name}** (Step {comment['created_step']})")
                        st.markdown(f"  _{comment['content']}_")
                        if comment['like_count'] > 0:
                            st.caption(f"  👍 {comment['like_count']} likes")
        
        # Fetch and display content
        try:
            import nest_asyncio
            nest_asyncio.apply()
            
            content = asyncio.run(fetch_sample_content())
            
            if not content['campaign_posts'] and not content['posts_with_threads']:
                st.info("No posts found. Run a simulation first to see sample content.")
            else:
                # Display campaign posts
                if content['campaign_posts']:
                    st.subheader("📢 Campaign Posts")
                    st.markdown("Sample of campaign posts shown to agents:")
                    
                    for post in content['campaign_posts']:
                        with st.container():
                            display_post(post, content['agent_map'])
                            st.markdown("---")
                
                # Display conversation threads
                if content['posts_with_threads']:
                    st.markdown("##")
                    st.subheader("💬 Popular Conversation Threads")
                    st.markdown("Posts with the most discussion:")
                    
                    for post in content['posts_with_threads']:
                        with st.expander(f"🧵 Thread by {content['agent_map'].get(post['agent_id'], {}).get('name', post['agent_id'])} - {post['comment_count']} replies"):
                            comments = content['threads'].get(post['post_id'], [])
                            display_thread(post, comments, content['agent_map'])
                
                # Display high engagement posts
                if content['high_engagement_posts']:
                    st.markdown("##")
                    st.subheader("🔥 High Engagement Posts")
                    st.markdown("Posts with the most likes and comments:")
                    
                    for post in content['high_engagement_posts'][:5]:
                        with st.container():
                            display_post(post, content['agent_map'])
                            st.markdown("---")
        
        except Exception as e:
            st.error(f"Error loading sample content: {e}")
            import traceback
            with st.expander("Show Error Details"):
                st.code(traceback.format_exc())
    
    # Tab 8: Export
    with tab8:
        st.header("Export Results")
        
        # JSON export
        st.subheader("📄 Full Report (JSON)")
        
        # Custom JSON encoder to handle NumPy types
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                if isinstance(obj, np.floating):
                    return float(obj)
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                if isinstance(obj, np.bool_):
                    return bool(obj)
                return super().default(obj)
        
        json_str = json.dumps(results, indent=2, cls=NumpyEncoder)
        st.download_button(
            label="Download Full Report",
            data=json_str,
            file_name=f"simulation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        st.markdown("---")
        
        # CSV export
        st.subheader("📊 Metrics Summary (CSV)")
        
        # Create CSV data
        csv_data = {
            'Metric': [
                'Hope Total Engagement',
                'Fear Total Engagement',
                'Hope Reach',
                'Fear Reach',
                'Hope Virality',
                'Fear Virality',
                'Hope Amplification',
                'Fear Amplification'
            ],
            'Value': [
                comparison['hope']['engagement']['total'],
                comparison['fear']['engagement']['total'],
                comparison['hope']['reach']['total_unique'],
                comparison['fear']['reach']['total_unique'],
                comparison['hope']['virality'],
                comparison['fear']['virality'],
                comparison['hope']['amplification'],
                comparison['fear']['amplification']
            ]
        }
        
        df = pd.DataFrame(csv_data)
        csv = df.to_csv(index=False)
        
        st.download_button(
            label="Download Metrics CSV",
            data=csv,
            file_name=f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
        
        st.markdown("---")
        
        # Configuration export
        st.subheader("⚙️ Simulation Configuration")
        
        config_data = {
            'n_agents': n_agents,
            'n_steps': n_steps,
            'campaign_step': campaign_step,
            'temperature': temperature,
            'seed': seed,
            'timestamp': datetime.now().isoformat()
        }
        
        config_json = json.dumps(config_data, indent=2)
        
        st.download_button(
            label="Download Configuration",
            data=config_json,
            file_name=f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

else:
    # Show placeholder message in results tabs
    with tab3:
        st.info("👈 Configure simulation parameters in the sidebar and click 'RUN SIMULATION' to see results here.")
    
    with tab4:
        st.info("👈 Configure simulation parameters in the sidebar and click 'RUN SIMULATION' to see results here.")
    
    with tab5:
        st.info("👈 Configure simulation parameters in the sidebar and click 'RUN SIMULATION' to see results here.")
    
    with tab6:
        st.info("👈 Configure simulation parameters in the sidebar and click 'RUN SIMULATION' to see results here.")
    
    with tab7:
        st.info("👈 Configure simulation parameters in the sidebar and click 'RUN SIMULATION' to see results here.")
    
    with tab8:
        st.info("👈 Run a simulation first to export results.")


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
<p>AI Social Media Simulation for Campaign Effectiveness Research</p>
<p>Bachelor Thesis Project | 2025</p>
</div>
""", unsafe_allow_html=True)


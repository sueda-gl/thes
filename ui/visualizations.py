"""
Visualization functions for Streamlit UI.
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any


def create_engagement_comparison_chart(comparison: Dict) -> go.Figure:
    """
    Create bar chart comparing engagement metrics.
    
    Args:
        comparison: Campaign comparison dict
    
    Returns:
        Plotly figure
    """
    categories = ['Likes', 'Comments', 'Posts']
    hope_values = [
        comparison['hope']['engagement']['likes'],
        comparison['hope']['engagement']['comments'],
        comparison['hope']['engagement']['posts']
    ]
    fear_values = [
        comparison['fear']['engagement']['likes'],
        comparison['fear']['engagement']['comments'],
        comparison['fear']['engagement']['posts']
    ]
    
    fig = go.Figure(data=[
        go.Bar(name='Hope Campaign', x=categories, y=hope_values, marker_color='#2ecc71'),
        go.Bar(name='Fear Campaign', x=categories, y=fear_values, marker_color='#e74c3c')
    ])
    
    fig.update_layout(
        title='Engagement Comparison: Hope vs Fear',
        xaxis_title='Engagement Type',
        yaxis_title='Count',
        barmode='group',
        height=400
    )
    
    return fig


def create_reach_visualization(comparison: Dict) -> go.Figure:
    """
    Create stacked bar chart showing reach breakdown.
    
    Args:
        comparison: Campaign comparison dict
    
    Returns:
        Plotly figure
    """
    campaigns = ['Hope', 'Fear']
    
    direct = [
        comparison['hope']['reach']['direct'],
        comparison['fear']['reach']['direct']
    ]
    secondary = [
        comparison['hope']['reach']['secondary'],
        comparison['fear']['reach']['secondary']
    ]
    tertiary = [
        comparison['hope']['reach']['tertiary'],
        comparison['fear']['reach']['tertiary']
    ]
    
    fig = go.Figure(data=[
        go.Bar(name='Direct', x=campaigns, y=direct, marker_color='#3498db'),
        go.Bar(name='Secondary', x=campaigns, y=secondary, marker_color='#9b59b6'),
        go.Bar(name='Tertiary', x=campaigns, y=tertiary, marker_color='#e67e22')
    ])
    
    fig.update_layout(
        title='Network Reach Breakdown',
        xaxis_title='Campaign',
        yaxis_title='Agents Reached',
        barmode='stack',
        height=400
    )
    
    return fig


def create_temporal_chart(hope_timeline: List[Dict], fear_timeline: List[Dict]) -> go.Figure:
    """
    Create line chart showing engagement over time.
    
    Args:
        hope_timeline: Hope campaign timeline
        fear_timeline: Fear campaign timeline
    
    Returns:
        Plotly figure
    """
    hope_steps = [item['step'] for item in hope_timeline]
    hope_totals = [item['total'] for item in hope_timeline]
    
    fear_steps = [item['step'] for item in fear_timeline]
    fear_totals = [item['total'] for item in fear_timeline]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=hope_steps,
        y=hope_totals,
        mode='lines+markers',
        name='Hope Campaign',
        line=dict(color='#2ecc71', width=3),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=fear_steps,
        y=fear_totals,
        mode='lines+markers',
        name='Fear Campaign',
        line=dict(color='#e74c3c', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title='Engagement Over Time',
        xaxis_title='Simulation Step',
        yaxis_title='Total Engagement',
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_personality_chart(personality_data: Dict) -> go.Figure:
    """
    Create grouped bar chart for personality moderation across all Big Five traits.
    
    Args:
        personality_data: Personality moderation analysis
    
    Returns:
        Plotly figure
    """
    if not personality_data:
        # Return empty figure
        return go.Figure()
    
    # Define trait display names
    trait_names = {
        'openness': 'Openness',
        'conscientiousness': 'Conscientiousness',
        'extraversion': 'Extraversion',
        'agreeableness': 'Agreeableness',
        'neuroticism': 'Neuroticism'
    }
    
    # Prepare data for all available traits
    categories = []
    hope_values = []
    fear_values = []
    
    for trait_key, trait_display in trait_names.items():
        if trait_key in personality_data:
            trait_data = personality_data[trait_key]
            
            # High trait values
            categories.append(f'High {trait_display}')
            hope_values.append(trait_data.get('hope_high_engagement', 0) * 100)
            fear_values.append(trait_data.get('fear_high_engagement', 0) * 100)
            
            # Low trait values
            categories.append(f'Low {trait_display}')
            hope_values.append(trait_data.get('hope_low_engagement', 0) * 100)
            fear_values.append(trait_data.get('fear_low_engagement', 0) * 100)
    
    if not categories:
        return go.Figure()
    
    fig = go.Figure(data=[
        go.Bar(name='Hope Campaign', x=categories, y=hope_values, marker_color='#2ecc71'),
        go.Bar(name='Fear Campaign', x=categories, y=fear_values, marker_color='#e74c3c')
    ])
    
    fig.update_layout(
        title='Engagement Rate by Personality Trait',
        xaxis_title='Trait Level',
        yaxis_title='Engagement Rate (%)',
        barmode='group',
        height=500,
        xaxis={'tickangle': -45}
    )
    
    return fig


def create_virality_comparison(comparison: Dict) -> go.Figure:
    """
    Create gauge charts for virality metrics.
    
    Args:
        comparison: Campaign comparison dict
    
    Returns:
        Plotly figure with subplots
    """
    from plotly.subplots import make_subplots
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{'type': 'indicator'}, {'type': 'indicator'}]],
        subplot_titles=('Hope Virality', 'Fear Virality')
    )
    
    fig.add_trace(go.Indicator(
        mode='gauge+number',
        value=comparison['hope']['virality'],
        title={'text': 'Coefficient'},
        gauge={'axis': {'range': [0, 1]},
               'bar': {'color': '#2ecc71'},
               'steps': [
                   {'range': [0, 0.3], 'color': '#ecf0f1'},
                   {'range': [0.3, 0.6], 'color': '#bdc3c7'},
                   {'range': [0.6, 1], 'color': '#95a5a6'}
               ]}
    ), row=1, col=1)
    
    fig.add_trace(go.Indicator(
        mode='gauge+number',
        value=comparison['fear']['virality'],
        title={'text': 'Coefficient'},
        gauge={'axis': {'range': [0, 1]},
               'bar': {'color': '#e74c3c'},
               'steps': [
                   {'range': [0, 0.3], 'color': '#ecf0f1'},
                   {'range': [0.3, 0.6], 'color': '#bdc3c7'},
                   {'range': [0.6, 1], 'color': '#95a5a6'}
               ]}
    ), row=1, col=2)
    
    fig.update_layout(height=300)
    
    return fig


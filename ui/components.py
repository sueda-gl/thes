"""
Reusable Streamlit UI components.
"""
import streamlit as st
from typing import Dict, Any


def display_metric_card(title: str, value: Any, delta: str = None, help_text: str = None):
    """
    Display a metric card.
    
    Args:
        title: Metric title
        value: Metric value
        delta: Optional delta/comparison value
        help_text: Optional help text
    """
    st.metric(label=title, value=value, delta=delta, help=help_text)


def display_key_findings(findings: list):
    """
    Display key findings in an attractive format.
    
    Args:
        findings: List of finding strings
    """
    st.subheader("Key Findings")
    
    for i, finding in enumerate(findings, 1):
        st.markdown(f"**{i}.** {finding}")


def display_statistical_test(test_result: Dict):
    """
    Display statistical test results.
    
    Args:
        test_result: Test result dict
    """
    st.markdown(f"**{test_result['test']}**")
    
    # Check if test has error
    if 'error' in test_result:
        st.warning(f"⚠️ {test_result['error']}")
        return
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        stat_val = test_result.get('statistic', 'N/A')
        if stat_val is not None:
            st.metric("Statistic", f"{stat_val}")
        else:
            st.metric("Statistic", "N/A")
    
    with col2:
        p_val = test_result.get('p_value', 'N/A')
        if p_val is not None:
            st.metric("p-value", f"{p_val}")
        else:
            st.metric("p-value", "N/A")
    
    with col3:
        is_sig = test_result.get('significant', False)
        st.metric("Significant?", "Yes ✓" if is_sig else "No ✗")


def display_campaign_comparison_table(comparison: Dict):
    """
    Display campaign comparison as a table.
    
    Args:
        comparison: Campaign comparison dict
    """
    import pandas as pd
    
    data = {
        'Metric': [
            'Total Engagement',
            'Engagement Rate',
            'Total Reach',
            'Reach %',
            'Virality Coefficient',
            'Amplification Rate'
        ],
        'Hope Campaign': [
            comparison['hope']['engagement']['total'],
            f"{comparison['hope']['engagement_rate']:.1%}",
            comparison['hope']['reach']['total_unique'],
            f"{comparison['hope']['reach_pct']}%",
            comparison['hope']['virality'],
            f"{comparison['hope']['amplification']:.1%}"
        ],
        'Fear Campaign': [
            comparison['fear']['engagement']['total'],
            f"{comparison['fear']['engagement_rate']:.1%}",
            comparison['fear']['reach']['total_unique'],
            f"{comparison['fear']['reach_pct']}%",
            comparison['fear']['virality'],
            f"{comparison['fear']['amplification']:.1%}"
        ]
    }
    
    df = pd.DataFrame(data)
    st.table(df)


def display_progress_bar(step: int, total_steps: int, message: str = ""):
    """
    Display simulation progress.
    
    Args:
        step: Current step
        total_steps: Total steps
        message: Optional message
    """
    progress = step / total_steps
    st.progress(progress)
    st.caption(f"Step {step}/{total_steps} {message}")


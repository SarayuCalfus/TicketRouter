from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from analytics import (
    analytics_snapshot,
)
from csv_handler import load_ticket_history
from ui import (
    apply_ui_theme,
    render_metric_card,
    render_page_header,
    render_section_heading,
    render_sidebar,
    render_weekly_insights_card,
)

CHART_COLOR_SEQUENCE = ["#4A7FD4", "#6D5BD0", "#7EA6E0", "#B7A0E8", "#2E3A59"]


def _configure_page() -> None:
    st.set_page_config(page_title="Analytics", layout="wide")
    apply_ui_theme()


def _load_dashboard_data() -> object:
    history_df = load_ticket_history()
    if history_df.empty:
        history_df = load_ticket_history("data/sample_tickets.csv")
    return history_df


def _render_metric_row(snapshot: dict) -> None:
    metrics = [
        ("Total Tickets", snapshot["total_tickets"]),
        ("High Priority Tickets", snapshot["high_priority_tickets"]),
        ("Average Confidence", f"{snapshot['average_confidence']:.2f}"),
        ("Needs Human Review", snapshot["needs_human_review"]),
    ]

    cols = st.columns(4)
    for col, (title, value) in zip(cols, metrics):
        with col:
            render_metric_card(title, value)


def _render_charts(snapshot: dict) -> None:
    category_df = pd.DataFrame(
        [
            {"category": label, "count": count}
            for label, count in snapshot["category_distribution"].items()
        ]
    )
    priority_df = pd.DataFrame(
        [
            {"priority": label, "count": count}
            for label, count in snapshot["priority_distribution"].items()
        ]
    )
    sentiment_df = pd.DataFrame(
        [
            {"sentiment": label, "count": count}
            for label, count in snapshot["sentiment_distribution"].items()
        ]
    )

    chart_layout = dict(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="#5B6B8C",
        title_font_color="#2E3A59",
        margin=dict(t=48, l=10, r=10, b=10),
    )

    chart_col_1, chart_col_2 = st.columns(2)
    with chart_col_1:
        render_section_heading("Category Distribution")
        if not category_df.empty:
            fig = px.bar(category_df, x="category", y="count", color="category", title="Category Distribution", color_discrete_sequence=CHART_COLOR_SEQUENCE)
            fig.update_layout(**chart_layout)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available yet.")

    with chart_col_2:
        render_section_heading("Priority Distribution")
        if not priority_df.empty:
            fig = px.bar(priority_df, x="priority", y="count", color="priority", title="Priority Distribution", color_discrete_sequence=CHART_COLOR_SEQUENCE)
            fig.update_layout(**chart_layout)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No priority data available yet.")

    chart_col_3, chart_col_4 = st.columns(2)
    with chart_col_3:
        render_section_heading("Sentiment Distribution")
        if not sentiment_df.empty:
            fig = px.bar(sentiment_df, x="sentiment", y="count", color="sentiment", title="Sentiment Distribution", color_discrete_sequence=CHART_COLOR_SEQUENCE)
            fig.update_layout(**chart_layout)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No sentiment data available yet.")

    with chart_col_4:
        render_section_heading("Weekly Ticket Trend")
        weekly_df = snapshot["weekly_counts"]
        if weekly_df.empty:
            st.info("No weekly trend data available yet.")
        else:
            fig = px.line(weekly_df, x="week", y="ticket_count", markers=True, title="Weekly Ticket Trend", color_discrete_sequence=["#4A7FD4"])
            fig.update_layout(**chart_layout)
            st.plotly_chart(fig, use_container_width=True)


def _render_weekly_insights(snapshot: dict) -> None:
    render_weekly_insights_card(snapshot["weekly_insights"])


def main() -> None:
    _configure_page()
    render_sidebar(active_page="Analytics")

    render_page_header(
        "Analytics & Insights",
        "Monitor ticket volume, priority distribution, sentiment trends, and team performance metrics.",
    )

    data = _load_dashboard_data()
    snapshot = analytics_snapshot(data)

    _render_metric_row(snapshot)
    st.markdown("---")
    _render_charts(snapshot)
    st.markdown("---")
    _render_weekly_insights(snapshot)


if __name__ == "__main__":
    main()

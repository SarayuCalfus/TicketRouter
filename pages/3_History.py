from __future__ import annotations

import pandas as pd
import streamlit as st

from csv_handler import export_processed_json, export_processed_tickets
from ui import (
    apply_ui_theme,
    render_empty_state,
    render_metric_card,
    render_page_header,
    render_section_heading,
    render_sidebar,
)

try:
    from database.crud import get_all_tickets
    from database.db import SessionLocal
except Exception:  # pragma: no cover - handled at runtime
    get_all_tickets = None
    SessionLocal = None


HISTORY_COLUMNS = [
    "ticket_id",
    "ticket_text",
    "category",
    "priority",
    "assigned_team",
    "sentiment",
    "confidence",
    "needs_human_review",
    "summary",
    "tags",
    "auto_reply",
    "reason",
]


def _configure_page() -> None:
    st.set_page_config(page_title="History", layout="wide")
    apply_ui_theme()


def _tickets_to_dataframe(tickets: list) -> pd.DataFrame:
    """Convert Ticket ORM rows into the DataFrame shape the rest of this page expects."""
    if not tickets:
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    records = [
        {
            "ticket_id": ticket.ticket_id,
            "ticket_text": ticket.ticket_text,
            "category": ticket.category,
            "priority": ticket.priority,
            "assigned_team": ticket.assigned_team,
            "sentiment": ticket.sentiment,
            "confidence": ticket.confidence,
            "needs_human_review": ticket.needs_human_review,
            "summary": ticket.summary,
            "tags": ticket.tags,
            "auto_reply": ticket.auto_reply,
            "reason": ticket.reason,
        }
        for ticket in tickets
    ]
    return pd.DataFrame(records, columns=HISTORY_COLUMNS).sort_values("ticket_id").reset_index(drop=True)


def _load_history_dataframe() -> pd.DataFrame:
    """Load all routed tickets from PostgreSQL, tolerating a missing configuration or a database outage."""
    if SessionLocal is None or get_all_tickets is None:
        st.error("Database connection is not configured. Unable to load ticket history.")
        return pd.DataFrame(columns=HISTORY_COLUMNS)

    db = None
    try:
        db = SessionLocal()
        tickets = get_all_tickets(db)
    except Exception:
        st.error("Unable to reach the database right now. Please try again shortly.")
        return pd.DataFrame(columns=HISTORY_COLUMNS)
    finally:
        if db is not None:
            db.close()

    return _tickets_to_dataframe(tickets)


def _filter_history(df: pd.DataFrame) -> pd.DataFrame:
    search_text = st.session_state.get("history_search", "")
    selected_category = st.session_state.get("history_category", "All")
    selected_priority = st.session_state.get("history_priority", "All")
    selected_sentiment = st.session_state.get("history_sentiment", "All")

    if search_text:
        search_query = search_text.lower()
        df = df[
            df.astype(str).apply(lambda row: search_query in " ".join(row).lower(), axis=1)
        ]

    if selected_category != "All" and "category" in df.columns:
        df = df[df["category"].astype(str) == selected_category]

    if selected_priority != "All" and "priority" in df.columns:
        df = df[df["priority"].astype(str) == selected_priority]

    if selected_sentiment != "All" and "sentiment" in df.columns:
        df = df[df["sentiment"].astype(str) == selected_sentiment]

    return df.reset_index(drop=True)


def _render_summary_metrics(df: pd.DataFrame) -> None:
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric_card("Total Records", len(df))
    with metric_cols[1]:
        render_metric_card("High Priority", int(df[df["priority"].astype(str).isin({"High", "Urgent"})].shape[0]))
    with metric_cols[2]:
        render_metric_card("Needs Review", int(df[df["needs_human_review"].astype(str).str.lower().isin({"true", "1", "yes"})].shape[0]))
    with metric_cols[3]:
        (render_metric_card("Categories", int(df["category"].nunique())) if "category" in df.columns else render_metric_card("Categories", 0))


def _render_export_controls(df: pd.DataFrame) -> None:
    export_col_1, export_col_2 = st.columns(2)

    with export_col_1:
        if st.button("Export CSV", use_container_width=True):
            export_path = export_processed_tickets(df.to_dict(orient="records"), "data/ticket_export.csv")
            st.success(f"CSV exported to {export_path}")

    with export_col_2:
        if st.button("Export JSON", use_container_width=True):
            export_path = export_processed_json(df.to_dict(orient="records"), "data/ticket_export.json")
            st.success(f"JSON exported to {export_path}")


def _render_history_table(df: pd.DataFrame) -> None:
    if df.empty:
        render_empty_state("No history available", "Save a routed ticket to build the ticket history dataset.")
        return

    display_df = df.copy()
    
    # Clean up tags and ticket_text
    display_df["tags"] = display_df["tags"].fillna("").astype(str)
    display_df["ticket_text"] = display_df["ticket_text"].fillna("").astype(str)
    display_df["ticket_id"] = display_df["ticket_id"].fillna("").astype(str)
    
    # Select columns to display (ticket_id first)
    display_df = display_df[[
        "ticket_id",
        "category",
        "priority",
        "assigned_team",
        "sentiment",
        "confidence",
        "needs_human_review",
        "summary",
        "tags",
        "auto_reply",
    ]]
    
    # Rename columns for user-friendly display
    column_mapping = {
        "ticket_id": "Ticket #",
        "category": "Category",
        "priority": "Priority",
        "assigned_team": "Assigned Team",
        "sentiment": "Sentiment",
        "confidence": "Confidence",
        "needs_human_review": "Needs Review",
        "summary": "Summary",
        "tags": "Tags",
        "auto_reply": "Suggested Reply",
    }
    display_df = display_df.rename(columns=column_mapping)

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def main() -> None:
    _configure_page()
    render_sidebar(active_page="History")

    render_page_header(
        "Ticket History",
        "Search, filter, and export your routed tickets. Review decisions and track patterns over time.",
    )

    history_df = _load_history_dataframe()

    if history_df.empty:
        render_empty_state("No history available", "The history dataset is empty. Route a ticket first to populate the table.")
        return

    render_section_heading("Filters")
    filter_col_1, filter_col_2, filter_col_3, filter_col_4 = st.columns(4)

    with filter_col_1:
        st.session_state.history_search = st.text_input("Search tickets", value=st.session_state.get("history_search", ""))
    with filter_col_2:
        category_options = ["All"] + sorted(history_df["category"].astype(str).dropna().unique().tolist())
        st.session_state.history_category = st.selectbox("Category", category_options, index=category_options.index(st.session_state.get("history_category", "All")))
    with filter_col_3:
        priority_options = ["All"] + sorted(history_df["priority"].astype(str).dropna().unique().tolist())
        st.session_state.history_priority = st.selectbox("Priority", priority_options, index=priority_options.index(st.session_state.get("history_priority", "All")))
    with filter_col_4:
        sentiment_options = ["All"] + sorted(history_df["sentiment"].astype(str).dropna().unique().tolist())
        st.session_state.history_sentiment = st.selectbox("Sentiment", sentiment_options, index=sentiment_options.index(st.session_state.get("history_sentiment", "All")))

    filtered_df = _filter_history(history_df)

    render_section_heading("Overview")
    _render_summary_metrics(filtered_df)
    st.markdown("---")
    render_section_heading("Export")
    _render_export_controls(filtered_df)
    st.markdown("---")
    render_section_heading("Records")
    _render_history_table(filtered_df)


if __name__ == "__main__":
    main()

import logging

import streamlit as st

try:
    import database.models  # noqa: F401 - registers Ticket on Base.metadata before create_all runs
    from database.db import Base, engine
except Exception:  # pragma: no cover - handled at runtime
    Base = None
    engine = None

from ui import (
    PAGE_DEFINITIONS,
    apply_ui_theme,
    render_feature_card,
    render_hero,
    render_section_heading,
    render_sidebar,
)

logger = logging.getLogger(__name__)


@st.cache_resource
def _initialize_database_schema() -> None:
    """Create any missing tables once per app process; a no-op on every rerun after that."""
    if Base is None or engine is None:
        logger.warning("Database layer is unavailable; skipping schema initialization.")
        return

    try:
        Base.metadata.create_all(bind=engine)
    except Exception:  # pragma: no cover - safety net, must never crash app startup
        logger.exception("Failed to initialize the database schema.")


def configure_application() -> None:
    st.set_page_config(
        page_title="AutoRoute",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_ui_theme()


def initialize_session_state() -> None:
    defaults = {
        "selected_nav": "Home",
        "ticket_text": "",
        "ticket_result": {},
        "history_records": [],
        "last_action": "Landing page loaded",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_landing_page() -> None:
    render_hero(
        eyebrow="AI Support Intelligence",
        title="AutoRoute",
        subtitle=(
            "Transform support tickets into structured AI-driven triage decisions. "
            "Route intelligently. Respond faster. Scale effortlessly."
        ),
    )

    render_section_heading("Get Started")
    action_items = [
        ("Route Ticket", "Paste or upload a ticket and let AI classify, prioritize, and route it.", "Route Ticket"),
        ("View Analytics", "Monitor ticket volume, priority mix, and sentiment trends at a glance.", "Analytics"),
        ("View History", "Search, filter, and export previously routed tickets.", "History"),
    ]

    action_cols = st.columns(3)
    for column, (title, description, page_name) in zip(action_cols, action_items):
        with column:
            render_feature_card("", title, description)
            if st.button(f"Open {title}", use_container_width=True, key=f"home_{page_name}"):
                st.switch_page(PAGE_DEFINITIONS[page_name])

    render_section_heading("Core Capabilities")
    capability_cols = st.columns(4)
    capability_items = [
        ("Classification", "Automatically detect ticket category and intent."),
        ("Priority", "Identify urgent and high-risk tickets instantly."),
        ("Routing", "Assign work to the right team automatically."),
        ("Responses", "Generate professional customer-facing replies."),
    ]
    for column, (title, description) in zip(capability_cols, capability_items):
        with column:
            render_feature_card("", title, description)

    render_section_heading("Processing Pipeline")
    pipeline_cols = st.columns(4)
    pipeline_items = [
        ("1", "Capture", "Paste or upload support ticket content."),
        ("2", "Classify", "AI analyzes and categorizes the ticket."),
        ("3", "Validate", "Verify confidence and review requirements."),
        ("4", "Respond", "Generate reply and save to history."),
    ]
    for column, (step, title, description) in zip(pipeline_cols, pipeline_items):
        with column:
            render_feature_card(step, title, description)


def main() -> None:
    _initialize_database_schema()
    configure_application()
    initialize_session_state()
    render_sidebar(active_page="Home")
    render_landing_page()


if __name__ == "__main__":
    main()

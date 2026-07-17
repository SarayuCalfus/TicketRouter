from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit as st


PAGE_DEFINITIONS: dict[str, str] = {
    "Home": "app.py",
    "Route Ticket": "pages/1_Route_ticket.py",
    "Analytics": "pages/2_Analytics.py",
    "History": "pages/3_History.py",
}


# Maps a ticket priority to a badge tone, giving an at-a-glance severity ramp:
# calm (Low) -> neutral (Medium) -> warning (High) -> urgent (Urgent).
PRIORITY_TONE_MAP: dict[str, str] = {
    "Low": "success",
    "Medium": "primary",
    "High": "warning",
    "Urgent": "danger",
}


def _render_html(html: str) -> None:
    """Render a block of custom HTML, immune to indentation-triggered Markdown code blocks.

    Streamlit's CommonMark parser treats any line indented 4+ spaces (after a blank line)
    as an indented code block, rendered as literal monospace text rather than parsed HTML.
    Pretty-printed, nested multi-line HTML templates in this file have deeper indentation on
    inner tags than the outer wrapping tag, and a single textwrap.dedent pass (which Streamlit
    applies internally) only removes the *smallest* common indent - the inner lines keep a
    residual indent large enough to trigger this rule, which is why several cards rendered as
    raw HTML text instead of styled content. Stripping every line individually guarantees each
    one starts at column 0 before Streamlit's parser ever sees it, regardless of how the
    template is nested/indented in the Python source.
    """
    flattened = "\n".join(line.strip() for line in html.strip().splitlines())
    st.markdown(flattened, unsafe_allow_html=True)


def apply_ui_theme() -> None:
    """Apply the shared soft glassmorphism theme (pastel blue/lavender/off-white palette) app-wide."""
    # All styling is injected once via st.markdown with unsafe_allow_html=True; every page
    # calls this before rendering any content, so the whole app shares one design system.
    _render_html(
        """
        <style>
        :root {
            --blue-100: #EAF2FF;
            --blue-300: #C9DFF7;
            --blue-500: #7EA6E0;
            --blue-700: #4A7FD4;
            --lavender-100: #F1ECFC;
            --lavender-300: #DCCFF5;
            --lavender-500: #B7A0E8;
            --lavender-700: #6D5BD0;
            --success: #10B981;
            --success-light: #D1FAE5;
            --success-dark: #047857;
            --warning: #F59E0B;
            --warning-light: #FEF3C7;
            --warning-dark: #B45309;
            --error: #EF4444;
            --error-light: #FEE2E2;
            --error-dark: #B91C1C;
            --bg-page: #F6F8FC;
            --card-bg: rgba(255, 255, 255, 0.88);
            --card-bg-strong: rgba(255, 255, 255, 0.96);
            --card-blur: 10px;
            --border-color: rgba(139, 111, 209, 0.2);
            --text-primary: #2E3A59;
            --text-secondary: #5B6B8C;
            --text-muted: #8A97B3;
            --shadow-sm: 0 1px 3px rgba(74, 127, 212, 0.07);
            --shadow-md: 0 8px 24px rgba(74, 127, 212, 0.12);
            --shadow-lg: 0 20px 48px rgba(74, 127, 212, 0.16);
            --radius-lg: 18px;
            --radius-md: 15px;
            --radius-sm: 11px;
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        html, body, [data-testid="stAppViewContainer"], .stMainBlockContainer {
            background: var(--bg-page) !important;
        }

        /* Subtle pastel wash behind the glass cards - kept light, no neon, no heavy transparency */
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(900px 480px at 6% -10%, rgba(126, 166, 224, 0.10) 0%, transparent 58%),
                radial-gradient(800px 440px at 96% -5%, rgba(183, 160, 232, 0.10) 0%, transparent 55%),
                var(--bg-page) !important;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        [data-testid="stAppDeployButton"],
        .stDeployButton {
            display: none !important;
        }

        h1, h2, h3, h4 {
            color: var(--text-primary) !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em !important;
        }

        p, span, label, .stMarkdown {
            color: var(--text-secondary);
        }

        [data-testid="stCaptionContainer"] {
            color: var(--text-muted) !important;
        }

        /* Page header block, used via render_page_header() */
        .page-header {
            display: flex;
            align-items: center;
            gap: 0.9rem;
            margin-bottom: 0.4rem;
        }

        /* Centered "hero" variant - used on the Route Ticket page's main input screen */
        .page-header-centered {
            flex-direction: column;
            justify-content: center;
            text-align: center;
            gap: 0.6rem;
            margin-top: 0.6rem;
            margin-bottom: 0.2rem;
        }

        .page-header-centered .page-header-title {
            font-size: 2.15rem;
        }

        .page-header-centered .page-header-subtitle {
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }

        .page-header-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 48px;
            height: 48px;
            border-radius: var(--radius-sm);
            background: linear-gradient(135deg, var(--blue-500), var(--lavender-500));
            font-size: 1.4rem;
            box-shadow: var(--shadow-sm);
            flex-shrink: 0;
        }

        .page-header-title {
            font-size: 1.9rem;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -0.02em;
            line-height: 1.2;
        }

        .page-header-subtitle {
            color: var(--text-muted);
            font-size: 0.98rem;
            margin-top: 0.15rem;
        }

        .page-header-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, var(--border-color) 50%, transparent 100%);
            margin: 1.1rem 0 1.6rem 0;
            border: none;
        }

        /* Shared glass card base - frosted, subtly blurred, thin translucent border, soft shadow */
        .metric-card,
        .feature-card,
        .insights-card,
        .duplicate-card,
        .content-card,
        .empty-state-card {
            background: var(--card-bg);
            backdrop-filter: blur(var(--card-blur));
            -webkit-backdrop-filter: blur(var(--card-blur));
            border: 1px solid var(--border-color);
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-sm);
            transition: transform 0.22s ease, box-shadow 0.22s ease;
            animation: fadeInUp 0.35s ease both;
        }

        .metric-card {
            padding: 1.1rem 1.3rem;
            margin-bottom: 0.9rem;
        }

        .metric-card:hover,
        .feature-card:hover,
        .insights-card:hover,
        .duplicate-card:hover,
        .content-card:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }

        .metric-card-label {
            font-size: 0.76rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .metric-card-value {
            font-size: 1.9rem;
            font-weight: 800;
            color: var(--blue-700);
            margin-top: 0.35rem;
            line-height: 1.15;
            min-height: 4.4rem;
            display: flex;
            align-items: center;
        }

        /* Reserves the same vertical space as .metric-card-value for non-text content
           (e.g. the priority badge pill), so every metric card ends up the same height
           regardless of whether its value wraps to one line or two. */
        .metric-card-value-slot {
            min-height: 4.4rem;
            display: flex;
            align-items: center;
            margin-top: 0.35rem;
        }

        .metric-card-help {
            font-size: 0.78rem;
            color: var(--text-muted);
            margin-top: 0.4rem;
        }

        /* Colour-coded priority badge, used inside the Priority metric card */
        .priority-badge {
            display: inline-flex;
            align-items: center;
            margin-top: 0.45rem;
            padding: 0.3rem 0.85rem;
            border-radius: 999px;
            font-weight: 800;
            font-size: 1rem;
            letter-spacing: 0.01em;
        }

        /* Titled content card, used for Summary / Suggested Reply / AI Reasoning */
        .content-card {
            padding: 1.2rem 1.4rem;
            margin-bottom: 1rem;
        }

        .content-card-title {
            font-size: 0.78rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--lavender-700);
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .content-card-body {
            color: var(--text-secondary);
            font-size: 0.95rem;
            line-height: 1.65;
        }

        /* Pill badges + status chips */
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.3rem 0.75rem;
            border-radius: 999px;
            font-size: 0.76rem;
            font-weight: 600;
            letter-spacing: 0.01em;
            background: var(--lavender-100);
            color: var(--lavender-700);
            border: 1px solid rgba(109, 91, 208, 0.18);
            margin: 0 0.35rem 0.35rem 0;
        }

        .status-chip {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.32rem 0.85rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.01em;
            background: var(--lavender-100);
            color: var(--lavender-700);
            border: 1px solid rgba(109, 91, 208, 0.18);
        }

        .status-chip-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: currentColor;
            flex-shrink: 0;
        }

        /* Section eyebrow heading */
        .section-heading {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 0.82rem;
            font-weight: 700;
            color: var(--blue-700);
            margin-top: 1.4rem;
            margin-bottom: 0.7rem;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .section-heading::before {
            content: "";
            width: 3px;
            height: 0.95rem;
            border-radius: 2px;
            background: linear-gradient(180deg, var(--blue-500), var(--lavender-500));
            display: inline-block;
        }

        /* Buttons - single consistent primary style */
        .stButton > button {
            background: linear-gradient(135deg, var(--blue-500), var(--lavender-500)) !important;
            color: #ffffff !important;
            border: 1px solid rgba(74, 127, 212, 0.3) !important;
            border-radius: var(--radius-sm) !important;
            font-weight: 600 !important;
            letter-spacing: 0.01em !important;
            padding: 0.55rem 1.3rem !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.18s ease !important;
        }

        .stButton > button:hover {
            background: linear-gradient(135deg, var(--blue-700), var(--lavender-700)) !important;
            box-shadow: 0 10px 24px rgba(74, 127, 212, 0.24) !important;
            transform: translateY(-1px);
            border-color: rgba(74, 127, 212, 0.4) !important;
        }

        .stButton > button:active {
            transform: translateY(0);
        }

        .stDownloadButton > button {
            background: var(--card-bg-strong) !important;
            color: var(--blue-700) !important;
            border: 1px solid rgba(74, 127, 212, 0.3) !important;
            border-radius: var(--radius-sm) !important;
            font-weight: 600 !important;
            transition: all 0.18s ease !important;
        }

        .stDownloadButton > button:hover {
            background: var(--blue-100) !important;
            border-color: var(--blue-500) !important;
            transform: translateY(-1px);
        }

        /* Inputs */
        .stTextInput input,
        .stTextArea textarea,
        .stSelectbox > div > div,
        .stNumberInput input {
            background: var(--card-bg-strong) !important;
            color: var(--text-primary) !important;
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border-color) !important;
        }

        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border: 1px solid var(--blue-500) !important;
            box-shadow: 0 0 0 3px rgba(126, 166, 224, 0.2) !important;
        }

        [data-testid="stFileUploaderDropzone"] {
            background: rgba(255, 255, 255, 0.6) !important;
            backdrop-filter: blur(var(--card-blur));
            border: 1.5px dashed var(--lavender-500) !important;
            border-radius: var(--radius-md) !important;
        }

        /* Alerts */
        .stAlert {
            border-radius: var(--radius-md) !important;
        }

        div[data-testid="stAlertContentInfo"], .stInfo {
            background: var(--blue-100) !important;
        }

        div[data-testid="stAlertContentSuccess"], .stSuccess {
            background: var(--success-light) !important;
        }

        div[data-testid="stAlertContentWarning"], .stWarning {
            background: var(--warning-light) !important;
        }

        div[data-testid="stAlertContentError"], .stError {
            background: var(--error-light) !important;
        }

        /* Metric widget (native st.metric, if used) */
        [data-testid="stMetricValue"] {
            color: var(--blue-700);
        }

        [data-testid="stMetricLabel"] {
            color: var(--text-muted);
        }

        /* Spinner (used for the "Beautiful loading state" while the AI call is in flight) */
        [data-testid="stSpinner"] > div {
            color: var(--blue-700) !important;
            font-weight: 600;
        }

        /* Dataframe / table container */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border-color);
            border-radius: var(--radius-md);
            overflow: hidden;
            background: var(--card-bg-strong);
        }

        /* Expander */
        .streamlit-expanderHeader, [data-testid="stExpander"] summary {
            background: var(--card-bg-strong) !important;
            border-radius: var(--radius-sm) !important;
            border: 1px solid var(--border-color) !important;
            font-weight: 600 !important;
            color: var(--text-primary) !important;
        }

        /* Progress bar */
        .stProgress > div > div {
            background: linear-gradient(90deg, var(--blue-500), var(--lavender-500)) !important;
        }

        hr {
            border-color: var(--border-color) !important;
            margin: 1.4rem 0 !important;
        }

        /* Sidebar */
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.7) !important;
            backdrop-filter: blur(var(--card-blur));
            -webkit-backdrop-filter: blur(var(--card-blur));
            border-right: 1px solid var(--border-color);
        }

        .sidebar-card {
            padding: 1.1rem 1.2rem;
            border-radius: var(--radius-md);
            background: linear-gradient(135deg, var(--blue-500), var(--lavender-500));
            margin-bottom: 1.3rem;
            box-shadow: var(--shadow-sm);
        }

        .sidebar-title {
            font-size: 1.25rem;
            font-weight: 800;
            color: #ffffff;
            letter-spacing: -0.01em;
        }

        .sidebar-subtitle {
            color: rgba(255, 255, 255, 0.9);
            margin-top: 0.25rem;
            font-size: 0.82rem;
            font-weight: 500;
        }

        .nav-section-label {
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin: 0.2rem 0 0.6rem 0.1rem;
        }

        .nav-item-active {
            display: flex;
            align-items: center;
            gap: 0.55rem;
            width: 100%;
            padding: 0.55rem 0.9rem;
            border-radius: var(--radius-sm);
            background: var(--lavender-100);
            color: var(--lavender-700) !important;
            font-weight: 700;
            font-size: 0.92rem;
            border: 1px solid rgba(109, 91, 208, 0.3);
            margin-bottom: 0.45rem;
            box-sizing: border-box;
        }

        section[data-testid="stSidebar"] .stButton > button {
            background: rgba(255, 255, 255, 0.6) !important;
            color: var(--text-secondary) !important;
            border: 1px solid var(--border-color) !important;
            box-shadow: none !important;
            text-align: left !important;
            justify-content: flex-start !important;
            font-weight: 600 !important;
        }

        section[data-testid="stSidebar"] .stButton > button:hover {
            background: var(--lavender-100) !important;
            color: var(--lavender-700) !important;
            border-color: var(--lavender-500) !important;
            transform: none;
            box-shadow: none !important;
        }

        /* Hero (landing page) */
        .hero-card {
            position: relative;
            padding: 2.6rem 2.6rem;
            border-radius: var(--radius-lg);
            background: linear-gradient(135deg, var(--blue-500) 0%, var(--lavender-500) 100%);
            color: #ffffff;
            margin-bottom: 1.8rem;
            box-shadow: var(--shadow-lg);
            overflow: hidden;
            animation: fadeInUp 0.35s ease both;
        }

        .hero-card::after {
            content: "";
            position: absolute;
            top: -70px;
            right: -70px;
            width: 280px;
            height: 280px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.16);
            filter: blur(2px);
        }

        .hero-eyebrow {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.22);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: #ffffff;
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
            position: relative;
            z-index: 1;
        }

        .hero-card h1 {
            margin-bottom: 0.6rem;
            color: #ffffff !important;
            font-size: 2.3rem;
            font-weight: 800;
            letter-spacing: -0.02em;
            position: relative;
            z-index: 1;
        }

        .hero-card p {
            margin: 0;
            color: rgba(255, 255, 255, 0.94);
            font-size: 1.05rem;
            line-height: 1.65;
            font-weight: 400;
            max-width: 640px;
            position: relative;
            z-index: 1;
        }

        /* Feature / capability cards */
        .feature-card {
            padding: 1.4rem 1.5rem;
            border-top: 3px solid var(--blue-500);
            height: 100%;
            min-height: 168px;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .feature-card:hover {
            border-top-color: var(--lavender-500);
        }

        .feature-icon {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 40px;
            height: 40px;
            border-radius: var(--radius-sm);
            background: var(--lavender-100);
            font-size: 1.15rem;
            margin-bottom: 0.3rem;
        }

        .feature-card-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .feature-card-description {
            color: var(--text-muted);
            font-size: 0.9rem;
            line-height: 1.5;
        }

        /* Weekly insights card */
        .insights-card {
            border-left: 4px solid var(--blue-500);
            padding: 1.6rem 1.8rem;
            margin: 0.6rem 0 1.4rem 0;
        }

        .insights-card-header {
            display: flex;
            align-items: center;
            gap: 0.65rem;
            margin-bottom: 1.1rem;
        }

        .insights-card-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: var(--text-primary);
            letter-spacing: -0.01em;
        }

        .insights-summary-banner {
            background: var(--warning-light);
            border: 1px solid rgba(245, 158, 11, 0.25);
            border-radius: var(--radius-md);
            padding: 0.85rem 1.1rem;
            color: var(--text-primary);
            font-weight: 600;
            font-size: 0.95rem;
            line-height: 1.55;
            margin-bottom: 1.3rem;
        }

        .insights-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.2rem;
            margin-bottom: 1.3rem;
        }

        @media (max-width: 900px) {
            .insights-grid {
                grid-template-columns: 1fr;
            }
        }

        .insights-group-label {
            font-size: 0.72rem;
            font-weight: 700;
            color: var(--blue-700);
            text-transform: uppercase;
            letter-spacing: 0.06em;
            margin-bottom: 0.55rem;
        }

        .insights-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
        }

        .insights-chip {
            display: inline-flex;
            align-items: center;
            padding: 0.3rem 0.7rem;
            border-radius: 999px;
            background: var(--lavender-100);
            color: var(--lavender-700);
            font-size: 0.78rem;
            font-weight: 600;
            border: 1px solid rgba(109, 91, 208, 0.18);
        }

        .insights-empty {
            color: var(--text-muted);
            font-size: 0.85rem;
            font-style: italic;
        }

        .insights-actions {
            border-top: 1px solid var(--border-color);
            padding-top: 1.1rem;
        }

        .insights-action-list {
            list-style: none;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            gap: 0.55rem;
        }

        .insights-action-list li {
            position: relative;
            padding-left: 1.5rem;
            color: var(--text-secondary);
            font-size: 0.92rem;
            line-height: 1.5;
        }

        .insights-action-list li::before {
            content: "–";
            position: absolute;
            left: 0;
            top: 0;
            color: var(--success-dark);
            font-weight: 800;
        }

        /* Duplicate ticket detection panel */
        .duplicate-card {
            border-left: 4px solid var(--lavender-500);
            padding: 1.4rem 1.6rem;
            margin: 0.6rem 0 1.4rem 0;
        }

        .duplicate-card-header {
            display: flex;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 1rem;
        }

        .duplicate-card-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: var(--text-primary);
        }

        .duplicate-row {
            display: flex;
            align-items: center;
            gap: 0.8rem;
            padding: 0.65rem 0;
            border-bottom: 1px solid var(--border-color);
            flex-wrap: wrap;
        }

        .duplicate-row:last-child {
            border-bottom: none;
        }

        .duplicate-id {
            font-weight: 700;
            color: var(--text-primary);
            font-size: 0.88rem;
            min-width: 70px;
        }

        .duplicate-similarity {
            display: inline-flex;
            align-items: center;
            padding: 0.22rem 0.6rem;
            border-radius: 999px;
            background: var(--blue-100);
            color: var(--blue-700);
            font-size: 0.78rem;
            font-weight: 700;
        }

        .duplicate-category {
            display: inline-flex;
            align-items: center;
            padding: 0.22rem 0.6rem;
            border-radius: 999px;
            background: var(--lavender-100);
            color: var(--lavender-700);
            font-size: 0.76rem;
            font-weight: 600;
        }

        .duplicate-preview {
            color: var(--text-muted);
            font-size: 0.85rem;
            font-style: italic;
            flex: 1;
            min-width: 180px;
        }

        /* Empty state */
        .empty-state-card {
            text-align: center;
            padding: 2.4rem 1.5rem;
            border: 1.5px dashed rgba(109, 91, 208, 0.3);
        }

        .empty-state-icon {
            font-size: 2.2rem;
            margin-bottom: 0.6rem;
        }

        .empty-state-title {
            font-weight: 700;
            font-size: 1.05rem;
            color: var(--text-primary);
            margin-bottom: 0.35rem;
        }

        .empty-state-body {
            color: var(--text-muted);
            font-size: 0.92rem;
        }
        </style>
        """
    )


def get_available_pages() -> dict[str, str]:
    """Return only the nav pages whose backing files actually exist on disk."""
    root_dir = Path(__file__).resolve().parent
    available: dict[str, str] = {}

    for name, relative_path in PAGE_DEFINITIONS.items():
        page_path = root_dir / relative_path
        if page_path.exists():
            available[name] = relative_path

    return available


def render_sidebar(active_page: str) -> None:
    """Render the shared sidebar: brand card, nav links with active-state highlighting, and system info."""
    available_pages = get_available_pages()

    with st.sidebar:
        _render_html(
            """
            <div class="sidebar-card">
                <div class="sidebar-title">AutoRoute</div>
                <div class="sidebar-subtitle">AI Support Intelligence</div>
            </div>
            """
        )

        _render_html('<div class="nav-section-label">Navigation</div>')

        for name, path in PAGE_DEFINITIONS.items():
            if name == active_page:
                _render_html(f'<div class="nav-item-active">{name}</div>')
                continue

            if name not in available_pages:
                continue

            if st.button(name, use_container_width=True, key=f"nav_{name}"):
                st.switch_page(path)

        st.markdown("---")
        _render_html('<div class="nav-section-label">System</div>')
        st.caption("Modular architecture with separation of concerns. AI logic isolated from UI layer.")

        if len(available_pages) != len(PAGE_DEFINITIONS):
            st.warning("Some requested pages are not present in the workspace yet.")


def render_page_header(title: str, subtitle: str = "", icon: str = "", centered: bool = False) -> None:
    """Render a consistent page header (icon chip + title + subtitle).

    Set centered=True for the hero-style centered presentation used on the Route Ticket page;
    other pages omit it and keep the standard left-aligned layout.
    """
    icon_html = f'<div class="page-header-icon">{icon}</div>' if icon else ""
    wrapper_class = "page-header page-header-centered" if centered else "page-header"
    _render_html(
        f"""
        <div class="{wrapper_class}">
            {icon_html}
            <div>
                <div class="page-header-title">{title}</div>
                {f'<div class="page-header-subtitle">{subtitle}</div>' if subtitle else ''}
            </div>
        </div>
        <hr class="page-header-divider" />
        """
    )


def render_metric_card(title: str, value: Any, help_text: str | None = None, icon: str = "") -> None:
    """Render a reusable metric card for the analytics dashboard and landing experience."""
    icon_html = f"<span>{icon}</span>" if icon else ""
    _render_html(
        f"""
        <div class="metric-card">
            <div class="metric-card-label">{icon_html}{title}</div>
            <div class="metric-card-value">{value}</div>
            {f'<div class="metric-card-help">{help_text}</div>' if help_text else ''}
        </div>
        """
    )


def render_priority_metric_card(priority: str) -> None:
    """Render the Priority metric card with a colour-coded severity badge instead of plain text."""
    tone = PRIORITY_TONE_MAP.get(priority, "primary")
    tone_colors = {
        "primary": ("#F1ECFC", "#6D5BD0"),
        "success": ("#D1FAE5", "#047857"),
        "warning": ("#FEF3C7", "#B45309"),
        "danger": ("#FEE2E2", "#B91C1C"),
    }
    background, color = tone_colors.get(tone, tone_colors["primary"])
    _render_html(
        f"""
        <div class="metric-card">
            <div class="metric-card-label">Priority</div>
            <div class="metric-card-value-slot">
                <span class="priority-badge" style="background: {background}; color: {color};">{priority}</span>
            </div>
        </div>
        """
    )


def render_content_card(title: str, body: str, icon: str = "") -> None:
    """Render a titled glass card for a block of AI-generated text (summary, reply, reasoning)."""
    icon_html = f"<span>{icon}</span>" if icon else ""
    _render_html(
        f"""
        <div class="content-card">
            <div class="content-card-title">{icon_html}{title}</div>
            <div class="content-card-body">{body}</div>
        </div>
        """
    )


def render_badge(label: str, tone: str = "primary") -> None:
    """Render a reusable pill badge using the soft glassmorphism pastel palette."""
    tone_map = {
        "primary": ("#F1ECFC", "#6D5BD0"),
        "success": ("#D1FAE5", "#047857"),
        "warning": ("#FEF3C7", "#B45309"),
        "danger": ("#FEE2E2", "#B91C1C"),
    }
    background, color = tone_map.get(tone, tone_map["primary"])
    _render_html(
        f'<span class="badge" style="background: {background}; color: {color}; border-color: {color}22;">{label}</span>'
    )


def render_status_chip(label: str, tone: str = "neutral") -> None:
    """Render a compact status chip for review, confidence, or sentiment indicators."""
    tone_map = {
        "neutral": ("#F1ECFC", "#6D5BD0"),
        "success": ("#D1FAE5", "#047857"),
        "warning": ("#FEF3C7", "#B45309"),
        "danger": ("#FEE2E2", "#B91C1C"),
    }
    background, color = tone_map.get(tone, tone_map["neutral"])
    _render_html(
        f"""
        <span class="status-chip" style="background: {background}; color: {color}; border-color: {color}22;">
            <span class="status-chip-dot"></span>{label}
        </span>
        """
    )


def render_section_heading(text: str) -> None:
    """Render a consistent eyebrow-style section heading for UI composition."""
    _render_html(f'<div class="section-heading">{text}</div>')


def render_tag_list(tags: list[str]) -> None:
    """Render a compact list of tag badges for ticket results."""
    if not tags:
        return

    for tag in tags:
        render_badge(str(tag), tone="primary")


def render_duplicate_matches(matches: list[dict[str, Any]]) -> None:
    """Render the informational duplicate-ticket panel: top similarity matches, or a not-found notice."""
    if not matches:
        st.info("No Similar Tickets Found.")
        return

    rows_html = ""
    for match in matches:
        raw_ticket_id = match.get("ticket_id", "")
        ticket_label = f"TK-{int(raw_ticket_id):04d}" if str(raw_ticket_id).strip().isdigit() else str(raw_ticket_id)
        rows_html += f"""
            <div class="duplicate-row">
                <span class="duplicate-id">{ticket_label}</span>
                <span class="duplicate-similarity">{match.get('similarity', 0):.0f}% match</span>
                <span class="duplicate-category">{match.get('category', 'General Inquiry')}</span>
                <span class="duplicate-preview">{match.get('preview', '')}</span>
            </div>
        """

    _render_html(
        f"""
        <div class="duplicate-card">
            <div class="duplicate-card-header">
                <div class="duplicate-card-title">Possible Duplicate Tickets</div>
            </div>
            {rows_html}
        </div>
        """
    )


def render_empty_state(title: str, body: str, icon: str = "") -> None:
    """Render a polished empty-state card for empty histories or missing records."""
    icon_html = f'<div class="empty-state-icon">{icon}</div>' if icon else ""
    _render_html(
        f"""
        <div class="empty-state-card">
            {icon_html}
            <div class="empty-state-title">{title}</div>
            <div class="empty-state-body">{body}</div>
        </div>
        """
    )


def render_weekly_insights_card(insights: dict[str, Any]) -> None:
    """Render the Weekly AI Insights summary as a modern dashboard card with chips and an action checklist."""

    def _chip_row(items: list[str]) -> str:
        if not items:
            return '<span class="insights-empty">No data available.</span>'
        return "".join(f'<span class="insights-chip">{item}</span>' for item in items)

    def _action_items(items: list[str]) -> str:
        if not items:
            return '<li class="insights-empty" style="padding-left: 0;">No recommended actions at this time.</li>'
        return "".join(f"<li>{item}</li>" for item in items)

    summary = insights.get("summary", "")
    top_categories = insights.get("top_categories") or []
    top_priorities = insights.get("top_priorities") or []
    recurring_issues = insights.get("recurring_issues") or []
    recommended_actions = insights.get("recommended_actions") or []

    _render_html(
        f"""
        <div class="insights-card">
            <div class="insights-card-header">
                <div class="insights-card-title">Weekly AI Insights</div>
            </div>
            <div class="insights-summary-banner">{summary}</div>
            <div class="insights-grid">
                <div class="insights-group">
                    <div class="insights-group-label">Top Categories</div>
                    <div class="insights-chip-row">{_chip_row(top_categories)}</div>
                </div>
                <div class="insights-group">
                    <div class="insights-group-label">Top Priorities</div>
                    <div class="insights-chip-row">{_chip_row(top_priorities)}</div>
                </div>
                <div class="insights-group">
                    <div class="insights-group-label">Recurring Sentiment</div>
                    <div class="insights-chip-row">{_chip_row(recurring_issues)}</div>
                </div>
            </div>
            <div class="insights-actions">
                <div class="insights-group-label">Recommended Actions</div>
                <ul class="insights-action-list">{_action_items(recommended_actions)}</ul>
            </div>
        </div>
        """
    )


def render_feature_card(icon: str, title: str, description: str) -> None:
    """Render a capability/feature card for grid layouts (landing page, pipeline steps)."""
    icon_html = f'<div class="feature-icon">{icon}</div>' if icon else ""
    _render_html(
        f"""
        <div class="feature-card">
            {icon_html}
            <div class="feature-card-title">{title}</div>
            <div class="feature-card-description">{description}</div>
        </div>
        """
    )


def render_hero(eyebrow: str, title: str, subtitle: str) -> None:
    """Render the landing page hero banner."""
    _render_html(
        f"""
        <div class="hero-card">
            <div class="hero-eyebrow">{eyebrow}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """
    )

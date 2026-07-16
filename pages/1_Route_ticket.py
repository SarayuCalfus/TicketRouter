from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from csv_handler import append_ticket_record, export_processed_json, save_ticket_history
from duplicate_detector import find_similar_tickets, format_duplicate_match_label
from router import generate_reply, process_batch_tickets, route_ticket
from ui import (
    apply_ui_theme,
    render_content_card,
    render_duplicate_matches,
    render_metric_card,
    render_page_header,
    render_priority_metric_card,
    render_section_heading,
    render_sidebar,
    render_status_chip,
    render_tag_list,
)
from validator import validate_ticket_result

try:
    from database.crud import get_all_tickets
    from database.db import SessionLocal
except Exception:  # pragma: no cover - handled at runtime
    get_all_tickets = None
    SessionLocal = None


def _load_history_for_duplicate_check() -> pd.DataFrame:
    """Fetch existing tickets from the database for duplicate comparison.

    Duplicate detection is informational only, so any database issue here yields an
    empty result rather than raising, and never blocks ticket creation.
    """
    empty_history = pd.DataFrame(columns=["ticket_id", "ticket_text", "category"])

    if SessionLocal is None or get_all_tickets is None:
        return empty_history

    db = None
    try:
        db = SessionLocal()
        tickets = get_all_tickets(db)
    except Exception:
        return empty_history
    finally:
        if db is not None:
            db.close()

    if not tickets:
        return empty_history

    return pd.DataFrame(
        [{"ticket_id": ticket.ticket_id, "ticket_text": ticket.ticket_text, "category": ticket.category} for ticket in tickets]
    )


def _configure_page() -> None:
    st.set_page_config(page_title="Route Ticket", layout="wide")
    apply_ui_theme()


def _get_selected_result() -> dict:
    return st.session_state.get("ticket_result", {}) if isinstance(st.session_state.get("ticket_result"), dict) else {}


def _bind_ticket_result(result: dict) -> None:
    st.session_state.ticket_result = result


def _save_current_result() -> None:
    result = _get_selected_result()
    if not result:
        st.warning("No routed ticket result is available to save yet.")
        return

    ticket_text = st.session_state.get("ticket_text", "")
    payload = {
        "ticket_text": ticket_text,
        **result,
    }

    try:
        append_ticket_record(payload)
        st.success("The routed ticket has been saved to history.")
    except Exception as exc:  # pragma: no cover - safety net
        st.error(f"Unable to save the routed ticket: {exc}")


def _download_json(result: dict) -> None:
    json_data = json.dumps(result, indent=2, ensure_ascii=False)
    st.download_button(
        label="Download JSON",
        data=json_data,
        file_name="ticket_result.json",
        mime="application/json",
        use_container_width=True,
    )


def _render_result_panel(result: dict) -> None:
    if not result:
        return

    status = "Needs Human Review" if result.get("needs_human_review") else "Auto Routed"
    status_tone = "danger" if result.get("needs_human_review") else "success"

    header_col, status_col = st.columns([3, 1])
    with header_col:
        st.markdown("### Routed Ticket Result")
    with status_col:
        render_status_chip(status, tone=status_tone)

    metric_cols = st.columns(5)
    with metric_cols[0]:
        render_metric_card("Category", result.get("category", "General Inquiry"))
    with metric_cols[1]:
        render_priority_metric_card(result.get("priority", "Medium"))
    with metric_cols[2]:
        render_metric_card("Assigned Team", result.get("assigned_team", "Customer Success"))
    with metric_cols[3]:
        render_metric_card("Sentiment", result.get("sentiment", "Neutral"))
    with metric_cols[4]:
        render_metric_card("Confidence", result.get("confidence", "Low"))

    st.markdown("---")

    render_content_card("Ticket Summary", result.get("summary", ""))

    render_section_heading("Tags")
    render_tag_list(result.get("tags", []))

    render_content_card("Suggested Reply", result.get("auto_reply", ""))

    render_content_card("AI Reasoning", result.get("reason", ""))

    render_section_heading("Possible Duplicate Tickets")
    render_duplicate_matches(st.session_state.get("duplicate_matches", []))

    st.markdown("---")
    action_col_1, action_col_2 = st.columns([1, 1])
    with action_col_1:
        if st.button("Save to History", use_container_width=True):
            _save_current_result()
    with action_col_2:
        _download_json(result)


def _render_upload_panel() -> None:
    st.markdown("## Batch Processing")
    uploaded_file = st.file_uploader("Upload CSV with ticket data", type=["csv"])
    if uploaded_file is None:
        return

    try:
        df = pd.read_csv(uploaded_file)
        if df.empty:
            st.warning("The uploaded CSV file is empty.")
            return

        st.success(f"Loaded {len(df)} ticket rows for batch processing.")
        st.session_state.uploaded_batch_df = df

        if st.button("Process Batch", use_container_width=True):
            _process_batch_workflow()
    except Exception as exc:  # pragma: no cover - safety net
        st.error(f"Unable to parse the CSV upload: {exc}")


def _process_batch_workflow() -> None:
    """Process the uploaded batch of tickets with progress tracking and result display."""
    batch_df = st.session_state.get("uploaded_batch_df")
    if batch_df is None or batch_df.empty:
        st.warning("No batch data available to process.")
        return

    ticket_column = _find_ticket_column(batch_df)
    if ticket_column is None:
        st.error("The CSV must contain a column with ticket text (e.g., 'ticket_text' or 'text' or 'content').")
        return

    tickets_to_process = batch_df[ticket_column].astype(str).tolist()
    total_tickets = len(tickets_to_process)

    progress_bar = st.progress(0)
    status_text = st.empty()

    # Snapshot existing history once so every ticket in this batch is compared against the
    # same pre-batch baseline, rather than against other tickets processed earlier in this batch.
    history_before_batch = _load_history_for_duplicate_check()

    try:
        processed_results = []
        for idx, ticket_text in enumerate(tickets_to_process):
            ai_result = route_ticket(ticket_text)
            validated_result = validate_ticket_result(ai_result)
            # Preserve the original ticket text with the AI result
            validated_result["ticket_text"] = ticket_text
            duplicate_matches = find_similar_tickets(ticket_text, history_before_batch)
            validated_result["duplicate_match"] = format_duplicate_match_label(duplicate_matches)
            processed_results.append(validated_result)
            progress = (idx + 1) / total_tickets
            progress_bar.progress(progress)
            status_text.text(f"Processing tickets: {idx + 1}/{total_tickets}")

        progress_bar.empty()
        status_text.empty()

        save_ticket_history(processed_results)
        st.success(f"Successfully processed and saved {len(processed_results)} tickets to history.")
        st.session_state.processed_batch_results = processed_results

        _render_batch_results_panel(processed_results)
    except Exception as exc:  # pragma: no cover - safety net
        progress_bar.empty()
        status_text.empty()
        st.error(f"An error occurred while processing the batch: {exc}")


def _find_ticket_column(df: pd.DataFrame) -> str | None:
    """Identify the ticket text column in the uploaded CSV."""
    possible_names = ["ticket_text", "text", "content", "ticket", "message", "issue", "description"]
    for col_name in possible_names:
        if col_name in df.columns:
            return col_name
    return None


def _export_batch_results_csv(results: list[dict], output_path: str) -> str:
    """Export batch results to CSV, including the informational Duplicate Match column.

    csv_handler.export_processed_tickets rebuilds each row from a fixed schema and would
    silently drop the duplicate_match field, so this batch-specific export is built directly
    from the already-validated in-memory results instead.
    """
    export_rows = []
    for idx, result in enumerate(results, start=1):
        tags = result.get("tags", [])
        tags_text = ", ".join(str(tag) for tag in tags) if isinstance(tags, list) else str(tags or "")
        export_rows.append(
            {
                "ticket_id": idx,
                "ticket_text": result.get("ticket_text", ""),
                "category": result.get("category", "General Inquiry"),
                "priority": result.get("priority", "Medium"),
                "assigned_team": result.get("assigned_team", "Customer Success"),
                "sentiment": result.get("sentiment", "Neutral"),
                "confidence": result.get("confidence", "Low"),
                "needs_human_review": result.get("needs_human_review", False),
                "summary": result.get("summary", ""),
                "tags": tags_text,
                "auto_reply": result.get("auto_reply", ""),
                "reason": result.get("reason", ""),
                "Duplicate Match": result.get("duplicate_match", "No Similar Tickets"),
            }
        )

    pd.DataFrame(export_rows).to_csv(output_path, index=False)
    return output_path


def _render_batch_results_panel(results: list[dict]) -> None:
    """Display processed batch results with export options and expandable details."""
    st.markdown("## Batch Results")

    display_df = pd.DataFrame(results)
    display_cols_to_show = [
        col for col in [
            "category",
            "priority",
            "assigned_team",
            "sentiment",
            "confidence",
            "needs_human_review",
            "duplicate_match",
        ]
        if col in display_df.columns
    ]

    if display_cols_to_show:
        display_table = display_df[display_cols_to_show].rename(columns={"duplicate_match": "Duplicate Match"})
        st.dataframe(display_table, use_container_width=True, hide_index=True)
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("## Ticket Details")

    for idx, result in enumerate(results, start=1):
        with st.expander(f"Ticket {idx}: {result.get('category', 'General Inquiry')} | {result.get('priority', 'Medium')} | {result.get('sentiment', 'Neutral')}"):
            detail_col_1, detail_col_2 = st.columns(2)
            with detail_col_1:
                render_section_heading("Summary")
                st.write(result.get("summary", ""))
                render_section_heading("Suggested Reply")
                st.write(result.get("auto_reply", ""))
            with detail_col_2:
                render_section_heading("AI Reasoning")
                st.write(result.get("reason", ""))
                render_section_heading("Tags")
                render_tag_list(result.get("tags", []))

    st.markdown("---")
    export_col_1, export_col_2 = st.columns(2)
    with export_col_1:
        if st.button("Download Batch CSV", use_container_width=True):
            export_path = _export_batch_results_csv(results, "data/batch_results.csv")
            st.success(f"Batch CSV exported to {export_path}")

    with export_col_2:
        if st.button("Download Batch JSON", use_container_width=True):
            export_path = export_processed_json(results, "data/batch_results.json")
            st.success(f"Batch JSON exported to {export_path}")


def main() -> None:
    _configure_page()
    render_sidebar(active_page="Route Ticket")

    render_page_header(
        "Ticket Routing Engine",
        "Enter or upload support tickets. AI will classify, prioritize, and route them. Save results to history.",
        centered=True,
    )

    ticket_text = st.text_area(
        "Support Ticket",
        value=st.session_state.get("ticket_text", ""),
        height=260,
        placeholder="Paste the customer support ticket here...",
    )
    st.session_state.ticket_text = ticket_text

    ticket_attachment = st.file_uploader(
        "Attach a file (optional)",
        type=["txt", "pdf", "docx", "png", "jpg", "jpeg"],
        key="ticket_attachment",
        help="TXT, PDF, and DOCX are read for text. Screenshots (PNG/JPG/JPEG) get an AI-generated description.",
    )

    route_col, reply_col = st.columns([1, 1])
    with route_col:
        if st.button("Route Ticket", use_container_width=True):
            if not ticket_text.strip() and ticket_attachment is None:
                st.warning("Please enter a support ticket or attach a file before routing.")
            else:
                with st.spinner("Analyzing ticket with AI..."):
                    history_before_routing = _load_history_for_duplicate_check()
                    st.session_state.duplicate_matches = find_similar_tickets(ticket_text, history_before_routing)

                    ai_result = route_ticket(ticket_text, attachment=ticket_attachment)
                    validated_result = validate_ticket_result(ai_result)
                _bind_ticket_result(validated_result)
                st.session_state.last_action = "Ticket routed"
                st.success("Ticket routing completed.")
    with reply_col:
        if st.button("Generate Reply", use_container_width=True):
            if not ticket_text.strip() and ticket_attachment is None:
                st.warning("Please enter a support ticket or attach a file before generating a reply.")
            else:
                with st.spinner("Generating suggested reply..."):
                    reply_result = generate_reply(ticket_text, attachment=ticket_attachment)
                st.session_state.reply_result = reply_result
                st.success("Suggested reply generated.")

    if "reply_result" in st.session_state:
        render_content_card("Suggested Response", st.session_state.reply_result.get("auto_reply", ""))

    result = _get_selected_result()
    if result:
        _render_result_panel(result)

    _render_upload_panel()


if __name__ == "__main__":
    main()

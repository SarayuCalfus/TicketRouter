from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

import pandas as pd

SIMILARITY_THRESHOLD = 0.80
TOP_MATCHES_LIMIT = 3
PREVIEW_LENGTH = 70


def normalize_text(text: Any) -> str:
    """Normalize ticket text for comparison: lowercase with collapsed whitespace."""
    return " ".join(str(text or "").lower().split())


def calculate_similarity(text_a: Any, text_b: Any) -> float:
    """Return a similarity ratio between 0.0 and 1.0 for two ticket texts, after normalization."""
    return SequenceMatcher(None, normalize_text(text_a), normalize_text(text_b)).ratio()


def _build_preview(ticket_text: Any, length: int = PREVIEW_LENGTH) -> str:
    text = str(ticket_text or "").strip()
    if len(text) <= length:
        return text
    return text[:length].rstrip() + "..."


def find_similar_tickets(
    ticket_text: str,
    history_df: pd.DataFrame,
    *,
    threshold: float = SIMILARITY_THRESHOLD,
    limit: int = TOP_MATCHES_LIMIT,
) -> list[dict[str, Any]]:
    """Find prior tickets whose text is at least `threshold` similar to `ticket_text`.

    `history_df` must contain `ticket_text` and `category` columns and, ideally, `ticket_id`.
    Returns up to `limit` matches sorted by similarity descending, each with ticket_id,
    similarity (0-100), category, and a short preview of the stored ticket text.
    """
    if not ticket_text or not str(ticket_text).strip():
        return []
    if history_df is None or history_df.empty or "ticket_text" not in history_df.columns:
        return []

    matches: list[dict[str, Any]] = []
    for _, row in history_df.iterrows():
        existing_text = row.get("ticket_text", "")
        if not str(existing_text).strip():
            continue

        similarity = calculate_similarity(ticket_text, existing_text)
        if similarity < threshold:
            continue

        matches.append(
            {
                "ticket_id": row.get("ticket_id", ""),
                "similarity": round(similarity * 100, 1),
                "category": row.get("category", "General Inquiry"),
                "preview": _build_preview(existing_text),
            }
        )

    matches.sort(key=lambda match: match["similarity"], reverse=True)
    return matches[:limit]


def format_duplicate_match_label(matches: list[dict[str, Any]]) -> str:
    """Format the single best match for a compact label, e.g. for a CSV export column."""
    if not matches:
        return "No Similar Tickets"

    best = matches[0]
    raw_ticket_id = best.get("ticket_id", "")
    ticket_label = f"TK-{int(raw_ticket_id):04d}" if str(raw_ticket_id).strip().isdigit() else str(raw_ticket_id)
    return f"{ticket_label} ({best.get('similarity', 0):.0f}%)"

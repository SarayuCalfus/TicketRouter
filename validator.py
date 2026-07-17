from __future__ import annotations

import json
from typing import Any


TICKET_RESULT_SCHEMA = {
    "category": str,
    "priority": str,
    "assigned_team": str,
    "sentiment": str,
    "confidence": str,
    "needs_human_review": bool,
    "summary": str,
    "tags": list,
    "auto_reply": str,
    "reason": str,
}

VALID_PRIORITIES = {"Low", "Medium", "High", "Urgent"}
VALID_SENTIMENTS = {"Positive", "Neutral", "Negative", "Frustrated"}
VALID_CONFIDENCE = {"High", "Medium", "Low"}


def _validate_string_field(value: Any, default: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return default


def _validate_bool_field(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes"}:
            return True
        if normalized in {"false", "0", "no"}:
            return False
    return default


def _validate_tags_field(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _validate_enum_field(value: Any, allowed_values: set[str], default: str) -> str:
    if isinstance(value, str) and value.strip() in allowed_values:
        return value.strip()
    return default


def _ensure_object(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict):
        return payload
    return {}


def normalize_ticket_result(payload: Any) -> dict[str, Any]:
    """Validate and normalize a single AI ticket-routing response into a stable schema.

    A sentiment of None is preserved as-is rather than defaulted: it signals that sentiment
    analysis was intentionally skipped (e.g. the ticket had an attachment), not that the value
    is missing or malformed.
    """
    source = _ensure_object(payload)

    raw_sentiment = source.get("sentiment")
    normalized_sentiment = (
        None if raw_sentiment is None else _validate_enum_field(raw_sentiment, VALID_SENTIMENTS, "Neutral")
    )

    normalized_payload = {
        "category": _validate_string_field(source.get("category"), "General Inquiry"),
        "priority": _validate_enum_field(source.get("priority"), VALID_PRIORITIES, "Medium"),
        "assigned_team": _validate_string_field(source.get("assigned_team"), "Customer Success"),
        "sentiment": normalized_sentiment,
        "confidence": _validate_enum_field(source.get("confidence"), VALID_CONFIDENCE, "Low"),
        "needs_human_review": _validate_bool_field(source.get("needs_human_review"), False),
        "summary": _validate_string_field(source.get("summary"), "Ticket analyzed successfully."),
        "tags": _validate_tags_field(source.get("tags")),
        "auto_reply": _validate_string_field(source.get("auto_reply"), "Thank you for contacting support."),
        "reason": _validate_string_field(source.get("reason"), "The ticket was analyzed with the best available inference."),
    }

    if not normalized_payload["tags"]:
        normalized_payload["tags"] = ["manual-review"]

    return normalized_payload


def validate_ticket_result(payload: Any) -> dict[str, Any]:
    """Return a validated ticket result or a safe fallback object if the payload is malformed."""
    try:
        if isinstance(payload, str):
            parsed_payload = json.loads(payload)
        else:
            parsed_payload = payload

        return normalize_ticket_result(parsed_payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return fallback_ticket_result()


def normalize_reply_result(payload: Any) -> dict[str, Any]:
    """Validate and normalize a reply-generation response."""
    source = _ensure_object(payload)

    return {
        "auto_reply": _validate_string_field(source.get("auto_reply"), "Thank you for contacting support."),
        "tone": _validate_enum_field(source.get("tone"), {"Professional", "Empathetic", "Supportive"}, "Professional"),
        "length": _validate_enum_field(source.get("length"), {"Short", "Medium", "Long"}, "Medium"),
    }


def validate_reply_result(payload: Any) -> dict[str, Any]:
    """Return a validated reply response or a safe fallback object if malformed."""
    try:
        if isinstance(payload, str):
            parsed_payload = json.loads(payload)
        else:
            parsed_payload = payload

        return normalize_reply_result(parsed_payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return fallback_reply_result()


def normalize_insights_result(payload: Any) -> dict[str, Any]:
    """Validate and normalize a weekly insights response."""
    source = _ensure_object(payload)

    return {
        "summary": _validate_string_field(source.get("summary"), "Weekly insights generated successfully."),
        "top_categories": _validate_tags_field(source.get("top_categories")),
        "top_priorities": _validate_tags_field(source.get("top_priorities")),
        "recurring_issues": _validate_tags_field(source.get("recurring_issues")),
        "recommended_actions": _validate_tags_field(source.get("recommended_actions")),
    }


def validate_insights_result(payload: Any) -> dict[str, Any]:
    """Return a validated weekly insights response or a safe fallback object if malformed."""
    try:
        if isinstance(payload, str):
            parsed_payload = json.loads(payload)
        else:
            parsed_payload = payload

        return normalize_insights_result(parsed_payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return fallback_insights_result()


def fallback_ticket_result() -> dict[str, Any]:
    """Provide a conservative fallback for any malformed ticket-routing response."""
    return {
        "category": "General Inquiry",
        "priority": "Medium",
        "assigned_team": "Customer Success",
        "sentiment": "Neutral",
        "confidence": "Low",
        "needs_human_review": True,
        "summary": "The ticket could not be confidently classified automatically.",
        "tags": ["manual-review"],
        "auto_reply": "Thank you for contacting support. A support specialist will review your request shortly.",
        "reason": "The AI output was invalid or incomplete, so the system fell back to a safe manual-review response.",
    }


def fallback_reply_result() -> dict[str, Any]:
    """Provide a safe fallback for any malformed reply-generation response."""
    return {
        "auto_reply": "Thank you for contacting support. We are reviewing your request and will follow up soon.",
        "tone": "Professional",
        "length": "Medium",
    }


def fallback_insights_result() -> dict[str, Any]:
    """Provide a safe fallback for any malformed weekly insights response."""
    return {
        "summary": "Weekly insights could not be generated automatically.",
        "top_categories": [],
        "top_priorities": [],
        "recurring_issues": [],
        "recommended_actions": [],
    }

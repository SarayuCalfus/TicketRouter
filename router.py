from __future__ import annotations

import json
import logging
import os
from typing import TYPE_CHECKING, Any, Iterable, Sequence

from dotenv import load_dotenv

if TYPE_CHECKING:
    from openai import OpenAI

try:
    from openai import OpenAI as OpenAIRuntime, OpenAIError
except ImportError:  # pragma: no cover - handled at runtime
    OpenAIRuntime = None
    OpenAIError = Exception

try:
    from database.crud import create_ticket
    from database.db import SessionLocal
except Exception:  # pragma: no cover - handled at runtime
    create_ticket = None
    SessionLocal = None

from prompts import (
    BATCH_PROCESSING_PROMPT,
    REPLY_GENERATION_PROMPT,
    SYSTEM_PROMPT,
    TICKET_ROUTING_PROMPT,
    WEEKLY_INSIGHTS_PROMPT,
)


load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
DEFAULT_TEMPERATURE = 0.2


def _get_client() -> OpenAI:
    if OpenAIRuntime is None:
        raise RuntimeError(
            "The 'openai' package is required to use router.py. Install it from requirements.txt."
        )

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not configured. Add it to your environment or .env file."
        )

    return OpenAIRuntime(api_key=api_key)


def _call_openai(prompt: str, *, system_prompt: str = SYSTEM_PROMPT) -> str:
    client = _get_client()
    model_name = os.getenv("OPENAI_MODEL", DEFAULT_MODEL)

    response = client.chat.completions.create(
        model=model_name,
        temperature=DEFAULT_TEMPERATURE,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("OpenAI returned an empty response.")

    return content.strip()


def _extract_json_payload(raw_text: str) -> Any:
    cleaned = raw_text.strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start_index = cleaned.find("{")
    end_index = cleaned.rfind("}")

    if start_index != -1 and end_index != -1 and end_index > start_index:
        cleaned = cleaned[start_index : end_index + 1]

    return json.loads(cleaned)


def _normalize_ticket_result(payload: Any) -> dict[str, Any]:
    ticket_payload = payload if isinstance(payload, dict) else {}

    category = str(ticket_payload.get("category") or "General Inquiry")
    priority = str(ticket_payload.get("priority") or "Medium")
    assigned_team = str(ticket_payload.get("assigned_team") or "Customer Success")
    sentiment = str(ticket_payload.get("sentiment") or "Neutral")
    confidence = str(ticket_payload.get("confidence") or "Low")
    needs_human_review = bool(ticket_payload.get("needs_human_review", False))
    summary = str(ticket_payload.get("summary") or "Ticket analyzed successfully.")
    tags = ticket_payload.get("tags")
    auto_reply = str(ticket_payload.get("auto_reply") or "Thank you for contacting support.")
    reason = str(ticket_payload.get("reason") or "The ticket was analyzed with the best available inference.")

    if not isinstance(tags, list):
        tags = []

    normalized_priority = priority if priority in {"Low", "Medium", "High", "Urgent"} else "Medium"
    normalized_confidence = confidence if confidence in {"High", "Medium", "Low"} else "Low"
    normalized_sentiment = (
        sentiment
        if sentiment in {"Positive", "Neutral", "Negative", "Frustrated"}
        else "Neutral"
    )

    return {
        "category": category,
        "priority": normalized_priority,
        "assigned_team": assigned_team,
        "sentiment": normalized_sentiment,
        "confidence": normalized_confidence,
        "needs_human_review": needs_human_review,
        "summary": summary,
        "tags": [str(tag) for tag in tags if str(tag).strip()],
        "auto_reply": auto_reply,
        "reason": reason,
    }


def _normalize_insight_result(payload: Any) -> dict[str, Any]:
    insight_payload = payload if isinstance(payload, dict) else {}

    return {
        "summary": str(insight_payload.get("summary") or "Weekly insights generated successfully."),
        "top_categories": _ensure_string_list(insight_payload.get("top_categories")),
        "top_priorities": _ensure_string_list(insight_payload.get("top_priorities")),
        "recurring_issues": _ensure_string_list(insight_payload.get("recurring_issues")),
        "recommended_actions": _ensure_string_list(insight_payload.get("recommended_actions")),
    }


def _normalize_reply_result(payload: Any) -> dict[str, Any]:
    reply_payload = payload if isinstance(payload, dict) else {}

    return {
        "auto_reply": str(reply_payload.get("auto_reply") or "Thank you for contacting support."),
        "tone": str(reply_payload.get("tone") or "Professional"),
        "length": str(reply_payload.get("length") or "Medium"),
    }


def _ensure_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str):
        return [value]
    return []


def _fallback_ticket_result(ticket_text: str) -> dict[str, Any]:
    return {
        "category": "General Inquiry",
        "priority": "Medium",
        "assigned_team": "Customer Success",
        "sentiment": "Neutral",
        "confidence": "Low",
        "needs_human_review": True,
        "summary": "The ticket could not be confidently classified automatically.",
        "tags": ["manual-review"],
        "auto_reply": "Thanks for reaching out. A support specialist will review your request shortly.",
        "reason": f"The AI request was incomplete or invalid for the ticket: {ticket_text[:120]}",
    }


def _persist_ticket_to_database(ticket_text: str, validated_payload: dict[str, Any]) -> None:
    """Best-effort save of a successfully classified ticket to PostgreSQL.

    Database availability is not guaranteed yet, so any failure here is logged and
    swallowed rather than raised, ensuring ticket routing keeps working regardless.
    """
    if SessionLocal is None or create_ticket is None:
        logger.warning("Database layer is unavailable; skipping database save for routed ticket.")
        return

    db = None
    try:
        db = SessionLocal()
        create_ticket(db, {"ticket_text": ticket_text, **validated_payload})
    except Exception:  # pragma: no cover - safety net, must never crash ticket routing
        logger.exception("Failed to save routed ticket to the database.")
    finally:
        if db is not None:
            db.close()


def route_ticket(ticket_text: str) -> dict[str, Any]:
    """Route a single support ticket through the OpenAI workflow and return validated JSON."""
    if not ticket_text or not str(ticket_text).strip():
        return _fallback_ticket_result("")

    stripped_ticket_text = ticket_text.strip()
    prompt = TICKET_ROUTING_PROMPT.format(ticket_text=stripped_ticket_text)

    try:
        raw_output = _call_openai(prompt)
        parsed_payload = _extract_json_payload(raw_output)
        validated_payload = _normalize_ticket_result(parsed_payload)
        _persist_ticket_to_database(stripped_ticket_text, validated_payload)
        return validated_payload
    except (OpenAIError, ValueError, json.JSONDecodeError, TypeError):
        return _fallback_ticket_result(ticket_text)


def generate_weekly_insights(weekly_data: Any) -> dict[str, Any]:
    """Generate high-level weekly support insights from ticket data."""
    if isinstance(weekly_data, dict):
        prompt_payload = json.dumps(weekly_data, ensure_ascii=False)
    else:
        prompt_payload = str(weekly_data)

    prompt = WEEKLY_INSIGHTS_PROMPT.format(weekly_data=prompt_payload)

    try:
        raw_output = _call_openai(prompt)
        parsed_payload = _extract_json_payload(raw_output)
        return _normalize_insight_result(parsed_payload)
    except (OpenAIError, ValueError, json.JSONDecodeError, TypeError):
        return {
            "summary": "Weekly insights could not be generated automatically.",
            "top_categories": [],
            "top_priorities": [],
            "recurring_issues": [],
            "recommended_actions": [],
        }


def process_batch_tickets(ticket_batch: Sequence[str]) -> list[dict[str, Any]]:
    """Process a batch of support tickets and return one validated JSON result per ticket."""
    normalized_batch = [str(ticket).strip() for ticket in ticket_batch if str(ticket).strip()]
    if not normalized_batch:
        return []

    prompt_payload = json.dumps(normalized_batch, ensure_ascii=False)
    prompt = BATCH_PROCESSING_PROMPT.format(ticket_batch_json=prompt_payload)

    try:
        raw_output = _call_openai(prompt)
        parsed_payload = _extract_json_payload(raw_output)

        if isinstance(parsed_payload, list):
            return [_normalize_ticket_result(item) for item in parsed_payload]
    except (OpenAIError, ValueError, json.JSONDecodeError, TypeError):
        pass

    return [route_ticket(ticket) for ticket in normalized_batch]


def generate_reply(ticket_context: str) -> dict[str, Any]:
    """Generate a customer-facing support reply in structured JSON form."""
    if not ticket_context or not str(ticket_context).strip():
        return {
            "auto_reply": "Thank you for contacting support. A specialist will review your issue shortly.",
            "tone": "Professional",
            "length": "Medium",
        }

    prompt = REPLY_GENERATION_PROMPT.format(ticket_context=ticket_context.strip())

    try:
        raw_output = _call_openai(prompt)
        parsed_payload = _extract_json_payload(raw_output)
        return _normalize_reply_result(parsed_payload)
    except (OpenAIError, ValueError, json.JSONDecodeError, TypeError):
        return {
            "auto_reply": "Thank you for contacting support. We are reviewing your request and will follow up soon.",
            "tone": "Professional",
            "length": "Medium",
        }

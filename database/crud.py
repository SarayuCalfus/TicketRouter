from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from database.models import Ticket

logger = logging.getLogger(__name__)


def _normalize_tags(tags_value: Any) -> str:
    """Convert a list or string of tags into the comma-separated text stored on Ticket.tags."""
    if isinstance(tags_value, list):
        return ", ".join(str(tag) for tag in tags_value if str(tag).strip())
    if isinstance(tags_value, str):
        return tags_value
    return ""


def create_ticket(db: Session, ticket_data: dict[str, Any]) -> Ticket | None:
    """Persist a routed ticket to the database and return the saved row, or None on failure."""
    ticket = Ticket(
        ticket_text=str(ticket_data.get("ticket_text") or ""),
        category=str(ticket_data.get("category") or "General Inquiry"),
        priority=str(ticket_data.get("priority") or "Medium"),
        assigned_team=str(ticket_data.get("assigned_team") or "Customer Success"),
        sentiment=str(ticket_data.get("sentiment") or "Neutral"),
        confidence=str(ticket_data.get("confidence") or "Low"),
        needs_human_review=bool(ticket_data.get("needs_human_review", False)),
        summary=str(ticket_data.get("summary") or ""),
        tags=_normalize_tags(ticket_data.get("tags", [])),
        auto_reply=str(ticket_data.get("auto_reply") or ""),
        reason=str(ticket_data.get("reason") or ""),
    )

    try:
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        return ticket
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to save ticket to the database.")
        return None


def get_all_tickets(db: Session) -> list[Ticket]:
    """Return all tickets ordered by most recently created first, or an empty list on failure."""
    try:
        return db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to load tickets from the database.")
        return []


def get_ticket_by_id(db: Session, ticket_id: int) -> Ticket | None:
    """Return a single ticket by its primary key, or None if it does not exist or the query fails."""
    try:
        return db.get(Ticket, ticket_id)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to load ticket %s from the database.", ticket_id)
        return None

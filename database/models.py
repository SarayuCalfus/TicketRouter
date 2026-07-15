from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from database.db import Base


class Ticket(Base):
    """A single AI-processed support ticket, mirroring the fields routed by router.py."""

    __tablename__ = "tickets"

    ticket_id: int = Column(Integer, primary_key=True, autoincrement=True)
    ticket_text: str = Column(Text, nullable=False)
    category: str = Column(String(100), nullable=False)
    priority: str = Column(String(50), nullable=False)
    assigned_team: str = Column(String(100), nullable=False)
    sentiment: str = Column(String(50), nullable=False)
    confidence: str = Column(String(50), nullable=False)
    needs_human_review: bool = Column(Boolean, nullable=False, default=False)
    summary: str = Column(Text, nullable=True)
    tags: str = Column(Text, nullable=True)
    auto_reply: str = Column(Text, nullable=True)
    reason: str = Column(Text, nullable=True)
    created_at: datetime = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

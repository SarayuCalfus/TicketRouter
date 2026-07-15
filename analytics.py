from __future__ import annotations

from collections import Counter
from typing import Any

import pandas as pd


def _ensure_dataframe(data: Any) -> pd.DataFrame:
    if isinstance(data, pd.DataFrame):
        return data.copy()
    if isinstance(data, list):
        return pd.DataFrame(data)
    if isinstance(data, dict):
        return pd.DataFrame([data])
    raise TypeError("Unsupported data type for analytics computation.")


def total_tickets(data: Any) -> int:
    """Return the total number of ticket records in the dataset."""
    df = _ensure_dataframe(data)
    return int(len(df))


def high_priority_tickets(data: Any) -> int:
    """Return the number of tickets marked as High or Urgent priority."""
    df = _ensure_dataframe(data)
    if "priority" not in df.columns:
        return 0
    high_mask = df["priority"].astype(str).isin({"High", "Urgent"})
    return int(high_mask.sum())


def average_confidence(data: Any) -> float:
    """Return the mean confidence score across tickets where confidence is available."""
    df = _ensure_dataframe(data)
    if "confidence" not in df.columns:
        return 0.0

    mapping = {"High": 1.0, "Medium": 0.6, "Low": 0.3}
    confidence_values = df["confidence"].astype(str).map(mapping)
    return float(confidence_values.mean()) if confidence_values.notna().any() else 0.0


def needs_human_review_count(data: Any) -> int:
    """Return the number of tickets that require human review."""
    df = _ensure_dataframe(data)
    if "needs_human_review" not in df.columns:
        return 0
    return int(df["needs_human_review"].astype(str).str.lower().isin({"true", "1", "yes"}).sum())


def category_distribution(data: Any) -> dict[str, int]:
    """Return category counts for dashboard charts."""
    df = _ensure_dataframe(data)
    if "category" not in df.columns:
        return {}
    return dict(Counter(df["category"].astype(str).fillna("General Inquiry")))


def priority_distribution(data: Any) -> dict[str, int]:
    """Return priority counts for dashboard charts."""
    df = _ensure_dataframe(data)
    if "priority" not in df.columns:
        return {}
    return dict(Counter(df["priority"].astype(str).fillna("Medium")))


def sentiment_distribution(data: Any) -> dict[str, int]:
    """Return sentiment counts for dashboard charts."""
    df = _ensure_dataframe(data)
    if "sentiment" not in df.columns:
        return {}
    return dict(Counter(df["sentiment"].astype(str).fillna("Neutral")))


def weekly_ticket_counts(data: Any) -> pd.DataFrame:
    """Aggregate ticket counts by week for trend analysis."""
    df = _ensure_dataframe(data)
    if df.empty:
        return pd.DataFrame(columns=["week", "ticket_count"])

    if "created_at" not in df.columns:
        df["created_at"] = pd.Timestamp.now().normalize()

    df = df.copy()
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.dropna(subset=["created_at"])

    if df.empty:
        return pd.DataFrame(columns=["week", "ticket_count"])

    weekly_counts = df.groupby(df["created_at"].dt.to_period("W")).size().reset_index(name="ticket_count")
    weekly_counts.columns = ["week", "ticket_count"]
    weekly_counts["week"] = weekly_counts["week"].astype(str)
    return weekly_counts


def weekly_summary_insights(data: Any) -> dict[str, Any]:
    """Generate a compact business-ready summary of the week's ticket activity."""
    df = _ensure_dataframe(data)
    if df.empty:
        return {
            "summary": "No ticket activity recorded yet.",
            "top_categories": [],
            "top_priorities": [],
            "recurring_issues": [],
            "recommended_actions": [],
        }

    category_counts = category_distribution(df)
    priority_counts = priority_distribution(df)
    sentiment_counts = sentiment_distribution(df)

    top_categories = [item[0] for item in sorted(category_counts.items(), key=lambda entry: entry[1], reverse=True)[:3]]
    top_priorities = [item[0] for item in sorted(priority_counts.items(), key=lambda entry: entry[1], reverse=True)[:3]]
    recurring_issues = [item[0] for item in sorted(sentiment_counts.items(), key=lambda entry: entry[1], reverse=True)[:3]]

    summary = (
        f"Processed {total_tickets(df)} tickets with {high_priority_tickets(df)} high-priority items and "
        f"{needs_human_review_count(df)} requiring manual review."
    )

    recommended_actions = []
    if high_priority_tickets(df) > 0:
        recommended_actions.append("Escalate high-priority tickets for faster triage.")
    if needs_human_review_count(df) > 0:
        recommended_actions.append("Route manual-review tickets to support specialists.")
    if top_categories:
        recommended_actions.append(f"Focus on recurring category trends in {', '.join(top_categories)}.")

    return {
        "summary": summary,
        "top_categories": top_categories,
        "top_priorities": top_priorities,
        "recurring_issues": recurring_issues,
        "recommended_actions": recommended_actions,
    }


def analytics_snapshot(data: Any) -> dict[str, Any]:
    """Return a complete analytics snapshot for the dashboard."""
    df = _ensure_dataframe(data)

    return {
        "total_tickets": total_tickets(df),
        "high_priority_tickets": high_priority_tickets(df),
        "average_confidence": average_confidence(df),
        "needs_human_review": needs_human_review_count(df),
        "category_distribution": category_distribution(df),
        "priority_distribution": priority_distribution(df),
        "sentiment_distribution": sentiment_distribution(df),
        "weekly_counts": weekly_ticket_counts(df),
        "weekly_insights": weekly_summary_insights(df),
    }

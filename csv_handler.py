from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


logger = logging.getLogger(__name__)


DATA_DIR = Path(__file__).resolve().parent / "data"
HISTORY_CSV_PATH = DATA_DIR / "ticket_history.csv"
DEFAULT_HISTORY_COLUMNS = [
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


def ensure_data_directory() -> None:
    """Ensure the data folder exists before writing CSV or JSON files."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _empty_history_dataframe() -> pd.DataFrame:
    """Return a consistently shaped empty DataFrame for ticket history operations."""
    return pd.DataFrame(columns=DEFAULT_HISTORY_COLUMNS)


def _safe_read_csv(input_path: str | Path) -> pd.DataFrame:
    """Read a CSV file safely and return an empty DataFrame if the file is missing or blank."""
    input_path = Path(input_path)

    if not input_path.exists():
        logger.info("CSV file not found at %s. Returning an empty DataFrame.", input_path)
        return _empty_history_dataframe()

    try:
        df = pd.read_csv(input_path)
    except pd.errors.EmptyDataError:
        logger.info("CSV file at %s is empty. Returning an empty DataFrame.", input_path)
        return _empty_history_dataframe()

    if df.empty:
        logger.info("CSV file at %s contains no rows. Returning an empty DataFrame.", input_path)
        return _empty_history_dataframe()

    return df


def _normalize_ticket_record(record: dict[str, Any], ticket_id: int | None = None) -> dict[str, Any]:
    tags_value = record.get("tags", [])
    if isinstance(tags_value, list):
        tags_text = ", ".join(str(tag) for tag in tags_value if str(tag).strip())
    elif isinstance(tags_value, str):
        tags_text = tags_value
    else:
        tags_text = ""

    return {
        "ticket_id": ticket_id or "",
        "ticket_text": str(record.get("ticket_text") or ""),
        "category": str(record.get("category") or "General Inquiry"),
        "priority": str(record.get("priority") or "Medium"),
        "assigned_team": str(record.get("assigned_team") or "Customer Success"),
        "sentiment": str(record.get("sentiment") or "Neutral"),
        "confidence": str(record.get("confidence") or "Low"),
        "needs_human_review": bool(record.get("needs_human_review", False)),
        "summary": str(record.get("summary") or ""),
        "tags": tags_text,
        "auto_reply": str(record.get("auto_reply") or ""),
        "reason": str(record.get("reason") or ""),
    }


def _ensure_history_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Guarantee the standard history columns are present, backfilling ticket_id when it is missing.

    Older ticket_history.csv files were written before ticket_id existed in the schema, so any
    rows lacking a usable id are assigned a generated sequential id continuing after the highest
    real id already present, keeping generated and real ids consistent and collision-free.
    """
    if df.empty:
        return df.reindex(columns=DEFAULT_HISTORY_COLUMNS)

    df = df.reindex(columns=DEFAULT_HISTORY_COLUMNS, fill_value="")

    ticket_id_numeric = pd.to_numeric(df["ticket_id"], errors="coerce")
    missing_mask = ticket_id_numeric.isna()
    if missing_mask.any():
        max_existing_id = ticket_id_numeric.max()
        next_id = int(max_existing_id) + 1 if pd.notna(max_existing_id) else 1
        generated_ids = range(next_id, next_id + int(missing_mask.sum()))
        ticket_id_numeric.loc[missing_mask] = list(generated_ids)

    df["ticket_id"] = ticket_id_numeric.astype(int)
    return df


def save_ticket_history(records: Iterable[dict[str, Any]], output_path: str | Path = HISTORY_CSV_PATH) -> Path:
    """Save a collection of routed tickets to the ticket history CSV file."""
    ensure_data_directory()
    output_path = Path(output_path)

    # Normalize any existing rows first so ticket_id is always numeric and gap-free, whether the
    # file already has real ids, is missing the column entirely, or predates the ticket_id schema.
    existing_df = _ensure_history_schema(_safe_read_csv(output_path)) if output_path.exists() else _empty_history_dataframe()

    if not existing_df.empty:
        max_id = pd.to_numeric(existing_df["ticket_id"], errors="coerce").max()
        next_id = int(max_id) + 1 if pd.notna(max_id) else 1
    else:
        next_id = 1

    # Normalize new records with auto-incrementing ticket_id continuing from the existing max
    normalized_records = []
    for record in records:
        normalized = _normalize_ticket_record(record, ticket_id=next_id)
        normalized_records.append(normalized)
        next_id += 1

    new_df = pd.DataFrame(normalized_records, columns=DEFAULT_HISTORY_COLUMNS)

    if not existing_df.empty:
        combined_df = pd.concat([existing_df, new_df], ignore_index=True, sort=False)
        combined_df = combined_df.reindex(columns=DEFAULT_HISTORY_COLUMNS)
        combined_df.to_csv(output_path, index=False)
    else:
        new_df.to_csv(output_path, index=False)

    return output_path


def load_ticket_history(input_path: str | Path = HISTORY_CSV_PATH) -> pd.DataFrame:
    """Load ticket history from a CSV file into a pandas DataFrame with a normalized schema."""
    return _ensure_history_schema(_safe_read_csv(input_path))


def import_ticket_csv(input_path: str | Path) -> list[dict[str, Any]]:
    """Import a CSV file containing ticket rows and return them as a list of dictionaries."""
    input_path = Path(input_path)
    df = _safe_read_csv(input_path)

    if df.empty:
        logger.info("No ticket rows were available to import from %s.", input_path)
        return []

    return df.to_dict(orient="records")


def process_imported_tickets(ticket_rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize imported ticket rows into the standard routed-ticket structure."""
    processed_rows: list[dict[str, Any]] = []

    for row in ticket_rows:
        processed_rows.append(_normalize_ticket_record(row, ticket_id=None))

    return processed_rows


def export_processed_tickets(records: Iterable[dict[str, Any]], output_path: str | Path) -> Path:
    """Export processed tickets to a CSV file using the standard history schema."""
    ensure_data_directory()
    output_path = Path(output_path)

    records_list = list(records)
    normalized_records = []
    for ticket_id, record in enumerate(records_list, start=1):
        normalized = _normalize_ticket_record(record, ticket_id=ticket_id)
        normalized_records.append(normalized)
    
    df = pd.DataFrame(normalized_records, columns=DEFAULT_HISTORY_COLUMNS)
    df.to_csv(output_path, index=False)
    return output_path


def export_processed_json(records: Iterable[dict[str, Any]], output_path: str | Path) -> Path:
    """Export processed tickets to a JSON file."""
    ensure_data_directory()
    output_path = Path(output_path)

    records_list = list(records)
    normalized_records = []
    for ticket_id, record in enumerate(records_list, start=1):
        normalized = _normalize_ticket_record(record, ticket_id=ticket_id)
        normalized_records.append(normalized)
    
    with output_path.open("w", encoding="utf-8") as file_handle:
        json.dump(normalized_records, file_handle, indent=2, ensure_ascii=False)

    return output_path


def append_ticket_record(record: dict[str, Any], output_path: str | Path = HISTORY_CSV_PATH) -> Path:
    """Append a single routed ticket record to the ticket history CSV file."""
    return save_ticket_history([record], output_path=output_path)


def batch_import_and_save(input_path: str | Path, output_path: str | Path = HISTORY_CSV_PATH) -> list[dict[str, Any]]:
    """Import a CSV file, normalize records, and persist them into the ticket history file."""
    tickets = import_ticket_csv(input_path)
    processed_tickets = process_imported_tickets(tickets)
    save_ticket_history(processed_tickets, output_path=output_path)
    return processed_tickets

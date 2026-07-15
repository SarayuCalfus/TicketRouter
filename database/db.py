from __future__ import annotations

import os
from collections.abc import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

load_dotenv()

DATABASE_URL: str | None = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Define it in your .env file, e.g. "
        "DATABASE_URL=postgresql://user:password@localhost:5432/ticketrouter"
    )

try:
    engine: Engine = create_engine(DATABASE_URL)
except ArgumentError as exc:
    raise RuntimeError(f"DATABASE_URL is not a valid SQLAlchemy connection string: {exc}") from exc
except SQLAlchemyError as exc:
    raise RuntimeError(f"Failed to create the database engine: {exc}") from exc

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for a single unit of work, closing it when the caller is done."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

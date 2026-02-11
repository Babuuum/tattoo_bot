from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type
from datetime import time as time_type

from sqlalchemy import Date, DateTime, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from infra.db.base import Base


class BlockedSlot(Base):
    __tablename__ = "blocked_slot"

    # Composite primary key: (date, time).
    date: Mapped[date_type] = mapped_column(Date, primary_key=True)
    time: Mapped[time_type] = mapped_column(Time, primary_key=True)
    reason: Mapped[str | None] = mapped_column(String(length=200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

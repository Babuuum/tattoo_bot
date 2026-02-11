from __future__ import annotations

from datetime import UTC, datetime
from datetime import date as date_type

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from infra.db.base import Base


class DayOff(Base):
    __tablename__ = "day_off"

    # Keep schema aligned with the ticket: key is the date itself.
    date: Mapped[date_type] = mapped_column(Date, primary_key=True)
    reason: Mapped[str | None] = mapped_column(String(length=200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

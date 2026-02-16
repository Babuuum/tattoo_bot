from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.db.base import Base

if TYPE_CHECKING:
    from .pricing_body_zone_coefficient import PricingBodyZoneCoefficient
    from .pricing_style_coefficient import PricingStyleCoefficient


class PricingConfig(Base):
    __tablename__ = "pricing_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    base_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rounding_policy: Mapped[str] = mapped_column(
        String(32), default="round", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    style_coefficients: Mapped[list[PricingStyleCoefficient]] = relationship(
        "PricingStyleCoefficient",
        back_populates="pricing_config",
        cascade="all, delete-orphan",
    )
    body_zone_coefficients: Mapped[list[PricingBodyZoneCoefficient]] = relationship(
        "PricingBodyZoneCoefficient",
        back_populates="pricing_config",
        cascade="all, delete-orphan",
    )

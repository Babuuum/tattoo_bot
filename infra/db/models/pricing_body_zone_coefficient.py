from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.db.base import Base

if TYPE_CHECKING:
    from .pricing_config import PricingConfig


class PricingBodyZoneCoefficient(Base):
    __tablename__ = "pricing_body_zone_coefficient"
    __table_args__ = (
        UniqueConstraint(
            "pricing_config_id",
            "body_zone",
            name="uq_pricing_body_zone_coefficient_config_zone",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pricing_config_id: Mapped[int] = mapped_column(
        ForeignKey("pricing_config.id", ondelete="CASCADE"), nullable=False
    )
    body_zone: Mapped[str] = mapped_column(String(50), nullable=False)
    coefficient: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    pricing_config: Mapped[PricingConfig] = relationship(
        "PricingConfig", back_populates="body_zone_coefficients"
    )

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.db.base import Base

if TYPE_CHECKING:
    from .pricing_config import PricingConfig
    from .style import Style


class PricingStyleCoefficient(Base):
    __tablename__ = "pricing_style_coefficient"
    __table_args__ = (
        UniqueConstraint(
            "pricing_config_id",
            "style_id",
            name="uq_pricing_style_coefficient_config_style",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    pricing_config_id: Mapped[int] = mapped_column(
        ForeignKey("pricing_config.id", ondelete="CASCADE"), nullable=False
    )
    style_id: Mapped[int] = mapped_column(ForeignKey("styles.id"), nullable=False)
    coefficient: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)

    pricing_config: Mapped[PricingConfig] = relationship(
        "PricingConfig", back_populates="style_coefficients"
    )
    style: Mapped[Style] = relationship("Style")

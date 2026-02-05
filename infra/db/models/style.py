from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.db.base import Base

if TYPE_CHECKING:
    from .tattoo import Tattoo


class Style(Base):
    __tablename__ = "styles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    multiplyer: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0)

    tattoos: Mapped[list[Tattoo]] = relationship("Tattoo", back_populates="style")

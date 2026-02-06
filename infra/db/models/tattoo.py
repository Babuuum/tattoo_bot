from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infra.db.base import Base

if TYPE_CHECKING:
    from .order import Order
    from .style import Style


class Tattoo(Base):
    __tablename__ = "tattoos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    style_id: Mapped[int] = mapped_column(ForeignKey("styles.id"), nullable=False)
    price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    views: Mapped[int] = mapped_column(Integer, default=0)
    photo_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    style: Mapped[Style] = relationship("Style", back_populates="tattoos")
    orders: Mapped[list[Order]] = relationship("Order", back_populates="tattoo")

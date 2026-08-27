"""Initial database models for the recovery foundation."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    """A customer whose payments may need recovery."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recovery_cases: Mapped[list["RecoveryCase"]] = relationship(back_populates="customer")


class RecoveryCase(Base):
    """A failed or at-risk payment case under recovery."""

    __tablename__ = "recovery_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="USD")
    status: Mapped[str] = mapped_column(String(64), default="open", index=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="recovery_cases")
    events: Mapped[list["Event"]] = relationship(back_populates="recovery_case")
    actions: Mapped[list["Action"]] = relationship(back_populates="recovery_case")


class Event(Base):
    """An observed event related to a recovery case."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recovery_case_id: Mapped[int] = mapped_column(
        ForeignKey("recovery_cases.id"), nullable=False, index=True
    )
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="events")


class Action(Base):
    """A recovery action taken for a case."""

    __tablename__ = "actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    recovery_case_id: Mapped[int] = mapped_column(
        ForeignKey("recovery_cases.id"), nullable=False, index=True
    )
    action_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), default="pending", index=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="actions")

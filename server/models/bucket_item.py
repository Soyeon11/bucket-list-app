"""
SQLAlchemy 2.0 ORM model for the bucket_items table.

Note: Supabase / PostgreSQL-specific types (enums, uuid) are mapped
to native SQLAlchemy types that produce compatible DDL.  The actual
enum types are created in migrations/001_initial_schema.sql.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BucketItem(Base):
    """Maps to the `bucket_items` table."""

    __tablename__ = "bucket_items"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), nullable=False, server_default="medium")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="active")
    last_recommended_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tags: Mapped[list["ItemTag"]] = relationship(
        "ItemTag", back_populates="item", cascade="all, delete-orphan", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<BucketItem id={self.id} title={self.title!r} status={self.status}>"


class ItemTag(Base):
    """Maps to the `item_tags` table (item ↔ tag many-to-many via join table)."""

    __tablename__ = "item_tags"

    item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bucket_items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Relationship back to BucketItem
    item: Mapped["BucketItem"] = relationship("BucketItem", back_populates="tags")

    def __repr__(self) -> str:
        return f"<ItemTag item_id={self.item_id} tag={self.tag!r}>"

"""SQLAlchemy models for the naive PDF to answer loop (spec 0001)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Declarative base for Atlas Postgres tables."""


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    content_type: Mapped[str] = mapped_column(String(128), nullable=False)
    byte_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    chunks: Mapped[list[Chunk]] = relationship(back_populates="document", cascade="all, delete-orphan")
    jobs: Mapped[list[Job]] = relationship(back_populates="document")


class Chunk(Base):
    __tablename__ = "chunks"
    __table_args__ = (UniqueConstraint("document_id", "ordinal", name="uq_chunks_document_ordinal"),)

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    document_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    embedding_model: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    document: Mapped[Document] = relationship(back_populates="chunks")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    type: Mapped[str] = mapped_column(String(64), nullable=False, default="ingest_document")
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    document_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    document: Mapped[Document] = relationship(back_populates="jobs")


class Ask(Base):
    __tablename__ = "asks"

    id: Mapped[Any] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    abstained: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    citations: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, server_default="[]")
    retrieved_chunk_ids: Mapped[list[Any]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"
    )
    model_name: Mapped[str] = mapped_column(String(256), nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    ask_documents: Mapped[list[AskDocument]] = relationship(
        back_populates="ask", cascade="all, delete-orphan"
    )


class AskDocument(Base):
    __tablename__ = "ask_documents"

    ask_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("asks.id", ondelete="CASCADE"), primary_key=True
    )
    document_id: Mapped[Any] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True
    )

    ask: Mapped[Ask] = relationship(back_populates="ask_documents")

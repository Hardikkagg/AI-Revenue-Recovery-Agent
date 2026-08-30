"""Pydantic schemas for LLM reasoning and customer message generation."""

from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field


class LLMGenerationResult(BaseModel):
    """Structured result of LLM reasoning and personalized message generation."""

    provider: str
    model: str
    reasoning: str
    customer_message: str | None = None
    fallback_used: bool = False
    fallback_reason: str | None = None

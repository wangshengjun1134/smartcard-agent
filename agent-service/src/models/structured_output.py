"""Structured output models for LLM responses.

This module provides Pydantic models for structured LLM output parsing.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class IntentOutput(BaseModel):
    """Intent classification output."""

    execution_intent: str = Field(
        description="Intent type: KNOWLEDGE_ONLY, REQUIRES_CARD, REQUIRES_APDU, REQUIRES_DYNAMIC_REASONING, REQUIRES_MULTI_STEP"
    )


class GoalOutput(BaseModel):
    """Goal planning output."""

    goal: str = Field(description="High-level goal name (e.g., read_imsi, discover_card)")
    confidence: float = Field(default=0.8, description="Confidence level 0-1")


class SkillDecision(BaseModel):
    """Skill decision output from think node."""

    skill_name: str = Field(description="Name of skill to execute")
    params: Dict[str, Any] = Field(default_factory=dict, description="Skill parameters")
    reasoning: str = Field(description="Why this skill was selected")
    confidence: float = Field(default=0.8, description="Confidence level")


class ObservationAnalysis(BaseModel):
    """Observation analysis output."""

    success: bool = Field(description="Whether the operation succeeded")
    need_retry: bool = Field(default=False, description="Whether to retry")
    need_rag: bool = Field(default=False, description="Whether RAG lookup needed")
    error_type: Optional[str] = Field(default=None, description="Error type if failed")
    next_step: str = Field(description="Recommended next step")


class FinalResponse(BaseModel):
    """Final response output."""

    response: str = Field(description="Response to user")
    success: bool = Field(description="Overall success")
    summary: str = Field(description="Brief summary of what was done")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations if any")
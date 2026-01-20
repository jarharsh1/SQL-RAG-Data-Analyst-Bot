"""
LangGraph Agent State Definition.

Defines the state schema for the agent workflow.
"""

from typing import TypedDict, Optional, List

from src.models.schemas import (
    AgentState,
    FinalResponse,
    GeneratedSQL,
    ParsedQuestion,
    QueryPlan,
    QueryRequest,
    QueryResult,
    RetrievedContext,
    ResultSummary,
    ValidatedSQL,
)


class AgentGraphState(TypedDict):
    """State passed between agent nodes."""

    # Input
    request: QueryRequest

    # Current state
    current_state: AgentState
    state_history: List[str]

    # Intermediate results
    parsed_question: Optional[ParsedQuestion]
    retrieved_context: Optional[RetrievedContext]
    query_plan: Optional[QueryPlan]
    generated_sql: Optional[GeneratedSQL]
    validated_sql: Optional[ValidatedSQL]
    query_result: Optional[QueryResult]
    result_summary: Optional[ResultSummary]

    # Output
    response: Optional[FinalResponse]

    # Error handling
    error: Optional[str]
    error_state: Optional[str]

    # Clarification
    needs_clarification: bool
    clarification_questions: List[str]

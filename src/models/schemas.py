"""
Pydantic schemas for data validation and serialization.
All data structures used throughout the application are defined here.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================


class QuestionIntent(str, Enum):
    """Type of user intent."""

    ANALYSIS = "analysis"  # Requires SQL execution
    DEFINITION = "definition"  # Lookup only, no SQL
    COMPARISON = "comparison"  # Compare metrics/dimensions
    TREND = "trend"  # Time-based analysis
    AGGREGATION = "aggregation"  # Sum, avg, count, etc.


class AgentState(str, Enum):
    """Agent workflow states."""

    INTERPRET = "interpret"
    RETRIEVE = "retrieve"
    PLAN = "plan"
    GENERATE_SQL = "generate_sql"
    VALIDATE = "validate"
    EXECUTE = "execute"
    SUMMARIZE = "summarize"
    RESPOND = "respond"
    AUDIT = "audit"
    ASK_CLARIFICATION = "ask_clarification"
    ERROR_HANDLER = "error_handler"
    END = "end"


class SQLOperation(str, Enum):
    """Allowed SQL operations."""

    SELECT = "SELECT"


class ValidationStatus(str, Enum):
    """SQL validation result."""

    VALID = "valid"
    INVALID = "invalid"
    NEEDS_REWRITE = "needs_rewrite"


# ============================================================================
# Request/Response Models
# ============================================================================


class QueryRequest(BaseModel):
    """User query request."""

    question: str = Field(..., description="Natural language question", min_length=3)
    user_id: str = Field(..., description="User identifier for audit")
    show_sql: bool = Field(default=True, description="Include SQL in response")
    show_transparency: bool = Field(default=True, description="Include transparency info")
    export_format: Optional[str] = Field(default=None, description="Optional: csv, json")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        """Ensure question is not empty or whitespace."""
        if not v or not v.strip():
            raise ValueError("Question cannot be empty")
        return v.strip()


class Citation(BaseModel):
    """Source citation for retrieved context."""

    source: str = Field(..., description="Source document/file")
    location: Optional[str] = Field(None, description="Line number or section")
    content: str = Field(..., description="Relevant excerpt")
    relevance_score: float = Field(..., ge=0.0, le=1.0)


class MetricDefinition(BaseModel):
    """Business metric definition."""

    name: str = Field(..., description="Metric name")
    formula: str = Field(..., description="Calculation formula")
    source_table: str = Field(..., description="Primary table")
    grain: str = Field(..., description="Aggregation grain")
    filters: List[str] = Field(default_factory=list, description="Default filters")
    citation: Optional[Citation] = None


class TableMetadata(BaseModel):
    """Database table metadata."""

    table_name: str
    columns: List[str]
    primary_key: Optional[str] = None
    foreign_keys: Dict[str, str] = Field(default_factory=dict)  # column -> referenced_table
    description: Optional[str] = None


class BusinessRule(BaseModel):
    """Business logic rule."""

    name: str
    description: str
    sql_filter: Optional[str] = None
    applies_to_tables: List[str] = Field(default_factory=list)


# ============================================================================
# Agent State Models
# ============================================================================


class ParsedQuestion(BaseModel):
    """Interpreted user question."""

    original_question: str
    intent: QuestionIntent
    metrics: List[str] = Field(default_factory=list, description="Identified metrics")
    dimensions: List[str] = Field(default_factory=list, description="Group by dimensions")
    filters: List[str] = Field(default_factory=list, description="WHERE conditions")
    time_range: Optional[Dict[str, str]] = Field(
        None, description="Start/end dates if applicable"
    )
    requires_sql: bool = Field(default=True, description="Whether SQL execution is needed")
    ambiguous: bool = Field(default=False, description="Needs clarification")
    clarification_questions: List[str] = Field(
        default_factory=list, description="Questions to ask user"
    )


class RetrievedContext(BaseModel):
    """Context retrieved from RAG."""

    metric_definitions: List[MetricDefinition] = Field(default_factory=list)
    table_metadata: List[TableMetadata] = Field(default_factory=list)
    business_rules: List[BusinessRule] = Field(default_factory=list)
    example_queries: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)


class QueryPlan(BaseModel):
    """Execution plan for the query."""

    strategy: str = Field(..., description="Query strategy description")
    required_tables: List[str] = Field(default_factory=list)
    required_joins: List[Dict[str, str]] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=list)
    filters: List[str] = Field(default_factory=list)
    business_logic_applied: List[str] = Field(default_factory=list)


class GeneratedSQL(BaseModel):
    """Generated SQL query."""

    sql: str = Field(..., description="SQL query string")
    tables_used: List[str] = Field(default_factory=list)
    definitions_applied: List[str] = Field(default_factory=list, description="Metric names")
    assumptions: List[str] = Field(
        default_factory=list, description="Assumptions made during generation"
    )
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0)


class ValidationResult(BaseModel):
    """SQL validation result."""

    status: ValidationStatus
    is_safe: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    checks_performed: Dict[str, bool] = Field(default_factory=dict)
    rewrite_suggestion: Optional[str] = None


class ValidatedSQL(BaseModel):
    """Validated and safe SQL."""

    sql: str = Field(..., description="Validated SQL with safety limits")
    original_sql: str = Field(..., description="SQL before validation modifications")
    validation_result: ValidationResult
    safety_limits: Dict[str, Any] = Field(
        default_factory=dict, description="Applied limits (timeout, rows, etc.)"
    )


class QueryResult(BaseModel):
    """SQL execution result."""

    data: List[Dict[str, Any]] = Field(default_factory=list, description="Result rows")
    columns: List[str] = Field(default_factory=list)
    row_count: int = Field(default=0, ge=0)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    truncated: bool = Field(default=False, description="Results were truncated")
    error: Optional[str] = None


class ResultSummary(BaseModel):
    """Human-readable summary of results."""

    summary: str = Field(..., description="Plain English summary")
    insights: List[str] = Field(default_factory=list, description="Key findings")
    data_formatted: Optional[Dict[str, Any]] = Field(
        None, description="Formatted data for presentation"
    )


class TransparencyInfo(BaseModel):
    """Transparency and explainability information."""

    sql_executed: str
    definitions_used: List[MetricDefinition] = Field(default_factory=list)
    tables_accessed: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    business_rules_applied: List[str] = Field(default_factory=list)


class QueryMetadata(BaseModel):
    """Query execution metadata."""

    execution_time_ms: float
    rows_returned: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_state_history: List[str] = Field(
        default_factory=list, description="State transitions"
    )


class SuggestedAction(BaseModel):
    """Suggested user action."""

    type: str = Field(..., description="Action type (export_csv, chart, etc.)")
    label: str = Field(..., description="Display label")
    description: Optional[str] = None
    requires_confirmation: bool = Field(default=True)


class FinalResponse(BaseModel):
    """Complete response to user."""

    answer: str = Field(..., description="Natural language answer")
    transparency: Optional[TransparencyInfo] = None
    data: Optional[QueryResult] = None
    metadata: QueryMetadata
    suggested_actions: List[SuggestedAction] = Field(default_factory=list)
    error: Optional[str] = None


# ============================================================================
# Agent Internal State
# ============================================================================


class AgentWorkflowState(BaseModel):
    """Complete agent state for LangGraph."""

    # Input
    request: QueryRequest

    # Processing
    current_state: AgentState = Field(default=AgentState.INTERPRET)
    state_history: List[str] = Field(default_factory=list)

    # Intermediate results
    parsed_question: Optional[ParsedQuestion] = None
    retrieved_context: Optional[RetrievedContext] = None
    query_plan: Optional[QueryPlan] = None
    generated_sql: Optional[GeneratedSQL] = None
    validated_sql: Optional[ValidatedSQL] = None
    query_result: Optional[QueryResult] = None
    result_summary: Optional[ResultSummary] = None

    # Output
    response: Optional[FinalResponse] = None

    # Error handling
    error: Optional[str] = None
    error_state: Optional[str] = None

    # Clarification
    needs_clarification: bool = Field(default=False)
    clarification_questions: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# Audit Models
# ============================================================================


class AuditLogEntry(BaseModel):
    """Audit log entry for a query."""

    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: str
    question: str
    sql_executed: Optional[str] = None
    tables_accessed: List[str] = Field(default_factory=list)
    rows_returned: int = Field(default=0)
    execution_time_ms: float = Field(default=0.0)
    success: bool
    error: Optional[str] = None
    actions_taken: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ============================================================================
# Configuration Models
# ============================================================================


class SafetyConfig(BaseModel):
    """Safety and validation configuration."""

    max_result_rows: int = Field(default=10000, gt=0)
    max_query_timeout_seconds: int = Field(default=30, gt=0)
    allowed_tables: List[str] = Field(default_factory=list)
    blocked_columns: List[str] = Field(default_factory=list)
    allowed_operations: List[SQLOperation] = Field(default=[SQLOperation.SELECT])


class DatabaseConfig(BaseModel):
    """Database connection configuration."""

    url: str
    type: str = Field(default="postgresql")  # postgresql, mysql, snowflake
    query_timeout: int = Field(default=30)
    pool_size: int = Field(default=5)


class LLMConfig(BaseModel):
    """LLM configuration."""

    provider: str = Field(default="openai")  # openai, anthropic
    model: str = Field(default="gpt-4-turbo-preview")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, gt=0)


class AppConfig(BaseModel):
    """Application configuration."""

    environment: str = Field(default="development")
    log_level: str = Field(default="INFO")
    audit_log_enabled: bool = Field(default=True)
    audit_log_path: str = Field(default="./data/audit_logs")
    enable_agentic_tools: bool = Field(default=False)

    safety: SafetyConfig
    database: DatabaseConfig
    llm: LLMConfig

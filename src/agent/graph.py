"""
LangGraph Agent Orchestration.

Defines the agent workflow as a state machine using LangGraph.
"""

from datetime import datetime
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from src.agent.state import AgentGraphState
from src.core.rag import get_rag_retriever
from src.core.sql_executor import SQLExecutor
from src.core.csv_executor import CSVExecutor
from src.core.sql_generator import SQLGenerator
from src.core.sql_validator import SQLValidator
from src.models.config import get_app_config, get_settings
from src.models.schemas import (
    AgentState,
    FinalResponse,
    ParsedQuestion,
    QueryMetadata,
    QueryPlan,
    QuestionIntent,
    SuggestedAction,
    TransparencyInfo,
)
from src.utils.audit_logger import get_audit_logger


class AnalystAgent:
    """
    Data Analyst Agent using LangGraph state machine.

    Workflow:
    INTERPRET → RETRIEVE → PLAN → GENERATE_SQL → VALIDATE →
    EXECUTE → RESPOND → AUDIT → END
    """

    def __init__(self):
        """Initialize agent with configuration."""
        self.config = get_app_config()
        self.settings = get_settings()

        self.rag = get_rag_retriever(
            persist_dir=self.config.llm.provider  # Placeholder
        )
        self.sql_generator = SQLGenerator(self.config.llm)
        self.sql_validator = SQLValidator(self.config.safety)

        # Use CSV executor if in CSV mode, otherwise use regular SQL executor
        if self.config.database.type == "csv":
            self.sql_executor = CSVExecutor(self.settings.csv_data_dir)
            print(f"✓ Using CSV mode with data from: {self.settings.csv_data_dir}")
        else:
            self.sql_executor = SQLExecutor(self.config.database)
            print(f"✓ Using database mode: {self.config.database.type}")

        self.audit_logger = get_audit_logger(self.config.audit_log_path)

        # Build graph
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build LangGraph state machine."""
        workflow = StateGraph(AgentGraphState)

        # Add nodes
        workflow.add_node("interpret", self.interpret_node)
        workflow.add_node("retrieve", self.retrieve_node)
        workflow.add_node("plan", self.plan_node)
        workflow.add_node("generate_sql", self.generate_sql_node)
        workflow.add_node("validate", self.validate_node)
        workflow.add_node("execute", self.execute_node)
        workflow.add_node("respond", self.respond_node)
        workflow.add_node("audit", self.audit_node)

        # Define edges (workflow)
        workflow.set_entry_point("interpret")
        workflow.add_edge("interpret", "retrieve")
        workflow.add_edge("retrieve", "plan")
        workflow.add_edge("plan", "generate_sql")
        workflow.add_edge("generate_sql", "validate")
        workflow.add_edge("validate", "execute")
        workflow.add_edge("execute", "respond")
        workflow.add_edge("respond", "audit")
        workflow.add_edge("audit", END)

        return workflow.compile()

    # ========================================================================
    # Node Implementations
    # ========================================================================

    def interpret_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Interpret user question."""
        question = state["request"].question

        # Simple question parsing (in production, use LLM for better parsing)
        parsed = ParsedQuestion(
            original_question=question,
            intent=QuestionIntent.ANALYSIS,
            metrics=self._extract_metrics(question),
            dimensions=self._extract_dimensions(question),
            filters=[],
            time_range=None,
            requires_sql=True,
            ambiguous=False,
            clarification_questions=[],
        )

        state["parsed_question"] = parsed
        state["state_history"].append("interpret")
        return state

    def retrieve_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Retrieve context from RAG."""
        parsed_question = state["parsed_question"]

        # Retrieve relevant context
        try:
            context = self.rag.retrieve(parsed_question, top_k=5)
            state["retrieved_context"] = context
        except Exception as e:
            # If RAG fails, continue with empty context
            from src.models.schemas import RetrievedContext
            state["retrieved_context"] = RetrievedContext()

        state["state_history"].append("retrieve")
        return state

    def plan_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Create query plan."""
        parsed = state["parsed_question"]
        context = state["retrieved_context"]

        # Simple planning (in production, use LLM for better planning)
        required_tables = []
        if context.table_metadata:
            required_tables = [t.table_name for t in context.table_metadata]

        plan = QueryPlan(
            strategy="Generate SQL query based on metric definitions",
            required_tables=required_tables,
            required_joins=[],
            aggregations=parsed.metrics,
            filters=parsed.filters,
            business_logic_applied=[],
        )

        state["query_plan"] = plan
        state["state_history"].append("plan")
        return state

    def generate_sql_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Generate SQL query."""
        try:
            generated = self.sql_generator.generate(
                state["parsed_question"],
                state["retrieved_context"],
                state["query_plan"],
            )
            state["generated_sql"] = generated
        except Exception as e:
            state["error"] = f"SQL generation failed: {str(e)}"
            state["error_state"] = "generate_sql"

        state["state_history"].append("generate_sql")
        return state

    def validate_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Validate SQL for safety."""
        if state.get("error"):
            return state

        try:
            validated = self.sql_validator.validate(state["generated_sql"])
            state["validated_sql"] = validated

            if not validated.validation_result.is_safe:
                state["error"] = f"SQL validation failed: {validated.validation_result.errors}"
                state["error_state"] = "validate"
        except Exception as e:
            state["error"] = f"Validation error: {str(e)}"
            state["error_state"] = "validate"

        state["state_history"].append("validate")
        return state

    def execute_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Execute SQL query."""
        if state.get("error"):
            return state

        try:
            result = self.sql_executor.execute(state["validated_sql"])
            state["query_result"] = result

            if result.error:
                state["error"] = result.error
                state["error_state"] = "execute"
        except Exception as e:
            state["error"] = f"Execution error: {str(e)}"
            state["error_state"] = "execute"

        state["state_history"].append("execute")
        return state

    def respond_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Build final response."""
        result = state.get("query_result")
        validated_sql = state.get("validated_sql")
        context = state["retrieved_context"]
        error = state.get("error")

        # Build transparency info
        transparency = None
        if validated_sql and state["request"].show_transparency:
            transparency = TransparencyInfo(
                sql_executed=validated_sql.sql,
                definitions_used=context.metric_definitions,
                tables_accessed=validated_sql.validation_result.checks_performed.keys(),
                assumptions=state["generated_sql"].assumptions if state.get("generated_sql") else [],
                citations=context.citations,
                business_rules_applied=[],
            )

        # Build metadata
        metadata = QueryMetadata(
            execution_time_ms=result.execution_time_ms if result else 0.0,
            rows_returned=result.row_count if result else 0,
            timestamp=datetime.utcnow(),
            agent_state_history=state["state_history"],
        )

        # Build answer
        if error:
            answer = f"I encountered an error: {error}"
        elif result and result.row_count > 0:
            answer = self._summarize_results(result, state["parsed_question"])
        else:
            answer = "No results found for your query."

        # Suggested actions
        actions = []
        if result and result.row_count > 0 and not error:
            actions.append(
                SuggestedAction(
                    type="export_csv",
                    label="Download as CSV",
                    description="Export results to CSV file",
                )
            )

        response = FinalResponse(
            answer=answer,
            transparency=transparency if state["request"].show_transparency else None,
            data=result,
            metadata=metadata,
            suggested_actions=actions,
            error=error,
        )

        state["response"] = response
        state["state_history"].append("respond")
        return state

    def audit_node(self, state: AgentGraphState) -> Dict[str, Any]:
        """Audit log the query."""
        if self.config.audit_log_enabled:
            try:
                self.audit_logger.log_query(
                    request=state["request"],
                    validated_sql=state.get("validated_sql"),
                    result=state.get("query_result"),
                    success=state.get("error") is None,
                    error=state.get("error"),
                )
            except Exception:
                # Don't fail on audit logging errors
                pass

        state["state_history"].append("audit")
        return state

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _extract_metrics(self, question: str) -> list[str]:
        """Extract metric names from question (simple keyword matching)."""
        metrics = []
        metric_keywords = ["revenue", "profit", "sales", "customers", "orders", "count"]
        question_lower = question.lower()
        for keyword in metric_keywords:
            if keyword in question_lower:
                metrics.append(keyword)
        return metrics

    def _extract_dimensions(self, question: str) -> list[str]:
        """Extract dimension names from question (simple keyword matching)."""
        dimensions = []
        dimension_keywords = ["region", "country", "product", "category", "month", "quarter"]
        question_lower = question.lower()
        for keyword in dimension_keywords:
            if keyword in question_lower:
                dimensions.append(keyword)
        return dimensions

    def _summarize_results(self, result: Any, parsed_question: ParsedQuestion) -> str:
        """Generate natural language summary of results."""
        # Simple summary (in production, use LLM for better summarization)
        count = result.row_count
        question = parsed_question.original_question

        if count == 1:
            return f"Found 1 result for your question: '{question}'"
        else:
            return f"Found {count} results for your question: '{question}'"

    def invoke(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke the agent with a query request.

        Args:
            request: Query request dict

        Returns:
            Final state with response
        """
        from src.models.schemas import QueryRequest

        # Initialize state
        initial_state: AgentGraphState = {
            "request": QueryRequest(**request),
            "current_state": AgentState.INTERPRET,
            "state_history": [],
            "parsed_question": None,
            "retrieved_context": None,
            "query_plan": None,
            "generated_sql": None,
            "validated_sql": None,
            "query_result": None,
            "result_summary": None,
            "response": None,
            "error": None,
            "error_state": None,
            "needs_clarification": False,
            "clarification_questions": [],
        }

        # Run graph
        final_state = self.graph.invoke(initial_state)
        return final_state


# ============================================================================
# Factory Function
# ============================================================================


def create_analyst_agent() -> AnalystAgent:
    """Create and return analyst agent instance."""
    return AnalystAgent()

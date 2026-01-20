"""
Text-to-SQL Generator.

Generates SQL queries from natural language using LLM with:
- User question
- Retrieved metric definitions
- Schema context
- Business rules

Includes detailed prompts for accurate SQL generation.
"""

from typing import List

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from src.models.schemas import (
    GeneratedSQL,
    LLMConfig,
    ParsedQuestion,
    QueryPlan,
    RetrievedContext,
    TableMetadata,
)


class SQLGenerator:
    """
    Text-to-SQL generator using LLM.

    Generates SELECT queries based on:
    - Natural language question
    - Metric definitions (from RAG)
    - Table schema
    - Business rules
    """

    def __init__(self, llm_config: LLMConfig):
        """
        Initialize SQL generator.

        Args:
            llm_config: LLM configuration
        """
        self.config = llm_config

        # Initialize LLM client
        if llm_config.provider == "openai":
            self.llm = ChatOpenAI(
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            )
        elif llm_config.provider == "anthropic":
            self.llm = ChatAnthropic(
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")

    def generate(
        self,
        parsed_question: ParsedQuestion,
        retrieved_context: RetrievedContext,
        query_plan: QueryPlan,
    ) -> GeneratedSQL:
        """
        Generate SQL query.

        Args:
            parsed_question: Parsed user question
            retrieved_context: Context from RAG
            query_plan: Query execution plan

        Returns:
            Generated SQL with metadata
        """
        # Build prompt
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(
            parsed_question, retrieved_context, query_plan
        )

        # Generate SQL
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        response = self.llm.invoke(messages)
        sql = self._extract_sql(response.content)

        # Extract metadata
        tables_used = query_plan.required_tables
        definitions_applied = [m.name for m in retrieved_context.metric_definitions]
        assumptions = self._extract_assumptions(response.content)

        return GeneratedSQL(
            sql=sql,
            tables_used=tables_used,
            definitions_applied=definitions_applied,
            assumptions=assumptions,
            confidence_score=0.9,  # Could be computed based on context
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt for SQL generation."""
        return """You are an expert SQL query generator for business analytics.

Your task is to generate accurate, safe SQL SELECT queries based on:
1. Natural language business questions
2. Official metric definitions from the company's data dictionary
3. Table schemas and relationships
4. Business rules and filters

CRITICAL REQUIREMENTS:
- Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP, ALTER, etc.)
- Use ONLY the provided metric definitions - do not invent calculations
- Use ONLY the tables and columns provided in the schema
- Apply all relevant business rules and filters
- Include proper JOINs based on foreign key relationships
- Add appropriate WHERE clauses for filters and time ranges
- Use GROUP BY when aggregating
- Always include ORDER BY for consistent results
- Add comments to explain complex logic

SQL STYLE:
- Use explicit JOIN syntax (not implicit joins in WHERE)
- Prefer table aliases for readability
- Use meaningful column aliases
- Format SQL for readability (multi-line, indented)
- Include metric names in column aliases

OUTPUT FORMAT:
1. First, provide a brief explanation of your approach
2. Then provide the SQL query wrapped in ```sql ``` code blocks
3. Finally, list any assumptions you made

Example:
Explanation: I'll calculate revenue by region for Q4 2024...

```sql
SELECT
  c.region,
  SUM(oli.price * oli.quantity) as revenue
FROM orders o
JOIN order_line_items oli ON o.order_id = oli.order_id
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date >= '2024-10-01'
  AND o.order_date < '2025-01-01'
  AND o.status != 'cancelled'
GROUP BY c.region
ORDER BY revenue DESC
```

Assumptions:
- Excluded cancelled orders per business rules
- Last quarter defined as Q4 2024 (Oct 1 - Dec 31)
"""

    def _build_user_prompt(
        self,
        parsed_question: ParsedQuestion,
        retrieved_context: RetrievedContext,
        query_plan: QueryPlan,
    ) -> str:
        """Build user prompt with context."""
        prompt_parts = []

        # 1. User question
        prompt_parts.append(f"USER QUESTION:\n{parsed_question.original_question}\n")

        # 2. Metric definitions
        if retrieved_context.metric_definitions:
            prompt_parts.append("METRIC DEFINITIONS:")
            for metric in retrieved_context.metric_definitions:
                prompt_parts.append(f"- {metric.name}:")
                prompt_parts.append(f"  Formula: {metric.formula}")
                prompt_parts.append(f"  Source: {metric.source_table}")
                prompt_parts.append(f"  Grain: {metric.grain}")
                if metric.filters:
                    prompt_parts.append(f"  Default Filters: {', '.join(metric.filters)}")
            prompt_parts.append("")

        # 3. Table schemas
        if retrieved_context.table_metadata:
            prompt_parts.append("TABLE SCHEMAS:")
            for table in retrieved_context.table_metadata:
                prompt_parts.append(f"- {table.table_name}:")
                prompt_parts.append(f"  Columns: {', '.join(table.columns)}")
                if table.primary_key:
                    prompt_parts.append(f"  Primary Key: {table.primary_key}")
                if table.foreign_keys:
                    for col, ref in table.foreign_keys.items():
                        prompt_parts.append(f"  Foreign Key: {col} -> {ref}")
                if table.description:
                    prompt_parts.append(f"  Description: {table.description}")
            prompt_parts.append("")

        # 4. Business rules
        if retrieved_context.business_rules:
            prompt_parts.append("BUSINESS RULES:")
            for rule in retrieved_context.business_rules:
                prompt_parts.append(f"- {rule.name}: {rule.description}")
                if rule.sql_filter:
                    prompt_parts.append(f"  SQL Filter: {rule.sql_filter}")
            prompt_parts.append("")

        # 5. Example queries (if available)
        if retrieved_context.example_queries:
            prompt_parts.append("EXAMPLE QUERIES:")
            for i, example in enumerate(retrieved_context.example_queries[:2], 1):
                prompt_parts.append(f"Example {i}:")
                prompt_parts.append(f"```sql\n{example}\n```")
            prompt_parts.append("")

        # 6. Query strategy
        prompt_parts.append(f"QUERY STRATEGY:\n{query_plan.strategy}\n")

        # 7. Required tables and joins
        prompt_parts.append(f"REQUIRED TABLES: {', '.join(query_plan.required_tables)}")
        if query_plan.required_joins:
            prompt_parts.append("REQUIRED JOINS:")
            for join in query_plan.required_joins:
                prompt_parts.append(f"  - {join}")
        prompt_parts.append("")

        # 8. Additional context
        if parsed_question.time_range:
            prompt_parts.append(
                f"TIME RANGE: {parsed_question.time_range.get('start')} to {parsed_question.time_range.get('end')}"
            )

        if parsed_question.filters:
            prompt_parts.append(f"FILTERS: {', '.join(parsed_question.filters)}")

        prompt_parts.append("\nPlease generate the SQL query following the format specified.")

        return "\n".join(prompt_parts)

    def _extract_sql(self, response: str) -> str:
        """Extract SQL from LLM response."""
        # Find SQL code block
        if "```sql" in response:
            start = response.find("```sql") + 6
            end = response.find("```", start)
            sql = response[start:end].strip()
        elif "```" in response:
            # Fallback: any code block
            start = response.find("```") + 3
            end = response.find("```", start)
            sql = response[start:end].strip()
        else:
            # No code blocks, use the whole response (cleaned)
            sql = response.strip()

        return sql

    def _extract_assumptions(self, response: str) -> List[str]:
        """Extract assumptions from LLM response."""
        assumptions = []
        if "Assumptions:" in response:
            assumptions_section = response.split("Assumptions:")[1].strip()
            # Split by newlines and clean
            for line in assumptions_section.split("\n"):
                line = line.strip()
                if line and not line.startswith("```"):
                    # Remove bullet points
                    line = line.lstrip("- *•")
                    if line:
                        assumptions.append(line)
        return assumptions


# ============================================================================
# Convenience Function
# ============================================================================


def generate_sql(
    parsed_question: ParsedQuestion,
    retrieved_context: RetrievedContext,
    query_plan: QueryPlan,
    llm_config: LLMConfig,
) -> GeneratedSQL:
    """
    Convenience function to generate SQL.

    Args:
        parsed_question: Parsed question
        retrieved_context: Retrieved context
        query_plan: Query plan
        llm_config: LLM configuration

    Returns:
        Generated SQL
    """
    generator = SQLGenerator(llm_config)
    return generator.generate(parsed_question, retrieved_context, query_plan)

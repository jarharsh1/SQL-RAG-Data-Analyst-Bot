"""
Audit Logger - Persistent audit trail for all queries.

Logs every query execution with:
- User identity
- Question and SQL
- Execution metadata
- Results summary
- Timestamp

Audit logs are append-only and stored as JSONL for easy parsing.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from src.models.schemas import AuditLogEntry, QueryRequest, QueryResult, ValidatedSQL


class AuditLogger:
    """
    Audit logger for query execution.

    Writes audit entries to JSONL files with daily rotation.
    """

    def __init__(self, log_dir: str = "./data/audit_logs"):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory to store audit logs
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log_query(
        self,
        request: QueryRequest,
        validated_sql: Optional[ValidatedSQL] = None,
        result: Optional[QueryResult] = None,
        success: bool = True,
        error: Optional[str] = None,
        actions_taken: Optional[list] = None,
    ) -> None:
        """
        Log a query execution.

        Args:
            request: Original query request
            validated_sql: Validated SQL (if generated)
            result: Query execution result (if successful)
            success: Whether execution succeeded
            error: Error message (if failed)
            actions_taken: List of actions performed (exports, etc.)
        """
        entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            user_id=request.user_id,
            question=request.question,
            sql_executed=validated_sql.sql if validated_sql else None,
            tables_accessed=(
                list(set(validated_sql.validation_result.checks_performed.keys()))
                if validated_sql
                else []
            ),
            rows_returned=result.row_count if result else 0,
            execution_time_ms=result.execution_time_ms if result else 0.0,
            success=success,
            error=error,
            actions_taken=actions_taken or [],
        )

        self._write_entry(entry)

    def _write_entry(self, entry: AuditLogEntry) -> None:
        """
        Write audit entry to JSONL file.

        Uses daily rotation: query_audit_YYYYMMDD.jsonl
        """
        date_str = entry.timestamp.strftime("%Y%m%d")
        log_file = self.log_dir / f"query_audit_{date_str}.jsonl"

        # Convert to dict and serialize
        entry_dict = entry.model_dump()
        entry_dict["timestamp"] = entry.timestamp.isoformat()

        # Append to file (atomic write)
        with open(log_file, "a") as f:
            f.write(json.dumps(entry_dict) + "\n")

    def read_logs(
        self, date: Optional[datetime] = None, user_id: Optional[str] = None
    ) -> list[AuditLogEntry]:
        """
        Read audit logs for a specific date and/or user.

        Args:
            date: Date to read logs for (default: today)
            user_id: Filter by user ID (optional)

        Returns:
            List of audit log entries
        """
        if date is None:
            date = datetime.utcnow()

        date_str = date.strftime("%Y%m%d")
        log_file = self.log_dir / f"query_audit_{date_str}.jsonl"

        if not log_file.exists():
            return []

        entries = []
        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    entry_dict = json.loads(line)
                    # Filter by user if specified
                    if user_id and entry_dict.get("user_id") != user_id:
                        continue
                    entries.append(AuditLogEntry(**entry_dict))

        return entries


# Singleton instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(log_dir: str = "./data/audit_logs") -> AuditLogger:
    """Get or create audit logger singleton."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(log_dir)
    return _audit_logger

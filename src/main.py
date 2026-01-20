"""
FastAPI Application - SQL + RAG Data Analyst Bot.

Main entry point for the REST API.
"""

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.agent.graph import create_analyst_agent
from src.models.config import get_settings
from src.models.schemas import FinalResponse, QueryRequest

# Global agent instance
agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    global agent
    # Startup
    print("Starting SQL + RAG Data Analyst Bot...")
    settings = get_settings()
    print(f"Environment: {settings.app_env}")
    print(f"LLM Provider: {settings.llm_provider}")

    # Initialize agent
    agent = create_analyst_agent()
    print("Agent initialized successfully")

    yield

    # Shutdown
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="SQL + RAG Data Analyst Bot",
    description="AI-powered data analyst with RAG and Text-to-SQL",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# API Endpoints
# ============================================================================


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "name": "SQL + RAG Data Analyst Bot",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/api/query", response_model=FinalResponse)
async def query(request: QueryRequest) -> FinalResponse:
    """
    Process a natural language query.

    Args:
        request: Query request with question and user_id

    Returns:
        Final response with answer, SQL, and transparency info
    """
    global agent

    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Invoke agent
        result = agent.invoke(request.model_dump())

        # Extract response
        response = result.get("response")
        if response is None:
            raise HTTPException(
                status_code=500, detail="Agent failed to generate response"
            )

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.get("/api/audit/{user_id}")
async def get_audit_logs(user_id: str) -> JSONResponse:
    """
    Get audit logs for a user.

    Args:
        user_id: User identifier

    Returns:
        List of audit log entries
    """
    from src.utils.audit_logger import get_audit_logger

    try:
        audit_logger = get_audit_logger()
        logs = audit_logger.read_logs(user_id=user_id)
        return JSONResponse(content=[log.model_dump() for log in logs])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs: {str(e)}")


# ============================================================================
# Entry Point
# ============================================================================


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=(settings.app_env == "development"),
        log_level=settings.log_level.lower(),
    )

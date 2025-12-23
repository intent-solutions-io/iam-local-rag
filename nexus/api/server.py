"""
FastAPI server for headless NEXUS RAG operations.
Provides REST API for querying and indexing.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import time

from ..core.config import Config
from ..core.models import QueryRequest, QueryResponse, IndexRequest, IndexResult, HealthStatus, PerformanceMetrics
from ..core.rag_pipeline import RAGPipeline

# Initialize FastAPI app
app = FastAPI(
    title="NEXUS RAG API",
    description="Headless RAG API for document intelligence",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
_pipelines = {}  # workspace_id -> RAGPipeline
_start_time = time.time()
_query_count = 0


def get_pipeline(workspace_id: str = "default") -> RAGPipeline:
    """Get or create pipeline for workspace"""
    if workspace_id not in _pipelines:
        _pipelines[workspace_id] = RAGPipeline(workspace_id=workspace_id)
    return _pipelines[workspace_id]


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    global _query_count

    pipeline = get_pipeline()

    return HealthStatus(
        status="healthy",
        mode=Config.NEXUS_MODE.value,
        llm_provider=Config.NEXUS_LLM_PROVIDER.value,
        embed_provider=Config.NEXUS_EMBED_PROVIDER.value,
        vector_store_ready=pipeline._vectorstore is not None,
        documents_indexed=0,  # TODO: track this
        uptime_seconds=time.time() - _start_time,
        metrics=PerformanceMetrics(
            cache_hit_rate=0.0,
            avg_query_latency_ms=0.0,
            total_queries=_query_count,
            memory_mb=0.0
        )
    )


@app.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    """
    Query the knowledge base.

    Args:
        request: Query request with question and workspace_id

    Returns:
        QueryResponse with answer and citations
    """
    global _query_count

    try:
        pipeline = get_pipeline(request.workspace_id)
        response = pipeline.query(request)
        _query_count += 1
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index", response_model=IndexResult)
async def index_documents(request: IndexRequest):
    """
    Index documents into workspace.

    Args:
        request: Index request with file paths

    Returns:
        IndexResult with processing stats
    """
    try:
        pipeline = get_pipeline(request.workspace_id)
        result = pipeline.index_documents(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "NEXUS RAG API",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "query": "POST /query",
            "index": "POST /index"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        workers=Config.API_WORKERS
    )

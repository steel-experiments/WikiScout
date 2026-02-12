#!/usr/bin/env python3
"""
WikiScout FastAPI Web API

Modern async REST API for Wikipedia research with auto-generated documentation.

Run: uvicorn api:app --reload
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI, HTTPException, Query, Path, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Any, AsyncIterator, Dict, List
from datetime import datetime
import logging
from contextlib import asynccontextmanager

from agent import WikipediaAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize agent
agent = WikipediaAgent()

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("WikiScout API starting up...")
    logger.info("Docs available at: http://localhost:8000/docs")
    logger.info(f"Cache directory: {agent.cache_dir}")
    yield
    logger.info("WikiScout API shutting down...")


openapi_tags = [
    {"name": "General", "description": "Service metadata and health checks."},
    {"name": "Search", "description": "Search Wikipedia pages by query."},
    {"name": "Summarize", "description": "Summarize a Wikipedia article."},
    {"name": "Compare", "description": "Compare two Wikipedia topics."},
    {"name": "Batch", "description": "Batch fetch multiple pages in parallel."},
]


# Create FastAPI app
app = FastAPI(
    title="WikiScout API",
    description="Fast Wikipedia research agent with summarization, comparison, and structured extraction",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=openapi_tags,
    contact={
        "name": "WikiScout",
        "url": "https://github.com/steel-experiments/WikiScout",
    },
    license_info={
        "name": "MIT",
    },
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response Models
class Candidate(BaseModel):
    """Wikipedia page candidate"""
    title: str = Field(..., description="Wikipedia page title")
    url: str = Field(..., description="Full URL to Wikipedia page")
    description: str = Field(..., description="Article excerpt")
    score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    disambiguation: bool = Field(..., description="Is this a disambiguation page")
    pageid: int = Field(..., description="Wikipedia page ID")


class SearchResponse(BaseModel):
    """Search results"""
    status: str = Field(..., description="Status: success or error")
    query: str = Field(..., description="Original search query")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    candidates: List[Candidate] = Field(..., description="List of candidate pages")
    count: int = Field(..., description="Number of candidates found")
    offset: int = Field(..., ge=0, description="Result offset for pagination")
    limit: int = Field(..., ge=1, le=20, description="Max results returned")


class SummaryResponse(BaseModel):
    """Article summary"""
    status: str
    title: str
    timestamp: str
    summary: List[str] = Field(..., description="Key points from the article")
    source_url: str
    bullets_requested: int
    bullets_returned: int


class ComparisonResponse(BaseModel):
    """Topic comparison"""
    status: str
    topic1: str
    topic2: str
    timestamp: str
    comparison: Dict[str, List[str]]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    version: str
    cache_status: str


class ErrorResponse(BaseModel):
    """Error response"""
    status: str = "error"
    error: str
    timestamp: str


class BatchRequest(BaseModel):
    """Batch fetch request"""
    titles: List[str] = Field(..., description="Wikipedia page titles", min_length=1, max_length=20)
    use_cache: bool = Field(True, description="Use cached pages if available")


class BatchResponse(BaseModel):
    """Batch fetch response"""
    status: str
    timestamp: str
    count: int
    results: List[Dict[str, Any]]


# Endpoints
@app.get(
    "/",
    tags=["General"],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "name": "WikiScout API",
                        "version": "1.1.0",
                        "description": "Fast Wikipedia research agent",
                        "docs": "/docs",
                        "health": "/health",
                        "endpoints": {
                            "search": "/search/{query}",
                            "summarize": "/summarize/{query}",
                            "compare": "/compare",
                            "batch": "/batch",
                            "status": "/status",
                        },
                    }
                }
            }
        }
    },
)
async def read_root():
    """API root endpoint with basic information"""
    return {
        "name": "WikiScout API",
        "version": "1.1.0",
        "description": "Fast Wikipedia research agent",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "search": "/search/{query}",
            "summarize": "/summarize/{query}",
            "compare": "/compare",
            "batch": "/batch",
            "status": "/status",
        }
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["General"],
    responses={
        200: {
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2026-02-12T21:00:00",
                        "version": "1.1.0",
                        "cache_status": "active",
                    }
                }
            }
        }
    },
)
async def health_check(response: Response):
    """Health check endpoint"""
    response.headers["Cache-Control"] = "no-store"
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0",
        "cache_status": "active",
    }


@app.get(
    "/search/{query}",
    response_model=SearchResponse,
    tags=["Search"],
    summary="Search Wikipedia",
    responses={
        200: {
            "description": "Successful search results",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "query": "Python programming",
                        "timestamp": "2026-02-12T21:00:00",
                        "candidates": [
                            {
                                "title": "Python_(programming_language)",
                                "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
                                "description": "High-level programming language...",
                                "score": 1.0,
                                "disambiguation": False,
                                "pageid": 23862,
                            }
                        ],
                        "count": 1,
                        "offset": 0,
                        "limit": 5,
                    }
                }
            },
        },
        500: {"model": ErrorResponse, "description": "Internal server error"},
    }
)
async def search_wikipedia(
    response: Response,
    query: str = Path(..., description="Search query", min_length=1),
    candidates: int = Query(5, ge=1, le=20, description="Number of candidates to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    Search Wikipedia for articles matching the query.
    
    Returns a list of candidate articles with relevance scores and metadata.
    """
    try:
        logger.info(f"API Search: {query} (candidates={candidates})")
        result = await agent.search_async(query, candidates=candidates)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("error", "Not found"))
        
        candidates_list = result.get("candidates", [])
        paged_candidates = candidates_list[offset:offset + candidates]
        response.headers["Cache-Control"] = "public, max-age=300"
        
        return {
            "status": "success",
            "query": query,
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
            "candidates": paged_candidates,
            "count": len(paged_candidates),
            "offset": offset,
            "limit": candidates,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/summarize/{query}",
    response_model=SummaryResponse,
    tags=["Summarize"],
    summary="Summarize Wikipedia article",
    responses={
        200: {
            "description": "Summary response",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "title": "Machine_learning",
                        "timestamp": "2026-02-12T21:00:00",
                        "summary": ["Point 1", "Point 2"],
                        "source_url": "https://en.wikipedia.org/wiki/Machine_learning",
                        "bullets_requested": 2,
                        "bullets_returned": 2,
                    }
                }
            },
        },
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def summarize_article(
    response: Response,
    query: str = Path(..., description="Article title or search query", min_length=1),
    bullets: int = Query(5, ge=1, le=20, description="Number of summary bullets"),
):
    """
    Generate a bullet-point summary of a Wikipedia article.
    
    Returns key points extracted from the article content.
    """
    try:
        logger.info(f"API Summarize: {query} (bullets={bullets})")
        result = await agent.summarize_async(query, bullets=bullets)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("error", "Article not found"))
        
        summary_list = result.get("summary", [])
        response.headers["Cache-Control"] = "public, max-age=300"
        
        return {
            "status": "success",
            "title": result.get("title", query),
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
            "summary": summary_list,
            "source_url": result.get("source_url", ""),
            "bullets_requested": bullets,
            "bullets_returned": len(summary_list),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarize error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/compare",
    response_model=ComparisonResponse,
    tags=["Compare"],
    summary="Compare two Wikipedia topics",
    responses={
        200: {
            "description": "Comparison response",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "topic1": "Python",
                        "topic2": "JavaScript",
                        "timestamp": "2026-02-12T21:00:00",
                        "comparison": {
                            "similarities": ["Both are popular languages"],
                            "differences": ["Python is dynamically typed"],
                        },
                    }
                }
            },
        },
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def compare_topics(
    response: Response,
    topic1: str = Query(..., description="First topic", min_length=1),
    topic2: str = Query(..., description="Second topic", min_length=1),
    bullets: int = Query(5, ge=1, le=20, description="Number of comparison points"),
):
    """
    Compare two Wikipedia topics side-by-side.
    
    Returns similarities and differences between the topics.
    """
    try:
        logger.info(f"API Compare: {topic1} vs {topic2} (bullets={bullets})")
        result = await agent.compare_async(topic1, topic2, bullets=bullets)
        
        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("error", "Topics not found"))
        
        response.headers["Cache-Control"] = "public, max-age=300"
        return {
            "status": "success",
            "topic1": result.get("topic1", topic1),
            "topic2": result.get("topic2", topic2),
            "timestamp": result.get("timestamp", datetime.now().isoformat()),
            "comparison": result.get("comparison", {}),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Compare error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/status",
    tags=["General"],
    responses={
        200: {
            "description": "Status response",
            "content": {
                "application/json": {
                    "example": {
                        "status": "operational",
                        "timestamp": "2026-02-12T21:00:00",
                        "version": "1.1.0",
                        "cache": {
                            "directory": "cache",
                            "files": 10,
                            "size_bytes": 12345,
                            "size_mb": 0.01,
                        },
                    }
                }
            },
        }
    },
)
async def get_status(response: Response):
    """Get agent status and cache statistics"""
    try:
        # Get cache directory size
        import os
        cache_dir = agent.cache_dir
        cache_files = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0
        cache_size = sum(f.stat().st_size for f in cache_dir.glob("*.json")) if cache_dir.exists() else 0
        
        response.headers["Cache-Control"] = "no-store"
        return {
            "status": "operational",
            "timestamp": datetime.now().isoformat(),
            "version": "1.1.0",
            "cache": {
                "directory": str(cache_dir),
                "files": cache_files,
                "size_bytes": cache_size,
                "size_mb": round(cache_size / 1024 / 1024, 2),
            },
            "config": {
                "language": agent.config.get("wikipedia_lang", "en"),
                "cache_ttl": agent.config.get("cache_ttl_seconds", 3600),
                "timeout": agent.config.get("timeout_seconds", 60),
            }
        }
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/batch",
    response_model=BatchResponse,
    tags=["Batch"],
    summary="Fetch multiple Wikipedia pages in parallel",
    responses={
        200: {
            "description": "Batch response",
            "content": {
                "application/json": {
                    "example": {
                        "status": "success",
                        "timestamp": "2026-02-12T21:00:00",
                        "count": 2,
                        "results": [
                            {"success": True, "title": "Python"},
                            {"success": False, "title": "Missing", "error": "Page not found"},
                        ],
                    }
                }
            },
        }
    },
)
async def batch_fetch(payload: BatchRequest, response: Response):
    """
    Fetch multiple Wikipedia pages in parallel for high performance.

    Returns a list of page payloads (success or error per title).
    """
    if not payload.titles:
        raise HTTPException(status_code=400, detail="titles must not be empty")

    try:
        logger.info(f"API Batch: {len(payload.titles)} titles")
        results = await agent.fetch_pages_async(payload.titles, use_cache=payload.use_cache)
        response.headers["Cache-Control"] = "public, max-age=300"
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "count": len(results),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Batch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "error": "Resource not found",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )

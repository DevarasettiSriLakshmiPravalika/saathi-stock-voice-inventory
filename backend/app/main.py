"""
Saathi FastAPI application entry point.

All API routes wired here.
Global exception handler ensures contract-compliant error responses.
"""
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings

settings = get_settings()

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Saathi API",
    version="1.0.0",
    description="Voice-first inventory management system",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -- Global Exception Handlers ------------------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return contract-compliant error envelope for all HTTPExceptions."""
    detail = exc.detail
    if isinstance(detail, dict):
        error = detail
    else:
        error = {"code": "INTERNAL_ERROR", "message": str(detail)}
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": error},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Return safe error response for unhandled exceptions (no internal details)."""
    logger.exception("Unhandled exception: %s", str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {"code": "INTERNAL_ERROR", "message": "An internal error occurred."},
        },
    )


# -- Health Check -------------------------------------------------------------

@app.get("/api/v1/health", tags=["system"])
async def health():
    """
    Standard Saathi health check.
    Must not expose secrets, credentials, or internal details.
    """
    return {"success": True, "status": "healthy"}


# -- Register Routers ---------------------------------------------------------

from app.api import auth, users, shops, products, members, voice, statements, inventory, reviews, vocabulary, query, dashboard  # noqa

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(shops.router)
app.include_router(products.router)
app.include_router(members.router)
app.include_router(voice.router)
app.include_router(statements.router)
app.include_router(inventory.router)
app.include_router(reviews.router)
app.include_router(vocabulary.router)
app.include_router(query.router)
app.include_router(dashboard.router)

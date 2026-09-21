import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import settings
from routers import (
    auth,
    users,
    vocabulary,
    practice,
    reviews,
    conversations,
    personalization,
    knowledge,
    dashboard,
    progress,
    gamification,
    daily,
    export,
    adaptive,
)

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG or not settings.is_production else None,
    redoc_url="/redoc" if settings.DEBUG or not settings.is_production else None,
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds standard security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# Security Headers middleware
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler to avoid leaking raw exceptions in production."""
    if settings.DEBUG:
        # In debug mode, re-raise or return detailed error for development
        return JSONResponse(
            status_code=500,
            content={"detail": f"Internal Server Error: {str(exc)}"},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# Include Routers with API v1 prefix
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(vocabulary.router, prefix="/api/v1")
app.include_router(practice.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(conversations.router, prefix="/api/v1")
app.include_router(personalization.router, prefix="/api/v1")
app.include_router(knowledge.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(progress.router, prefix="/api/v1")
app.include_router(gamification.router, prefix="/api/v1")
app.include_router(daily.router, prefix="/api/v1")
app.include_router(export.router, prefix="/api/v1")
app.include_router(adaptive.router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint for Render/uptime monitoring."""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": "0.1.0",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "KirubAI API",
        "docs": "/docs" if (settings.DEBUG or not settings.is_production) else "disabled in production",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=settings.DEBUG)


from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import init_db
from app.routes import auth, users, reports, admin, audit

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    logger.info("Starting up Crime Report Management System...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")

    # Initialize database tables
    try:
        await init_db()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down...")


# Create FastAPI application
app = FastAPI(
    title="Crime Report Management System",
    description="A production-ready FastAPI backend for managing crime reports with secure RBAC",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {exc}", exc_info=True)

    # Don't expose internal errors in production
    if settings.ENVIRONMENT == "production":
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )


# Include routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(reports.router)
app.include_router(admin.router)
app.include_router(audit.router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "Crime Report Management System API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "redoc": "/redoc"
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
from datetime import datetime
import time
from sqlalchemy import text

# Import routers
from api import auth_endpoints, trust_endpoints, mirage_endpoints, user_endpoints, session_endpoints, monitoring_endpoints

# Import database with fixed functions
from database.database import engine, check_database_health, get_database_info, initialize_database_connection

# Import middleware
from middleware.rate_limit_middleware import RateLimitMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="NETHRA Backend API",
    description="AI-Powered Mobile Banking Security with Adaptive Mirage Interface",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    swagger_ui_parameters={
        "oauth2RedirectUrl": "/docs/oauth2-redirect",
        "usePkceWithAuthorizationCodeGrant": False
    }
)

# CORS middleware for Flutter integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RateLimitMiddleware)

# Add request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-NETHRA-Version"] = "1.0.0"
    return response

# Include API routers
app.include_router(
    auth_endpoints.router, 
    prefix="/api/auth", 
    tags=["Authentication"]
)

app.include_router(
    trust_endpoints.router, 
    prefix="/api/trust", 
    tags=["Trust & AI"]
)

app.include_router(
    mirage_endpoints.router, 
    prefix="/api/mirage", 
    tags=["Mirage Interface"]
)

app.include_router(
    user_endpoints.router, 
    prefix="/api/user", 
    tags=["User Management"]
)

app.include_router(
    session_endpoints.router, 
    prefix="/api/session", 
    tags=["Session Management"]
)

app.include_router(
    monitoring_endpoints.router, 
    prefix="/api/monitoring", 
    tags=["Monitoring"]
)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "NETHRA Backend API - Mobile Banking Security System",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "🎭 Adaptive Mirage Interface",
            "🎯 Dynamic Personal Thresholds", 
            "🤖 AI-Powered Trust Scoring",
            "🔐 JWT Authentication",
            "⏰ Session Management",
            "📊 Real-time Monitoring"
        ],
        "endpoints": {
            "authentication": "/api/auth/",
            "trust_scoring": "/api/trust/",
            "mirage_interface": "/api/mirage/",
            "user_management": "/api/user/",
            "session_management": "/api/session/",
            "monitoring": "/api/monitoring/"
        }
    }

# Health check endpoint - Uses the fixed database functions
@app.get("/health")
async def health_check():
    try:
        # Use the fixed database health check function
        db_healthy = check_database_health()
        db_info = get_database_info()
        
        if db_healthy:
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected",
                "user_count": db_info.get("total_users", 0),
                "active_sessions": db_info.get("active_sessions", 0),
                "behavioral_records": db_info.get("behavioral_records", 0),
                "components": {
                    "ai_model": "loaded",
                    "mirage_controller": "active",
                    "authentication": "operational",
                    "database": "connected"
                },
                "version": "1.0.0",
                "uptime": "active"
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "degraded",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database": "error",
                    "version": "1.0.0"
                }
            )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "error",
                "error": str(e),
                "version": "1.0.0"
            }
        )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception on {request.url}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": str(hash(str(request.url) + str(time.time())))
        }
    )

# Startup event with database schema fix
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 NETHRA Backend starting up...")
    logger.info("🎭 Adaptive Mirage Interface: Ready")
    logger.info("🎯 Dynamic Threshold Manager: Ready") 
    logger.info("🤖 AI Trust Predictor: Loading Member 1's model...")
    
    try:
        # CRITICAL: Fix database schema - add missing intensity_level column
        logger.info("🔧 Checking database schema...")
        with engine.connect() as conn:
            try:
                # Check if mirage_sessions table exists and get columns
                result = conn.execute(text("PRAGMA table_info(mirage_sessions)"))
                columns = [row[1] for row in result.fetchall()]
                
                if 'intensity_level' not in columns:
                    logger.info("🔧 Adding missing intensity_level column...")
                    conn.execute(text("ALTER TABLE mirage_sessions ADD COLUMN intensity_level VARCHAR(20) DEFAULT 'moderate'"))
                    conn.commit()
                    logger.info("✅ Successfully added intensity_level column to mirage_sessions")
                else:
                    logger.info("✅ intensity_level column already exists")
                    
            except Exception as schema_error:
                logger.info(f"Database schema note: {str(schema_error)}")
                # Table might not exist yet, will be created by SQLAlchemy
        
        # Initialize database connection with fixed functions
        db_initialized = initialize_database_connection()
        if not db_initialized:
            logger.warning("⚠️ Database connection issues detected")
        
        # Initialize AI model on startup
        from services.ai_interface import get_trust_predictor
        predictor = get_trust_predictor()
        logger.info("✅ Member 1's AI model loaded successfully")
        
        # Initialize mirage controller
        from services.mirage_controller import get_mirage_controller
        mirage = get_mirage_controller()
        logger.info("✅ Mirage Controller initialized")
        
    except Exception as e:
        logger.error(f"❌ Startup initialization failed: {str(e)}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 NETHRA Backend shutting down...")
    logger.info("👋 NETHRA Backend stopped")

if __name__ == "__main__":
    logger.info("🚀 Starting NETHRA Backend Server...")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )

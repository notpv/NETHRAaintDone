from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT Authentication Middleware for protected routes"""
    
    def __init__(self, app):
        super().__init__(app)
        self.security = HTTPBearer()
        self.protected_paths = [
            "/api/trust/",
            "/api/mirage/",
            "/api/user/",
            "/api/session/"
        ]
        self.public_paths = [
            "/api/auth/login",
            "/api/auth/register",
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next):
        # Check if path requires authentication
        path = request.url.path
        
        # Allow public paths
        if any(path.startswith(public_path) for public_path in self.public_paths):
            response = await call_next(request)
            return response
        
        # Check if path requires protection
        requires_auth = any(path.startswith(protected_path) for protected_path in self.protected_paths)
        
        if requires_auth:
            # Verify JWT token
            auth_header = request.headers.get("Authorization")
            
            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing or invalid authorization header"
                )
            
            try:
                from utils.jwt_utils import verify_token
                token = auth_header.split(" ")[1]
                payload = verify_token(token)
                
                # Add user info to request state
                request.state.user = payload.get("sub")
                
            except Exception as e:
                logger.error(f"JWT verification failed: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token"
                )
        
        response = await call_next(request)
        return response

# API package initialization for NETHRA Guardian AI Backend

from .auth import router as auth_router
from .trust import router as trust_router
from .user import router as user_router
from .monitoring import router as monitoring_router

# List of all available routers
__routers__ = [
    ("auth", auth_router, "/auth"),
    ("trust", trust_router, "/trust"), 
    ("user", user_router, "/user"),
    ("monitoring", monitoring_router, "/monitor")
]

__all__ = [
    "auth_router",
    "trust_router", 
    "user_router",
    "monitoring_router",
    "__routers__"
]

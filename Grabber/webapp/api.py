from fastapi import APIRouter

# Import the refactored modular routes
from .routes.users import router as users_router
from .routes.harem import router as harem_router
from .routes.progression import router as progression_router
from .routes.shop import router as shop_router
from .routes.auth import router as auth_router

# Create Master Router
router = APIRouter()

# Include Sub-Routers
router.include_router(auth_router, tags=["auth"])
router.include_router(users_router, tags=["users"])
router.include_router(harem_router, tags=["harem"])
router.include_router(progression_router, tags=["progression"])
router.include_router(shop_router, tags=["shop"])

from fastapi import APIRouter

from .routes.auth import router as auth_router
from .routes.harem import router as harem_router
from .routes.progression import router as progression_router
from .routes.shop import router as shop_router
from .routes.staff import router as staff_router
from .routes.upload import router as upload_router
# Import the refactored modular routes
from .routes.users import router as users_router
from .routes.social import router as social_router
from .routes.minigames import router as minigames_router

# Create Master Router
router = APIRouter()

# Include Sub-Routers
router.include_router(auth_router, tags=["auth"])
router.include_router(users_router, tags=["users"])
router.include_router(harem_router, tags=["harem"])
router.include_router(progression_router, tags=["progression"])
router.include_router(shop_router, tags=["shop"])
router.include_router(social_router, tags=["social"])
router.include_router(minigames_router, tags=["minigames"])
router.include_router(staff_router, tags=["staff"])
router.include_router(upload_router, tags=["upload"])

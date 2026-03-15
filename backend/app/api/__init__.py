from fastapi import APIRouter, Depends
from .endpoints import router as endpoints_router
from .auth import router as auth_router, verify_token

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(endpoints_router, dependencies=[Depends(verify_token)])

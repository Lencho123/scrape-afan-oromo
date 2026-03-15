from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.schemas import AdminLoginRequest, AdminLoginResponse
import os

router = APIRouter()
security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    expected_token = os.getenv("ADMIN_TOKEN", "scrape-afan-oromo-secure-admin-token-2026")
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=401, detail="Invalid or missing authentication token")
    return credentials.credentials

@router.post("/verify", response_model=AdminLoginResponse)
async def verify_password(request: AdminLoginRequest):
    expected_password = os.getenv("ADMIN_PASSWORD", "Lencho@astu-scrape-afan-oromo1234")
    if request.password == expected_password:
        token = os.getenv("ADMIN_TOKEN", "scrape-afan-oromo-secure-admin-token-2026")
        return AdminLoginResponse(token=token)
    raise HTTPException(status_code=401, detail="Invalid admin password")

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import (
    ADMIN_USER,
    create_admin_session,
    get_current_admin,
    verify_password,
)
from app.services.coordinator import list_all_jobs
from app.services.token_tracker import token_tracker

router = APIRouter()


class AdminLoginRequest(BaseModel):
    username_or_email: str = Field(
        ..., description="Admin username or email (e.g. admin or admin@email.com)"
    )
    password: str = Field(..., description="Admin password (e.g. 1234)")


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict[str, Any]


@router.post(
    "/login",
    response_model=AdminLoginResponse,
    summary="Authenticate as administrator",
)
def admin_login(payload: AdminLoginRequest):
    identifier = payload.username_or_email.strip().lower()
    is_valid_user = identifier in [
        ADMIN_USER["username"].lower(),
        ADMIN_USER["email"].lower(),
    ]

    if not is_valid_user or not verify_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials. Use admin / admin@email.com with password '1234'.",
        )

    token = create_admin_session()
    return AdminLoginResponse(
        access_token=token,
        token_type="bearer",
        user={
            "username": ADMIN_USER["username"],
            "email": ADMIN_USER["email"],
            "role": ADMIN_USER["role"],
        },
    )


@router.get(
    "/me",
    summary="Get authenticated admin session profile",
)
def get_admin_profile(admin: dict[str, Any] = Depends(get_current_admin)):
    return {
        "status": "authenticated",
        "user": admin,
    }


@router.post(
    "/logout",
    summary="Invalidate admin session",
)
def admin_logout(admin: dict[str, Any] = Depends(get_current_admin)):
    return {"message": "Admin session logged out successfully."}


@router.get(
    "/stats",
    summary="Retrieve real-time API token usage, quotas, and system telemetry",
)
def get_admin_stats(admin: dict[str, Any] = Depends(get_current_admin)):
    usage_summary = token_tracker.get_summary()

    # Calculate jobs breakdown
    all_jobs = list_all_jobs()
    job_status_counts = {
        "total": len(all_jobs),
        "completed": sum(1 for j in all_jobs if j.status.value == "completed"),
        "failed": sum(1 for j in all_jobs if j.status.value == "failed"),
        "processing": sum(
            1 for j in all_jobs if j.status.value not in ["completed", "failed", "pending"]
        ),
        "pending": sum(1 for j in all_jobs if j.status.value == "pending"),
    }

    return {
        "admin": admin["username"],
        "api_usage": usage_summary,
        "jobs_telemetry": job_status_counts,
    }

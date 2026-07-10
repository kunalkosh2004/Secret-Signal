from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.users.models import User


router = APIRouter(
    prefix="/api/v1/votes",
    tags=["votes"],
)

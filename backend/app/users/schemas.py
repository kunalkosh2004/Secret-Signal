"""
Pydantic schemas for user data.

These define how user data is serialised to and validated from JSON.

TODO: Define schemas when you implement the User model.

Planned schemas:

    UserResponse
        - id: UUID or int
        - username: str
        - email: str
        - created_at: datetime

    (No password-related fields ever appear in response schemas.)

Design notes:
    - UserCreate is handled by the auth signup schema, not here,
      because password confirmation logic belongs in the auth domain.
    - Never return password_hash or any internal database fields.
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
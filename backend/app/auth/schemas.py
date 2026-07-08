"""
Pydantic schemas for authentication requests and responses.

These define what the API accepts and returns.
They are the contract between frontend and backend.

TODO: When you implement the handlers, add the proper field validators.

Planned schemas:

    SignupRequest
        - username: str  (validated: 2-30 chars, alphanumeric + underscores)
        - email: EmailStr (from pydantic, validates format)
        - password: str   (validated: min length, complexity)

    LoginRequest
        - email: EmailStr
        - password: str

    TokenResponse
        - access_token: str
        - token_type: str = "bearer"
        - user: UserResponse

Design rules:
    - Passwords are received, validated, and immediately hashed.
      The plaintext password is never logged, stored, or returned.
    - Email is normalised to lowercase before storage/comparison.
"""

from pydantic import BaseModel, EmailStr, field_validator
from app.users.schemas import UserResponse

class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2 or len(value) > 30:
            raise ValueError(
                "Username must be between 2 and 30 characters"
            )

        if not value.replace("_", "").isalnum():
            raise ValueError(
                "Username can contain only letters, numbers, and underscores"
            )

        return value


    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError(
                "Password must be at least 8 characters long"
            )

        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
"""
User service — business logic layer for user operations.

This layer sits between the auth/ API handlers and the user repository.
For simple read operations it may be thin; for signup/login it coordinates
hashing, validation, and token creation.

TODO: Implement after repository methods exist.

Planned:

    async def get_user_by_id(db, user_id)
    async def get_user_by_email(db, email)
    async def create_user(db, username, email, password_hash)
"""

# TODO: from app.users.repository import user_repository  (once implemented)
# TODO: from app.users.schemas import UserResponse

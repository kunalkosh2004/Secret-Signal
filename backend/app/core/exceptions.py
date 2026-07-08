"""
Application-level exceptions.

These are raised from service layers and caught by exception handlers
to return appropriate HTTP responses.
"""


class AppException(Exception):
    """Base application exception."""

    status_code: int = 500
    detail: str = "Internal server error"


class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found"


class ConflictError(AppException):
    status_code = 409
    detail = "Resource already exists"


class UnauthorizedError(AppException):
    status_code = 401
    detail = "Not authenticated"


class ForbiddenError(AppException):
    status_code = 403
    detail = "Not authorized"


class ValidationError(AppException):
    status_code = 422
    detail = "Validation failed"

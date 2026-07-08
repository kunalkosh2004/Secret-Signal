"""
OAuth schemas for external identity provider data.

Planned:

    GoogleUserInfo
    - sub: str  (unique Google account ID — the "subject" claim)
    - email: str
    - email_verified: bool
    - name: str | None
    - picture: str | None

Why use `sub` instead of email for identity linking?
    - Email addresses can change. Google's `sub` is a stable identifier
      tied to the Google account for its entire lifetime.
    - Relying only on email would break if the user changes their
      Google account email, or if two accounts somehow have the same email.
    - Always link to `sub`, then use email as a display/find helper.
"""

from typing import Optional

from pydantic import BaseModel, EmailStr


class GoogleUserInfo(BaseModel):
    sub: str
    email: EmailStr
    email_verified: bool
    name: Optional[str] = None
    picture: Optional[str] = None

"""
Google OAuth 2.0 / OpenID Connect integration.

Architecture:
    This module is called from the auth router's `/google/login` and
    `/google/callback` endpoints.

Flow (to implement):
    1. User clicks "Continue with Google" on the frontend.
    2. Frontend redirects to GET /api/v1/auth/google/login.
    3. Backend generates a random `state` value (for CSRF protection),
       stores it temporarily (Redis or DB), and builds the Google OAuth URL.
    4. Backend redirects the browser to Google's consent screen.
    5. Google authenticates the user.
    6. Google redirects to GET /api/v1/auth/google/callback?code=...&state=...
    7. Backend verifies `state` matches the stored value.
    8. Backend exchanges the `code` for tokens (POST to Google's token endpoint).
    9. Backend validates the ID token (JWT) — verify signature, issuer, audience.
    10. Backend extracts `sub` (Google user ID) and email from the ID token.
    11. Backend looks up `auth_identities` by provider + provider_subject.
    12. If found → log the user in.
    13. If not found → create a new local user + auth_identity record, then log in.
    14. Backend creates an application session/token.
    15. Backend redirects the browser to the frontend with the session.

Security notes (read carefully):
    - The `state` parameter prevents CSRF on the callback.
    - The `nonce` parameter in OpenID Connect prevents replay attacks.
    - Validate the ID token's signature using Google's public keys.
    - Validate the `aud` (audience) claim — it must match your client ID.
    - Validate the `iss` (issuer) claim — it must be https://accounts.google.com.
    - Never trust user-supplied data from the callback without verification.
    - The Google client secret must live ONLY in backend environment variables.

TODO: build_authorization_url(state: str) -> str
TODO: verify_google_token(code: str, state: str) -> GoogleUserInfo
"""

from urllib.parse import urlencode
import httpx
from google.auth.transport import requests
from google.oauth2 import id_token

from app.auth.oauth.schemas import GoogleUserInfo
from app.core.config import settings

def build_authorization_url(
    state: str,
    redirect_uri: str = None,
) -> str:
    redirect_uri = redirect_uri or settings.google_redirect_uri

    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    query_string = urlencode(params)

    return (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?{query_string}"
    )

async def verify_google_token(
    code: str,
) -> GoogleUserInfo:
    token_url = "https://oauth2.googleapis.com/token"

    token_data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_url,
            data=token_data,
        )

        response.raise_for_status()
        tokens = response.json()

    google_id_token = tokens.get("id_token")

    if google_id_token is None:
        raise ValueError("Google did not return an ID token")

    payload = id_token.verify_oauth2_token(
        google_id_token,
        requests.Request(),
        settings.google_client_id,
    )

    if not payload.get("email_verified", False):
        raise ValueError("Google email is not verified")

    return GoogleUserInfo(
        sub=payload["sub"],
        email=payload["email"],
        email_verified=payload["email_verified"],
        name=payload.get("name"),
        picture=payload.get("picture"),
    )
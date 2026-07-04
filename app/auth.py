import os
import time
from typing import Dict, Optional

from authlib.integrations.starlette_client import OAuth, OAuthError
from authlib.jose import jwt
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .models import User

oauth = OAuth()

PROVIDER_CONFIG = {
    "google": {
        "client_id": "GOOGLE_CLIENT_ID",
        "client_secret": "GOOGLE_CLIENT_SECRET",
        "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        "client_kwargs": {"scope": "openid email profile"},
    },
    "facebook": {
        "client_id": "FACEBOOK_CLIENT_ID",
        "client_secret": "FACEBOOK_CLIENT_SECRET",
        "authorize_url": "https://www.facebook.com/v17.0/dialog/oauth",
        "access_token_url": "https://graph.facebook.com/v17.0/oauth/access_token",
        "api_base_url": "https://graph.facebook.com/v17.0/",
        "client_kwargs": {"scope": "email public_profile"},
    },
    "apple": {
        "client_id": "APPLE_CLIENT_ID",
        "team_id": "APPLE_TEAM_ID",
        "key_id": "APPLE_KEY_ID",
        "private_key": "APPLE_PRIVATE_KEY",
        "server_metadata_url": "https://appleid.apple.com/.well-known/openid-configuration",
        "client_kwargs": {
            "scope": "name email",
            "response_type": "code id_token",
            "response_mode": "form_post",
        },
    },
}


def _env(name: str) -> str:
    return os.getenv(name, "")


def _build_apple_client_secret() -> Optional[str]:
    team_id = _env("APPLE_TEAM_ID")
    client_id = _env("APPLE_CLIENT_ID")
    key_id = _env("APPLE_KEY_ID")
    private_key = _env("APPLE_PRIVATE_KEY")
    if not all([team_id, client_id, key_id, private_key]):
        return None

    key = private_key.replace("\\n", "\n")
    headers = {"kid": key_id}
    claims = {
        "iss": team_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 15777000,
        "aud": "https://appleid.apple.com",
        "sub": client_id,
    }
    token = jwt.encode(headers, claims, key, algorithm="ES256")
    return token.decode() if isinstance(token, bytes) else token


def register_oauth_providers(oauth_client: OAuth) -> None:
    if _env("GOOGLE_CLIENT_ID") and _env("GOOGLE_CLIENT_SECRET"):
        oauth_client.register(
            name="google",
            client_id=_env("GOOGLE_CLIENT_ID"),
            client_secret=_env("GOOGLE_CLIENT_SECRET"),
            server_metadata_url=PROVIDER_CONFIG["google"]["server_metadata_url"],
            client_kwargs=PROVIDER_CONFIG["google"]["client_kwargs"],
        )

    if _env("FACEBOOK_CLIENT_ID") and _env("FACEBOOK_CLIENT_SECRET"):
        oauth_client.register(
            name="facebook",
            client_id=_env("FACEBOOK_CLIENT_ID"),
            client_secret=_env("FACEBOOK_CLIENT_SECRET"),
            authorize_url=PROVIDER_CONFIG["facebook"]["authorize_url"],
            access_token_url=PROVIDER_CONFIG["facebook"]["access_token_url"],
            api_base_url=PROVIDER_CONFIG["facebook"]["api_base_url"],
            client_kwargs=PROVIDER_CONFIG["facebook"]["client_kwargs"],
        )

    apple_client_secret = _build_apple_client_secret()
    if _env("APPLE_CLIENT_ID") and apple_client_secret:
        oauth_client.register(
            name="apple",
            client_id=_env("APPLE_CLIENT_ID"),
            client_secret=apple_client_secret,
            server_metadata_url=PROVIDER_CONFIG["apple"]["server_metadata_url"],
            client_kwargs=PROVIDER_CONFIG["apple"]["client_kwargs"],
        )


def get_available_providers(request: Request) -> Dict[str, bool]:
    return {
        "google": bool(_env("GOOGLE_CLIENT_ID") and _env("GOOGLE_CLIENT_SECRET")),
        "facebook": bool(_env("FACEBOOK_CLIENT_ID") and _env("FACEBOOK_CLIENT_SECRET")),
        "apple": bool(
            _env("APPLE_CLIENT_ID")
            and _env("APPLE_TEAM_ID")
            and _env("APPLE_KEY_ID")
            and _env("APPLE_PRIVATE_KEY")
        ),
    }


def authorize_provider(request: Request, provider: str):
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=404, detail=f"OAuth provider '{provider}' is not configured")
    redirect_uri = request.url_for("auth_callback", provider=provider)
    return client.authorize_redirect(request, redirect_uri)


async def handle_provider_callback(request: Request, provider: str, db: Session) -> User:
    client = oauth.create_client(provider)
    if not client:
        raise HTTPException(status_code=404, detail=f"OAuth provider '{provider}' is not configured")

    try:
        token = await client.authorize_access_token(request)
    except OAuthError as exc:
        raise HTTPException(status_code=400, detail=f"OAuth callback failed: {str(exc)}")

    if provider == "google":
        user_info = await client.parse_id_token(request, token)
    elif provider == "facebook":
        resp = await client.get("me?fields=id,email,name")
        user_info = resp.json()
    elif provider == "apple":
        user_info = await client.parse_id_token(request, token)
    else:
        raise HTTPException(status_code=400, detail="Unknown OAuth provider")

    if not user_info or not user_info.get("email"):
        raise HTTPException(status_code=400, detail="Unable to retrieve user email from provider")

    email = user_info.get("email")
    name = user_info.get("name") or ""
    provider_name = provider

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, provider=provider_name, name=name)
        db.add(user)
    else:
        user.provider = provider_name
        user.name = name or user.name
    db.commit()
    db.refresh(user)
    return user

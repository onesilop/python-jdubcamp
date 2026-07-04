import os
from fastapi import FastAPI, Depends, Request, HTTPException
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import User
from .auth import (
    oauth,
    register_oauth_providers,
    get_available_providers,
    authorize_provider,
    handle_provider_callback,
)

SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

app = FastAPI(title="JDubCamp Auth App", version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
register_oauth_providers(oauth)

Base.metadata.create_all(bind=engine)

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html><body><h1>JDubCamp Auth App</h1>
    <p>Sign in using Google, Facebook, or Apple.</p>
    <p>Set your provider credentials in the environment to enable real OAuth sign-in.</p>
    <p>Use <code>POST /auth/demo</code> to exercise login locally without external credentials.</p>
    </body></html>
    """

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/auth/providers")
def providers(request: Request):
    return get_available_providers(request)

@app.get("/auth/login/{provider}")
async def auth_login(provider: str, request: Request):
    return await authorize_provider(request, provider)

@app.api_route("/auth/callback/{provider}", methods=["GET", "POST"])
async def auth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    user = await handle_provider_callback(request, provider, db)
    return {
        "message": "authentication successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "provider": user.provider,
            "name": user.name,
        },
    }

@app.post("/auth/demo")
def demo_login(db: Session = Depends(get_db)):
    email = os.getenv("DEMO_EMAIL", "demo@example.com")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, provider="demo", name="Demo User")
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"message": "demo login successful", "user": {"id": user.id, "email": user.email, "provider": user.provider}}

@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "email": u.email, "provider": u.provider, "name": u.name} for u in users]

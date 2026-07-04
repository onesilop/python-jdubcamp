# JDubCamp Auth App

A Python FastAPI app with SQL backend and social login support for Google, Facebook, and Apple.

## Features

- FastAPI backend
- SQLAlchemy PostgreSQL-ready database layer
- Docker and Docker Compose support
- Dev container configuration
- OAuth-ready routes for Google, Facebook, and Apple
- Demo login endpoint for local testing

## Run locally with Docker

1. Copy `.env.example` to `.env`
2. Set provider credentials in `.env` for social login providers
3. Run:

```bash
docker compose up --build
```

4. Visit `http://localhost:8000`

## Routes

- `GET /` - landing page
- `GET /health` - health check
- `GET /auth/providers` - available providers
- `GET /auth/login/{provider}` - redirect to the provider login
- `POST /auth/demo` - demo login
- `GET /users` - list users

## Railway deployment

The project is configured to deploy with Railway using `railway.json` and the Dockerfile.

### Environment variables for Railway

Set the following Railway environment variables in your project settings:

- `DATABASE_URL`
- `SECRET_KEY`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `FACEBOOK_CLIENT_ID`
- `FACEBOOK_CLIENT_SECRET`
- `APPLE_CLIENT_ID`
- `APPLE_TEAM_ID`
- `APPLE_KEY_ID`
- `APPLE_PRIVATE_KEY`
- `DEMO_EMAIL`

If you do not configure the provider variables, the app will still start, but provider login endpoints will return a provider-not-configured error.

### Callback URLs

When registering OAuth apps, use these callback URLs for local and Railway deployment:

- Local development:
  - `http://localhost:8000/auth/callback/google`
  - `http://localhost:8000/auth/callback/facebook`
  - `http://localhost:8000/auth/callback/apple`

- Railway / production:
  - `https://<your-railway-app>.up.railway.app/auth/callback/google`
  - `https://<your-railway-app>.up.railway.app/auth/callback/facebook`
  - `https://<your-railway-app>.up.railway.app/auth/callback/apple`

### Provider setup checklist

#### Google

1. Create an OAuth 2.0 Client ID in Google Cloud Console.
2. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
3. Add both the local and Railway callback URLs to Authorized redirect URIs.

#### Facebook

1. Create a Facebook App in Meta for Developers.
2. Set `FACEBOOK_CLIENT_ID` and `FACEBOOK_CLIENT_SECRET`.
3. Add the callback URLs under Valid OAuth Redirect URIs.
4. Ensure the app is in development mode or approved for public use.

#### Apple

1. Create an App ID or Service ID in Apple Developer.
2. Generate a private key and keep the full key text in `APPLE_PRIVATE_KEY`.
3. Set `APPLE_CLIENT_ID`, `APPLE_TEAM_ID`, `APPLE_KEY_ID`, and `APPLE_PRIVATE_KEY`.
4. Add the callback URLs in your Apple Sign In settings.

### Local development notes

- Use `POST /auth/demo` to create a demo user without external provider setup.
- Use `.env` locally and `docker compose up --build` to start the app.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import os

from routers import (
    auth,
    organizations,
    projects,
    upload,
    mapping,
    draft,
    export,
    ai_providers,
    jobs,
    templates,
)

def get_org_user_key(request) -> str:
    user = getattr(request.state, "user", None)
    org_id = request.path_params.get("org_id") or (getattr(user, "current_org_id", None) if user else None) or "unknown"
    user_id = getattr(user, "id", "anonymous") if user else "anonymous"
    return f"{org_id}:{user_id}"

limiter = Limiter(key_func=get_org_user_key)

app = FastAPI(title="FinDraft AI API", version="1.0.0")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS — ปรับ origins ก่อน go live
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(organizations.router, prefix="/organizations", tags=["organizations"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(upload.router, prefix="/projects", tags=["upload"])
app.include_router(mapping.router, prefix="/projects", tags=["mapping"])
app.include_router(draft.router, prefix="/projects", tags=["draft"])
app.include_router(export.router, prefix="/projects", tags=["export"])
app.include_router(jobs.router, prefix="/projects", tags=["jobs"])
app.include_router(templates.router, prefix="/templates", tags=["templates"])
app.include_router(ai_providers.router, prefix="/organizations", tags=["ai-providers"])


@app.get("/health")
async def health():
    return {"status": "ok"}

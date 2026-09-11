from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.routers import auth, profile, fridge, suggestions
from app.routers.profile_router import router as profile_router
from app.routers.recipe_router import router as recipe_router
from app.core.deps import get_current_user_optional
from app.json_store import get_profiles, get_fridges

app = FastAPI(title="Smart Fridge & Nutrition Coach")

# Dynamic Static & Templates setup
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ingestion de tous les routeurs
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(profile_router)
app.include_router(recipe_router)
app.include_router(fridge.router)
app.include_router(suggestions.router)

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/", response_class=HTMLResponse)
def index(request: Request, user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    profiles = get_profiles()
    user_profile = next((p for p in profiles if p.get("user_id") == user_id), None)
    
    fridges = get_fridges()
    user_fridge = next((f for f in fridges if f.get("user_id") == user_id), None)
    ingredients = user_fridge.get("ingredients", []) if user_fridge else []

    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"profile": user_profile, "ingredients": ingredients}
    )

@app.get("/profile-page", response_class=HTMLResponse)
def profile_page(request: Request, user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    profiles = get_profiles()
    user_profile = next((p for p in profiles if p.get("user_id") == user_id), None)

    return templates.TemplateResponse(
        request=request, 
        name="profile.html", 
        context={"profile": user_profile}
    )
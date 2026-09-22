from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.routers import auth, profile, fridge, suggestions
from app.routers.recipe_router import router as recipe_router
from app.routers.profile import calculate_calories  
from app.core.deps import get_current_user_optional
from app.database import supabase
from app.routers import journal

app = FastAPI(title="Smart Fridge & Nutrition Coach")

# Fichiers statiques et templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(fridge.router)
app.include_router(suggestions.router)
app.include_router(recipe_router)
app.include_router(journal.router)

def format_profile_for_template(profile_data: dict | None) -> dict | None:
    """Helper pour mapper 'weight'/'height' et recalculer BMR/TDEE pour Jinja2"""
    if not profile_data:
        return None
    
    weight = profile_data.get("weight", 0)
    height = profile_data.get("height", 0)
    age = profile_data.get("age", 0)
    gender = profile_data.get("gender", "male")
    activity_level = profile_data.get("activity_level", "sedentary")
    goal = profile_data.get("goal", "maintain")

    # Recalcul de BMR et TDEE pour le rendu HTML
    calc = calculate_calories(weight, height, age, gender, activity_level, goal)
    profile_data.update(calc)

    # Mappage des variables attendues dans les templates Jinja2
    profile_data["weight_kg"] = weight
    profile_data["height_cm"] = height

    return profile_data

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/", response_class=HTMLResponse)
def index(request: Request, user_id: str | None = Depends(get_current_user_optional)):
    print(f"\n[MAIN DEBUG] Chargement du dashboard pour user_id: {user_id}")
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    # Récupération du profil depuis Supabase
    profile_res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
    raw_profile = profile_res.data[0] if profile_res.data else None
    user_profile = format_profile_for_template(raw_profile)
    
    # Récupération du frigo depuis Supabase
    fridge_res = supabase.table("fridge_items").select("ingredient").eq("user_id", user_id).execute()
    ingredients = [row["ingredient"] for row in fridge_res.data] if fridge_res.data else []

    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"profile": user_profile, "ingredients": ingredients}
    )

@app.get("/profile-page", response_class=HTMLResponse)
def profile_page(request: Request, user_id: str | None = Depends(get_current_user_optional)):
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    profile_res = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
    raw_profile = profile_res.data[0] if profile_res.data else None
    user_profile = format_profile_for_template(raw_profile)

    return templates.TemplateResponse(
        request=request, 
        name="profile.html", 
        context={"profile": user_profile}
    )
from fastapi import FastAPI
from app.routers.profile_router import router as profile_router
from app.routers.recipe_router import router as recipe_router

app = FastAPI(title="Smart Fridge & Nutrition Coach")

app.include_router(profile_router)
app.include_router(recipe_router)

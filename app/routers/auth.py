import uuid
from fastapi import APIRouter, HTTPException, Response, status
from app.schemas.user import UserCreate, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.json_store import get_users, save_users

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register")
def register(user_data: UserCreate):
    users = get_users()
    if any(u["email"] == user_data.email for u in users):
        raise HTTPException(status_code=400, detail="Email déjà enregistré")
    
    user_id = str(uuid.uuid4())
    new_user = {
        "id": user_id, 
        "email": user_data.email, 
        "password": hash_password(user_data.password)
    }
    users.append(new_user)
    save_users(users)
    return {"message": "Utilisateur créé avec succès"}

@router.post("/login", response_model=Token)
def login(response: Response, user_data: UserCreate):
    users = get_users()
    user = next((u for u in users if u["email"] == user_data.email), None)
    if not user or not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=400, detail="Identifiants incorrects")
    
    token = create_access_token({"sub": user["id"]})
    response.set_cookie(key="access_token", value=token, httponly=True)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    return {"message": "Déconnexion réussie"}
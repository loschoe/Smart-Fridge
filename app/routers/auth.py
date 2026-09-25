from fastapi import APIRouter, HTTPException, Response, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.database import supabase
from app.core.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel, EmailStr, ValidationError

router = APIRouter(tags=["Auth"])

# Valide une adresse email via Pydantic.
# Permet d'avoir un message d'erreur propre et cohérent.
def validate_email_address(email_str: str) -> str:
    class EmailModel(BaseModel):
        email: EmailStr

    try:
        validated = EmailModel(email=email_str)
        return validated.email
    except ValidationError:
        raise HTTPException(
            status_code=422,
            detail="Format d'adresse email invalide (exemple requis : nom@domaine.com)."
        )

# Inscription utilisateur.
# Double décorateur pour supporter deux routes différentes.
@router.post("/signup")
@router.post("/auth/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None):
    raw_email = form_data.username.strip().lower()
    email = validate_email_address(raw_email)
    password = form_data.password

    existing = supabase.table("users").select("id").eq("email", email).execute()
    if existing.data:
        raise HTTPException(status_code=400, detail="Cet email est déjà utilisé.")

    try:
        new_user = supabase.table("users").insert({
            "email": email,
            "hashed_password": hash_password(password)
        }).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur Supabase : {str(e)}")

    user_id = str(new_user.data[0]["id"])
    token = create_access_token({"sub": user_id})

    if response:
        response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)

    return {"access_token": token, "token_type": "bearer", "message": f"Compte créé pour {email}"}

# Connexion utilisateur.
@router.post("/token")
@router.post("/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), response: Response = None):
    raw_email = form_data.username.strip().lower()
    email = validate_email_address(raw_email)
    password = form_data.password

    res = supabase.table("users").select("*").eq("email", email).execute()
    if not res.data:
        raise HTTPException(status_code=400, detail="Identifiants incorrects.")

    user = res.data[0]
    
    if not verify_password(password, user.get("hashed_password", "")):
        raise HTTPException(status_code=400, detail="Identifiants incorrects.")

    token = create_access_token({"sub": str(user["id"])})

    if response:
        response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)

    return {"access_token": token, "token_type": "bearer"}

# Déconnexion : suppression du cookie JWT.
@router.post("/logout")
@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Déconnexion réussie"}
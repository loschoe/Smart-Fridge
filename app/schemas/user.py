from pydantic import BaseModel, EmailStr

# Modèle utilisé lors de la création d'un utilisateur.
# EmailStr garantit un format valide.
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Réponse renvoyée après création ou récupération d'un utilisateur.
class UserResponse(BaseModel):
    id: str
    email: EmailStr

# Token JWT renvoyé après authentification.
class Token(BaseModel):
    access_token: str
    token_type: str
    
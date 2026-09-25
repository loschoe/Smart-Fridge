from fastapi import Request, HTTPException, status, Depends
from app.core.security import decode_access_token

# Récupère l'utilisateur courant si un access_token est présent dans les cookies.
# Ne lève pas d'erreur : utilisé pour les routes où l'auth est optionnelle.
def get_current_user_optional(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    payload = decode_access_token(token)
    if not payload:
        return None
        
    return payload.get("sub")

# Variante stricte : exige un utilisateur authentifié.
# Utilisée pour les routes protégées.
def get_current_user(user_id: str | None = Depends(get_current_user_optional)) -> str:
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        )
    return user_id
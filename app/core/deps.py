from fastapi import Request, HTTPException, status, Depends
from app.core.security import decode_access_token

def get_current_user_optional(request: Request) -> str | None:
    # Récupère le cookie access_token
    token = request.cookies.get("access_token")
    if not token:
        return None
    
    # Si le token contient "Bearer ", on le nettoie
    if token.startswith("Bearer "):
        token = token.split(" ")[1]
        
    payload = decode_access_token(token)
    if not payload:
        return None
        
    return payload.get("sub")

def get_current_user(user_id: str | None = Depends(get_current_user_optional)) -> str:
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        )
    return user_id
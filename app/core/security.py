import datetime
import hashlib
from jose import jwt, JWTError
from app.config import settings

# Hash SHA‑256 simple. Suffisant pour un projet interne, mais à remplacer
# par un algo avec salt (bcrypt/argon2) si tu gères de vrais utilisateurs.
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# Compare un mot de passe en clair avec son hash.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

# Génère un JWT avec date d’expiration.
# Le payload est enrichi avec "exp" en timestamp UNIX.
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": int(expire.timestamp())})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

# Décode un JWT. Retourne None si invalide ou expiré.
def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError:
        return None
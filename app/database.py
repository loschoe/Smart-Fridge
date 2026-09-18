import os
from dotenv import load_dotenv
from supabase import create_client, Client
from app.config import settings

load_dotenv()

SUPABASE_URL = settings.supabase_url or os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = settings.supabase_key or os.getenv("SUPABASE_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL ou SUPABASE_KEY manquante")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
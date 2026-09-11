import json
from pathlib import Path
from typing import Any, List, Dict

DATA_DIR = Path(__file__).parent / "data"

def _read_json(filename: str) -> List[Dict[str, Any]]:
    filepath = DATA_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def _write_json(filename: str, data: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Métiers JSON
def get_users(): return _read_json("users.json")
def save_users(users): _write_json("users.json", users)

def get_profiles(): return _read_json("profiles.json")
def save_profiles(profiles): _write_json("profiles.json", profiles)

def get_fridges(): return _read_json("fridge.json")
def save_fridges(fridges): _write_json("fridge.json", fridges)
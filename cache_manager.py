import os
import json
import hashlib

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".quizlab_cache")

def _get_hash(text, custom_focus=""):
    """
    Generate an MD5 hash of the input text and custom focus keywords.
    """
    hasher = hashlib.md5()
    hasher.update(text.encode("utf-8", errors="ignore"))
    hasher.update(custom_focus.strip().encode("utf-8", errors="ignore"))
    return hasher.hexdigest()

def get_cached_material(text, custom_focus=""):
    """
    Attempts to read cached JSON learning material for the given text and focus.
    Returns the parsed dict if successful, otherwise None.
    """
    if not os.path.exists(CACHE_DIR):
        return None
        
    cache_key = _get_hash(text, custom_focus)
    cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def set_cached_material(text, custom_focus, data):
    """
    Saves the generated learning material JSON locally.
    """
    try:
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR, exist_ok=True)
            
        cache_key = _get_hash(text, custom_focus)
        cache_path = os.path.join(CACHE_DIR, f"{cache_key}.json")
        
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

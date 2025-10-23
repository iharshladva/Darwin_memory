from functools import lru_cache

@lru_cache(maxsize=1024)
def cached_embed_key(text: str):
    
    return text

@lru_cache(maxsize=256)
def cached_retrieval_key(user_id: str, task: str, query: str, modalities_key: str, must_share: bool):
    return f"{user_id}|{task}|{query}|{modalities_key}|{must_share}"

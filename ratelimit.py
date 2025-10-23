import time
WINDOW = 60  
MAX_REQ = 20
BUCKET = {}

def allow(user_id: str) -> bool:
    now = time.time()
    t, n = BUCKET.get(user_id, (now, 0))
    if now - t > WINDOW:
        BUCKET[user_id] = (now, 1); return True
    if n < MAX_REQ:
        BUCKET[user_id] = (t, n+1); return True
    return False

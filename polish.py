import math, time, json

def iso_now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ")

def age_days(iso_ts: str) -> float:
    
    try:
        y, m, d = int(iso_ts[:4]), int(iso_ts[5:7]), int(iso_ts[8:10])
        
        return max(0, (time.time() - time.mktime((y, m, d, 0, 0, 0, 0, 0, 0))) / 86400.0)
    except:
        return 0.0

def decay_by_ttl(created_at: str, ttl_days: int | None) -> float:
    if not ttl_days or ttl_days <= 0:
        
        return 0.5
    age = age_days(created_at)
   
    return math.exp(-age / max(1.0, ttl_days))

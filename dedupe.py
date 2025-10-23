import json, numpy as np
from util import embed
import time, uuid

SIM_THRESHOLD = 0.90  

def maybe_merge(conn, user_id: str, text: str, source_id: str, tags, ttl_days, confidence, modality="text"):
   
    from darwin_memory.storage import get_conn
    v = embed(text).astype("float32")
    
    rows = conn.execute("SELECT * FROM memories WHERE user_id=?", (user_id,)).fetchall()
    best_id, best_sim = None, 0.0
    for r in rows:
        if r["modality"] != modality: continue
        if r["embedding"] is None: continue
        rv = np.frombuffer(r["embedding"], dtype="float32")
        sim = float(np.dot(v, rv))
        if sim > best_sim:
            best_sim, best_id = sim, r["memory_id"]
    if best_sim >= SIM_THRESHOLD:
        
        new_conf = min(0.98, (r["confidence"] or 0.8) + 0.02)
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        conn.execute("UPDATE memories SET confidence=?, updated_at=? WHERE memory_id=?",
                     (new_conf, now, best_id))
        ev_id = f"e_{uuid.uuid4().hex[:10]}"
        conn.execute("INSERT INTO evidence(evidence_id,memory_id,raw_excerpt,explanation,timestamp) VALUES(?,?,?,?,?)",
                     (ev_id, best_id, text, "Merged duplicate", now))
        conn.commit()
        return best_id  
    return None  

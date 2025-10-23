import uuid, time, json, numpy as np
from util import embed, extract_keywords
from storage import get_conn

def ingest_image_caption(conn, user_id: str, caption: str, source_id: str, tags=None, ttl_days=365, confidence=0.88):
    """Ingest image caption/metadata as a Memory + Evidence entry."""
    mem_id = f"m_{uuid.uuid4().hex[:10]}"
    ev_id  = f"e_{uuid.uuid4().hex[:10]}"
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")

    kw = extract_keywords(caption)
    vec = embed(caption)
    vec_bytes = vec.astype("float32").tobytes()

    conn.execute("""
        INSERT INTO memories(memory_id,user_id,type,value,modality,source_id,embedding,keywords,
            confidence,freshness_score,ttl,tags,pii_sensitivity,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (mem_id,user_id,"fact",caption,"image",source_id,vec_bytes,
          json.dumps(kw),confidence,1.0,ttl_days,json.dumps(tags or ["general_interest"]),
          "none",now,now))

    conn.execute("INSERT INTO memories_fts(memory_id,value) VALUES(?,?)", (mem_id,caption))

    conn.execute("""
        INSERT INTO evidence(evidence_id,memory_id,raw_excerpt,explanation,timestamp)
        VALUES(?,?,?,?,?)
    """, (ev_id,mem_id,caption,"Image caption metadata",now))

    conn.commit()
    return mem_id

import json, time

def sweep_retention(conn):
    tags = {r["name"]: r["retention_days"] for r in conn.execute("SELECT * FROM policy_tags")}
    rows = conn.execute("SELECT memory_id, tags, created_at FROM memories").fetchall()
    to_delete = []
    now = time.time()
    for r in rows:
        m_tags = set(json.loads(r["tags"] or "[]"))
        rdays = min([tags.get(t, 365) for t in m_tags]) if m_tags else 365
        if rdays <= 0:
            to_delete.append(r["memory_id"])
            continue
        
        y, m, d = int(r["created_at"][:4]), int(r["created_at"][5:7]), int(r["created_at"][8:10])
        age_days = max(0, (now - time.mktime((y,m,d,0,0,0,0,0,0))) / 86400.0)
        if age_days > rdays:
            to_delete.append(r["memory_id"])
    for mid in to_delete:
        conn.execute("DELETE FROM evidence WHERE memory_id=?", (mid,))
        conn.execute("DELETE FROM memories_fts WHERE memory_id=?", (mid,))
        conn.execute("DELETE FROM memories WHERE memory_id=?", (mid,))
    conn.commit()
    return {"deleted": len(to_delete), "ids": to_delete}

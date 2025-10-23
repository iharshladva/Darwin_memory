from fastapi import APIRouter
from storage import get_conn

router = APIRouter()
conn = get_conn()

@router.delete("/delete_memory/{memory_id}")
def delete_memory(memory_id: str):
    cur = conn.execute("DELETE FROM memories WHERE memory_id=?", (memory_id,))
    conn.execute("DELETE FROM memories_fts WHERE memory_id=?", (memory_id,))
    conn.execute("DELETE FROM evidence WHERE memory_id=?", (memory_id,))
    conn.commit()
    return {"deleted": cur.rowcount}

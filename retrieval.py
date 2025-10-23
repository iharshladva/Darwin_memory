import json, math, time, uuid
import numpy as np

from typing import List, Dict, Any, Tuple, Optional
from util import embed

TRACE: dict[str, dict] = {}  # request_id -> trace dict

def _from_blob(b: bytes) -> np.ndarray:
    if b is None:
        return None
    v = np.frombuffer(b, dtype="float32")

    if v.size == 0:
        return None

    return v

def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    if a is None or b is None:
        return 0.0

    return float(np.dot(a, b))

def _token_estimate(text: str) -> int:

    return max(1, int(len((text or "").split()) * 1.3))

def _compact(rows, token_budget: int, item_budget: int):
    out, used_tokens = [], 0
    for r in rows:
        t = _token_estimate(r["value"])
        if len(out) >= item_budget:
            break
        if used_tokens + t > token_budget:
            continue
        out.append(r)
        used_tokens += t
    return out, {"used_tokens": used_tokens, "used_items": len(out)}

def _allowed_for_task(conn, mem_row, task: str, must_shareable: bool, modalities: Optional[List[str]]):
    # modality filter
    if modalities and mem_row["modality"] not in modalities:
        return False, "modality_not_allowed"

    if not must_shareable:
        return True, "ok"


    llm_tasks = {"chat_reply", "video_style_selection"}
    flag = "shareable_with_llm" if task in llm_tasks else "shareable_with_recsys"

   
    tag_perms = {r["name"]: bool(r[flag]) for r in conn.execute(f"SELECT name,{flag} FROM policy_tags").fetchall()}

    tags = set(json.loads(mem_row["tags"] or "[]"))
    for t in tags:
        if t in tag_perms and not tag_perms[t]:
            return False, f"policy_block:{t}"
    return True, "ok"

def _keyword_candidates(conn, query: str, limit: int = 50):

    sql = """
      SELECT m.*
      FROM memories m
      JOIN memories_fts f ON m.memory_id = f.memory_id
      WHERE f.value MATCH ?
      LIMIT ?
    """
    return conn.execute(sql, (query, limit)).fetchall()

def _vector_candidates(conn, qvec: np.ndarray, limit: int = 50):
    sims: List[Tuple[Any, float]] = []
  
    for r in conn.execute("SELECT memory_id, embedding FROM memories"):
        v = _from_blob(r["embedding"])
        sims.append((r["memory_id"], _cosine(qvec, v)))
    sims.sort(key=lambda x: x[1], reverse=True)
    ids = [mid for (mid, _) in sims[:limit]]
    if not ids:
        return [], {}

    q = "SELECT * FROM memories WHERE memory_id IN ({})".format(",".join(["?"] * len(ids)))
    rows = conn.execute(q, ids).fetchall()
    sim_map = {mid: s for (mid, s) in sims[:limit]}
    return rows, sim_map

def _score(sim: float, freshness: float, confidence: float) -> float:
  
    return 0.55 * sim + 0.25 * (freshness or 0.0) + 0.20 * (confidence or 0.0)

def retrieve_context(conn,
                     user_id: str,
                     task: str,
                     query: str,
                     budget: Dict[str, int] = {"tokens": 1200, "items": 15},
                     constraints: Dict[str, Any] = {"must_shareable": True, "modalities": None}):
    """
    Returns: {"request_id": "...", "context_pack": {...}}
    """
    rid = f"r_{uuid.uuid4().hex[:8]}"
    must_shareable = bool(constraints.get("must_shareable", True))
    modalities = constraints.get("modalities", None)


    qvec = embed(query)


    kw_rows = _keyword_candidates(conn, query, limit=50)
    vc_rows, sim_map = _vector_candidates(conn, qvec, limit=50)


    seen, candidates, drops = set(), [], []
    for r in list(kw_rows) + list(vc_rows):
        mid = r["memory_id"]
        if mid in seen:
            continue
        seen.add(mid)
        sim = float(sim_map.get(mid, 0.0))
       
        if r["user_id"] != user_id:
            drops.append((mid, "user_mismatch"))
            continue
        ok, reason = _allowed_for_task(conn, r, task, must_shareable, modalities)
        if not ok:
            drops.append((mid, reason))
            continue
        candidates.append((r, sim))


    ranked = sorted(
        candidates,
        key=lambda t: _score(t[1], t[0]["freshness_score"], t[0]["confidence"]),
        reverse=True
    )

    final_rows = [r for (r, _) in ranked]
    packed, budget_report = _compact(
        final_rows,
        token_budget=int(budget.get("tokens", 1200)),
        item_budget=int(budget.get("items", 15))
    )

   
    memories = []
    for r in packed:
        memories.append({
            "memory_id": r["memory_id"],
            "value": r["value"],
            "confidence": r["confidence"],
            "freshness": r["freshness_score"],
            "modality": r["modality"],
            "policy": json.loads(r["tags"] or "[]"),
            "why": f"vector sim: {sim_map.get(r['memory_id'], 0.0):.2f}; policy ok; user match"
        })


    TRACE[rid] = {
        "input": {
            "user_id": user_id, "task": task, "query": query,
            "budget": budget, "constraints": constraints
        },
        "candidates": [t[0]["memory_id"] for t in ranked],
        "drops": drops,
        "final": [m["memory_id"] for m in memories],
        "budget": budget_report
    }

    return {
        "request_id": rid,
        "context_pack": {
            "user_id": user_id,
            "task": task,
            "memories": memories,
            "budget_report": budget_report
        }
    }

def explain(request_id: str) -> dict:
    return TRACE.get(request_id, {"error": "request_id not found"})

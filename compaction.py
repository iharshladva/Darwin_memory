import json

def token_estimate(text: str) -> int:
    return max(1, int(len((text or "").split()) * 1.3))

def compact(mem_rows, token_budget=1200, item_budget=15):
    out, used_tokens = [], 0
    seen_sig = set()
    for r in mem_rows:
        
        kws = json.loads(r["keywords"] or "[]")
        sig = (tuple(sorted(kws[:5])), r["modality"])
        if sig in seen_sig:
            continue
        t = token_estimate(r["value"])
        if len(out) >= item_budget:
            break
        if used_tokens + t > token_budget:
            continue
        out.append(r); used_tokens += t; seen_sig.add(sig)
    return out, {"used_tokens": used_tokens, "used_items": len(out)}

def task_weights(task: str):
    # (similarity, freshness, confidence)
    if task == "video_style_selection":
        return 0.55, 0.25, 0.20  
    if task == "chat_reply":
        return 0.60, 0.15, 0.25  
    if task == "feed_ranking":
        return 0.45, 0.40, 0.15  
    return 0.55, 0.25, 0.20

def score(task: str, similarity: float, freshness: float, confidence: float) -> float:
    ws = task_weights(task)
    return ws[0]*similarity + ws[1]*(freshness or 0.0) + ws[2]*(confidence or 0.0)

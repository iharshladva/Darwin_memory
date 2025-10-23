from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from storage import get_conn
from retrieval import retrieve_context as _retrieve_context
from retrieval import explain as _explain

router = APIRouter()
conn = get_conn()  
class Budget(BaseModel):
    tokens: int = Field(1200, ge=1)
    items: int = Field(15, ge=1)

class Constraints(BaseModel):
    must_shareable: bool = True
    modalities: Optional[List[str]] = None

class RetrieveRequest(BaseModel):
    user_id: str
    task: str
    query: str
    budget: Budget = Budget()
    constraints: Constraints = Constraints()

@router.post("/retrieve_context")
def retrieve_context(body: RetrieveRequest):
    return _retrieve_context(
        conn,
        user_id=body.user_id,
        task=body.task,
        query=body.query,
        budget=body.budget.model_dump(),
        constraints=body.constraints.model_dump()
    )

@router.get("/explain/{request_id}")
def explain(request_id: str):
    tr = _explain(request_id)
    if "error" in tr:
        raise HTTPException(status_code=404, detail=tr["error"])
    return tr


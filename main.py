from fastapi import FastAPI
from api import router as api_router
from admin_api import router as admin_router

app = FastAPI(title="Darwin Memory System (POC)")

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

app.include_router(api_router)
app.include_router(admin_router)

from fastapi import FastAPI
from app.controllers.auth_controller import router as auth_router

app = FastAPI(title="Orpheus API")

@app.get("/ping")
async def ping():
    return {"status": "pong"}

app.include_router(auth_router)
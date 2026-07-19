from fastapi import FastAPI
from app.controllers.auth_controller import router as auth_router
from app.controllers.device_controller import router as device_router
from app.controllers.vinyl_controller import router as vinyl_router
from app.controllers.resource_controller import router as resource_router

app = FastAPI(title="Orpheus API")

@app.get("/ping")
async def ping():
    return {"status": "pong"}

app.include_router(auth_router)
app.include_router(device_router)
app.include_router(vinyl_router)
app.include_router(resource_router)
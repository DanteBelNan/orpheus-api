from fastapi import FastAPI

app = FastAPI(title="Orpheus API")

@app.get("/ping")
async def ping():
    return {"status": "pong"}
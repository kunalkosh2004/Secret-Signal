from fastapi import FastAPI

app = FastAPI(title="Secret Signal Backend")


@app.get("/health")
async def health():
    return {"status": "ok"}
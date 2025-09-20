# main.py
from fastapi import FastAPI
from datetime import datetime

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, World!"}


@app.get("/api/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"}

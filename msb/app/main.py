from fastapi import FastAPI
from data import meldingen
app = FastAPI()


@app.get("/api/")
async def root():
    return meldingen()
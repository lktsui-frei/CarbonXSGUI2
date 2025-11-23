from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import fitting

app = FastAPI(title="CarbonXS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(fitting.router, prefix="/api", tags=["fitting"])

@app.get("/")
def read_root():
    return {"message": "CarbonXS API is running"}

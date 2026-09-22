from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from routers import jobs, downloads, settings

app = FastAPI(
    title="Octagora — Extração Consolidada (SP + ES)",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(jobs.router)
app.include_router(downloads.router)
app.include_router(settings.router)

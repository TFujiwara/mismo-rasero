from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Sistema Operativo de España — API",
        description="Blueprint técnico v2.5 — transparencia administrativa con fuente citada",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.get("/")
    def root():
        return {"proyecto": "blueprint", "docs": "/docs", "api": "/api/v1"}

    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)

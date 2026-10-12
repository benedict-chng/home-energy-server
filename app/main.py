"""FastAPI app entrypoint."""

from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import engine, get_session
from app.ingest.router import router as ingest_router
from app.query.router import router as query_router


@asynccontextmanager
async def lifespan(app):
    yield
    await engine.dispose()


def create_app() -> "FastAPI":
    from fastapi import FastAPI

    app = FastAPI(title="PowerPal Server", version="0.1.0", lifespan=lifespan)

    @app.get("/healthz", tags=["ops"])
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz", tags=["ops"])
    async def readyz(session: AsyncSession = Depends(get_session)) -> dict:
        await session.execute(text("SELECT 1"))
        return {"status": "ready"}

    app.include_router(ingest_router)
    app.include_router(query_router)
    return app


app = create_app()

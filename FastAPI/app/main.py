import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.core.database import init_db, SessionLocal
from app.api.v1 import api_router
from app.services import LinkService


def _run_cleanup_inactive() -> None:
    db = SessionLocal()
    try:
        LinkService(db, base_url='').cleanup_inactive()
    finally:
        db.close()


async def _cleanup_loop() -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run_cleanup_inactive)
    while True:
        await asyncio.sleep(settings.cleanup_interval_hours * 3600)
        await loop.run_in_executor(None, _run_cleanup_inactive)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.include_router(api_router, prefix='/api/v1')


@app.get('/health')
def health():
    return {'status': 'ok'}

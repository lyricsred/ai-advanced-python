from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.core.database import init_db
from app.api.v1 import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.include_router(api_router, prefix='/api/v1')


@app.get('/health')
def health():
    return {'status': 'ok'}

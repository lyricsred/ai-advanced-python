import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

_test_db = Path(__file__).resolve().parent.parent / 'test_db.sqlite'
os.environ['DATABASE_URL'] = f'sqlite:///{_test_db}'
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/15')

root = Path(__file__).resolve().parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))


class FakeCache:
    def get(self, key: str):
        return None

    def set(self, key: str, value, ttl=None):
        pass

    def delete(self, key: str):
        pass

    def delete_pattern(self, pattern: str):
        pass


@pytest.fixture
def client():
    from app.main import app
    from app.core.database import SessionLocal, init_db
    from app.models.link import Link
    from app.models.user import User

    with patch('app.services.link_service.cache', FakeCache()):
        init_db()
        db = SessionLocal()
        try:
            db.query(Link).delete()
            db.query(User).delete()
            db.commit()
        finally:
            db.close()
        from fastapi.testclient import TestClient
        yield TestClient(app)


@pytest.fixture
def auth_headers(client):
    client.post('/api/v1/auth/register', json={
        'email': 'test@example.com',
        'password': 'secret123',
    })
    r = client.post('/api/v1/auth/login', json={
        'email': 'test@example.com',
        'password': 'secret123',
    })
    assert r.status_code == 200
    token = r.json()['access_token']
    return {'Authorization': f'Bearer {token}'}

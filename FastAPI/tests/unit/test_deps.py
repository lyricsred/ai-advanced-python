from unittest.mock import MagicMock, patch

import pytest

from app.api.deps import get_link_service, get_user_service
from app.services import LinkService, UserService


class TestGetLinkService:
    def test_returns_link_service_with_base_url_from_request(self):
        request = MagicMock()
        request.base_url = 'https://api.example.com/'
        db = MagicMock()
        svc = get_link_service(request, db=db)
        assert isinstance(svc, LinkService)
        assert svc.db is db
        assert svc.base_url == 'https://api.example.com'

    def test_without_request_uses_empty_base_url(self):
        db = MagicMock()
        svc = get_link_service(None, db=db)
        assert svc.base_url == ''

    def test_strips_trailing_slash(self):
        request = MagicMock()
        request.base_url = 'https://x.com/'
        db = MagicMock()
        svc = get_link_service(request, db=db)
        assert svc.base_url == 'https://x.com'


class TestGetUserService:
    def test_returns_user_service_with_db(self):
        db = MagicMock()
        svc = get_user_service(db=db)
        assert isinstance(svc, UserService)
        assert svc.db is db

    def test_get_link_service_with_db_none_uses_get_db(self):
        mock_db = MagicMock()
        with patch('app.api.deps.get_db', return_value=iter([mock_db])):
            request = MagicMock()
            request.base_url = 'http://test'
            svc = get_link_service(request, db=None)
        assert isinstance(svc, LinkService)
        assert svc.db is mock_db

    def test_get_user_service_with_db_none_uses_get_db(self):
        mock_db = MagicMock()
        with patch('app.api.deps.get_db', return_value=iter([mock_db])):
            svc = get_user_service(db=None)
        assert svc.db is mock_db

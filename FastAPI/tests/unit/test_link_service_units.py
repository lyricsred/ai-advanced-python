import string
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.models.link import Link
from app.schemas.link import LinkCreate, LinkUpdate
from app.services.link_service import (
    LinkService,
    _generate_short_code,
    _is_expired,
)


VALID_ALPHABET = set(string.ascii_lowercase + string.digits)


class TestGenerateShortCode:
    def test_length_uses_settings_when_zero(self):
        with patch('app.services.link_service.settings') as mock_settings:
            mock_settings.short_code_length = 8
            code = _generate_short_code(0)
        assert len(code) == 8

    def test_length_explicit(self):
        code = _generate_short_code(5)
        assert len(code) == 5

    def test_characters_from_alphabet_only(self):
        code = _generate_short_code(20)
        assert set(code) <= VALID_ALPHABET
        assert len(code) == 20

    def test_different_calls_produce_different_codes(self):
        codes = [_generate_short_code(6) for _ in range(50)]
        assert len(set(codes)) > 1

    def test_default_length_from_settings(self):
        with patch('app.services.link_service.settings') as mock_settings:
            mock_settings.short_code_length = 7
            code = _generate_short_code()
        assert len(code) == 7


class TestIsExpired:
    def test_no_expires_at_not_expired(self):
        link = MagicMock(expires_at=None)
        assert _is_expired(link) is False

    def test_expires_at_in_past_is_expired(self):
        link = MagicMock(expires_at=datetime.utcnow() - timedelta(minutes=1))
        assert _is_expired(link) is True

    def test_expires_at_in_future_not_expired(self):
        link = MagicMock(expires_at=datetime.utcnow() + timedelta(days=1))
        assert _is_expired(link) is False

    def test_expires_at_now_is_expired(self):
        link = MagicMock(expires_at=datetime.utcnow())
        assert _is_expired(link) is True


class TestLinkToResponse:
    def test_short_url_with_base_url(self):
        service = LinkService(db=MagicMock(), base_url='https://short.example.com')
        link = MagicMock(
            short_code='abc123',
            original_url='https://long.com/page',
            created_at=datetime(2025, 1, 15, 12, 0),
            expires_at=None,
        )
        result = service._link_to_response(link)
        assert result['short_code'] == 'abc123'
        assert result['original_url'] == 'https://long.com/page'
        assert result['short_url'] == 'https://short.example.com/abc123'
        assert result['created_at'] == link.created_at
        assert result['expires_at'] is None

    def test_short_url_without_base_url(self):
        service = LinkService(db=MagicMock(), base_url='')
        link = MagicMock(
            short_code='xyz',
            original_url='https://a.b',
            created_at=datetime(2025, 1, 1),
            expires_at=datetime(2025, 2, 1),
        )
        result = service._link_to_response(link)
        assert result['short_url'] == '/xyz'
        assert result['expires_at'] == datetime(2025, 2, 1)

    def test_base_url_trailing_slash_removed(self):
        service = LinkService(db=MagicMock(), base_url='https://s.com/')
        link = MagicMock(
            short_code='q',
            original_url='https://x.com',
            created_at=datetime.utcnow(),
            expires_at=None,
        )
        result = service._link_to_response(link)
        assert result['short_url'] == 'https://s.com/q'


class TestLinkServiceCleanupInactive:
    def test_returns_zero_when_no_links(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        with patch('app.services.link_service.cache') as mock_cache:
            svc = LinkService(db, base_url='')
            n = svc.cleanup_inactive(inactive_days=30)
        assert n == 0
        mock_cache.delete_pattern.assert_not_called()

    def test_deletes_inactive_links_and_returns_count(self):
        old_link = MagicMock(spec=Link)
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [old_link]
        with patch('app.services.link_service.cache') as mock_cache:
            with patch('app.services.link_service.settings') as mock_settings:
                mock_settings.link_inactive_days = 30
                svc = LinkService(db, base_url='')
                n = svc.cleanup_inactive(inactive_days=7)
        assert n == 1
        db.delete.assert_called_once_with(old_link)
        db.commit.assert_called()
        assert mock_cache.delete_pattern.call_count >= 1


class TestLinkServiceCachePaths:
    def test_get_by_short_code_cache_hit_returns_link(self):
        link = MagicMock(spec=Link)
        link.expires_at = None
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = link
        with patch('app.services.link_service.cache') as mock_cache:
            mock_cache.get.return_value = {'original_url': 'https://x.com'}
            svc = LinkService(db, base_url='')
            result = svc.get_by_short_code('abc', use_cache=True)
        assert result is link

    def test_get_by_short_code_cache_hit_but_expired_returns_none(self):
        link = MagicMock(spec=Link)
        link.expires_at = datetime.utcnow() - timedelta(days=1)
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = link
        with patch('app.services.link_service.cache') as mock_cache:
            mock_cache.get.return_value = {'original_url': 'https://x.com'}
            svc = LinkService(db, base_url='')
            result = svc.get_by_short_code('abc', use_cache=True)
        assert result is None

    def test_get_stats_cache_hit_returns_link(self):
        link = MagicMock(spec=Link)
        link.expires_at = None
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = link
        with patch('app.services.link_service.cache') as mock_cache:
            mock_cache.get.return_value = {'short_code': 'x'}
            svc = LinkService(db, base_url='')
            result = svc.get_stats('abc', use_cache=True)
        assert result is link

    def test_search_by_original_url_cache_hit_with_ids_returns_links(self):
        link = MagicMock(spec=Link)
        link.id = 1
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = [link]
        with patch('app.services.link_service.cache') as mock_cache:
            mock_cache.get.return_value = {'ids': [1]}
            svc = LinkService(db, base_url='')
            result = svc.search_by_original_url('https://example.com', use_cache=True)
        assert result == [link]

    def test_search_by_original_url_cache_hit_empty_ids_returns_empty(self):
        with patch('app.services.link_service.cache') as mock_cache:
            mock_cache.get.return_value = {'ids': []}
            svc = LinkService(MagicMock(), base_url='')
            result = svc.search_by_original_url('https://example.com', use_cache=True)
        assert result == []

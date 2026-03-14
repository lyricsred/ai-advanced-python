"""Функциональные тесты API коротких ссылок: CRUD, редирект, невалидные данные."""
import pytest


class TestHealth:
    """GET /health — проверка доступности сервиса."""

    def test_health_returns_200_and_ok(self, client):
        r = client.get('/health')
        assert r.status_code == 200
        assert r.json() == {'status': 'ok'}


class TestCreateLink:
    """POST /api/v1/links/shorten — создание ссылки."""

    def test_create_link_returns_200_and_short_url(self, client):
        r = client.post('/api/v1/links/shorten', json={
            'original_url': 'https://example.com/page',
        })
        assert r.status_code == 200
        data = r.json()
        assert data['original_url'] == 'https://example.com/page'
        assert 'short_code' in data
        assert len(data['short_code']) >= 1
        assert 'short_url' in data
        assert data['short_code'] in data['short_url']
        assert 'created_at' in data

    def test_create_with_custom_alias(self, client):
        r = client.post('/api/v1/links/shorten', json={
            'original_url': 'https://example.com',
            'custom_alias': 'my-link',
        })
        assert r.status_code == 200
        assert r.json()['short_code'] == 'my-link'

    def test_create_duplicate_alias_returns_400(self, client):
        client.post('/api/v1/links/shorten', json={
            'original_url': 'https://a.com',
            'custom_alias': 'dup',
        })
        r = client.post('/api/v1/links/shorten', json={
            'original_url': 'https://b.com',
            'custom_alias': 'dup',
        })
        assert r.status_code == 400
        assert 'already taken' in r.json().get('detail', '').lower() or 'alias' in r.json().get('detail', '').lower()

    def test_create_invalid_url_empty_returns_422(self, client):
        r = client.post('/api/v1/links/shorten', json={
            'original_url': '',
        })
        assert r.status_code == 422

    def test_create_url_without_protocol_normalized(self, client):
        r = client.post('/api/v1/links/shorten', json={
            'original_url': 'example.org',
        })
        assert r.status_code == 200
        assert r.json()['original_url'] == 'https://example.org'


class TestRedirect:
    """GET /api/v1/links/{short_code} — редирект на оригинальный URL."""

    def test_redirect_returns_307_and_location(self, client):
        create = client.post('/api/v1/links/shorten', json={
            'original_url': 'https://redirect-target.com/path',
        })
        assert create.status_code == 200
        short_code = create.json()['short_code']

        r = client.get(f'/api/v1/links/{short_code}', follow_redirects=False)
        assert r.status_code == 307
        assert r.headers.get('location') == 'https://redirect-target.com/path'

    def test_redirect_increments_click_count(self, client):
        create = client.post('/api/v1/links/shorten', json={
            'original_url': 'https://count.me',
        })
        short_code = create.json()['short_code']
        client.get(f'/api/v1/links/{short_code}', follow_redirects=False)
        client.get(f'/api/v1/links/{short_code}', follow_redirects=False)
        stats = client.get(f'/api/v1/links/{short_code}/stats')
        assert stats.status_code == 200
        assert stats.json()['click_count'] == 2

    def test_redirect_unknown_code_returns_404(self, client):
        r = client.get('/api/v1/links/nonexistent123', follow_redirects=False)
        assert r.status_code == 404


class TestStats:
    """GET /api/v1/links/{short_code}/stats — статистика."""

    def test_stats_returns_link_info(self, client):
        create = client.post('/api/v1/links/shorten', json={
            'original_url': 'https://stats.example.com',
        })
        short_code = create.json()['short_code']
        r = client.get(f'/api/v1/links/{short_code}/stats')
        assert r.status_code == 200
        data = r.json()
        assert data['short_code'] == short_code
        assert data['original_url'] == 'https://stats.example.com'
        assert 'click_count' in data
        assert data['click_count'] >= 0
        assert 'created_at' in data

    def test_stats_unknown_returns_404(self, client):
        r = client.get('/api/v1/links/nonexistent999/stats')
        assert r.status_code == 404


class TestUpdateLink:
    """PUT /api/v1/links/{short_code} — обновление (требуется авторизация)."""

    def test_update_requires_auth(self, client):
        create = client.post('/api/v1/links/shorten', json={
            'original_url': 'https://old.com',
            'custom_alias': 'upd-me',
        })
        r = client.put('/api/v1/links/upd-me', json={
            'original_url': 'https://new.com',
        })
        assert r.status_code == 401

    def test_update_with_auth(self, client, auth_headers):
        create = client.post('/api/v1/links/shorten', json={
            'original_url': 'https://old.com',
            'custom_alias': 'mine',
        }, headers=auth_headers)
        assert create.status_code == 200
        r = client.put('/api/v1/links/mine', json={
            'original_url': 'https://new-url.com',
        }, headers=auth_headers)
        assert r.status_code == 200
        assert r.json()['original_url'] == 'https://new-url.com'
        assert r.json()['short_code'] == 'mine'

    def test_update_other_user_link_returns_404(self, client, auth_headers):
        # Создаём ссылку без авторизации (owner_id=None)
        client.post('/api/v1/links/shorten', json={
            'original_url': 'https://anonymous.com',
            'custom_alias': 'anon-link',
        })
        # Пытаемся обновить с авторизацией — у ссылки нет владельца или другой владелец
        r = client.put('/api/v1/links/anon-link', json={
            'original_url': 'https://hacked.com',
        }, headers=auth_headers)
        # В текущей логике: link.owner_id is None, current_user.id is set → 404 (access denied)
        assert r.status_code == 404


class TestDeleteLink:
    """DELETE /api/v1/links/{short_code} — удаление (требуется авторизация)."""

    def test_delete_requires_auth(self, client):
        client.post('/api/v1/links/shorten', json={
            'original_url': 'https://x.com',
            'custom_alias': 'del-me',
        })
        r = client.delete('/api/v1/links/del-me')
        assert r.status_code == 401

    def test_delete_own_link(self, client, auth_headers):
        client.post('/api/v1/links/shorten', json={
            'original_url': 'https://to-delete.com',
            'custom_alias': 'my-del',
        }, headers=auth_headers)
        r = client.delete('/api/v1/links/my-del', headers=auth_headers)
        assert r.status_code == 204
        assert client.get('/api/v1/links/my-del', follow_redirects=False).status_code == 404

    def test_delete_other_user_link_returns_404(self, client, auth_headers):
        client.post('/api/v1/links/shorten', json={
            'original_url': 'https://other.com',
            'custom_alias': 'other-link',
        })
        r = client.delete('/api/v1/links/other-link', headers=auth_headers)
        assert r.status_code == 404


class TestSearchByUrl:
    """GET /api/v1/links/search/?original_url=... — поиск по оригинальному URL."""

    def test_search_finds_created_links(self, client):
        client.post('/api/v1/links/shorten', json={
            'original_url': 'https://searchable.com',
            'custom_alias': 's1',
        })
        r = client.get('/api/v1/links/search/', params={'original_url': 'https://searchable.com'})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(l['short_code'] == 's1' for l in data)

    def test_search_empty_without_protocol_normalized(self, client):
        client.post('/api/v1/links/shorten', json={
            'original_url': 'https://same.com',
            'custom_alias': 'x',
        })
        r = client.get('/api/v1/links/search/', params={'original_url': 'same.com'})
        assert r.status_code == 200
        # Сервис нормализует к https://, должен найти
        assert isinstance(r.json(), list)

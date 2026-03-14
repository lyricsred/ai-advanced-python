import pytest
from pydantic import ValidationError

from app.schemas.link import LinkCreate, LinkUpdate


class TestLinkCreate:
    def test_valid_url_with_https(self):
        data = LinkCreate(original_url='https://example.com/path')
        assert data.original_url == 'https://example.com/path'

    def test_valid_url_with_http(self):
        data = LinkCreate(original_url='http://example.com')
        assert data.original_url == 'http://example.com'

    def test_url_without_protocol_adds_https(self):
        data = LinkCreate(original_url='example.com')
        assert data.original_url == 'https://example.com'

    def test_url_stripped(self):
        data = LinkCreate(original_url='  https://example.com  ')
        assert data.original_url == 'https://example.com'

    def test_url_without_protocol_stripped_and_adds_https(self):
        data = LinkCreate(original_url='  example.org  ')
        assert data.original_url == 'https://example.org'

    def test_empty_url_raises(self):
        with pytest.raises(ValidationError, match='URL is required'):
            LinkCreate(original_url='')

    def test_whitespace_only_url_raises(self):
        with pytest.raises(ValidationError, match='URL is required'):
            LinkCreate(original_url='   ')

    def test_custom_alias_optional(self):
        data = LinkCreate(original_url='https://a.com', custom_alias='my-link')
        assert data.custom_alias == 'my-link'

    def test_expires_at_optional(self):
        data = LinkCreate(original_url='https://a.com')
        assert data.expires_at is None


class TestLinkUpdate:
    def test_valid_url(self):
        data = LinkUpdate(original_url='https://new-url.com')
        assert data.original_url == 'https://new-url.com'

    def test_url_without_protocol_adds_https(self):
        data = LinkUpdate(original_url='new.example.com')
        assert data.original_url == 'https://new.example.com'

    def test_url_stripped(self):
        data = LinkUpdate(original_url='  https://new.com  ')
        assert data.original_url == 'https://new.com'

    def test_empty_url_raises(self):
        with pytest.raises(ValidationError, match='URL is required'):
            LinkUpdate(original_url='')

    def test_whitespace_only_url_raises(self):
        with pytest.raises(ValidationError, match='URL is required'):
            LinkUpdate(original_url='   ')

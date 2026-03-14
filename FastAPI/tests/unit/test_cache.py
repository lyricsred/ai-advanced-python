import json
import sys
from unittest.mock import MagicMock, patch

import pytest

from app.core.cache import Cache, get_redis

# Модуль cache.py: в app.core имя "cache" переопределено на экземпляр Cache, поэтому берём из sys.modules
cache_module = sys.modules['app.core.cache']


class TestCache:
    @pytest.fixture
    def mock_redis(self):
        r = MagicMock()
        r.get.return_value = None
        r.setex = MagicMock()
        r.delete = MagicMock()
        r.scan_iter.return_value = []
        return r

    def test_get_returns_none_when_key_missing(self, mock_redis):
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache()
            assert cache.get('key') is None
            mock_redis.get.assert_called_once_with('key')

    def test_get_returns_deserialized_value(self, mock_redis):
        mock_redis.get.return_value = json.dumps({'a': 1})
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache()
            assert cache.get('key') == {'a': 1}

    def test_get_returns_none_on_redis_error(self, mock_redis):
        import redis
        mock_redis.get.side_effect = redis.RedisError()
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache()
            assert cache.get('key') is None

    def test_get_returns_none_on_invalid_json(self, mock_redis):
        mock_redis.get.return_value = 'not json'
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache()
            assert cache.get('key') is None

    def test_set_calls_setex(self, mock_redis):
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache(default_ttl=100)
            cache.set('key', {'x': 1})
            mock_redis.setex.assert_called_once()
            args = mock_redis.setex.call_args[0]
            assert args[0] == 'key'
            assert args[1] == 100
            assert json.loads(args[2]) == {'x': 1}

    def test_delete_calls_redis_delete(self, mock_redis):
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache()
            cache.delete('key')
            mock_redis.delete.assert_called_once_with('key')

    def test_delete_pattern_iterates_and_deletes(self, mock_redis):
        mock_redis.scan_iter.return_value = ['link:1', 'link:2']
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache()
            cache.delete_pattern('link:*')
            assert mock_redis.delete.call_count == 2

    def test_delete_swallows_redis_error(self, mock_redis):
        import redis
        mock_redis.delete.side_effect = redis.RedisError()
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache()
            cache.delete('key')

    def test_set_swallows_redis_error(self, mock_redis):
        import redis
        mock_redis.setex.side_effect = redis.RedisError()
        with patch.object(cache_module, 'get_redis', return_value=mock_redis):
            cache = Cache()
            cache.set('key', 'val')


class TestGetRedis:
    def test_get_redis_returns_same_instance(self):
        old_redis = getattr(cache_module, '_redis', None)
        try:
            cache_module._redis = None
            with patch.object(cache_module, 'redis') as mock_redis_module:
                mock_redis_module.from_url.return_value = MagicMock()
                r1 = get_redis()
                r2 = get_redis()
                assert r1 is r2
                mock_redis_module.from_url.assert_called_once()
        finally:
            cache_module._redis = old_redis

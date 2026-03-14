from datetime import timedelta

import pytest

from app.core.security import (
    create_access_token,
    decode_token,
    get_password_hash,
    verify_password,
)


class TestPasswordHash:
    def test_hash_roundtrip(self):
        password = 'mySecretPass123'
        hashed = get_password_hash(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = get_password_hash('correct')
        assert verify_password('wrong', hashed) is False

    def test_empty_password(self):
        hashed = get_password_hash('')
        assert verify_password('', hashed) is True

    def test_different_passwords_different_hashes(self):
        h1 = get_password_hash('pass1')
        h2 = get_password_hash('pass2')
        assert h1 != h2


class TestJWT:
    def test_create_and_decode_token(self):
        payload = {'sub': '42', 'scope': 'user'}
        token = create_access_token(payload)
        assert isinstance(token, str)
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded.get('sub') == '42'
        assert 'exp' in decoded

    def test_decode_invalid_token_returns_none(self):
        assert decode_token('invalid.jwt.token') is None
        assert decode_token('') is None
        assert decode_token('not-even-jwt') is None

    def test_token_with_custom_expiry(self):
        payload = {'sub': '1'}
        token = create_access_token(payload, expires_delta=timedelta(minutes=5))
        decoded = decode_token(token)
        assert decoded is not None
        assert decoded.get('sub') == '1'

    def test_token_contains_exp_claim(self):
        token = create_access_token({'sub': '1'})
        decoded = decode_token(token)
        assert decoded is not None
        assert 'exp' in decoded
        assert decoded['exp'] > 0

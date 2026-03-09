import random
import string
from datetime import datetime
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.core.cache import cache
from app.models.link import Link
from app.schemas.link import LinkCreate, LinkUpdate

CACHE_KEY_LINK = 'link:{}'
CACHE_KEY_STATS = 'stats:{}'
CACHE_KEY_SEARCH_PREFIX = 'search:'


def _generate_short_code(length: int = 0) -> str:
    length = length or settings.short_code_length
    alphabet = string.ascii_lowercase + string.digits
    return ''.join(random.choices(alphabet, k=length))


def _invalidate_link_cache(short_code: str) -> None:
    cache.delete(CACHE_KEY_LINK.format(short_code))
    cache.delete(CACHE_KEY_STATS.format(short_code))
    cache.delete_pattern(CACHE_KEY_SEARCH_PREFIX + '*')


def _is_expired(link: Link) -> bool:
    if not link.expires_at:
        return False
    return datetime.utcnow() >= link.expires_at


class LinkService:
    def __init__(self, db: Session, base_url: str = ''):
        self.db = db
        self.base_url = base_url.rstrip('/')

    def _link_to_response(self, link: Link) -> dict:
        short_url = f'{self.base_url}/{link.short_code}' if self.base_url else f'/{link.short_code}'
        return {
            'short_code': link.short_code,
            'original_url': link.original_url,
            'short_url': short_url,
            'created_at': link.created_at,
            'expires_at': link.expires_at,
        }

    def create(self, data: LinkCreate, owner_id: Optional[int] = None) -> Link:
        short_code = data.custom_alias
        if short_code:
            short_code = short_code.strip().lower()
            if self.db.query(Link).filter(Link.short_code == short_code).first():
                raise ValueError('Alias already taken')
        else:
            while True:
                short_code = _generate_short_code()
                if not self.db.query(Link).filter(Link.short_code == short_code).first():
                    break

        link = Link(
            short_code=short_code,
            original_url=data.original_url,
            expires_at=data.expires_at,
            owner_id=owner_id,
        )
        self.db.add(link)
        self.db.commit()
        self.db.refresh(link)
        return link

    def get_by_short_code(self, short_code: str, use_cache: bool = True) -> Optional[Link]:
        short_code = short_code.lower()
        if use_cache:
            cached = cache.get(CACHE_KEY_LINK.format(short_code))
            if cached:
                link = self.db.query(Link).filter(Link.short_code == short_code).first()
                if link and not _is_expired(link):
                    return link
                return None

        link = self.db.query(Link).filter(Link.short_code == short_code).first()
        if not link or _is_expired(link):
            return None
        cache.set(CACHE_KEY_LINK.format(short_code), {'original_url': link.original_url})
        return link

    def resolve_and_track(self, short_code: str) -> Optional[str]:
        link = self.get_by_short_code(short_code, use_cache=False)
        if not link:
            return None
        link.click_count += 1
        link.last_clicked_at = datetime.utcnow()
        self.db.commit()
        _invalidate_link_cache(short_code)
        return link.original_url

    def delete(self, short_code: str, owner_id: Optional[int] = None) -> bool:
        short_code = short_code.lower()
        link = self.db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            return False
        if owner_id is not None and link.owner_id != owner_id:
            return False
        self.db.delete(link)
        self.db.commit()
        _invalidate_link_cache(short_code)
        return True

    def update(self, short_code: str, data: LinkUpdate, owner_id: Optional[int] = None) -> Optional[Link]:
        short_code = short_code.lower()
        link = self.db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            return None
        if owner_id is not None and link.owner_id != owner_id:
            return None
        if _is_expired(link):
            return None
        link.original_url = data.original_url
        self.db.commit()
        self.db.refresh(link)
        _invalidate_link_cache(short_code)
        return link

    def get_stats(self, short_code: str, use_cache: bool = True) -> Optional[Link]:
        short_code = short_code.lower()
        if use_cache:
            cached = cache.get(CACHE_KEY_STATS.format(short_code))
            if cached:
                link = self.db.query(Link).filter(Link.short_code == short_code).first()
                if link and not _is_expired(link):
                    return link
                return None

        link = self.db.query(Link).filter(Link.short_code == short_code).first()
        if not link or _is_expired(link):
            return None
        cache.set(
            CACHE_KEY_STATS.format(short_code),
            {
                'short_code': link.short_code,
                'original_url': link.original_url,
                'created_at': link.created_at.isoformat(),
                'click_count': link.click_count,
                'last_clicked_at': link.last_clicked_at.isoformat() if link.last_clicked_at else None,
                'expires_at': link.expires_at.isoformat() if link.expires_at else None,
            },
        )
        return link

    def search_by_original_url(self, original_url: str, use_cache: bool = True) -> list[Link]:
        url_normalized = original_url.strip().lower()
        if not url_normalized.startswith(('http://', 'https://')):
            url_normalized = 'https://' + url_normalized
        cache_key = CACHE_KEY_SEARCH_PREFIX + url_normalized
        if use_cache:
            cached = cache.get(cache_key)
            if cached is not None:
                ids = cached.get('ids', [])
                if ids:
                    return self.db.query(Link).filter(Link.id.in_(ids)).all()
                return []

        links = (
            self.db.query(Link)
            .filter(func.lower(Link.original_url) == url_normalized)
            .all()
        )
        valid = [l for l in links if not _is_expired(l)]
        cache.set(cache_key, {'ids': [l.id for l in valid]})
        return valid

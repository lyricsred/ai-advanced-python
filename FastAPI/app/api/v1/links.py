from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_optional, get_current_user_required
from app.models.user import User
from app.schemas.link import LinkCreate, LinkUpdate, LinkResponse, LinkStatsResponse, LinkSearchResponse
from app.services import LinkService, UserService

router = APIRouter()


def _link_service(request: Request, db: Session = Depends(get_db)) -> LinkService:
    base_url = str(request.base_url).rstrip('/')
    return LinkService(db, base_url=base_url)


@router.get('/search/', response_model=list[LinkSearchResponse])
def search_by_url(
    original_url: str,
    request: Request,
    db: Session = Depends(get_db),
):
    svc = _link_service(request, db)
    links = svc.search_by_original_url(original_url)
    return [
        LinkSearchResponse(
            short_code=l.short_code,
            original_url=l.original_url,
            created_at=l.created_at,
            expires_at=l.expires_at,
        )
        for l in links
    ]


@router.post('/shorten', response_model=LinkResponse)
def shorten(
    data: LinkCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    svc = _link_service(request, db)
    try:
        link = svc.create(data, owner_id=current_user.id if current_user else None)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    base = str(request.base_url).rstrip('/')
    short_url = f'{base}/api/v1/links/{link.short_code}'
    return LinkResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=short_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )


@router.get('/{short_code}/stats', response_model=LinkStatsResponse)
def link_stats(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    svc = _link_service(request, db)
    link = svc.get_stats(short_code)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found or expired')
    return LinkStatsResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        created_at=link.created_at,
        click_count=link.click_count,
        last_clicked_at=link.last_clicked_at,
        expires_at=link.expires_at,
    )


@router.get('/{short_code}', status_code=status.HTTP_307_TEMPORARY_REDIRECT)
def redirect_to_original(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
):
    svc = _link_service(request, db)
    url = svc.resolve_and_track(short_code)
    if not url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found or expired')
    return RedirectResponse(url=url, status_code=307)


@router.delete('/{short_code}', status_code=status.HTTP_204_NO_CONTENT)
def delete_link(
    short_code: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    svc = _link_service(request, db)
    if not svc.delete(short_code, owner_id=current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found or access denied')
    return None


@router.put('/{short_code}', response_model=LinkResponse)
def update_link(
    short_code: str,
    data: LinkUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
):
    svc = _link_service(request, db)
    link = svc.update(short_code, data, owner_id=current_user.id)
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Link not found or access denied')
    base = str(request.base_url).rstrip('/')
    short_url = f'{base}/api/v1/links/{link.short_code}'
    return LinkResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        short_url=short_url,
        created_at=link.created_at,
        expires_at=link.expires_at,
    )

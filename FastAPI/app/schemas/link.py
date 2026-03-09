from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class LinkCreate(BaseModel):
    original_url: str
    custom_alias: Optional[str] = None
    expires_at: Optional[datetime] = None

    @field_validator('original_url')
    @classmethod
    def url_must_be_string(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('URL is required')
        if not v.startswith(('http://', 'https://')):
            return 'https://' + v.strip()
        return v.strip()


class LinkUpdate(BaseModel):
    original_url: str

    @field_validator('original_url')
    @classmethod
    def url_must_be_string(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('URL is required')
        if not v.startswith(('http://', 'https://')):
            return 'https://' + v.strip()
        return v.strip()


class LinkResponse(BaseModel):
    short_code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {'from_attributes': True}


class LinkStatsResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    click_count: int
    last_clicked_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = {'from_attributes': True}


class LinkSearchResponse(BaseModel):
    short_code: str
    original_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None

    model_config = {'from_attributes': True}

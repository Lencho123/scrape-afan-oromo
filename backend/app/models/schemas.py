from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime, timezone
from typing import List, Optional

class CommentSchema(BaseModel):
    text: str
    date: Optional[str] = None

class PostSchema(BaseModel):
    post_id: str
    post_text: str
    post_date: Optional[str] = None
    comments: List[CommentSchema] = []
    # Using timezone-aware UTC for modern Python standards
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Config:
        # This allows the model to work seamlessly if you switch to an ORM later
        from_attributes = True

class ScrapeRequest(BaseModel):
    # Validates that the input is a real URL
    url: HttpUrl
    post_id: Optional[str] = None

class FilterRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class StatisticsResponse(BaseModel):
    total_posts: int
    total_comments: int
    total_tokens: int
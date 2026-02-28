from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class CommentSchema(BaseModel):
    text: str
    date: Optional[str] = None

class PostSchema(BaseModel):
    post_id: str
    post_text: str
    post_date: Optional[str] = None
    comments: List[CommentSchema] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScrapeRequest(BaseModel):
    url: str

class FilterRequest(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

class StatisticsResponse(BaseModel):
    total_posts: int
    total_comments: int
    total_tokens: int

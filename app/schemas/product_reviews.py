from typing import Optional
from pydantic import BaseModel


class ProductReviewsRequest(BaseModel):

    asin: str = "B00939I7EK"

    cookie: str

    country: str = "US"

    cursor: Optional[str] = None

    sort_by: str = "TOP_REVIEWS"

    star_rating: str = "ALL"

    verified_purchases_only: bool = False

    images_or_videos_only: bool = False

    current_format_only: bool = False

    query: Optional[str] = None

    fields: Optional[str] = None

    language: Optional[str] = None
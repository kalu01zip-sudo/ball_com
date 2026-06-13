from typing import Optional
from pydantic import BaseModel


class TopReviewsRequest(BaseModel):

    asin: str = "B00939I7EK"

    country: str = "US"

    fields: Optional[str] = None

    language: Optional[str] = None
from typing import Optional
from pydantic import BaseModel


class ReviewDetailsRequest(BaseModel):

    review_id: str = "R2FZOU359SHU21"

    cookie: str

    country: str = "US"

    language: Optional[str] = None

    fields: Optional[str] = None
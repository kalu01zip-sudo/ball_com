from typing import Optional
from pydantic import BaseModel


class ScrapeUrlRequest(BaseModel):

    url: str = "https://www.amazon.com/s?k=ninja"

    country: str = "US"

    language: Optional[str] = None

    cookie: Optional[str] = None

    return_html: bool = False
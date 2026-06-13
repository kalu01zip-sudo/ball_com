from typing import Optional
from pydantic import BaseModel, Field


class ProductDetailsRequest(BaseModel):

    asin: str = Field(
        default="B07ZPKBL9V",
        description="Amazon product ASIN."
    )

    country: str = "US"

    autoselect_variant: bool = False

    more_info_query: Optional[str] = None

    language: Optional[str] = None

    fields: Optional[str] = None
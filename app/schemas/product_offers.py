from typing import Optional
from pydantic import BaseModel


class ProductOffersRequest(BaseModel):

    asin: str = "B09SM24S8C"

    country: str = "US"

    product_condition: Optional[str] = (
        "NEW,USED_LIKE_NEW,USED_VERY_GOOD,USED_GOOD,USED_ACCEPTABLE"
    )

    delivery: Optional[str] = None

    autoselect_variant: bool = False

    limit: int = 100

    page: int = 1

    language: Optional[str] = None

    fields: Optional[str] = None
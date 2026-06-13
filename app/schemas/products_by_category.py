from typing import Optional
from pydantic import BaseModel


class ProductsByCategoryRequest(BaseModel):

    category_id: str = "281407"

    page: int = 1

    country: str = "US"

    sort_by: str = "RELEVANCE"

    min_price: Optional[float] = None

    max_price: Optional[float] = None

    product_condition: str = "ALL"

    brand: Optional[str] = None

    is_prime: bool = False

    deals_and_discounts: str = "NONE"

    four_stars_and_up: bool = False

    language: Optional[str] = None

    additional_filters: Optional[str] = None

    fields: Optional[str] = None
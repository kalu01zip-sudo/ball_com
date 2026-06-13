from typing import Optional
from pydantic import BaseModel, Field


class ProductSearchRequest(BaseModel):
    query: str = Field(
        default="Phone",
        description="Search query (supports both free-form text queries or a product ASIN)."
    )

    page: int = Field(
        default=1,
        description="Results page to return."
    )

    country: str = Field(
        default="US",
        description="Amazon marketplace country."
    )

    sort_by: str = Field(
        default="RELEVANCE",
        description="RELEVANCE, LOWEST_PRICE, HIGHEST_PRICE, REVIEWS, NEWEST, BEST_SELLERS"
    )

    category_id: Optional[str] = None
    category: Optional[str] = None

    min_price: Optional[float] = None
    max_price: Optional[float] = None

    product_condition: str = "ALL"

    brand: Optional[str] = Field(
        default=None,
        examples=["SAMSUNG"]
    )

    seller_id: Optional[str] = None

    is_prime: bool = False

    deals_and_discounts: str = "NONE"

    four_stars_and_up: bool = False

    language: Optional[str] = None

    additional_filters: Optional[str] = None

    fields: Optional[str] = Field(
        default=None,
        examples=["product_price,product_url,is_best_seller"]
    )
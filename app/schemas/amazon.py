from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.enums import (
    CountryEnum,
    SortByEnum,
    ProductConditionEnum,
)


class ProductSearchRequest(BaseModel):

    query: str = "Phone"

    country: CountryEnum = CountryEnum.US

    sort_by: SortByEnum = SortByEnum.RELEVANCE

    product_condition: ProductConditionEnum = (
        ProductConditionEnum.ALL
    )
from pydantic import BaseModel, Field
from typing import Optional
from app.schemas.enums import CountryEnum

class FetchFromDocRequest(BaseModel):
    doc_url: str = Field(..., description="Google Doc or Google Sheet public link")
    country: CountryEnum = Field(CountryEnum.US, description="Marketplace country")
    page: int = Field(1, description="Results page to fetch (pagination over extracted products)")
    limit: int = Field(10, description="Number of products to fetch per page")

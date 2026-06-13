from fastapi import APIRouter, Body, Path, Query
from typing import Optional

from app.schemas import ProductSearchRequest
from app.schemas.enums import (
    CountryEnum,
    BestSellerTypeEnum,
    DealStarRatingEnum,
    DealPriceRangeEnum,
    DealDiscountRangeEnum,
    DealProductSortByEnum,
    InfluencerPostScopeEnum,
    SortByEnum,
    StarRatingEnum,
)
from app.services.amazon_service import AmazonService

router = APIRouter(
    prefix="/amazon",
    tags=["Amazon"]
)


@router.get("/products/search")
async def search_products(
    query: str = Query(..., description="Search query"),
    page: int = Query(1, description="Results page"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country") 
):

    return await AmazonService.product_search(
        {
            "query": query,
            "page": page,
            "country": country
        }
    )

@router.get(
    "/product-details/{asin}",
    summary="Product Details"
)
async def product_details(
    asin: str = Path(
        ...,
        description="Amazon Product ASIN",
        examples=["B07ZPKBL9V"]
    ),

    country: CountryEnum = Query(
        CountryEnum.US,
        description="Marketplace country"
    )
):
    return await AmazonService.product_details(
        asin=asin,
        country=country,
    )

@router.get("/product-offers/{asin}")
async def product_offers(
    asin: str = Path(
        ...,
        description="Amazon Product ASIN",
        examples=["B07ZPKBL9V"]
    ),
    country: CountryEnum = Query(
        CountryEnum.US,
        description="Marketplace country"
    ),
    page: int = Query(
        1,
        description="Results page"
    ),
):
    return await AmazonService.product_offers(
        asin=asin,
        country=country,
        page=page,
    )

@router.get("/product-reviews/{asin}")
async def product_reviews(
    asin: str = Path(
        ...,
        description="Amazon Product ASIN",
        examples=["B07ZPKBL9V"]
    ),
    country: CountryEnum = Query(
        CountryEnum.US,
        description="Marketplace country"
    ),
    page: int = Query(
        1,
        description="Results page"
    ),
):
    return await AmazonService.product_reviews(
        asin=asin,
        country=country,
        page=page,
    )

@router.get("/review-details/{review_id}")
async def review_details(
    review_id: str = Path(
        ...,
        description="Amazon Review ID",
        examples=["R3H8Z9K2L4M5N6P7Q8R9S0T1U2V3W4X5Y6Z7"]
    ),
    country: CountryEnum = Query(
        CountryEnum.US,
        description="Marketplace country"
    )
):
    return await AmazonService.review_details(
        review_id=review_id,
        country=country,
    )

@router.get("/top-reviews/{asin}")
async def top_reviews(
    asin: str = Path(
        ...,
        description="Amazon Product ASIN",
        examples=["B07ZPKBL9V"]
    ),
    country: CountryEnum = Query(
        CountryEnum.US,
        description="Marketplace country"
    ),
):
    return await AmazonService.top_reviews(
        asin=asin,
        country=country,
    )

@router.get("/category/{category_id}")
async def products_by_category(
    category_id: str = Path(
        ...,
        description="Amazon Category ID",
        examples=["electronics"]
    ),
    country: CountryEnum = Query(
        CountryEnum.US,
        description="Marketplace country"
    ),
    page: int = Query(
        1,
        description="Results page"
    ),
):
    return await AmazonService.products_by_category(
        category_id=category_id,
        country=country,
        page=page,
    )

@router.post("/scrape-url")
async def scrape_url(
    url: str = Body(
        ...,
        description="URL to scrape"
    ),
    country: CountryEnum = Query(
        CountryEnum.US,
        description="Marketplace country"
    ),
):
    return await AmazonService.scrape_by_url(
        url=url,
        country=country,
    )


# ---------------------------------------------------
# Seller Profile
# ---------------------------------------------------

@router.get("/seller-profile/{seller_id}")
async def seller_profile(
    seller_id: str = Path(..., description="Amazon Seller ID"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    language: Optional[str] = Query(None, description="The language of the results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
):
    return await AmazonService.seller_profile(
        seller_id=seller_id,
        country=country,
        language=language,
        fields=fields,
    )


# ---------------------------------------------------
# Seller Reviews
# ---------------------------------------------------

@router.get("/seller-reviews/{seller_id}")
async def seller_reviews(
    seller_id: str = Path(..., description="Amazon Seller ID"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    star_rating: StarRatingEnum = Query(StarRatingEnum.ALL, description="Star rating filter"),
    page: int = Query(1, description="Results page"),
    language: Optional[str] = Query(None, description="The language of the results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
):
    return await AmazonService.seller_reviews(
        seller_id=seller_id,
        country=country,
        star_rating=star_rating,
        page=page,
        language=language,
        fields=fields,
    )


# ---------------------------------------------------
# Seller Products
# ---------------------------------------------------

@router.get("/seller-products/{seller_id}")
async def seller_products(
    seller_id: str = Path(..., description="Amazon Seller ID"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    page: int = Query(1, description="Results page"),
    sort_by: SortByEnum = Query(SortByEnum.RELEVANCE, description="Sort order"),
    language: Optional[str] = Query(None, description="The language of the results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
):
    return await AmazonService.seller_products(
        seller_id=seller_id,
        country=country,
        page=page,
        sort_by=sort_by,
        language=language,
        fields=fields,
    )


# ---------------------------------------------------
# Best Sellers
# ---------------------------------------------------

@router.get("/best-sellers")
async def best_sellers(
    category: str = Query(..., description="Best sellers category to return products for"),
    type: BestSellerTypeEnum = Query(BestSellerTypeEnum.BEST_SELLERS, description="Type of Best Seller list"),
    page: int = Query(1, description="Results page"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    language: Optional[str] = Query(None, description="The language of the results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
):
    return await AmazonService.best_sellers(
        category=category,
        type=type,
        page=page,
        country=country,
        language=language,
        fields=fields,
    )


# ---------------------------------------------------
# Deals
# ---------------------------------------------------

@router.get("/deals")
async def deals(
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    offset: int = Query(0, description="Number of results to skip"),
    categories: Optional[str] = Query(None, description="Comma-separated category IDs"),
    min_product_star_rating: DealStarRatingEnum = Query(DealStarRatingEnum.ALL, description="Minimum product star rating"),
    price_range: DealPriceRangeEnum = Query(DealPriceRangeEnum.ALL, description="Price range category"),
    discount_range: DealDiscountRangeEnum = Query(DealDiscountRangeEnum.ALL, description="Discount range category"),
    brands: Optional[str] = Query(None, description="Comma-separated brand names"),
    prime_early_access: Optional[bool] = Query(None, description="Only return prime early access deals"),
    prime_exclusive: Optional[bool] = Query(None, description="Only return prime exclusive deals"),
    lightning_deals: Optional[bool] = Query(None, description="Only return lightning deals"),
    language: Optional[str] = Query(None, description="The language of the results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
):
    return await AmazonService.deals(
        country=country,
        offset=offset,
        categories=categories,
        min_product_star_rating=min_product_star_rating,
        price_range=price_range,
        discount_range=discount_range,
        brands=brands,
        prime_early_access=prime_early_access,
        prime_exclusive=prime_exclusive,
        lightning_deals=lightning_deals,
        language=language,
        fields=fields,
    )


# ---------------------------------------------------
# Deal Products
# ---------------------------------------------------

@router.get("/deal-products/{deal_id}")
async def deal_products(
    deal_id: str = Path(..., description="Deal ID of the deal to fetch"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    sort_by: DealProductSortByEnum = Query(DealProductSortByEnum.FEATURED, description="Return products in a specific order"),
    page: int = Query(1, description="Results page"),
    language: Optional[str] = Query(None, description="The language of the results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
):
    return await AmazonService.deal_products(
        deal_id=deal_id,
        country=country,
        sort_by=sort_by,
        page=page,
        language=language,
        fields=fields,
    )


# ---------------------------------------------------
# Promo Code Details
# ---------------------------------------------------

@router.get("/promo-code/{promo_code}")
async def promo_code_details(
    promo_code: str = Path(..., description="Promo code for which to get products"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    language: Optional[str] = Query(None, description="The language of the results"),
):
    return await AmazonService.promo_code_details(
        promo_code=promo_code,
        country=country,
        language=language,
    )


# ---------------------------------------------------
# Influencer Profile
# ---------------------------------------------------

@router.get("/influencer-profile/{influencer_name}")
async def influencer_profile(
    influencer_name: str = Path(..., description="The Amazon Influencer name"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
    language: Optional[str] = Query(None, description="The language of the results"),
):
    return await AmazonService.influencer_profile(
        influencer_name=influencer_name,
        country=country,
        fields=fields,
        language=language,
    )


# ---------------------------------------------------
# Influencer Posts
# ---------------------------------------------------

@router.get("/influencer-posts/{influencer_name}")
async def influencer_posts(
    influencer_name: str = Path(..., description="The Amazon Influencer name"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
    scope: InfluencerPostScopeEnum = Query(InfluencerPostScopeEnum.ALL, description="Return results in a specific scope"),
    query: Optional[str] = Query(None, description="Find posts matching a search query"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination next page"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of posts to return"),
    language: Optional[str] = Query(None, description="The language of the results"),
    fields: Optional[str] = Query(None, description="Comma-separated list of fields to include"),
):
    return await AmazonService.influencer_posts(
        influencer_name=influencer_name,
        country=country,
        scope=scope,
        query=query,
        cursor=cursor,
        limit=limit,
        language=language,
        fields=fields,
    )


# ---------------------------------------------------
# Influencer Post Products
# ---------------------------------------------------

@router.get("/influencer-post-products/{influencer_name}/{post_id}")
async def influencer_post_products(
    influencer_name: str = Path(..., description="The Amazon Influencer name"),
    post_id: str = Path(..., description="Influencer Post ID"),
    cursor: Optional[str] = Query(None, description="Cursor for pagination next page"),
    language: Optional[str] = Query(None, description="The language of the results"),
):
    return await AmazonService.influencer_post_products(
        influencer_name=influencer_name,
        post_id=post_id,
        cursor=cursor,
        language=language,
    )


# ---------------------------------------------------
# ASIN to GTIN
# ---------------------------------------------------

@router.get("/asin-to-gtin/{asin}")
async def asin_to_gtin(
    asin: str = Path(..., description="Amazon product ASIN to convert"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
):
    return await AmazonService.asin_to_gtin(
        asin=asin,
        country=country,
    )


# ---------------------------------------------------
# GTIN to ASIN
# ---------------------------------------------------

@router.get("/gtin-to-asin/{product_identifier}")
async def gtin_to_asin(
    product_identifier: str = Path(..., description="Product identifier (SKU, ISBN, UPC, EAN, ASIN) to look up"),
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
):
    return await AmazonService.gtin_to_asin(
        product_identifier=product_identifier,
        country=country,
    )


# ---------------------------------------------------
# Product Category List
# ---------------------------------------------------

@router.get("/product-category-list")
async def product_category_list(
    country: CountryEnum = Query(CountryEnum.US, description="Marketplace country"),
):
    return await AmazonService.product_category_list(
        country=country,
    )
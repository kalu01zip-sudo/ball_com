import httpx
from enum import Enum
import logging
import asyncio
from playwright.sync_api import sync_playwright

from app.core.config import settings

logger = logging.getLogger(__name__)

class AmazonService:

    BASE_URL = "https://real-time-amazon-data.p.rapidapi.com"

    HEADERS = {
        "x-rapidapi-key": settings.RAPIDAPI_KEY,
        "x-rapidapi-host": settings.RAPIDAPI_HOST,
    }

    @classmethod
    async def _get(cls, endpoint: str, params: dict):
        # Convert Enum parameters to their values
        serialized_params = {
            k: v.value if isinstance(v, Enum) else v
            for k, v in params.items()
        }

        async with httpx.AsyncClient(timeout=30) as client:

            response = await client.get(
                f"{cls.BASE_URL}{endpoint}",
                headers=cls.HEADERS,
                params=serialized_params,
            )

            response.raise_for_status()

            return response.json()

    # ---------------------------------------------------
    # Product Search
    # ---------------------------------------------------

    @classmethod
    async def product_search(cls, params: dict):
        return await cls._get("/search", params)

    # ---------------------------------------------------
    # Product Details
    # ---------------------------------------------------

    @classmethod
    async def product_details(
        cls,
        asin: str,
        country: str = "US",
        skip_cache: bool = False
    ):
        from app.core.database import get_db
        from datetime import datetime, timedelta
        
        db = get_db()
        fallback_cache = None
        
        if not skip_cache:
            cache_doc = await db.scraped_products.find_one({"asin": asin, "country": country})
            if cache_doc and cache_doc.get("updated_at"):
                # Cache for 30 days
                if datetime.utcnow() - cache_doc["updated_at"] < timedelta(days=30):
                    data = cache_doc["data"]
                    if data.get("request_id") == "fallback-manual-scrape":
                        fallback_cache = data
                    else:
                        return data
        
        # If cache miss or skip_cache, fetch from external API
        try:
            response = await cls._get(
                "/product-details",
                {
                    "asin": asin,
                    "country": country,
                },
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 403):
                logger.warning(f"RapidAPI {e.response.status_code} error. Falling back to manual scrape for ASIN: {asin}")
                
                if fallback_cache:
                    logger.info(f"Using existing fallback cache for ASIN: {asin}")
                    return fallback_cache
                
                response = await cls._fallback_scrape_product(asin, country)
            else:
                raise e
        
        # Save to cache if successful
        if response and response.get("status") == "OK":
            await db.scraped_products.update_one(
                {"asin": asin, "country": country},
                {"$set": {
                    "asin": asin,
                    "country": country,
                    "updated_at": datetime.utcnow(),
                    "data": response
                }},
                upsert=True
            )
            
        return response

    @classmethod
    def _sync_fallback_scrape_product(cls, asin: str, country: str):
        domain = "amazon.com" if country.upper() == "US" else f"amazon.{country.lower()}"
        if country.upper() == "UK":
            domain = "amazon.co.uk"
            
        url = f"https://www.{domain}/dp/{asin}"
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            page = context.new_page()
            
            try:
                page.goto(url, timeout=30000)
                # Wait for title to ensure page loaded
                try:
                    page.wait_for_selector("#productTitle", timeout=10000)
                except Exception:
                    logger.warning("Timeout waiting for #productTitle. Might be a captcha or different layout.")
                
                title = page.evaluate("() => { const el = document.querySelector('#productTitle'); return el ? el.innerText.trim() : null; }")
                price = page.evaluate("() => { const el = document.querySelector('.a-price .a-offscreen'); return el ? el.innerText.trim() : null; }")
                image = page.evaluate("() => { const el = document.querySelector('#landingImage'); return el ? el.getAttribute('src') : null; }")
                
                data = {
                    "status": "OK",
                    "request_id": "fallback-manual-scrape",
                    "parameters": {
                        "asin": asin,
                        "country": country
                    },
                    "data": {
                        "asin": asin,
                        "product_title": title,
                        "product_price": price,
                        "product_photo": image,
                        "product_url": url,
                        "country": country,
                        "currency": "$" if price and "$" in price else "UNKNOWN"
                    }
                }
                return data
            except Exception as e:
                logger.error(f"Manual scrape failed for {asin}: {e}")
                return {
                    "status": "ERROR",
                    "request_id": "fallback-manual-scrape",
                    "message": f"Manual scrape failed: {str(e)}"
                }
            finally:
                browser.close()

    @classmethod
    async def _fallback_scrape_product(cls, asin: str, country: str):
        # Run the synchronous Playwright scraper in a separate thread to avoid asyncio loop conflicts in Uvicorn on Windows
        return await asyncio.to_thread(cls._sync_fallback_scrape_product, asin, country)

    # ---------------------------------------------------
    # Product Offers
    # ---------------------------------------------------

    @classmethod
    async def product_offers(
        cls,
        asin: str,
        country: str = "US",
        page: int = 1,
    ):
        return await cls._get(
            "/product-offers",
            {
                "asin": asin,
                "country": country,
                "page": page,
            },
        )

    # ---------------------------------------------------
    # Product Reviews
    # ---------------------------------------------------

    @classmethod
    async def product_reviews(
        cls,
        asin: str,
        country: str = "US",
        sort_by: str = "TOP_REVIEWS",
        page: int = 1,
    ):
        return await cls._get(
            "/product-reviews",
            {
                "asin": asin,
                "country": country,
                "sort_by": sort_by,
                "page": page,
            },
        )

    # ---------------------------------------------------
    # Review Details
    # ---------------------------------------------------

    @classmethod
    async def review_details(
        cls,
        review_id: str,
        country: str = "US",
    ):
        return await cls._get(
            "/product-review-details",
            {
                "review_id": review_id,
                "country": country,
            },
        )

    # ---------------------------------------------------
    # Top Product Reviews
    # ---------------------------------------------------

    @classmethod
    async def top_reviews(
        cls,
        asin: str,
        country: str = "US",
    ):
        return await cls._get(
            "/top-product-reviews",
            {
                "asin": asin,
                "country": country,
            },
        )

    # ---------------------------------------------------
    # Products By Category
    # ---------------------------------------------------

    @classmethod
    async def products_by_category(
        cls,
        category_id: str,
        country: str = "US",
        page: int = 1,
        sort_by: str = "RELEVANCE",
    ):
        return await cls._get(
            "/products-by-category",
            {
                "category_id": category_id,
                "country": country,
                "page": page,
                "sort_by": sort_by,
            },
        )

    # ---------------------------------------------------
    # Scrape By URL
    # ---------------------------------------------------

    @classmethod
    async def scrape_by_url(
        cls,
        url: str,
        country: str = "US",
        return_html: bool = False,
    ):
        return await cls._get(
            "/scrape-by-url",
            {
                "url": url,
                "country": country,
                "return_html": str(return_html).lower(),
            },
        )

    # ---------------------------------------------------
    # Seller Profile
    # ---------------------------------------------------

    @classmethod
    async def seller_profile(
        cls,
        seller_id: str,
        country: str = "US",
        language: str = None,
        fields: str = None,
    ):
        params = {"seller_id": seller_id, "country": country}
        if language:
            params["language"] = language
        if fields:
            params["fields"] = fields
        return await cls._get("/seller-profile", params)

    # ---------------------------------------------------
    # Seller Reviews
    # ---------------------------------------------------

    @classmethod
    async def seller_reviews(
        cls,
        seller_id: str,
        country: str = "US",
        star_rating: str = "ALL",
        page: int = 1,
        language: str = None,
        fields: str = None,
    ):
        params = {
            "seller_id": seller_id,
            "country": country,
            "star_rating": star_rating,
            "page": page,
        }
        if language:
            params["language"] = language
        if fields:
            params["fields"] = fields
        return await cls._get("/seller-reviews", params)

    # ---------------------------------------------------
    # Seller Products
    # ---------------------------------------------------

    @classmethod
    async def seller_products(
        cls,
        seller_id: str,
        country: str = "US",
        page: int = 1,
        sort_by: str = "RELEVANCE",
        language: str = None,
        fields: str = None,
    ):
        params = {
            "seller_id": seller_id,
            "country": country,
            "page": page,
            "sort_by": sort_by,
        }
        if language:
            params["language"] = language
        if fields:
            params["fields"] = fields
        return await cls._get("/seller-products", params)

    # ---------------------------------------------------
    # Best Sellers
    # ---------------------------------------------------

    @classmethod
    async def best_sellers(
        cls,
        category: str,
        type: str = "BEST_SELLERS",
        page: int = 1,
        country: str = "US",
        language: str = None,
        fields: str = None,
    ):
        params = {
            "category": category,
            "type": type,
            "page": page,
            "country": country,
        }
        if language:
            params["language"] = language
        if fields:
            params["fields"] = fields
        return await cls._get("/best-sellers", params)

    # ---------------------------------------------------
    # Deals
    # ---------------------------------------------------

    @classmethod
    async def deals(
        cls,
        country: str = "US",
        offset: int = 0,
        categories: str = None,
        min_product_star_rating: str = "ALL",
        price_range: str = "ALL",
        discount_range: str = "ALL",
        brands: str = None,
        prime_early_access: bool = None,
        prime_exclusive: bool = None,
        lightning_deals: bool = None,
        language: str = None,
        fields: str = None,
    ):
        params = {
            "country": country,
            "offset": offset,
            "min_product_star_rating": min_product_star_rating,
            "price_range": price_range,
            "discount_range": discount_range,
        }
        if categories:
            params["categories"] = categories
        if brands:
            params["brands"] = brands
        if prime_early_access is not None:
            params["prime_early_access"] = str(prime_early_access).lower()
        if prime_exclusive is not None:
            params["prime_exclusive"] = str(prime_exclusive).lower()
        if lightning_deals is not None:
            params["lightning_deals"] = str(lightning_deals).lower()
        if language:
            params["language"] = language
        if fields:
            params["fields"] = fields
        return await cls._get("/deals-v2", params)

    # ---------------------------------------------------
    # Deal Products
    # ---------------------------------------------------

    @classmethod
    async def deal_products(
        cls,
        deal_id: str,
        country: str = "US",
        sort_by: str = "FEATURED",
        page: int = 1,
        language: str = None,
        fields: str = None,
    ):
        params = {
            "deal_id": deal_id,
            "country": country,
            "sort_by": sort_by,
            "page": page,
        }
        if language:
            params["language"] = language
        if fields:
            params["fields"] = fields
        return await cls._get("/deal-products", params)

    # ---------------------------------------------------
    # Promo Code Details
    # ---------------------------------------------------

    @classmethod
    async def promo_code_details(
        cls,
        promo_code: str,
        country: str = "US",
        language: str = None,
    ):
        params = {
            "promo_code": promo_code,
            "country": country,
        }
        if language:
            params["language"] = language
        return await cls._get("/promo-code-details", params)

    # ---------------------------------------------------
    # Influencer Profile
    # ---------------------------------------------------

    @classmethod
    async def influencer_profile(
        cls,
        influencer_name: str,
        country: str = "US",
        fields: str = None,
        language: str = None,
    ):
        params = {
            "influencer_name": influencer_name,
            "country": country,
        }
        if fields:
            params["fields"] = fields
        if language:
            params["language"] = language
        return await cls._get("/influencer-profile", params)

    # ---------------------------------------------------
    # Influencer Posts
    # ---------------------------------------------------

    @classmethod
    async def influencer_posts(
        cls,
        influencer_name: str,
        country: str = "US",
        scope: str = "ALL",
        query: str = None,
        cursor: str = None,
        limit: int = 20,
        language: str = None,
        fields: str = None,
    ):
        params = {
            "influencer_name": influencer_name,
            "country": country,
            "scope": scope,
            "limit": limit,
        }
        if query:
            params["query"] = query
        if cursor:
            params["cursor"] = cursor
        if language:
            params["language"] = language
        if fields:
            params["fields"] = fields
        return await cls._get("/influencer-posts", params)

    # ---------------------------------------------------
    # Influencer Post Products
    # ---------------------------------------------------

    @classmethod
    async def influencer_post_products(
        cls,
        influencer_name: str,
        post_id: str,
        cursor: str = None,
        language: str = None,
    ):
        params = {
            "influencer_name": influencer_name,
            "post_id": post_id,
        }
        if cursor:
            params["cursor"] = cursor
        if language:
            params["language"] = language
        return await cls._get("/influencer-post-products", params)

    # ---------------------------------------------------
    # ASIN to GTIN
    # ---------------------------------------------------

    @classmethod
    async def asin_to_gtin(
        cls,
        asin: str,
        country: str = "US",
    ):
        params = {
            "asin": asin,
            "country": country,
        }
        return await cls._get("/asin-to-gtin", params)

    # ---------------------------------------------------
    # GTIN to ASIN
    # ---------------------------------------------------

    @classmethod
    async def gtin_to_asin(
        cls,
        product_identifier: str,
        country: str = "US",
    ):
        params = {
            "product_identifier": product_identifier,
            "country": country,
        }
        return await cls._get("/gtin-to-asin", params)

    # ---------------------------------------------------
    # Product Category List
    # ---------------------------------------------------

    @classmethod
    async def product_category_list(
        cls,
        country: str = "US",
    ):
        params = {
            "country": country,
        }
        return await cls._get("/product-category-list", params)
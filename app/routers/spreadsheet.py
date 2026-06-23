from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated
from datetime import datetime, timedelta
from bson import ObjectId
from pymongo import UpdateOne

from app.schemas.spreadsheet import ImportPublicLinkRequest, ImportOAuthRequest, SetupWatchRequest, StopWatchRequest
from app.services.spreadsheet_service import SpreadsheetService
from app.core.auth_utils import get_current_user
from app.core.database import get_db

router = APIRouter(prefix="/spreadsheet", tags=["Spreadsheet Import"])
CurrentUser = Annotated[dict, Depends(get_current_user)]

@router.post("/import-public")
async def import_public(body: ImportPublicLinkRequest, current_user: CurrentUser):
    try:
        csv_text = await SpreadsheetService.fetch_public_csv(body.spreadsheet_url)
        data = SpreadsheetService.parse_csv_reversed(csv_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing spreadsheet: {str(e)}")

    user_id = current_user.get("sub")
    db = get_db()
    
    if not data:
        return {"success": True, "message": "No valid rows found to import."}
        
    requests = []
    for row in data:
        supplier_link = row.get("Supplier Link", "").strip()
        requests.append(
            UpdateOne(
                {"user_id": user_id, "supplier_link": supplier_link},
                {"$set": {
                    **row,
                    "user_id": user_id,
                    "supplier_link": supplier_link,
                    "updated_at": datetime.utcnow(),
                    "spreadsheet_url": body.spreadsheet_url,
                    "import_type": "public"
                }},
                upsert=True
            )
        )
        
    if requests:
        await db.user_spreadsheet_items.bulk_write(requests)
    
    return {
        "success": True,
        "message": f"Successfully imported/updated {len(requests)} rows."
    }

@router.post("/import-oauth")
async def import_oauth(body: ImportOAuthRequest, current_user: CurrentUser):
    try:
        csv_text = await SpreadsheetService.fetch_oauth_csv(body.spreadsheet_url, body.access_token)
        data = SpreadsheetService.parse_csv_reversed(csv_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing spreadsheet: {str(e)}")

    user_id = current_user.get("sub")
    db = get_db()
    
    if not data:
        return {"success": True, "message": "No valid rows found to import."}
        
    requests = []
    for row in data:
        supplier_link = row.get("Supplier Link", "").strip()
        requests.append(
            UpdateOne(
                {"user_id": user_id, "supplier_link": supplier_link},
                {"$set": {
                    **row,
                    "user_id": user_id,
                    "supplier_link": supplier_link,
                    "updated_at": datetime.utcnow(),
                    "spreadsheet_url": body.spreadsheet_url,
                    "import_type": "oauth",
                    "refresh_token": body.refresh_token
                }},
                upsert=True
            )
        )
        
    if requests:
        await db.user_spreadsheet_items.bulk_write(requests)
    
    return {
        "success": True,
        "message": f"Successfully imported/updated {len(requests)} rows."
    }

@router.post("/sync-spreadsheet")
async def sync_spreadsheet(current_user: CurrentUser):
    user_id = current_user.get("sub")
    db = get_db()
    
    # Get the last imported spreadsheet URL for this user
    last_item = await db.user_spreadsheet_items.find_one(
        {"user_id": user_id},
        sort=[("updated_at", -1)]
    )
    
    if not last_item or not last_item.get("spreadsheet_url"):
        raise HTTPException(status_code=400, detail="No previously imported spreadsheet found to sync.")
        
    url = last_item["spreadsheet_url"]
    import_type = last_item.get("import_type", "public")
    
    if import_type == "oauth":
        raise HTTPException(status_code=400, detail="This spreadsheet was imported via OAuth and requires a fresh access token. Please use the original import method to re-sync.")
        
    try:
        csv_text = await SpreadsheetService.fetch_public_csv(url)
        data = SpreadsheetService.parse_csv_reversed(csv_text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error importing spreadsheet: {str(e)}")
        
    if not data:
        return {"success": True, "message": "No valid rows found to import."}
        
    requests = []
    for row in data:
        supplier_link = row.get("Supplier Link", "").strip()
        requests.append(
            UpdateOne(
                {"user_id": user_id, "supplier_link": supplier_link},
                {"$set": {
                    **row,
                    "user_id": user_id,
                    "supplier_link": supplier_link,
                    "updated_at": datetime.utcnow(),
                    "spreadsheet_url": url,
                    "import_type": "public"
                }},
                upsert=True
            )
        )
        
    if requests:
        await db.user_spreadsheet_items.bulk_write(requests)
    
    return {
        "success": True,
        "message": f"Successfully synced and updated {len(requests)} rows from the spreadsheet."
    }

@router.post("/setup-watch")
async def setup_watch(body: SetupWatchRequest, current_user: CurrentUser):
    import uuid
    from app.core.config import settings
    
    user_id = current_user.get("sub")
    db = get_db()
    
    if not settings.WEBHOOK_BASE_URL:
        raise HTTPException(status_code=500, detail="WEBHOOK_BASE_URL is not configured on the server.")
        
    webhook_url = f"{settings.WEBHOOK_BASE_URL}/webhooks/google-drive"
    channel_id = str(uuid.uuid4())
    
    try:
        response = await SpreadsheetService.watch_spreadsheet(
            url=body.spreadsheet_url,
            access_token=body.access_token,
            channel_id=channel_id,
            webhook_url=webhook_url
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup watch with Google: {str(e)}")
        
    resource_id = response.get("resourceId")
    expiration = response.get("expiration")
    
    # Save the webhook registration to the database
    watch_doc = {
        "channel_id": channel_id,
        "resource_id": resource_id,
        "user_id": user_id,
        "spreadsheet_url": body.spreadsheet_url,
        "refresh_token": body.refresh_token,
        "expiration": expiration,
        "created_at": datetime.utcnow()
    }
    
    await db.spreadsheet_webhooks.update_one(
        {"user_id": user_id, "spreadsheet_url": body.spreadsheet_url},
        {"$set": watch_doc},
        upsert=True
    )
    
    return {
        "success": True,
        "message": "Successfully setup push notifications for this spreadsheet.",
        "channel_id": channel_id,
        "expiration": expiration
    }

@router.post("/stop-watch")
async def stop_watch(body: StopWatchRequest, current_user: CurrentUser):
    user_id = current_user.get("sub")
    db = get_db()
    
    # Find the active watch
    watch_doc = await db.spreadsheet_webhooks.find_one({
        "user_id": user_id, 
        "spreadsheet_url": body.spreadsheet_url
    })
    
    if not watch_doc:
        raise HTTPException(status_code=404, detail="No active auto-sync found for this spreadsheet.")
        
    try:
        await SpreadsheetService.stop_watch(
            access_token=body.access_token,
            channel_id=watch_doc["channel_id"],
            resource_id=watch_doc["resource_id"]
        )
    except ValueError as e:
        # We might still want to delete the doc from our DB even if Google fails (e.g. channel already expired)
        print(f"Warning: Failed to stop watch on Google side: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to communicate with Google: {str(e)}")
        
    # Delete the webhook from the database so we stop processing future pings (if any)
    await db.spreadsheet_webhooks.delete_one({"_id": watch_doc["_id"]})
    
    return {
        "success": True,
        "message": "Successfully stopped auto-sync for this spreadsheet."
    }

from fastapi import Query
from app.services.amazon_service import AmazonService
from app.schemas.enums import CountryEnum

@router.get("/scrape-supplier-link")
async def scrape_supplier_link(
    current_user: CurrentUser,
    supplier_link: str = Query(..., description="Amazon Supplier Link")
):
    asin, country_code = SpreadsheetService.extract_asin_and_country(supplier_link)
    if not asin or not country_code:
        raise HTTPException(status_code=400, detail="Could not extract ASIN or Country from the provided link.")
    
    try:
        country_enum = CountryEnum(country_code)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported country code: {country_code}")
        
    return await AmazonService.product_details(asin=asin, country=country_enum)


@router.get("/scrape-asin")
async def scrape_asin(
    current_user: CurrentUser,
    asin: str = Query(..., description="Amazon ASIN"),
    country: str = Query("US", description="Amazon Country Code (e.g. US, NL, UK)")
):
    try:
        country_enum = CountryEnum(country.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported country code: {country}")
        
    return await AmazonService.product_details(asin=asin, country=country_enum)


@router.post("/sync-asin")
async def sync_asin(
    current_user: CurrentUser,
    asin: str = Query(..., description="Amazon ASIN"),
    country: str = Query("US", description="Amazon Country Code (e.g. US, NL, UK)")
):
    try:
        country_enum = CountryEnum(country.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported country code: {country}")
        
    db = get_db()
    cache_doc = await db.scraped_products.find_one({"asin": asin, "country": country_enum.value})
    
    if cache_doc and cache_doc.get("updated_at"):
        if datetime.utcnow() - cache_doc["updated_at"] < timedelta(minutes=5):
            raise HTTPException(
                status_code=429, 
                detail="This product was refreshed less than 5 minutes ago. Please wait before syncing again."
            )
            
    # skip_cache=True bypasses the cache, forcing a live fetch and cache overwrite
    return await AmazonService.product_details(asin=asin, country=country_enum, skip_cache=True)
@router.get("/items")
async def get_items(
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    db = get_db()
    user_id = current_user.get("sub")
    
    skip = (page - 1) * limit
    # We sort by row_index descending to maintain spreadsheet bottom-up order
    cursor = db.user_spreadsheet_items.find({"user_id": user_id}).sort("row_index", -1).skip(skip).limit(limit)
    
    items = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        items.append(doc)
        
    total_items = await db.user_spreadsheet_items.count_documents({"user_id": user_id})
    
    return {
        "success": True,
        "page": page,
        "limit": limit,
        "total": total_items,
        "total_items": total_items,
        "total_pages": (total_items + limit - 1) // limit if limit > 0 else 0,
        "items": items
    }

import asyncio

@router.get("/scrape-items")
async def scrape_items(
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    db = get_db()
    user_id = current_user.get("sub")
    
    total_items = await db.user_spreadsheet_items.count_documents({"user_id": user_id})
    
    skip = (page - 1) * limit
    cursor = db.user_spreadsheet_items.find({"user_id": user_id}).sort("row_index", -1).skip(skip).limit(limit)
    
    items = []
    async for doc in cursor:
        items.append(doc)
        
    if not items:
        return {
            "status": "OK",
            "page": page,
            "limit": limit,
            "total": total_items,
            "data": []
        }

    sem = asyncio.Semaphore(2)
    
    async def fetch_product(item):
        supplier_link = item.get("supplier_link", "")
        asin, country_code = SpreadsheetService.extract_asin_and_country(supplier_link)
        if not asin or not country_code:
            return None
        
        try:
            country_enum = CountryEnum(country_code)
        except ValueError:
            return None
            
        async with sem:
            try:
                response = await AmazonService.product_details(asin=asin, country=country_enum)
                
                if not response or "data" not in response:
                    return None
                    
                data = response.get("data", {})
                
                return {
                    "asin": data.get("asin"),
                    "product_title": data.get("product_title"),
                    "product_price": data.get("product_price"),
                    "country": data.get("country"),
                    "product_star_rating": data.get("product_star_rating"),
                    "product_num_ratings": data.get("product_num_ratings"),
                    "product_url": data.get("product_url"),
                    "product_photo": data.get("product_photo"),
                    "return_policy": data.get("main_buy_box", {}).get("return_policy")
                }
            except Exception as e:
                print(f"Error fetching product details for {asin}: {e}")
                return None

    tasks = [fetch_product(item) for item in items]
    results = await asyncio.gather(*tasks)
    
    scraped_data = [res for res in results if res is not None]

    return {
        "status": "OK",
        "id": str(ObjectId()),
        "page": page,
        "limit": limit,
        "total": total_items,
        "data": scraped_data
    }

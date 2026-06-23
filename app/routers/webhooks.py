from fastapi import APIRouter, Request, Header
from app.core.database import get_db
from app.services.spreadsheet_service import SpreadsheetService
from pymongo import UpdateOne
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/google-drive")
async def google_drive_webhook(
    request: Request,
    x_goog_channel_id: str = Header(None, alias="X-Goog-Channel-ID"),
    x_goog_resource_state: str = Header(None, alias="X-Goog-Resource-State"),
    x_goog_resource_id: str = Header(None, alias="X-Goog-Resource-ID"),
):
    if not x_goog_channel_id:
        return {"status": "ignored", "reason": "Missing channel ID"}
        
    logger.info(f"Received Google Drive webhook. Channel: {x_goog_channel_id}, State: {x_goog_resource_state}")
    
    # We only care about update events (sync is the initial ping, trash is deletion)
    if x_goog_resource_state != "update":
        return {"status": "ignored", "reason": f"State is {x_goog_resource_state}"}

    db = get_db()
    watch_doc = await db.spreadsheet_webhooks.find_one({"channel_id": x_goog_channel_id})
    if not watch_doc:
        logger.warning(f"Received webhook for unknown channel: {x_goog_channel_id}")
        return {"status": "ignored", "reason": "Unknown channel"}
        
    user_id = watch_doc["user_id"]
    url = watch_doc["spreadsheet_url"]
    refresh_token = watch_doc["refresh_token"]
    
    try:
        # 1. Get a fresh access token using the offline refresh token
        access_token = await SpreadsheetService.refresh_google_token(refresh_token)
        
        # 2. Fetch the updated spreadsheet CSV
        csv_text = await SpreadsheetService.fetch_oauth_csv(url, access_token)
        data = SpreadsheetService.parse_csv_reversed(csv_text)
    except Exception as e:
        logger.error(f"Failed to fetch updated spreadsheet for user {user_id} via webhook: {str(e)}")
        return {"status": "error", "reason": str(e)}
        
    if not data:
        return {"status": "success", "message": "No rows to update"}
        
    # 3. Upsert rows into the database
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
                    "import_type": "oauth"
                }},
                upsert=True
            )
        )
        
    if requests:
        await db.user_spreadsheet_items.bulk_write(requests)
        
    logger.info(f"Successfully processed webhook for channel {x_goog_channel_id}. Upserted {len(requests)} rows.")
    return {"status": "success", "updated_rows": len(requests)}

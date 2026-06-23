from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

from pymongo import ASCENDING

class Database:
    client: AsyncIOMotorClient = None
    db = None

db_instance = Database()

def get_db():
    return db_instance.db

def users_col():
    return get_db()["users"]

def otp_col():
    return get_db()["otp_codes"]

def tokens_col():
    return get_db()["refresh_tokens"]

async def create_indexes():
    db = get_db()
    if db is None:
        return
    
    await db.users.create_index("email", unique=True)
    await db.users.create_index("google_id", sparse=True)
    await db.users.create_index("apple_id", sparse=True)
    
    await db.otp_codes.create_index("email")
    await db.otp_codes.create_index("expires_at", expireAfterSeconds=0)
    
    await db.refresh_tokens.create_index("token", unique=True)
    await db.refresh_tokens.create_index("user_id")
    await db.refresh_tokens.create_index("expires_at", expireAfterSeconds=0)
    
    await db.user_spreadsheet_items.create_index([("user_id", ASCENDING), ("supplier_link", ASCENDING)], unique=True)
    await db.user_spreadsheet_items.create_index([("updated_at", -1)])
    await db.user_spreadsheet_items.create_index([("row_index", -1)])
    
    await db.scraped_products.create_index([("asin", ASCENDING), ("country", ASCENDING)], unique=True)
    await db.scraped_products.create_index([("updated_at", -1)])
    
    print("[OK] MongoDB indexes created.")

async def connect_to_mongo():
    db_instance.client = AsyncIOMotorClient(settings.MONGO_URL)
    db_instance.db = db_instance.client.ball_com
    print("Connected to MongoDB")
    await create_indexes()

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        print("Closed MongoDB connection")

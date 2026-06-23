from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

from app.routers.amazon import router as amazon_router

from contextlib import asynccontextmanager
from app.core.database import connect_to_mongo, close_mongo_connection
from app.routers.auth import router as auth_router
from app.routers.spreadsheet import router as spreadsheet_router
from app.routers.webhooks import router as webhooks_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()

app = FastAPI(
    title="Ball Com API",
    version="1.0.0",
    lifespan=lifespan
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(spreadsheet_router)
app.include_router(webhooks_router)


@app.exception_handler(httpx.HTTPStatusError)
async def httpx_status_error_handler(request: Request, exc: httpx.HTTPStatusError):
    try:
        error_detail = exc.response.json()
    except Exception:
        error_detail = exc.response.text

    return JSONResponse(
        status_code=exc.response.status_code,
        content={
            "detail": "Upstream API error",
            "upstream_status_code": exc.response.status_code,
            "error": error_detail
        }
    )


@app.exception_handler(httpx.RequestError)
async def httpx_request_error_handler(request: Request, exc: httpx.RequestError):
    return JSONResponse(
        status_code=503,
        content={
            "detail": f"Failed to connect to upstream service: {str(exc)}"
        }
    )


app.include_router(amazon_router, include_in_schema=False)


@app.get("/")
async def root():
    return {"message": "Backend Running"}
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import httpx

from app.routers.amazon import router as amazon_router

app = FastAPI(
    title="Ball Com API",
    version="1.0.0"
)


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


app.include_router(amazon_router)


@app.get("/")
async def root():
    return {"message": "Backend Running"}
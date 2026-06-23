from datetime import datetime
from typing import Annotated
import httpx
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.database import users_col, otp_col, tokens_col
from app.core.auth_utils import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_access_token, decode_refresh_token,
    generate_otp, otp_expiry, refresh_expiry,
    send_verification_email, send_reset_email,
    get_current_user
)
from app.schemas.auth import (
    SignUpRequest, AdminSignUpRequest, SignInRequest, VerifyEmailRequest,
    ForgotPasswordRequest, ResetPasswordRequest,
    ChangePasswordRequest, RefreshTokenRequest,
    ResendOTPRequest, GoogleAuthRequest, AppleAuthRequest,
    ProfileUpdateRequest
)
from app.security.apple_auth import verify_apple_token

router = APIRouter(prefix="/auth", tags=["Authentication"])
CurrentUser = Annotated[dict, Depends(get_current_user)]

def _fmt(user: dict) -> dict:
    return {
        "id": str(user["_id"]),
        "email": user.get("email", ""),
        "full_name": user.get("full_name"),
        "role": user.get("role", "seller"),
        "is_verified": user.get("is_verified", False),
        "auth_provider": user.get("auth_provider", "email"),
        "created_at": user.get("created_at", datetime.utcnow()).isoformat(),
    }

def _tokens(user: dict) -> dict:
    uid = str(user["_id"])
    return {
        "access_token": create_access_token(uid, user["email"], user.get("role", "seller")),
        "refresh_token": create_refresh_token(uid),
    }

async def _save_refresh_token(user_id: str, token: str):
    await tokens_col().insert_one({
        "user_id": user_id,
        "token": token,
        "is_revoked": False,
        "expires_at": refresh_expiry(),
        "created_at": datetime.utcnow(),
    })

# ─────────────────────────────────────────────────
#  SIGN UP
# ─────────────────────────────────────────────────
@router.post("/signup", status_code=201)
async def signup(body: SignUpRequest):
    if await users_col().find_one({"email": body.email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    result = await users_col().insert_one({
        "email": body.email,
        "full_name": body.full_name,
        "hashed_password": hash_password(body.password),
        "role": "seller",
        "auth_provider": "email",
        "is_verified": False,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    otp = generate_otp()
    await otp_col().insert_one({
        "email": body.email,
        "code": otp,
        "purpose": "verify_email",
        "is_used": False,
        "expires_at": otp_expiry(),
        "created_at": datetime.utcnow(),
    })

    send_verification_email(body.email, body.full_name or "", otp)
    return {"success": True, "message": "Account created! Check your email for the verification code."}

@router.post("/signup/admin", status_code=201)
async def signup_admin(body: AdminSignUpRequest):
    from app.core.config import settings
    if body.admin_creation_secret != settings.ADMIN_CREATION_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin creation secret.")

    if await users_col().find_one({"email": body.email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    result = await users_col().insert_one({
        "email": body.email,
        "full_name": body.full_name,
        "hashed_password": hash_password(body.password),
        "role": "admin",
        "auth_provider": "email",
        "is_verified": False,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    })

    otp = generate_otp()
    await otp_col().insert_one({
        "email": body.email,
        "code": otp,
        "purpose": "verify_email",
        "is_used": False,
        "expires_at": otp_expiry(),
        "created_at": datetime.utcnow(),
    })

    send_verification_email(body.email, body.full_name or "", otp)
    return {"success": True, "message": "Admin account created! Check your email for the verification code."}

# ─────────────────────────────────────────────────
#  VERIFY EMAIL
# ─────────────────────────────────────────────────
@router.post("/verify-email")
async def verify_email(body: VerifyEmailRequest):
    otp_doc = await otp_col().find_one({
        "email": body.email,
        "code": body.otp,
        "purpose": "verify_email",
        "is_used": False,
        "expires_at": {"$gt": datetime.utcnow()},
    })
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP code.")

    await otp_col().update_one({"_id": otp_doc["_id"]}, {"$set": {"is_used": True}})
    await users_col().update_one({"email": body.email}, {"$set": {"is_verified": True, "updated_at": datetime.utcnow()}})
    return {"success": True, "message": "Email verified! You can now sign in."}

# ─────────────────────────────────────────────────
#  RESEND OTP
# ─────────────────────────────────────────────────
@router.post("/resend-otp")
async def resend_otp(body: ResendOTPRequest):
    user = await users_col().find_one({"email": body.email})
    if user:
        otp = generate_otp()
        await otp_col().insert_one({
            "email": body.email,
            "code": otp,
            "purpose": body.purpose,
            "is_used": False,
            "expires_at": otp_expiry(),
            "created_at": datetime.utcnow(),
        })
        if body.purpose == "reset_password":
            send_reset_email(body.email, otp)
        else:
            send_verification_email(body.email, user.get("full_name", ""), otp)
    return {"success": True, "message": "A new code has been sent to your email."}

# ─────────────────────────────────────────────────
#  SIGN IN
# ─────────────────────────────────────────────────
@router.post("/signin")
async def signin(body: SignInRequest):
    user = await users_col().find_one({"email": body.email})
    if not user or not user.get("hashed_password"):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account deactivated.")
    if not user.get("is_verified", False):
        raise HTTPException(status_code=403, detail="Email not verified. Please check your email for the OTP code.")

    tok = _tokens(user)
    await _save_refresh_token(str(user["_id"]), tok["refresh_token"])
    return {"success": True, **tok, "token_type": "bearer", "user": _fmt(user)}

# ─────────────────────────────────────────────────
#  GOOGLE SIGN IN
# ─────────────────────────────────────────────────
@router.post("/google")
async def google_signin(body: GoogleAuthRequest):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://oauth2.googleapis.com/tokeninfo?id_token={body.id_token}")
    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid Google token.")
    g = resp.json()
    if g.get("error_description"):
        raise HTTPException(status_code=401, detail=f"Google token error: {g['error_description']}")

    google_id = g.get("sub")
    email = g.get("email")
    full_name = g.get("name")
    
    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Could not retrieve Google account info.")

    user = await users_col().find_one({"$or": [{"google_id": google_id}, {"email": email}]})
    if user:
        update = {
            "google_id": google_id,
            "is_verified": True,
            "updated_at": datetime.utcnow(),
        }
        await users_col().update_one({"_id": user["_id"]}, {"$set": update})
        user = await users_col().find_one({"_id": user["_id"]})
    else:
        result = await users_col().insert_one({
            "email": email,
            "full_name": full_name,
            "hashed_password": None,
            "role": body.role,
            "auth_provider": "google",
            "is_verified": True,
            "is_active": True,
            "google_id": google_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        user = await users_col().find_one({"_id": result.inserted_id})

    tok = _tokens(user)
    await _save_refresh_token(str(user["_id"]), tok["refresh_token"])
    return {"success": True, **tok, "token_type": "bearer", "user": _fmt(user)}

# ─────────────────────────────────────────────────
#  APPLE SIGN IN
# ─────────────────────────────────────────────────
@router.post("/apple")
async def apple_signin(body: AppleAuthRequest):
    try:
        apple_data = await verify_apple_token(body.identity_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    apple_id = apple_data.get("sub")
    email = apple_data.get("email")

    if not apple_id:
        raise HTTPException(status_code=400, detail="Could not retrieve Apple account info.")

    query = {"apple_id": apple_id}
    if email:
        query = {"$or": [{"apple_id": apple_id}, {"email": email}]}

    user = await users_col().find_one(query)
    if user:
        update = {"apple_id": apple_id, "is_verified": True, "updated_at": datetime.utcnow()}
        if not user.get("full_name") and body.full_name and body.full_name.strip():
            update["full_name"] = body.full_name.strip()
        await users_col().update_one({"_id": user["_id"]}, {"$set": update})
        user = await users_col().find_one({"_id": user["_id"]})
    else:
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Apple.")
        result = await users_col().insert_one({
            "email": email,
            "full_name": body.full_name.strip() if body.full_name else None,
            "hashed_password": None,
            "role": body.role,
            "auth_provider": "apple",
            "is_verified": True,
            "is_active": True,
            "apple_id": apple_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        user = await users_col().find_one({"_id": result.inserted_id})

    tok = _tokens(user)
    await _save_refresh_token(str(user["_id"]), tok["refresh_token"])
    return {"success": True, **tok, "token_type": "bearer", "user": _fmt(user)}

# ─────────────────────────────────────────────────
#  REFRESH TOKEN
# ─────────────────────────────────────────────────
@router.post("/refresh")
async def refresh(body: RefreshTokenRequest):
    payload = decode_refresh_token(body.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    rt = await tokens_col().find_one({
        "token": body.refresh_token,
        "is_revoked": False,
        "expires_at": {"$gt": datetime.utcnow()},
    })
    if not rt:
        raise HTTPException(status_code=401, detail="Refresh token revoked or expired.")

    user = await users_col().find_one({"_id": ObjectId(rt["user_id"])})
    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    await tokens_col().update_one({"_id": rt["_id"]}, {"$set": {"is_revoked": True}})
    tok = _tokens(user)
    await _save_refresh_token(str(user["_id"]), tok["refresh_token"])
    return {"success": True, **tok, "token_type": "bearer", "user": _fmt(user)}

# ─────────────────────────────────────────────────
#  SIGN OUT
# ─────────────────────────────────────────────────
@router.post("/signout")
async def signout(body: RefreshTokenRequest):
    await tokens_col().update_one({"token": body.refresh_token}, {"$set": {"is_revoked": True}})
    return {"success": True, "message": "Signed out successfully."}

# ─────────────────────────────────────────────────
#  FORGOT PASSWORD
# ─────────────────────────────────────────────────
@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    user = await users_col().find_one({"email": body.email})
    if user and user.get("auth_provider") == "email":
        otp = generate_otp()
        await otp_col().insert_one({
            "email": body.email,
            "code": otp,
            "purpose": "reset_password",
            "is_used": False,
            "expires_at": otp_expiry(),
            "created_at": datetime.utcnow(),
        })
        send_reset_email(body.email, otp)
    return {"success": True, "message": "If this email is registered, a reset code has been sent."}

# ─────────────────────────────────────────────────
#  RESET PASSWORD
# ─────────────────────────────────────────────────
@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest):
    otp_doc = await otp_col().find_one({
        "email": body.email,
        "code": body.otp,
        "purpose": "reset_password",
        "is_used": False,
        "expires_at": {"$gt": datetime.utcnow()},
    })
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired reset code.")

    user = await users_col().find_one({"email": body.email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    await users_col().update_one({"_id": user["_id"]}, {"$set": {"hashed_password": hash_password(body.new_password), "updated_at": datetime.utcnow()}})
    await otp_col().update_one({"_id": otp_doc["_id"]}, {"$set": {"is_used": True}})
    await tokens_col().update_many({"user_id": str(user["_id"]), "is_revoked": False}, {"$set": {"is_revoked": True}})
    return {"success": True, "message": "Password reset! Please sign in with your new password."}

# ─────────────────────────────────────────────────
#  CHANGE PASSWORD
# ─────────────────────────────────────────────────
@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, current_user: CurrentUser):
    user_id = current_user.get("sub")
    user = await users_col().find_one({"_id": ObjectId(user_id)})
    if not user.get("hashed_password"):
        raise HTTPException(status_code=400, detail="OAuth accounts cannot use email password.")

    if not verify_password(body.current_password, user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    await users_col().update_one({"_id": user["_id"]}, {"$set": {"hashed_password": hash_password(body.new_password), "updated_at": datetime.utcnow()}})
    return {"success": True, "message": "Password changed successfully."}

# ─────────────────────────────────────────────────
#  ME (GET)
# ─────────────────────────────────────────────────
@router.get("/me")
async def get_me(current_user: CurrentUser):
    user = await users_col().find_one({"_id": ObjectId(current_user["sub"])})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "user": _fmt(user)}

# ─────────────────────────────────────────────────
#  ME (DELETE)
# ─────────────────────────────────────────────────
@router.delete("/me")
async def delete_me(current_user: CurrentUser):
    user_id = current_user["sub"]
    await users_col().delete_one({"_id": ObjectId(user_id)})
    await tokens_col().delete_many({"user_id": user_id})
    return {"success": True, "message": "Account deleted successfully."}

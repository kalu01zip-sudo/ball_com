import random, string, smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

from jose import JWTError, jwt


from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

security = HTTPBearer()

def decode_access_token(token: str) -> Optional[dict]:
    try:
        p = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return p if p.get("type") == "access" else None
    except JWTError:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return payload

import bcrypt

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), h.encode('utf-8'))
    except Exception:
        return False

def create_access_token(user_id: str, email: str, role: str) -> str:
    return jwt.encode({
        "sub": user_id, 
        "email": email, 
        "role": role,
        "type": "access",
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow(),
    }, settings.SECRET_KEY, algorithm="HS256")

def create_refresh_token(user_id: str) -> str:
    return jwt.encode({
        "sub": user_id, 
        "type": "refresh",
        "exp": datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.utcnow(),
    }, settings.REFRESH_SECRET_KEY, algorithm="HS256")

def decode_refresh_token(token: str) -> Optional[dict]:
    try:
        p = jwt.decode(token, settings.REFRESH_SECRET_KEY, algorithms=["HS256"])
        return p if p.get("type") == "refresh" else None
    except JWTError:
        return None

def refresh_expiry() -> datetime: 
    return datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

def otp_expiry() -> datetime: 
    return datetime.utcnow() + timedelta(minutes=10)

def generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))

def _send_email(to: str, subject: str, html: str) -> bool:
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print(f"\n[EMAIL MOCK] To: {to}\nSubject: {subject}\n{html}\n")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Ball Com <{settings.FROM_EMAIL}>"
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as s:
            s.ehlo()
            s.starttls()
            s.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            s.sendmail(settings.FROM_EMAIL, to, msg.as_string())
        return True
    except Exception as e:
        print(f"[ERROR] Email error: {e}")
        return False

def send_verification_email(to: str, name: str, otp: str) -> bool:
    return _send_email(to, "Verify your Ball Com account", f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2>Welcome to Ball Com</h2>
      <p>Hi <strong>{name or 'there'}</strong>, your verification code is:</p>
      <div style="background:#F0F7FF;border-radius:12px;padding:24px;text-align:center;margin:24px 0;">
        <span style="font-size:40px;font-weight:bold;letter-spacing:8px;">{otp}</span>
      </div>
      <p>Expires in <strong>10 minutes</strong>. Do not share this code.</p>
    </div>""")

def send_reset_email(to: str, otp: str) -> bool:
    return _send_email(to, "Reset your Ball Com password", f"""
    <div style="font-family:Arial,sans-serif;max-width:480px;margin:auto;padding:32px;">
      <h2>Ball Com — Password Reset</h2>
      <p>Use this code to reset your password:</p>
      <div style="background:#FFF0F0;border-radius:12px;padding:24px;text-align:center;margin:24px 0;">
        <span style="font-size:40px;font-weight:bold;letter-spacing:8px;">{otp}</span>
      </div>
      <p>Expires in <strong>10 minutes</strong>.</p>
    </div>""")

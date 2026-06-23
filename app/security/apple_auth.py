import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
import json
from app.core.config import settings

APPLE_KEYS_URL = "https://appleid.apple.com/auth/keys"
APPLE_ISSUER = "https://appleid.apple.com"

async def verify_apple_token(identity_token: str) -> dict:
    async with httpx.AsyncClient() as client:
        resp = await client.get(APPLE_KEYS_URL)
        if resp.status_code != 200:
            raise ValueError("Failed to fetch Apple public keys.")
        apple_keys = resp.json().get("keys", [])

    unverified_header = jwt.get_unverified_header(identity_token)
    kid = unverified_header.get("kid")
    if not kid:
        raise ValueError("No 'kid' in Apple token header.")

    matching_key = next((k for k in apple_keys if k["kid"] == kid), None)
    if not matching_key:
        raise ValueError("No matching Apple public key found.")

    public_key = RSAAlgorithm.from_jwk(json.dumps(matching_key))

    try:
        payload = jwt.decode(
            identity_token,
            public_key,
            algorithms=["RS256"],
            audience=settings.APPLE_BUNDLE_ID,
            issuer=APPLE_ISSUER,
        )
    except jwt.ExpiredSignatureError:
        raise ValueError("Apple token has expired.")
    except jwt.InvalidTokenError as e:
        raise ValueError(f"Apple token invalid: {str(e)}")

    return payload

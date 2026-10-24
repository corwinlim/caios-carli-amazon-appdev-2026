"""P0-A: offline HMAC-bound owner identity proof, NOT a production identity provider."""
import base64
import hashlib
import hmac
import json
import time

class IdentityDenied(Exception):
    pass

def _encode(obj):
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

def _decode(part):
    return base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))

def mint_test_token(secret, *, subject, pet_ids, scopes, expires_at, issued_at, issuer="carli-test", audience="carli-p0a"):
    """Test-only helper. Do not expose token minting in an API."""
    claims = dict(sub=subject, pets=pet_ids, scopes=scopes, exp=expires_at,
                  iat=issued_at, iss=issuer, aud=audience)
    body = _encode(claims)
    sig = hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest()
    return body + "." + base64.urlsafe_b64encode(sig).rstrip(b"=").decode()

def verify_owner_token(token, *, secret, pet_id, scope, now=None, issuer="carli-test", audience="carli-p0a", revoked_subjects=()):
    """Fail closed; verified identity must replace caller-supplied owner_id."""
    if not isinstance(token, str) or token.count(".") != 1 or len(token) > 4096:
        raise IdentityDenied("invalid token format")
    body, signature = token.split(".")
    expected = hmac.new(secret, body.encode("ascii"), hashlib.sha256).digest()
    try:
        supplied = _decode(signature)
        claims = json.loads(_decode(body))
    except (ValueError, UnicodeError, TypeError):
        raise IdentityDenied("malformed token") from None
    if not hmac.compare_digest(expected, supplied):
        raise IdentityDenied("signature mismatch")
    if not isinstance(claims, dict):
        raise IdentityDenied("invalid claims")
    current = int(time.time()) if now is None else now
    sub = claims.get("sub")
    if not isinstance(sub, str) or not sub or sub in revoked_subjects:
        raise IdentityDenied("subject invalid or revoked")
    if claims.get("iss") != issuer or claims.get("aud") != audience:
        raise IdentityDenied("wrong issuer or audience")
    if type(claims.get("exp")) is not int or type(claims.get("iat")) is not int:
        raise IdentityDenied("invalid timestamps")
    if claims["iat"] > current or claims["exp"] <= current or claims["exp"] <= claims["iat"]:
        raise IdentityDenied("expired or future token")
    pets, scopes = claims.get("pets"), claims.get("scopes")
    if not isinstance(pets, list) or not all(isinstance(x, str) for x in pets):
        raise IdentityDenied("invalid pet grants")
    if not isinstance(scopes, list) or not all(isinstance(x, str) for x in scopes):
        raise IdentityDenied("invalid scopes")
    if pet_id not in pets or scope not in scopes:
        raise IdentityDenied("pet or scope not granted")
    return {"verified_owner_id": sub, "verified_pet_id": pet_id, "verified_scope": scope}

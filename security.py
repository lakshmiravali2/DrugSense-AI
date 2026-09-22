"""Cryptographic integrity helpers: image hashing and record signing.

For the prototype, HMAC-SHA256 with a local secret stands in for the
"digital signature" requirement. In a production deployment this would be
replaced with a proper asymmetric signature (e.g. an officer's PKI-issued
key), so that a signature is non-repudiable and tied to a specific person.
"""

import hashlib
import hmac
import json

SECRET_KEY = b"prototype-demo-secret-change-me"  # NEVER use this in production


def hash_image_bytes(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def sign_record(record: dict) -> str:
    """
    Produce a deterministic HMAC over the record's core fields, so that any
    later change to the record (or the image it points to) is detectable.
    """
    payload = json.dumps(record, sort_keys=True).encode("utf-8")
    return hmac.new(SECRET_KEY, payload, hashlib.sha256).hexdigest()


def verify_record(record: dict, signature: str) -> bool:
    expected = sign_record(record)
    return hmac.compare_digest(expected, signature)

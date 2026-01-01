import asyncio
import base64
from contextlib import asynccontextmanager
from urllib.parse import urlencode

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.types import (
    PrivateKeyTypes,
    PublicKeyTypes,
)


@asynccontextmanager
async def set_event(event: asyncio.Event):
    """Temporarily sets up an event"""
    event.set()
    try:
        yield
    finally:
        event.clear()


@asynccontextmanager
async def remove_event(event: asyncio.Event):
    """Temporarily removes the event"""
    event.clear()
    try:
        yield
    finally:
        event.set()


def load_private_key_from_pep(
    path: str, password: bytes | None = None
) -> PrivateKeyTypes:
    """Load private key from .pem file."""
    with open(path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=password)


def load_public_key_from_pep(path: str) -> PublicKeyTypes:
    """Load public key from .pem file."""
    with open(path, "rb") as f:
        return serialization.load_pem_public_key(f.read())


def sign_msg(private_key: PrivateKeyTypes, payload: dict):
    """Format, encode and sign the payload msg using private_key."""
    return base64.b64encode(
        private_key.sign(urlencode(payload).encode("utf-8"))
    ).decode()

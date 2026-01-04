import asyncio
import base64
import time
from contextlib import asynccontextmanager, contextmanager
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


def sign_payload(private_key: PrivateKeyTypes, payload: dict) -> str:
    """Create signature for payload."""
    return base64.b64encode(
        private_key.sign(urlencode(payload).encode("utf-8"))
    ).decode()


def get_signed_payload(
    private_key: PrivateKeyTypes, payload: dict, key: str = "signature"
) -> str:
    """Return the received `payload` with a signature;
    The signature will be located behind the `key`."""

    _payload = {str(_key): str(_value) for _key, _value in payload.items()}
    return {**_payload, key: sign_payload(private_key, _payload)}


@contextmanager
def measure(label: str):
    """
    Measure time using time.time()
    
    Args:
        label (srt): used to denote a timestamp:
            print(f"{label}: {timedelta}")
    """
    start = time.time()
    try:
        yield
    finally:
        print(f"{label}: {time.time() - start}")

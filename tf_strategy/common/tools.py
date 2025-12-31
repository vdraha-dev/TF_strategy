import asyncio
from contextlib import asynccontextmanager


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
    event.set()
    try:
        yield
    finally:
        event.clear()

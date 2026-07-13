import asyncio

import pytest


def test_sanity():
    """Verify that synchronous tests run correctly."""
    assert True


@pytest.mark.asyncio
async def test_async_sanity():
    """Verify that asynchronous tests run correctly."""
    await asyncio.sleep(0.01)
    assert True

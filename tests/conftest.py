"""Asynchronous Python client for Tailwind garage door openers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import aiohttp
import pytest
from aioresponses import core as aioresponses_core

if TYPE_CHECKING:
    from collections.abc import Generator

AIOHTTP_REQUIRES_STREAM_WRITER = (
    "stream_writer" in aiohttp.ClientResponse.__init__.__code__.co_varnames
)


class AioresponsesClientResponse(aioresponses_core.ClientResponse):
    """Backwards-compatible ClientResponse for aioresponses."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize and provide a stream_writer for aiohttp 3.14+."""
        if AIOHTTP_REQUIRES_STREAM_WRITER:
            kwargs.setdefault("stream_writer", Mock(output_size=0))
        super().__init__(*args, **kwargs)


@pytest.fixture(autouse=True)
def setup_aioresponses_aiohttp_compat() -> Generator[None, None, None]:
    """Patch aioresponses ClientResponse for aiohttp compatibility in tests."""
    if not AIOHTTP_REQUIRES_STREAM_WRITER:
        yield
        return

    with patch.object(
        aioresponses_core,
        "ClientResponse",
        AioresponsesClientResponse,
    ):
        yield

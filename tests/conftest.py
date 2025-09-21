"""Fixtures for Tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest
from bleak.backends.device import BLEDevice


@pytest.fixture
def mock_bleak_client() -> Generator[AsyncMock]:
    """Mock bleak client."""

    with patch("pynecil.client.BleakClient", autospec=True) as mock_client:
        client = mock_client.return_value
        client.is_connected = True
        client.read_gatt_char.return_value = b"\x00\x00"
        yield client


@pytest.fixture
def mock_establish_connection(mock_bleak_client: AsyncMock) -> Generator[AsyncMock]:
    """Mock bleak_retry_connector."""
    with patch(
        "pynecil.client.establish_connection",
        return_value=mock_bleak_client,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_bleak_scanner() -> Generator[AsyncMock]:
    """Mock bleak scanner."""

    with patch("pynecil.client.BleakScanner", autospec=True) as mock_client:
        client = mock_client.return_value

        client.find_device_by_filter.return_value = BLEDevice(
            address="AA:BB:CC:DD:EE:FF", name="Pinecil-ABCDEF", details={}
        )
        yield client

"""Pynecil - Python library to communicate with Pinecil V2 soldering irons via Bluetooth."""

__version__ = "0.1.0"

from .client import Pynecil, discover
from .exceptions import CommunicationError
from .types import (
    CharBulk,
    CharLive,
    CharSetting,
    DeviceInfoResponse,
    LanguageCode,
    LiveDataResponse,
    OperatingMode,
    PowerSource,
    SettingsDataResponse,
)

__all__ = [
    "CharBulk",
    "CharLive",
    "CharSetting",
    "CommunicationError",
    "DeviceInfoResponse",
    "discover",
    "LanguageCode",
    "LiveDataResponse",
    "OperatingMode",
    "PowerSource",
    "Pynecil",
    "SettingsDataResponse",
]

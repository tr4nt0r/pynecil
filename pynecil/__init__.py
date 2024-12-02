"""Pynecil - Python library to communicate with Pinecil V2 soldering irons via Bluetooth."""

__version__ = "1.0.1"

from .client import Pynecil, discover
from .exceptions import CommunicationError
from .types import (
    AnimationSpeed,
    AutostartMode,
    BatteryType,
    CharBulk,
    CharLive,
    CharSetting,
    DeviceInfoResponse,
    LanguageCode,
    LiveDataResponse,
    LockingMode,
    LogoDuration,
    OperatingMode,
    PowerSource,
    ScreenOrientationMode,
    ScrollSpeed,
    SettingsDataResponse,
    TempUnit,
)

__all__ = [
    "AnimationSpeed",
    "AutostartMode",
    "BatteryType",
    "CharBulk",
    "CharLive",
    "CharSetting",
    "CommunicationError",
    "DeviceInfoResponse",
    "discover",
    "LanguageCode",
    "LiveDataResponse",
    "LockingMode",
    "LogoDuration",
    "OperatingMode",
    "PowerSource",
    "Pynecil",
    "ScreenOrientationMode",
    "ScrollSpeed",
    "SettingsDataResponse",
    "TempUnit",
]

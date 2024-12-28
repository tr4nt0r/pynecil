"""Pynecil - Python library to communicate with Pinecil V2 soldering irons via Bluetooth."""

__version__ = "3.0.0"
from .client import Pynecil, discover
from .exceptions import CommunicationError, UpdateException
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
from .update import IronOSUpdate, LatestRelease

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
    "IronOSUpdate",
    "LanguageCode",
    "LatestRelease",
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
    "UpdateException",
]

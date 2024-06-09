"""Parser for Pinecil V2 devices."""

from __future__ import annotations

import hashlib
import logging
import struct
from collections.abc import Callable
from typing import Any

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from . import const
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
)

_LOGGER = logging.getLogger(__name__)


async def discover() -> BLEDevice | None:
    """Discover Pinecil devices."""
    return await BleakScanner().find_device_by_filter(
        filterfunc=lambda device, advertisement: bool(
            str(const.SVC_UUID_BULK) in advertisement.service_uuids
        ),
    )


class Client:
    """Parser for Pinecil V2 Devices."""

    client_disconnected: bool = False

    def __init__(
        self,
        ble_device: BLEDevice,
        disconnected_callback: Callable[[BleakClient], None] | None = None,
    ) -> None:
        self.device_info = DeviceInfoResponse(
            name=ble_device.name, address=ble_device.address
        )

        def _disconnected_callback(client: BleakClient) -> None:
            _LOGGER.debug("Disconnected from %s", client.address)
            self.client_disconnected = True

        self._client = BleakClient(
            ble_device,
            disconnected_callback=disconnected_callback or _disconnected_callback,
        )

    async def connect(self):
        """Establish connection."""
        if not self._client.is_connected:
            if self.client_disconnected:  # close stale connection
                await self.disconnect()
            await self._client.connect()

    async def disconnect(self):
        """Disconnect connection."""
        await self._client.disconnect()
        self.client_disconnected = False

    async def get_device_info(self) -> DeviceInfoResponse:
        """Get device info."""
        if self.device_info.is_synced:
            return self.device_info

        try:
            self.device_info.build = await self.read(CharBulk.BUILD)
            self.device_info.device_sn = await self.read(CharBulk.DEVICE_SN)
            self.device_info.device_id = await self.read(CharBulk.DEVICE_ID)
            self.device_info.is_synced = True
        except (BleakError, TimeoutError) as e:
            _LOGGER.debug("Get device characteristics exception: %s", e)
            raise CommunicationError from e

        return self.device_info

    async def get_live_data(self) -> LiveDataResponse:
        """Get live sensor data."""

        return await self.read(CharBulk.LIVE_DATA)

    async def get_settings(
        self, settings: list[CharSetting | int] | None = None
    ) -> dict[str, Any]:
        """Get settings data."""

        if settings is None:
            settings = []
        return {
            characteristic.name.lower(): await self.read(characteristic)
            for characteristic in CHARACTERISTICS
            if isinstance(characteristic, CharSetting)
            and (
                not settings
                or characteristic in settings
                or characteristic.value in settings
            )
        }

    async def read(self, characteristic: CharLive | CharSetting | CharBulk) -> Any:
        """Read characteristic."""
        uuid, decode, *_ = CHARACTERISTICS[characteristic]
        if not decode:
            return
        try:
            await self.connect()
            result = await self._client.read_gatt_char(uuid)
            _LOGGER.debug("Read characteristic %s, result: %s", str(uuid), result)
        except (BleakError, TimeoutError) as e:
            _LOGGER.debug("Get device characteristics exception: %s", e)
            raise CommunicationError from e
        return decode(result)

    async def write(self, setting: CharSetting, value: Any) -> None:
        """Write characteristic."""
        uuid, _, convert, validate = CHARACTERISTICS[setting]
        data = validate(convert(value))
        try:
            await self.connect()
            await self._client.write_gatt_char(uuid, encode_int(data))
        except (BleakError, TimeoutError) as e:
            _LOGGER.debug("Get device characteristics exception: %s", e)
            raise CommunicationError from e


def decode_int(raw: bytearray) -> int:
    """Decode uint32."""
    return int.from_bytes(raw, byteorder="little", signed=False)


def decode_str(raw: bytearray) -> str:
    """Decode uint32."""
    return raw.decode("utf-8")


def decode_live_data(raw: bytearray) -> LiveDataResponse:
    """Parse bytearray from bulk live data."""
    data = struct.unpack("14I", raw)
    return LiveDataResponse(
        data[0],
        data[1],
        data[2] / 10,
        data[3] / 10,
        int(data[4] / 255 * 100),
        PowerSource(data[5]),
        data[6] / 10,
        data[7],
        data[8],
        data[9],
        data[10] / 1000,
        data[11],
        OperatingMode(data[12]),
        data[13] / 10,
    )


def clip(a: int, a_min: int, a_max: int) -> int:
    """Clamp a value between max and min limits."""
    a = min(a, a_max)
    return max(a, a_min)


def encode_int(val: int) -> bytes:
    """Encode integer as byte."""
    return val.to_bytes(2, byteorder="little", signed=False)


def encode_lang_code(val: str | LanguageCode) -> int:
    """Encode language code to corresponding byte value."""
    if isinstance(val, LanguageCode):
        return int(val.value)
    return int(hashlib.sha1(val.encode("utf-8")).hexdigest(), 16) % 0xFFFF


def decode_lang_code(raw: bytearray) -> LanguageCode | int | None:
    """Decode hashed value to language code."""
    try:
        return LanguageCode(decode_int(raw))
    except ValueError:
        return decode_int(raw)


# Define uuid, decoding, encoding and input sanitizing methods for each characteristic
CHARACTERISTICS: dict[CharLive | CharSetting | CharBulk, tuple] = {
    CharBulk.LIVE_DATA: (const.CHAR_UUID_BULK_LIVE_DATA, decode_live_data),
    CharBulk.BUILD: (const.CHAR_UUID_BULK_BUILD, decode_str),
    CharBulk.DEVICE_SN: (
        const.CHAR_UUID_BULK_DEVICE_SN,
        lambda x: f"{decode_int(x):016x}",
    ),
    CharBulk.DEVICE_ID: (
        const.CHAR_UUID_BULK_DEVICE_ID,
        lambda x: f"{decode_int(x):x}",
    ),
    CharLive.LIVE_TEMP: (const.CHAR_UUID_LIVE_LIVE_TEMP, decode_int),
    CharLive.SETPOINT_TEMP: (const.CHAR_UUID_LIVE_SETPOINT_TEMP, decode_int),
    CharLive.DC_VOLTAGE: (
        const.CHAR_UUID_LIVE_DC_VOLTAGE,
        lambda x: decode_int(x) / 10,
    ),
    CharLive.HANDLE_TEMP: (
        const.CHAR_UUID_LIVE_HANDLE_TEMP,
        lambda x: decode_int(x) / 10,
    ),
    CharLive.PWMLEVEL: (
        const.CHAR_UUID_LIVE_PWMLEVEL,
        lambda x: int(decode_int(x) / 255 * 100),  # convert to percent
    ),
    CharLive.POWER_SRC: (
        const.CHAR_UUID_LIVE_POWER_SRC,
        lambda x: PowerSource(decode_int(x)),
    ),
    CharLive.TIP_RESISTANCE: (
        const.CHAR_UUID_LIVE_TIP_RESISTANCE,
        lambda x: decode_int(x) / 10,
    ),
    CharLive.UPTIME: (const.CHAR_UUID_LIVE_UPTIME, decode_int),
    CharLive.MOVEMENT_TIME: (const.CHAR_UUID_LIVE_MOVEMENT_TIME, decode_int),
    CharLive.TIP_VOLTAGE: (
        const.CHAR_UUID_LIVE_TIP_VOLTAGE,
        lambda x: decode_int(x) / 1000,  # convert to mVolt
    ),
    CharLive.HALL_SENSOR: (const.CHAR_UUID_LIVE_HALL_SENSOR, decode_int),
    CharLive.OPERATING_MODE: (
        const.CHAR_UUID_LIVE_OPERATING_MODE,
        lambda x: OperatingMode(decode_int(x)),
    ),
    CharLive.ESTIMATED_POWER: (const.CHAR_UUID_LIVE_ESTIMATED_POWER, decode_int),
    CharSetting.SETPOINT_TEMP: (
        const.CHAR_UUID_SETTINGS_SETPOINT_TEMP,
        decode_int,
        int,
        lambda x: clip(x, 10, 450),
    ),
    CharSetting.SLEEP_TEMP: (
        const.CHAR_UUID_SETTINGS_SLEEP_TEMP,
        decode_int,
        int,
        lambda x: clip(x, 10, 450),
    ),
    CharSetting.SLEEP_TIMEOUT: (
        const.CHAR_UUID_SETTINGS_SLEEP_TIMEOUT,
        decode_int,
        int,
        lambda x: clip(x, 0, 15),
    ),
    CharSetting.MIN_DC_VOLTAGE_CELLS: (
        const.CHAR_UUID_SETTINGS_MIN_DC_VOLTAGE_CELLS,
        decode_int,
        int,
        lambda x: clip(x, 0, 4),
    ),
    CharSetting.MIN_VOLLTAGE_PER_CELL: (
        const.CHAR_UUID_SETTINGS_MIN_VOLLTAGE_PER_CELL,
        lambda x: decode_int(x) / 10,
        lambda x: int(x * 10),
        lambda x: clip(x, 24, 38),
    ),
    CharSetting.QC_IDEAL_VOLTAGE: (
        const.CHAR_UUID_SETTINGS_QC_IDEAL_VOLTAGE,
        lambda x: decode_int(x) / 10,
        lambda x: int(x * 10),
        lambda x: clip(x, 90, 220),
    ),
    CharSetting.ORIENTATION_MODE: (
        const.CHAR_UUID_SETTINGS_ORIENTATION_MODE,
        decode_int,
        int,
        lambda x: clip(x, 0, 2),
    ),
    CharSetting.ACCEL_SENSITIVITY: (
        const.CHAR_UUID_SETTINGS_ACCEL_SENSITIVITY,
        decode_int,
        int,
        lambda x: clip(x, 0, 9),
    ),
    CharSetting.ANIMATION_LOOP: (
        const.CHAR_UUID_SETTINGS_ANIMATION_LOOP,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.ANIMATION_SPEED: (
        const.CHAR_UUID_SETTINGS_ANIMATION_SPEED,
        decode_int,
        int,
        lambda x: clip(x, 0, 3),
    ),
    CharSetting.AUTOSTART_MODE: (
        const.CHAR_UUID_SETTINGS_AUTOSTART_MODE,
        decode_int,
        int,
        lambda x: clip(x, 0, 3),
    ),
    CharSetting.SHUTDOWN_TIME: (
        const.CHAR_UUID_SETTINGS_SHUTDOWN_TIME,
        decode_int,
        int,
        lambda x: clip(x, 0, 60),
    ),
    CharSetting.COOLING_TEMP_BLINK: (
        const.CHAR_UUID_SETTINGS_COOLING_TEMP_BLINK,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.IDLE_SCREEN_DETAILS: (
        const.CHAR_UUID_SETTINGS_IDLE_SCREEN_DETAILS,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.SOLDER_SCREEN_DETAILS: (
        const.CHAR_UUID_SETTINGS_SOLDER_SCREEN_DETAILS,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.TEMP_UNIT: (
        const.CHAR_UUID_SETTINGS_TEMP_UNIT,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.DESC_SCROLL_SPEED: (
        const.CHAR_UUID_SETTINGS_DESC_SCROLL_SPEED,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.LOCKING_MODE: (
        const.CHAR_UUID_SETTINGS_LOCKING_MODE,
        decode_int,
        int,
        lambda x: clip(x, 0, 2),
    ),
    CharSetting.KEEP_AWAKE_PULSE: (
        const.CHAR_UUID_SETTINGS_KEEP_AWAKE_PULSE,
        decode_int,
        int,
        lambda x: clip(x, 0, 99),
    ),
    CharSetting.KEEP_AWAKE_PULSE_WAIT: (
        const.CHAR_UUID_SETTINGS_KEEP_AWAKE_PULSE_WAIT,
        decode_int,
        int,
        lambda x: clip(x, 0, 9),
    ),
    CharSetting.KEEP_AWAKE_PULSE_DURATION: (
        const.CHAR_UUID_SETTINGS_KEEP_AWAKE_PULSE_DURATION,
        decode_int,
        int,
        lambda x: clip(x, 0, 9),
    ),
    CharSetting.VOLTAGE_DIV: (
        const.CHAR_UUID_SETTINGS_VOLTAGE_DIV,
        decode_int,
        int,
        lambda x: clip(x, 360, 900),
    ),
    CharSetting.BOOST_TEMP: (
        const.CHAR_UUID_SETTINGS_BOOST_TEMP,
        decode_int,
        int,
        lambda x: clip(x, 0, 450),
    ),
    CharSetting.CALIBRATION_OFFSET: (
        const.CHAR_UUID_SETTINGS_CALIBRATION_OFFSET,
        decode_int,
        int,
        lambda x: clip(x, 100, 2500),
    ),
    CharSetting.POWER_LIMIT: (
        const.CHAR_UUID_SETTINGS_POWER_LIMIT,
        decode_int,
        int,
        lambda x: clip(x, 0, 120),
    ),
    CharSetting.INVERT_BUTTONS: (
        const.CHAR_UUID_SETTINGS_INVERT_BUTTONS,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.TEMP_INCREMENT_LONG: (
        const.CHAR_UUID_SETTINGS_TEMP_INCREMENT_LONG,
        decode_int,
        int,
        lambda x: clip(x, 5, 90),
    ),
    CharSetting.TEMP_INCREMENT_SHORT: (
        const.CHAR_UUID_SETTINGS_TEMP_INCREMENT_SHORT,
        decode_int,
        int,
        lambda x: clip(x, 1, 50),
    ),
    CharSetting.HALL_SENSITIVITY: (
        const.CHAR_UUID_SETTINGS_HALL_SENSITIVITY,
        decode_int,
        int,
        lambda x: clip(x, 0, 9),
    ),
    CharSetting.ACCEL_WARN_COUNTER: (
        const.CHAR_UUID_SETTINGS_ACCEL_WARN_COUNTER,
        decode_int,
        int,
        lambda x: clip(x, 0, 9),
    ),
    CharSetting.PD_WARN_COUNTER: (
        const.CHAR_UUID_SETTINGS_PD_WARN_COUNTER,
        decode_int,
        int,
        lambda x: clip(x, 0, 9),
    ),
    CharSetting.UI_LANGUAGE: (
        const.CHAR_UUID_SETTINGS_UI_LANGUAGE,
        decode_lang_code,
        encode_lang_code,
        lambda x: clip(x, 0, 65535),
    ),
    CharSetting.PD_NEGOTIATION_TIMEOUT: (
        const.CHAR_UUID_SETTINGS_PD_NEGOTIATION_TIMEOUT,
        decode_int,
        int,
        lambda x: clip(x, 0, 50),
    ),
    CharSetting.DISPLAY_INVERT: (
        const.CHAR_UUID_SETTINGS_DISPLAY_INVERT,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.DISPLAY_BRIGHTNESS: (
        const.CHAR_UUID_SETTINGS_DISPLAY_BRIGHTNESS,
        lambda x: int((decode_int(x) + 24) / 25),  # convert to values 1-5
        lambda x: int(25 * x - 24),
        lambda x: clip(x, 1, 101),
    ),
    CharSetting.LOGO_DURATION: (
        const.CHAR_UUID_SETTINGS_LOGO_DURATION,
        decode_int,
        int,
        lambda: 1,
    ),
    CharSetting.CALIBRATE_CJC: (
        const.CHAR_UUID_SETTINGS_CALIBRATE_CJC,
        decode_int,
        int,
        lambda: 1,
    ),
    CharSetting.BLE_ENABLED: (
        const.CHAR_UUID_SETTINGS_BLE_ENABLED,
        decode_int,
        int,
        lambda: 1,
    ),
    CharSetting.USB_PD_MODE: (
        const.CHAR_UUID_SETTINGS_USB_PD_MODE,
        decode_int,
        int,
        lambda: 1,
    ),
    CharSetting.SETTINGS_SAVE: (
        const.CHAR_UUID_SETTINGS_SAVE,
        decode_int,
        int,
        lambda x: 1,
    ),
    CharSetting.SETTINGS_RESET: (
        const.CHAR_UUID_SETTINGS_RESET,
        decode_int,
        int,
        lambda x: 1,
    ),
}

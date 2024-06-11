"""Pynecil - Python library to communicate with Pinecil V2 soldering irons via Bluetooth."""

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
    Characteristic,
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


async def discover(timeout: float = 10) -> BLEDevice | None:
    """Discover Pinecil device.

    Parameters
    ----------
    timeout : float, optional
         Timeout to wait for detection before giving up, by default 10

    Returns
    -------
        BLEDevice | None
            The BLEDevice of a Pinecil or None if not detected
            before the timeout.

    """
    return await BleakScanner().find_device_by_filter(
        filterfunc=lambda device, advertisement: bool(
            str(const.SVC_UUID_BULK) in advertisement.service_uuids
        ),
        timeout=timeout,
    )


class Pynecil:
    """Client for Pinecil V2 Devices."""

    client_disconnected: bool = False

    def __init__(
        self,
        address_or_ble_device: BLEDevice | str,
        disconnected_callback: Callable[[BleakClient], None] | None = None,
    ) -> None:
        """Initialize a Pynecil client.

        Parameters
        ----------
        address_or_ble_device : BLEDevice | str
            Bluetooth address of the Pinecil V2 device to connect to or BLEDevice object,
            received from a BleakScanner, representing it.
        disconnected_callback : Callable[[BleakClient], None] | None, optional
            Callback passed to BleakClient that will be scheduled in the event loop
            when the client is disconnected. The callable must take one argument,
            which will be the client object, by default None

        """
        if isinstance(address_or_ble_device, BLEDevice):
            self.device_info = DeviceInfoResponse(
                name=address_or_ble_device.name, address=address_or_ble_device.address
            )
        else:
            self.device_info = DeviceInfoResponse(address=address_or_ble_device)

        def _disconnected_callback(client: BleakClient) -> None:
            _LOGGER.debug("Disconnected from %s", client.address)
            self.client_disconnected = True

        self._client = BleakClient(
            address_or_ble_device,
            disconnected_callback=disconnected_callback or _disconnected_callback,
        )

    async def connect(self) -> None:
        """Establish connection.

        Establishes a connection to the device, if not already connected, and closes
        previously opened stale connections if an unexpected disconnect occurred.

        """
        if not self._client.is_connected:
            if self.client_disconnected:  # close stale connection
                await self.disconnect()
            await self._client.connect()

    async def disconnect(self) -> None:
        """Disconnect from the Pinecil device."""
        await self._client.disconnect()
        self.client_disconnected = False

    async def get_device_info(self) -> DeviceInfoResponse:
        """Get device info.

        Returns
        -------
        DeviceInfoResponse
            Object containing `name`, `address`, `build`, `device_sn` and `device_id` of
            the Pinecil V2 device connected.

        Raises
        ------
        CommunicationError
            If an error occurred while connecting and retrieving data from device.

        """
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
        """Get live sensor data.

        Returns
        -------
        LiveDataResponse
            Object containing 14 values retrieved from the
            bulk live data characteristic.

        Raises
        ------
        CommunicationError
            If an error occurred while connecting and retrieving data from device.

        """
        return await self.read(CharBulk.LIVE_DATA)

    async def get_settings(
        self, settings: list[CharSetting | int] | None = None
    ) -> dict[str, Any]:
        """Get settings data.

        Parameters
        ----------
        settings : list[CharSetting  |  int] | None, optional
            List of Settings identified by a `CharSetting` item or their ID that should
            be retrieved from the device. Retrieves all Settings if ommited.

        Returns
        -------
        dict[str, Any]
            Dict with name (lowercase) and normalized values of the settings retrieved
            from the device.

        Raises
        ------
        CommunicationError
            If an error occurred while connecting and retrieving data from device.

        """
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

    async def read(self, characteristic: Characteristic) -> Any:
        """Read specified characteristic and decode the result.

        Parameters
        ----------
        characteristic : Characteristic
            Characteristic to retrieve from device.

        Returns
        -------
        Any
            Value read from characteristic and parsed with the corresponding decoder.

        Raises
        ------
        CommunicationError
            If an error occurred while connecting and retrieving data from device.

        """
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


def decode_int(value: bytearray) -> int:
    """Decode byte value to an integer.

    Parameters
    ----------
    value : bytearray
        The byte encoded integer value.

    Returns
    -------
    int
        Value as integer.

    """
    return int.from_bytes(value, byteorder="little", signed=False)


def decode_str(value: bytearray) -> str:
    """Decode byte encoded string.

    Parameters
    ----------
    value : bytearray
        A byte encoded string.

    Returns
    -------
    str
        A decoded string value.

    """
    return value.decode("utf-8")


def decode_live_data(value: bytearray) -> LiveDataResponse:
    """Parse bytearray from bulk live data.

    Parameters
    ----------
    value : bytearray
        Byte value from bulk live data characteristic.

    Returns
    -------
    LiveDataResponse
        All 14 values from bul live data decoded and normalized.

    """
    data = struct.unpack("14I", value)
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
    """Clip a value between max and min.

    Validate if the value is between the defined limits and set
    it to the max/min value if it exceeds one of them.

    Parameters
    ----------
    a : int
        The value to clip
    a_min : int
        The lower limit for the value
    a_max : int
        The upper limit for the value

    Returns
    -------
    int
        The value if it is between the limits or min/max if it exceeds one of them.

    """
    a = min(a, a_max)
    return max(a, a_min)


def encode_int(value: int) -> bytes:
    """Encode integer as byte.

    Parameters
    ----------
    value : int
        An integer value.

    Returns
    -------
    bytes
        The byte encoded value as unsigned little-endian of 2 bytes length.

    """
    return value.to_bytes(2, byteorder="little", signed=False)


def encode_lang_code(language_code: str | LanguageCode) -> int:
    """Encode language code to its hashed integer representation.

    ironOS stores languages as hashed integer representations of the language code.
    This method uses the same hash algorithm used in ironOS.

    Parameters
    ----------
    language_code : str | LanguageCode
        The language code as a string or as member of `LanguageCode`

    Returns
    -------
    int
        The value of the `LanguageCode` member or
        the hashed integer value of language_code.

    """
    if isinstance(language_code, LanguageCode):
        return int(language_code.value)
    return int(hashlib.sha1(language_code.encode("utf-8")).hexdigest(), 16) % 0xFFFF


def decode_lang_code(raw: bytearray) -> LanguageCode | int | None:
    """Decode hashed value to language code.

    Parameters
    ----------
    raw : bytearray
        A byte encoded integer value.

    Returns
    -------
    LanguageCode | int | None
        The `LanguageCode` corresponding to the hashed interger value or the integer
        if could not be matched to a known language codes.

    """
    try:
        return LanguageCode(decode_int(raw))
    except ValueError:
        return decode_int(raw)


# Define uuid, decoding, encoding and input sanitizing methods for each characteristic
CHARACTERISTICS: dict[Characteristic, tuple] = {
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
    CharSetting.KEEP_AWAKE_PULSE_POWER: (
        const.CHAR_UUID_SETTINGS_KEEP_AWAKE_PULSE_POWER,
        lambda x: decode_int(x) / 10,
        lambda x: int(x * 10),
        lambda x: clip(x, 0, 99),
    ),
    CharSetting.KEEP_AWAKE_PULSE_DELAY: (
        const.CHAR_UUID_SETTINGS_KEEP_AWAKE_PULSE_DELAY,
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
        lambda x: decode_int(x) / 10,
        lambda x: int(x * 10),
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
        lambda x,: decode_int(x) / 10,
        lambda x: int(x * 10),
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
        lambda x: clip(x, 0, 6),
    ),
    CharSetting.CALIBRATE_CJC: (
        const.CHAR_UUID_SETTINGS_CALIBRATE_CJC,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.BLE_ENABLED: (
        const.CHAR_UUID_SETTINGS_BLE_ENABLED,
        decode_int,
        int,
        lambda x: 0,
    ),
    CharSetting.USB_PD_MODE: (
        const.CHAR_UUID_SETTINGS_USB_PD_MODE,
        decode_int,
        int,
        lambda x: clip(x, 0, 1),
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

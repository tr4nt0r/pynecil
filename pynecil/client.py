"""Pynecil - Python library to communicate with Pinecil V2 soldering irons via Bluetooth."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import struct
from typing import TYPE_CHECKING, Any, cast

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice
from bleak.exc import BleakError

from . import const
from .exceptions import CommunicationError
from .types import (
    AnimationSpeed,
    AutostartMode,
    BatteryType,
    Characteristic,
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

if TYPE_CHECKING:
    from collections.abc import Callable

_LOGGER = logging.getLogger(__package__)


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
        filterfunc=lambda _, advertisement: bool(
            str(const.SVC_UUID_BULK) in advertisement.service_uuids
        ),
        timeout=timeout,
    )


class Pynecil:
    """Client for Pinecil V2 Devices.

    Attributes
    ----------
    client_disconnected : bool
        Flag indicating whether the client has experienced an unexpected disconnect.
        Defaults to False.

    """

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
            which will be the client object. Defaults to None.

        Notes
        -----
        If `address_or_ble_device` is a BLEDevice object, `device_info` will be initialized
        with its `name` and `address`. Otherwise, `device_info` will only have an `address`
        initialized.

        Callbacks for disconnection events can be specified via `disconnected_callback`.
        If not provided, a default callback will set `client_disconnected` to True upon
        disconnection.

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
            self.device_info.is_synced = False

        self._client = BleakClient(
            address_or_ble_device,
            disconnected_callback=disconnected_callback or _disconnected_callback,
        )

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected.

        Returns
        -------
        bool
            `True` if the client is connected, `False` otherwise.

        """
        return self._client.is_connected

    async def connect(self) -> None:
        """Establish or re-establish a connection to the device.

        This method ensures a connection to the device is established, handling both initial
        connections and reconnections if an unexpected disconnection occurred. If the device
        is not connected and there was a previous unexpected disconnect, it closes the stale
        connection before attempting to reconnect.

        Notes
        -----
        - If `self._client.is_connected` is `True`, the method returns without performing
        any connection operations.
        - If `self.client_disconnected` is `True`, indicating a previous unexpected
        disconnection, the method first closes the stale connection by calling `disconnect()`
        before attempting to establish a new connection.

        Raises
        ------
        BleakError
            If an error occurs during the connection attempt.

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
        """Retrieve device information from the Pinecil V2 device.

        This method fetches details such as `name`, `address`, `build`, `device_sn`,
        and `device_id` of the connected Pinecil V2 device.

        Returns
        -------
        DeviceInfoResponse
            An object containing the retrieved device information.

        Raises
        ------
        CommunicationError
            If an error occurred while connecting and retrieving data from device.

        Notes
        -----
        If `self.device_info.is_synced` is `True`, it returns the cached `device_info`
        without performing a new data fetch.

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
        """Fetch live sensor data from the device.

        Returns
        -------
        LiveDataResponse
            An object containing 14 sensor values retrieved from the
            bulk live data characteristic.


        Raises
        ------
        CommunicationError
            If an error occurred while connecting and retrieving data from device.

        """
        return await self.read(CharBulk.LIVE_DATA)

    async def get_settings(
        self, settings: list[CharSetting | int] | None = None
    ) -> SettingsDataResponse:
        """Fetch settings data from the device.

        Parameters
        ----------
        settings : list[CharSetting  |  int] | None, optional
            List of settings identified by a `CharSetting` item or their ID that should
            be retrieved from the device. Retrieves all settings if ommited.

        Returns
        -------
        SettingsDataResponse
            A dictionary containing lowercase names and normalized values of the settings
            retrieved from the device.

        Raises
        ------
        CommunicationError
            If an error occurred while connecting and retrieving data from device.

        Notes
        -----
        This method asynchronously reads data from the device for each specified setting,
        filtering based on the provided `settings` list.

        """
        if settings is None:
            settings = []
        tasks = [
            (characteristic.name.lower(), self.read(characteristic))
            for characteristic in CHAR_MAP
            if isinstance(characteristic, CharSetting)
            and (
                not settings
                or characteristic in settings
                or characteristic.value in settings
            )
        ]
        results = await asyncio.gather(*(task[1] for task in tasks))

        return cast(
            SettingsDataResponse,
            {key: value for (key, _), value in zip(tasks, results)},
        )

    async def read(self, characteristic: Characteristic) -> Any:
        """Read specified characteristic and decode the result.

        Parameters
        ----------
        characteristic : Characteristic
            The characteristic to retrieve from the device.

        Returns
        -------
        Any
            The value read from the characteristic and parsed with the corresponding decoder.

        Raises
        ------
        CommunicationError
            If an error occurred while connecting and retrieving data from device.

        """
        uuid, decode, *_ = CHAR_MAP.get(characteristic, (None, None))

        if not (decode and uuid):
            return None

        try:
            await self.connect()
            result = await self._client.read_gatt_char(uuid)
            _LOGGER.debug(
                "Read characteristic %s, result: %s", str(uuid), decode(result)
            )
        except (BleakError, TimeoutError) as e:
            _LOGGER.debug("Failed to read characteristic %s: %s", str(uuid), e)
            raise CommunicationError from e
        return decode(result)

    async def write(self, setting: CharSetting, value: Any) -> None:
        """Write to the specified characteristic.

        Parameters
        ----------
        setting : CharSetting
            The characteristic to write to.
        value : Any
            The value to write to the characteristic.

        Raises
        ------
        ValueError
            If no conversion or validation functions are found for the specified `setting`.
        CommunicationError
            If an error occurs while connecting to or writing data to the device.

        """
        uuid, _, convert, validate = CHAR_MAP.get(setting, (None, None, None, None))

        if not (convert and validate):
            raise ValueError(
                f"No conversion or validation functions found for {setting}"
            )

        data = validate(convert(value))
        try:
            await self.connect()
            await self._client.write_gatt_char(uuid, encode_int(data))
            _LOGGER.debug("Wrote characteristic %s with value: %s", str(uuid), value)
        except (BleakError, TimeoutError) as e:
            _LOGGER.debug("Failed to write characteristic %s: %s", str(uuid), e)
            raise CommunicationError from e


def decode_int(value: bytearray) -> int:
    """Decode byte-encoded integer value to an integer.

    Parameters
    ----------
    value : bytearray
        Byte-encoded integer value to decode.

    Returns
    -------
    int
        Decoded integer value.

    Notes
    -----
    The byte order is little-endian, and the integer is treated as unsigned.

    """
    return int.from_bytes(value, byteorder="little", signed=False)


def decode_str(value: bytearray) -> str:
    """Decode byte-encoded string to a UTF-8 string.

    Parameters
    ----------
    value : bytearray
        Byte-encoded string to decode.

    Returns
    -------
    str
        Decoded UTF-8 string.

    Raises
    ------
    UnicodeDecodeError
        If the byte sequence cannot be decoded as UTF-8.

    """

    return value.decode("utf-8")


def decode_live_data(value: bytearray) -> LiveDataResponse:
    """Parse bytearray from bulk live data into LiveDataResponse.

    Parameters
    ----------
    value : bytearray
        Byte value from bulk live data characteristic.

    Returns
    -------
    LiveDataResponse
        Object containing 14 decoded values:
        - live_temp: int
        - setpoint_temp: int
        - dc_voltage: float (normalized)
        - handle_temp: float (normalized)
        - pwm_level: int
        - power_src: PowerSource
        - tip_resistance: float (normalized)
        - uptime: float (normalized)
        - movement_time: float (normalized)
        - max_tip_temp_ability: int
        - tip_voltage: int
        - hall_sensor: int
        - operating_mode: OperatingMode
        - estimated_power: float (normalized)

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
        data[7] / 10,
        data[8] / 10,
        data[9],
        data[10],
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
        The lower bound for the value.
    a_max : int
        The upper bound for the value.

    Returns
    -------
    int
        The clipped value:
        - If `a` is less than `a_min`, return `a_min`.
        - If `a` is greater than `a_max`, return `a_max`.
        - Otherwise, return `a` itself.

    """
    a = min(a, a_max)
    return max(a, a_min)


def encode_int(value: int) -> bytes:
    """Encode integer as byte.

    Parameters
    ----------
    value : int
        An integer value to encode.

    Returns
    -------
    bytes
        Byte representation of the integer value in unsigned little-endian format,
        occupying 2 bytes.

    """
    return value.to_bytes(2, byteorder="little", signed=False)


def encode_lang_code(language_code: str | LanguageCode) -> int:
    """Encode language code to its hashed integer representation.

    ironOS stores languages as hashed integer representations of the language code.
    This method uses the same hash algorithm used in ironOS.

    Parameters
    ----------
    language_code : str | LanguageCode
        The language code as a string or as a member of LanguageCode enum.

    Returns
    -------
    int
        The hashed integer value of language_code.

    Notes
    -----
    If language_code is a member of LanguageCode enum, its integer value is returned directly.
    Otherwise, language_code is hashed using SHA-1, and the resulting hash is converted to an integer
    and returned.

    """
    if isinstance(language_code, LanguageCode):
        return int(language_code.value)

    return int(hashlib.sha1(language_code.encode("utf-8")).hexdigest(), 16) % 0xFFFF


def decode_lang_code(raw: bytearray) -> LanguageCode | int | None:
    """Decode hashed value to language code.

    Parameters
    ----------
    raw : bytearray
        A byte-encoded integer value representing the hashed language code.

    Returns
    -------
    LanguageCode | int | None
        The LanguageCode enum member corresponding to the hashed integer value,
        or the integer value itself if it couldn't be matched to a known LanguageCode.
        Returns None if decoding fails.

    """
    try:
        return LanguageCode(decode_int(raw))
    except ValueError:
        return decode_int(raw)


# Map uuid, decoding, encoding and input sanitizing methods for each characteristic
CHAR_MAP: dict[Characteristic, tuple] = {
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
    CharLive.PWM_LEVEL: (
        const.CHAR_UUID_LIVE_PWM_LEVEL,
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
    CharLive.UPTIME: (
        const.CHAR_UUID_LIVE_UPTIME,
        lambda x: decode_int(x) / 10,
    ),
    CharLive.MOVEMENT_TIME: (
        const.CHAR_UUID_LIVE_MOVEMENT_TIME,
        lambda x: decode_int(x) / 10,
    ),
    CharLive.TIP_VOLTAGE: (
        const.CHAR_UUID_LIVE_TIP_VOLTAGE,
        decode_int,
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
        lambda x: BatteryType(decode_int(x)),
        lambda x: x.value if isinstance(x, BatteryType) else int(x),
        lambda x: clip(x, 0, 4),
    ),
    CharSetting.MIN_VOLTAGE_PER_CELL: (
        const.CHAR_UUID_SETTINGS_MIN_VOLTAGE_PER_CELL,
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
        lambda x: ScreenOrientationMode(decode_int(x)),
        lambda x: x.value if isinstance(x, ScreenOrientationMode) else int(x),
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
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
    CharSetting.ANIMATION_SPEED: (
        const.CHAR_UUID_SETTINGS_ANIMATION_SPEED,
        lambda x: AnimationSpeed(decode_int(x)),
        lambda x: x.value if isinstance(x, AnimationSpeed) else int(x),
        lambda x: clip(x, 0, 3),
    ),
    CharSetting.AUTOSTART_MODE: (
        const.CHAR_UUID_SETTINGS_AUTOSTART_MODE,
        lambda x: AutostartMode(decode_int(x)),
        lambda x: x.value if isinstance(x, AutostartMode) else int(x),
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
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
    CharSetting.IDLE_SCREEN_DETAILS: (
        const.CHAR_UUID_SETTINGS_IDLE_SCREEN_DETAILS,
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
    CharSetting.SOLDER_SCREEN_DETAILS: (
        const.CHAR_UUID_SETTINGS_SOLDER_SCREEN_DETAILS,
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
    CharSetting.TEMP_UNIT: (
        const.CHAR_UUID_SETTINGS_TEMP_UNIT,
        lambda x: TempUnit(decode_int(x)),
        lambda x: x.value if isinstance(x, TempUnit) else int(x),
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.DESC_SCROLL_SPEED: (
        const.CHAR_UUID_SETTINGS_DESC_SCROLL_SPEED,
        lambda x: ScrollSpeed(decode_int(x)),
        lambda x: x.value if isinstance(x, ScrollSpeed) else int(x),
        lambda x: clip(x, 0, 1),
    ),
    CharSetting.LOCKING_MODE: (
        const.CHAR_UUID_SETTINGS_LOCKING_MODE,
        lambda x: LockingMode(decode_int(x)),
        lambda x: x.value if isinstance(x, LockingMode) else int(x),
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
        lambda x: clip(x, 250, 450) if x != 0 else 0,
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
        lambda x: bool(decode_int(x)),
        bool,
        int,
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
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
    CharSetting.DISPLAY_BRIGHTNESS: (
        const.CHAR_UUID_SETTINGS_DISPLAY_BRIGHTNESS,
        lambda x: int((decode_int(x) + 24) / 25),  # convert to values 1-5
        lambda x: int(25 * x - 24),
        lambda x: clip(x, 1, 101),
    ),
    CharSetting.LOGO_DURATION: (
        const.CHAR_UUID_SETTINGS_LOGO_DURATION,
        lambda x: LogoDuration(decode_int(x)),
        lambda x: x.value if isinstance(x, LockingMode) else int(x),
        lambda x: clip(x, 0, 6),
    ),
    CharSetting.CALIBRATE_CJC: (
        const.CHAR_UUID_SETTINGS_CALIBRATE_CJC,
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
    CharSetting.BLE_ENABLED: (
        const.CHAR_UUID_SETTINGS_BLE_ENABLED,
        lambda _: True,
        bool,
        int,
    ),
    CharSetting.USB_PD_MODE: (
        const.CHAR_UUID_SETTINGS_USB_PD_MODE,
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
    CharSetting.SETTINGS_SAVE: (
        const.CHAR_UUID_SETTINGS_SAVE,
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
    CharSetting.SETTINGS_RESET: (
        const.CHAR_UUID_SETTINGS_RESET,
        lambda x: bool(decode_int(x)),
        bool,
        int,
    ),
}

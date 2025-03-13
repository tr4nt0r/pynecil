"""Unit tests for the Pynecil client module."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest
from bleak.exc import BleakError

from pynecil import (
    AnimationSpeed,
    AutostartMode,
    BatteryType,
    CharLive,
    CharSetting,
    CommunicationError,
    DeviceInfoResponse,
    LanguageCode,
    LockingMode,
    LogoDuration,
    OperatingMode,
    PowerSource,
    Pynecil,
    ScreenOrientationMode,
    ScrollSpeed,
    TempUnit,
    TipType,
    USBPDMode,
    discover,
)


@pytest.mark.usefixtures("mock_bleak_scanner")
async def test_discover_success():
    """Test discover function success."""

    result = await discover()
    assert result is not None
    assert result.name == "Pinecil-ABCDEF"
    assert result.address == "AA:BB:CC:DD:EE:FF"


async def test_discover_timeout(mock_bleak_scanner: AsyncMock):
    """Test discover function timeout."""

    mock_bleak_scanner.find_device_by_filter.return_value = None

    result = await discover(timeout=0.1)
    assert result is None


@pytest.mark.usefixtures("mock_bleak_scanner")
async def test_connect_success(mock_bleak_client: AsyncMock):
    """Test connection success."""
    mock_bleak_client.is_connected = False

    device = await discover()
    client = Pynecil(device)  # type: ignore
    await client.connect()
    mock_bleak_client.connect.assert_awaited_once()


async def test_connect_already_connected(mock_bleak_client: AsyncMock):
    """Test connection when already connected."""

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    assert client.is_connected
    await client.connect()
    mock_bleak_client.connect.assert_not_awaited()


async def test_connect_reconnect(mock_bleak_client: AsyncMock):
    """Test reconnect after disconnection."""

    mock_bleak_client.is_connected = False

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    client.client_disconnected = True
    await client.connect()
    mock_bleak_client.connect.assert_awaited_once()
    mock_bleak_client.disconnect.assert_awaited_once()


async def test_disconnect(mock_bleak_client: AsyncMock):
    """Test disconnection."""

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    client.client_disconnected = True
    await client.disconnect()
    mock_bleak_client.disconnect.assert_awaited_once()
    assert not client.client_disconnected


async def test_get_device_info_success(mock_bleak_client: AsyncMock):
    """Test get_device_info success."""

    mock_bleak_client.read_gatt_char.side_effect = [
        b"2.22",
        b"\xef\xcd\xab\x90\x78\x56\x34\x12",
        b"\x78\x56\x34\x12",
    ]

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    info = await client.get_device_info()
    assert info.build == "2.22"
    assert info.device_sn == "1234567890abcdef"
    assert info.device_id == "12345678"
    assert info.address == "AA:BB:CC:DD:EE:FF"
    assert info.is_synced is True


async def test_get_device_info_cached(mock_bleak_client: AsyncMock):
    """Test get_device_info when data is cached."""

    mock_bleak_client.is_connected = True

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    client.device_info = DeviceInfoResponse(
        build="2.22",
        device_sn="1234567890abcdef",
        device_id="12345678",
        address="AA:BB:CC:DD:EE:FF",
        is_synced=True,
    )
    info = await client.get_device_info()
    assert info.build == "2.22"
    assert info.device_sn == "1234567890abcdef"
    assert info.device_id == "12345678"
    assert info.address == "AA:BB:CC:DD:EE:FF"
    mock_bleak_client.read_gatt_char.assert_not_awaited()


async def test_get_device_info_bleak_error(mock_bleak_client: AsyncMock):
    """Test get_device_info with BleakError."""

    mock_bleak_client.read_gatt_char.side_effect = BleakError

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    with pytest.raises(CommunicationError):
        await client.get_device_info()


async def test_get_device_info_timeout_error(mock_bleak_client: AsyncMock):
    """Test get_device_info with TimeoutError."""

    mock_bleak_client.read_gatt_char.side_effect = TimeoutError

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    with pytest.raises(CommunicationError):
        await client.get_device_info()


async def test_get_live_data(mock_bleak_client: AsyncMock):
    """Test get_live_data function."""

    mock_bleak_client.read_gatt_char.return_value = bytearray(
        b"\xf1\x00\x00\x00\xf0\x00\x00\x00\xc9\x00\x00\x00+\x01\x00\x00\n\x00\x00\x00\x03\x00\x00\x00>\x00\x00\x00E\x02\x00\x00\xc2\x00\x00\x00\xb8\x01\x00\x00^\x16\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x19\x00\x00\x00"
    )
    client = Pynecil("AA:BB:CC:DD:EE:FF")
    data = await client.get_live_data()

    assert data.live_temp == 241
    assert data.setpoint_temp == 240
    assert data.dc_voltage == 20.1
    assert data.handle_temp == 29.9
    assert data.pwm_level == 3
    assert data.power_src == PowerSource.PD
    assert data.tip_resistance == 6.2
    assert data.uptime == 58.1
    assert data.movement_time == 19.4
    assert data.max_tip_temp_ability == 440
    assert data.tip_voltage == 5726
    assert data.hall_sensor == 0
    assert data.operating_mode == OperatingMode.SOLDERING
    assert data.estimated_power == 2.5
    mock_bleak_client.read_gatt_char.assert_awaited_once()


async def test_get_live_data_communication_error(mock_bleak_client: AsyncMock):
    """Test get_live_data with communication error."""

    mock_bleak_client.read_gatt_char.side_effect = BleakError

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    with pytest.raises(CommunicationError):
        await client.get_live_data()


async def test_get_settings_all(mock_bleak_client: AsyncMock):
    """Test get_settings function."""

    mock_bleak_client.read_gatt_char.side_effect = [
        b"@\x01",
        b"\x96\x00",
        b"\x05\x00",
        b"\x01\x00",
        b"!\x00",
        b"Z\x00",
        b"\x02\x00",
        b"\x07\x00",
        b"\x01\x00",
        b"\x02\x00",
        b"\x03\x00",
        b"\x0a\x00",
        b"\x01\x00",
        b"\x01\x00",
        b"\x01\x00",
        b"\x00\x00",
        b"\x01\x00",
        b"\x02\x00",
        b"\x05\x00",
        b"\x04\x00",
        b"\x01\x00",
        b"X\x02",
        b"\xa4\x01",
        b"\x84\x03",
        b"x\x00",
        b"\x01\x00",
        b"\x0a\x00",
        b"\x01\x00",
        b"\x07\x00",
        b"\x09\x00",
        b"\x09\x00",
        b"\xd7\xa1",
        b"\x14\x00",
        b"\x01\x00",
        b"e\x00",
        b"\x06\x00",
        b"\x01\x00",
        b"\x01\x00",
        b"\x02\x00",
        b"\x05\x00",
        b"\x01\x00",
        b"\x00\x00",
        b"\x00\x00",
    ]

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    settings = await client.get_settings()

    assert settings.get("setpoint_temp") == 320
    assert settings.get("sleep_temp") == 150
    assert settings.get("sleep_timeout") == 5
    assert settings.get("min_dc_voltage_cells") == BatteryType.BATTERY_3S
    assert settings.get("min_voltage_per_cell") == 3.3
    assert settings.get("qc_ideal_voltage") == 9.0
    assert settings.get("orientation_mode") == ScreenOrientationMode.AUTO
    assert settings.get("accel_sensitivity") == 7
    assert settings.get("animation_loop") is True
    assert settings.get("animation_speed") == AnimationSpeed.MEDIUM
    assert settings.get("autostart_mode") == AutostartMode.IDLE
    assert settings.get("shutdown_time") == 10
    assert settings.get("cooling_temp_blink") is True
    assert settings.get("idle_screen_details") is True
    assert settings.get("solder_screen_details") is True
    assert settings.get("temp_unit") == TempUnit.CELSIUS
    assert settings.get("desc_scroll_speed") == ScrollSpeed.FAST
    assert settings.get("locking_mode") == LockingMode.FULL_LOCKING
    assert settings.get("keep_awake_pulse_power") == 0.5
    assert settings.get("keep_awake_pulse_delay") == 4
    assert settings.get("keep_awake_pulse_duration") == 1
    assert settings.get("voltage_div") == 600
    assert settings.get("boost_temp") == 420
    assert settings.get("calibration_offset") == 900
    assert settings.get("power_limit") == 120
    assert settings.get("invert_buttons") is True
    assert settings.get("temp_increment_long") == 10
    assert settings.get("temp_increment_short") == 1
    assert settings.get("hall_sensitivity") == 7
    assert settings.get("accel_warn_counter") == 9
    assert settings.get("pd_warn_counter") == 9
    assert settings.get("ui_language") == LanguageCode.EN
    assert settings.get("pd_negotiation_timeout") == 2.0
    assert settings.get("display_invert") is True
    assert settings.get("display_brightness") == 5
    assert settings.get("logo_duration") == LogoDuration.LOOP
    assert settings.get("calibrate_cjc") is True
    assert settings.get("ble_enabled") is True
    assert settings.get("usb_pd_mode") == USBPDMode.SAFE
    assert settings.get("hall_sleep_time") == 25
    assert settings.get("tip_type") == TipType.TS100_LONG
    assert settings.get("settings_save") is False
    assert settings.get("settings_reset") is False

    assert mock_bleak_client.read_gatt_char.call_count == 43


@pytest.mark.parametrize(
    ("setting", "raw_value", "result"),
    [
        (CharSetting.SETPOINT_TEMP, b"@\x01", 320),
        (CharSetting.SLEEP_TEMP, b"\x96\x00", 150),
        (CharSetting.SLEEP_TIMEOUT, b"\x05\x00", 5),
        (CharSetting.TEMP_UNIT, b"\x01\x00", TempUnit.FAHRENHEIT),
        (CharSetting.MIN_DC_VOLTAGE_CELLS, b"\x01\x00", BatteryType.BATTERY_3S),
        (CharSetting.MIN_VOLTAGE_PER_CELL, b"!\x00", 3.3),
        (CharSetting.QC_IDEAL_VOLTAGE, b"Z\x00", 9.0),
        (CharSetting.ORIENTATION_MODE, b"\x02\x00", ScreenOrientationMode.AUTO),
        (CharSetting.ACCEL_SENSITIVITY, b"\x07\x00", 7),
        (CharSetting.ANIMATION_LOOP, b"\x01\x00", True),
        (CharSetting.ANIMATION_SPEED, b"\x02\x00", AnimationSpeed.MEDIUM),
        (CharSetting.AUTOSTART_MODE, b"\x03\x00", AutostartMode.IDLE),
        (CharSetting.SHUTDOWN_TIME, b"\x0a\x00", 10),
        (CharSetting.COOLING_TEMP_BLINK, b"\x01\x00", True),
        (CharSetting.IDLE_SCREEN_DETAILS, b"\x01\x00", True),
        (CharSetting.SOLDER_SCREEN_DETAILS, b"\x01\x00", True),
        (CharSetting.DESC_SCROLL_SPEED, b"\x01\x00", ScrollSpeed.FAST),
        (CharSetting.LOCKING_MODE, b"\x02\x00", LockingMode.FULL_LOCKING),
        (CharSetting.KEEP_AWAKE_PULSE_POWER, b"\x05\x00", 0.5),
        (CharSetting.KEEP_AWAKE_PULSE_DELAY, b"\x04\x00", 4),
        (CharSetting.KEEP_AWAKE_PULSE_DURATION, b"\x01\x00", 1),
        (CharSetting.VOLTAGE_DIV, b"X\x02", 600),
        (CharSetting.BOOST_TEMP, b"\xa4\x01", 420),
        (CharSetting.CALIBRATION_OFFSET, b"\x84\x03", 900),
        (CharSetting.POWER_LIMIT, b"x\x00", 120),
        (CharSetting.INVERT_BUTTONS, b"\x03\x00", True),
        (CharSetting.TEMP_INCREMENT_LONG, b"\x0a\x00", 10),
        (CharSetting.TEMP_INCREMENT_SHORT, b"\x01\x00", 1),
        (CharSetting.HALL_SENSITIVITY, b"\x07\x00", 7),
        (CharSetting.ACCEL_WARN_COUNTER, b"\x0a\x00", 10),
        (CharSetting.PD_WARN_COUNTER, b"\x0a\x00", 10),
        (CharSetting.UI_LANGUAGE, b"\xd7\xa1", LanguageCode.EN),
        (CharSetting.PD_NEGOTIATION_TIMEOUT, b"\x14\x00", 2.0),
        (CharSetting.DISPLAY_INVERT, b"\x01\x00", True),
        (CharSetting.DISPLAY_BRIGHTNESS, b"e\x00", 5),
        (CharSetting.LOGO_DURATION, b"\x06\x00", LogoDuration.LOOP),
        (CharSetting.CALIBRATE_CJC, b"\x01\x00", True),
        (CharSetting.BLE_ENABLED, b"\x01\x00", True),
        (CharSetting.USB_PD_MODE, b"\x02\x00", USBPDMode.SAFE),
        (CharSetting.HALL_SLEEP_TIME, b"\x05\x00", 25),
        (CharSetting.TIP_TYPE, b"\x01\x00", TipType.TS100_LONG),
    ],
)
async def test_get_settings_specific(
    mock_bleak_client: AsyncMock,
    setting: CharSetting,
    raw_value: bytes,
    result: Any,
):
    """Test get_settings for specific settings."""

    mock_bleak_client.read_gatt_char.return_value = raw_value

    client = Pynecil("AA:BB:CC:DD:EE:FF")

    settings = await client.get_settings([setting])

    assert settings.get(setting.name.lower()) == result

    assert len(settings) == 1
    mock_bleak_client.read_gatt_char.assert_awaited()
    assert mock_bleak_client.read_gatt_char.call_count == 1


async def test_get_settings_communication_error(mock_bleak_client: AsyncMock):
    """Test get_settings with communication error."""

    mock_bleak_client.read_gatt_char.side_effect = BleakError

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    with pytest.raises(CommunicationError):
        await client.get_settings()


@pytest.mark.parametrize(
    ("setting", "characteristic", "raw_value", "value"),
    [
        (
            CharSetting.SETPOINT_TEMP,
            UUID("f6d70000-5a10-4eba-aa55-33e27f9bc533"),
            b"@\x01",
            320,
        ),
        (
            CharSetting.SLEEP_TEMP,
            UUID("f6d70001-5a10-4eba-aa55-33e27f9bc533"),
            b"\x96\x00",
            150,
        ),
        (
            CharSetting.SLEEP_TIMEOUT,
            UUID("f6d70002-5a10-4eba-aa55-33e27f9bc533"),
            b"\x05\x00",
            5,
        ),
        (
            CharSetting.MIN_DC_VOLTAGE_CELLS,
            UUID("f6d70003-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            BatteryType.BATTERY_3S,
        ),
        (
            CharSetting.MIN_VOLTAGE_PER_CELL,
            UUID("f6d70004-5a10-4eba-aa55-33e27f9bc533"),
            b"!\x00",
            3.3,
        ),
        (
            CharSetting.QC_IDEAL_VOLTAGE,
            UUID("f6d70005-5a10-4eba-aa55-33e27f9bc533"),
            b"Z\x00",
            9.0,
        ),
        (
            CharSetting.ORIENTATION_MODE,
            UUID("f6d70006-5a10-4eba-aa55-33e27f9bc533"),
            b"\x02\x00",
            ScreenOrientationMode.AUTO,
        ),
        (
            CharSetting.ACCEL_SENSITIVITY,
            UUID("f6d70007-5a10-4eba-aa55-33e27f9bc533"),
            b"\x07\x00",
            7,
        ),
        (
            CharSetting.ANIMATION_LOOP,
            UUID("f6d70008-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.ANIMATION_SPEED,
            UUID("f6d70009-5a10-4eba-aa55-33e27f9bc533"),
            b"\x02\x00",
            AnimationSpeed.MEDIUM,
        ),
        (
            CharSetting.AUTOSTART_MODE,
            UUID("f6d7000a-5a10-4eba-aa55-33e27f9bc533"),
            b"\x03\x00",
            AutostartMode.IDLE,
        ),
        (
            CharSetting.SHUTDOWN_TIME,
            UUID("f6d7000b-5a10-4eba-aa55-33e27f9bc533"),
            b"\x0a\x00",
            10,
        ),
        (
            CharSetting.COOLING_TEMP_BLINK,
            UUID("f6d7000c-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.IDLE_SCREEN_DETAILS,
            UUID("f6d7000d-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.SOLDER_SCREEN_DETAILS,
            UUID("f6d7000e-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.TEMP_UNIT,
            UUID("f6d7000f-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            TempUnit.FAHRENHEIT,
        ),
        (
            CharSetting.DESC_SCROLL_SPEED,
            UUID("f6d70010-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            ScrollSpeed.FAST,
        ),
        (
            CharSetting.LOCKING_MODE,
            UUID("f6d70011-5a10-4eba-aa55-33e27f9bc533"),
            b"\x02\x00",
            LockingMode.FULL_LOCKING,
        ),
        (
            CharSetting.KEEP_AWAKE_PULSE_POWER,
            UUID("f6d70012-5a10-4eba-aa55-33e27f9bc533"),
            b"\x05\x00",
            0.5,
        ),
        (
            CharSetting.KEEP_AWAKE_PULSE_DELAY,
            UUID("f6d70013-5a10-4eba-aa55-33e27f9bc533"),
            b"\x04\x00",
            4,
        ),
        (
            CharSetting.KEEP_AWAKE_PULSE_DURATION,
            UUID("f6d70014-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            1,
        ),
        (
            CharSetting.VOLTAGE_DIV,
            UUID("f6d70015-5a10-4eba-aa55-33e27f9bc533"),
            b"X\x02",
            600,
        ),
        (
            CharSetting.BOOST_TEMP,
            UUID("f6d70016-5a10-4eba-aa55-33e27f9bc533"),
            b"\xa4\x01",
            420,
        ),
        (
            CharSetting.CALIBRATION_OFFSET,
            UUID("f6d70017-5a10-4eba-aa55-33e27f9bc533"),
            b"\x84\x03",
            900,
        ),
        (
            CharSetting.POWER_LIMIT,
            UUID("f6d70018-5a10-4eba-aa55-33e27f9bc533"),
            b"x\x00",
            120,
        ),
        (
            CharSetting.INVERT_BUTTONS,
            UUID("f6d70019-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.TEMP_INCREMENT_LONG,
            UUID("f6d7001a-5a10-4eba-aa55-33e27f9bc533"),
            b"\x0a\x00",
            10,
        ),
        (
            CharSetting.TEMP_INCREMENT_SHORT,
            UUID("f6d7001b-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            1,
        ),
        (
            CharSetting.HALL_SENSITIVITY,
            UUID("f6d7001c-5a10-4eba-aa55-33e27f9bc533"),
            b"\x07\x00",
            7,
        ),
        (
            CharSetting.ACCEL_WARN_COUNTER,
            UUID("f6d7001d-5a10-4eba-aa55-33e27f9bc533"),
            b"\x09\x00",
            9,
        ),
        (
            CharSetting.PD_WARN_COUNTER,
            UUID("f6d7001e-5a10-4eba-aa55-33e27f9bc533"),
            b"\x09\x00",
            9,
        ),
        (
            CharSetting.UI_LANGUAGE,
            UUID("f6d7001f-5a10-4eba-aa55-33e27f9bc533"),
            b"\xd7\xa1",
            LanguageCode.EN,
        ),
        (
            CharSetting.PD_NEGOTIATION_TIMEOUT,
            UUID("f6d70020-5a10-4eba-aa55-33e27f9bc533"),
            b"\x14\x00",
            2.0,
        ),
        (
            CharSetting.DISPLAY_INVERT,
            UUID("f6d70021-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.DISPLAY_BRIGHTNESS,
            UUID("f6d70022-5a10-4eba-aa55-33e27f9bc533"),
            b"e\x00",
            5,
        ),
        (
            CharSetting.LOGO_DURATION,
            UUID("f6d70023-5a10-4eba-aa55-33e27f9bc533"),
            b"\x06\x00",
            LogoDuration.LOOP,
        ),
        (
            CharSetting.CALIBRATE_CJC,
            UUID("f6d70024-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.BLE_ENABLED,
            UUID("f6d70025-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.USB_PD_MODE,
            UUID("f6d70026-5a10-4eba-aa55-33e27f9bc533"),
            b"\x02\x00",
            USBPDMode.SAFE,
        ),
        (
            CharSetting.HALL_SLEEP_TIME,
            UUID("f6d70035-5a10-4eba-aa55-33e27f9bc533"),
            b"\x05\x00",
            25,
        ),
        (
            CharSetting.TIP_TYPE,
            UUID("f6d70036-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            TipType.TS100_LONG,
        ),
        (
            CharLive.LIVE_TEMP,
            UUID("d85ef001-168e-4a71-aa55-33e27f9bc533"),
            b"\xf1\x00",
            241,
        ),
        (
            CharLive.SETPOINT_TEMP,
            UUID("d85ef002-168e-4a71-aa55-33e27f9bc533"),
            b"\xf0\x00",
            240,
        ),
        (
            CharLive.DC_VOLTAGE,
            UUID("d85ef003-168e-4a71-aa55-33e27f9bc533"),
            b"\xc9\x00",
            20.1,
        ),
        (
            CharLive.HANDLE_TEMP,
            UUID("d85ef004-168e-4a71-aa55-33e27f9bc533"),
            b"+\x01",
            29.9,
        ),
        (
            CharLive.PWM_LEVEL,
            UUID("d85ef005-168e-4a71-aa55-33e27f9bc533"),
            b"\x08\x00",
            3,
        ),
        (
            CharLive.POWER_SRC,
            UUID("d85ef006-168e-4a71-aa55-33e27f9bc533"),
            b"\x03\x00",
            PowerSource.PD,
        ),
        (
            CharLive.TIP_RESISTANCE,
            UUID("d85ef007-168e-4a71-aa55-33e27f9bc533"),
            b">\x00",
            6.2,
        ),
        (
            CharLive.UPTIME,
            UUID("d85ef008-168e-4a71-aa55-33e27f9bc533"),
            b"E\x02",
            58.1,
        ),
        (
            CharLive.MOVEMENT_TIME,
            UUID("d85ef009-168e-4a71-aa55-33e27f9bc533"),
            b"\xc2\x00",
            19.4,
        ),
        (
            CharLive.MAX_TIP_TEMP_ABILITY,
            UUID("d85ef00a-168e-4a71-aa55-33e27f9bc533"),
            b"\xb8\x01",
            440,
        ),
        (
            CharLive.TIP_VOLTAGE,
            UUID("d85ef00b-168e-4a71-aa55-33e27f9bc533"),
            b"^\x16",
            5726,
        ),
        (
            CharLive.HALL_SENSOR,
            UUID("d85ef00c-168e-4a71-aa55-33e27f9bc533"),
            b"\x00\x00",
            0,
        ),
        (
            CharLive.OPERATING_MODE,
            UUID("d85ef00d-168e-4a71-aa55-33e27f9bc533"),
            b"\x01\x00",
            OperatingMode.SOLDERING,
        ),
        (
            CharLive.ESTIMATED_POWER,
            UUID("d85ef00e-168e-4a71-aa55-33e27f9bc533"),
            b"\x19\x00",
            2.5,
        ),
    ],
)
async def test_read_success(
    mock_bleak_client: AsyncMock,
    setting: CharSetting | CharLive,
    characteristic: UUID,
    raw_value: bytes,
    value: Any,
):
    """Test read function success."""

    mock_bleak_client.read_gatt_char.return_value = raw_value

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    result = await client.read(setting)
    assert result == value
    mock_bleak_client.read_gatt_char.assert_awaited_once_with(characteristic)


async def test_read_invalid_characteristic(mock_bleak_client: AsyncMock):
    """Test read function with invalid characteristic."""

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    result = await client.read(MagicMock())  # type: ignore
    assert result is None
    mock_bleak_client.read_gatt_char.assert_not_awaited()


async def test_read_communication_error(mock_bleak_client: AsyncMock):
    """Test read function with communication error."""

    mock_bleak_client.read_gatt_char.side_effect = BleakError
    client = Pynecil("AA:BB:CC:DD:EE:FF")
    with pytest.raises(CommunicationError):
        await client.get_settings()


@pytest.mark.parametrize(
    ("setting", "characteristic", "raw_value", "value"),
    [
        (
            CharSetting.SETPOINT_TEMP,
            UUID("f6d70000-5a10-4eba-aa55-33e27f9bc533"),
            b"@\x01",
            320,
        ),
        (
            CharSetting.SLEEP_TEMP,
            UUID("f6d70001-5a10-4eba-aa55-33e27f9bc533"),
            b"\x96\x00",
            150,
        ),
        (
            CharSetting.SLEEP_TIMEOUT,
            UUID("f6d70002-5a10-4eba-aa55-33e27f9bc533"),
            b"\x05\x00",
            5,
        ),
        (
            CharSetting.MIN_DC_VOLTAGE_CELLS,
            UUID("f6d70003-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            BatteryType.BATTERY_3S,
        ),
        (
            CharSetting.MIN_VOLTAGE_PER_CELL,
            UUID("f6d70004-5a10-4eba-aa55-33e27f9bc533"),
            b"!\x00",
            3.3,
        ),
        (
            CharSetting.QC_IDEAL_VOLTAGE,
            UUID("f6d70005-5a10-4eba-aa55-33e27f9bc533"),
            b"Z\x00",
            9.0,
        ),
        (
            CharSetting.ORIENTATION_MODE,
            UUID("f6d70006-5a10-4eba-aa55-33e27f9bc533"),
            b"\x02\x00",
            ScreenOrientationMode.AUTO,
        ),
        (
            CharSetting.ACCEL_SENSITIVITY,
            UUID("f6d70007-5a10-4eba-aa55-33e27f9bc533"),
            b"\x07\x00",
            7,
        ),
        (
            CharSetting.ANIMATION_LOOP,
            UUID("f6d70008-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.ANIMATION_SPEED,
            UUID("f6d70009-5a10-4eba-aa55-33e27f9bc533"),
            b"\x02\x00",
            AnimationSpeed.MEDIUM,
        ),
        (
            CharSetting.AUTOSTART_MODE,
            UUID("f6d7000a-5a10-4eba-aa55-33e27f9bc533"),
            b"\x03\x00",
            AutostartMode.IDLE,
        ),
        (
            CharSetting.SHUTDOWN_TIME,
            UUID("f6d7000b-5a10-4eba-aa55-33e27f9bc533"),
            b"\x0a\x00",
            10,
        ),
        (
            CharSetting.COOLING_TEMP_BLINK,
            UUID("f6d7000c-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.IDLE_SCREEN_DETAILS,
            UUID("f6d7000d-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.SOLDER_SCREEN_DETAILS,
            UUID("f6d7000e-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.TEMP_UNIT,
            UUID("f6d7000f-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            TempUnit.FAHRENHEIT,
        ),
        (
            CharSetting.DESC_SCROLL_SPEED,
            UUID("f6d70010-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            ScrollSpeed.FAST,
        ),
        (
            CharSetting.LOCKING_MODE,
            UUID("f6d70011-5a10-4eba-aa55-33e27f9bc533"),
            b"\x02\x00",
            LockingMode.FULL_LOCKING,
        ),
        (
            CharSetting.KEEP_AWAKE_PULSE_POWER,
            UUID("f6d70012-5a10-4eba-aa55-33e27f9bc533"),
            b"\x05\x00",
            0.5,
        ),
        (
            CharSetting.KEEP_AWAKE_PULSE_DELAY,
            UUID("f6d70013-5a10-4eba-aa55-33e27f9bc533"),
            b"\x04\x00",
            4,
        ),
        (
            CharSetting.KEEP_AWAKE_PULSE_DURATION,
            UUID("f6d70014-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            1,
        ),
        (
            CharSetting.VOLTAGE_DIV,
            UUID("f6d70015-5a10-4eba-aa55-33e27f9bc533"),
            b"X\x02",
            600,
        ),
        (
            CharSetting.BOOST_TEMP,
            UUID("f6d70016-5a10-4eba-aa55-33e27f9bc533"),
            b"\xa4\x01",
            420,
        ),
        (
            CharSetting.CALIBRATION_OFFSET,
            UUID("f6d70017-5a10-4eba-aa55-33e27f9bc533"),
            b"\x84\x03",
            900,
        ),
        (
            CharSetting.POWER_LIMIT,
            UUID("f6d70018-5a10-4eba-aa55-33e27f9bc533"),
            b"x\x00",
            120,
        ),
        (
            CharSetting.INVERT_BUTTONS,
            UUID("f6d70019-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.TEMP_INCREMENT_LONG,
            UUID("f6d7001a-5a10-4eba-aa55-33e27f9bc533"),
            b"\x0a\x00",
            10,
        ),
        (
            CharSetting.TEMP_INCREMENT_SHORT,
            UUID("f6d7001b-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            1,
        ),
        (
            CharSetting.HALL_SENSITIVITY,
            UUID("f6d7001c-5a10-4eba-aa55-33e27f9bc533"),
            b"\x07\x00",
            7,
        ),
        (
            CharSetting.ACCEL_WARN_COUNTER,
            UUID("f6d7001d-5a10-4eba-aa55-33e27f9bc533"),
            b"\x09\x00",
            9,
        ),
        (
            CharSetting.PD_WARN_COUNTER,
            UUID("f6d7001e-5a10-4eba-aa55-33e27f9bc533"),
            b"\x09\x00",
            9,
        ),
        (
            CharSetting.UI_LANGUAGE,
            UUID("f6d7001f-5a10-4eba-aa55-33e27f9bc533"),
            b"\xd7\xa1",
            LanguageCode.EN,
        ),
        (
            CharSetting.UI_LANGUAGE,
            UUID("f6d7001f-5a10-4eba-aa55-33e27f9bc533"),
            b"\xd7\xa1",
            "EN",
        ),
        (
            CharSetting.PD_NEGOTIATION_TIMEOUT,
            UUID("f6d70020-5a10-4eba-aa55-33e27f9bc533"),
            b"\x14\x00",
            2.0,
        ),
        (
            CharSetting.DISPLAY_INVERT,
            UUID("f6d70021-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.DISPLAY_BRIGHTNESS,
            UUID("f6d70022-5a10-4eba-aa55-33e27f9bc533"),
            b"e\x00",
            5,
        ),
        (
            CharSetting.LOGO_DURATION,
            UUID("f6d70023-5a10-4eba-aa55-33e27f9bc533"),
            b"\x06\x00",
            LogoDuration.LOOP,
        ),
        (
            CharSetting.CALIBRATE_CJC,
            UUID("f6d70024-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.BLE_ENABLED,
            UUID("f6d70025-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            True,
        ),
        (
            CharSetting.USB_PD_MODE,
            UUID("f6d70026-5a10-4eba-aa55-33e27f9bc533"),
            b"\x02\x00",
            USBPDMode.SAFE,
        ),
        (
            CharSetting.HALL_SLEEP_TIME,
            UUID("f6d70035-5a10-4eba-aa55-33e27f9bc533"),
            b"\x05\x00",
            25,
        ),
        (
            CharSetting.TIP_TYPE,
            UUID("f6d70036-5a10-4eba-aa55-33e27f9bc533"),
            b"\x01\x00",
            TipType.TS100_LONG,
        ),
    ],
)
async def test_write_success(
    mock_bleak_client: AsyncMock,
    setting: CharSetting,
    characteristic: UUID,
    value: Any,
    raw_value: bytes,
):
    """Test write function."""

    client = Pynecil("AA:BB:CC:DD:EE:FF")

    await client.write(setting, value)

    mock_bleak_client.write_gatt_char.assert_called_once_with(characteristic, raw_value)


async def test_write_clip_values(mock_bleak_client: AsyncMock):
    """Test write function with invalid value."""

    client = Pynecil("AA:BB:CC:DD:EE:FF")

    await client.write(CharSetting.SETPOINT_TEMP, 900)

    mock_bleak_client.write_gatt_char.assert_called_once_with(
        UUID("f6d70000-5a10-4eba-aa55-33e27f9bc533"), b"R\x03"
    )
    mock_bleak_client.reset_mock()
    await client.write(CharSetting.SETPOINT_TEMP, 0)

    mock_bleak_client.write_gatt_char.assert_called_once_with(
        UUID("f6d70000-5a10-4eba-aa55-33e27f9bc533"), b"\n\x00"
    )


async def test_write_communication_error(mock_bleak_client: AsyncMock):
    """Test write function with communication error."""

    mock_bleak_client.write_gatt_char.side_effect = BleakError

    client = Pynecil("AA:BB:CC:DD:EE:FF")

    with pytest.raises(CommunicationError):
        await client.write(CharSetting.SETPOINT_TEMP, 300)

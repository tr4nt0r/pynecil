"""Unit tests for the Pynecil client module."""

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

    mock_bleak_client.read_gatt_char.return_value = b"d\x00\x00\x00\xc8\x00\x00\x00d\x00\x00\x00\xc8\x00\x00\x00\x80\x00\x00\x00\x03\x00\x00\x00\x1e\x00\x00\x00(\x00\x00\x002\x00\x00\x00,\x01\x00\x00<\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00F\x00\x00\x00"

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    data = await client.get_live_data()

    assert data.live_temp == 100
    assert data.setpoint_temp == 200
    assert data.dc_voltage == 10.0
    assert data.handle_temp == 20.0
    assert data.pwm_level == 50
    assert data.power_src == PowerSource.PD
    assert data.tip_resistance == 3.0
    assert data.uptime == 4.0
    assert data.movement_time == 5.0
    assert data.max_tip_temp_ability == 300
    assert data.tip_voltage == 60
    assert data.hall_sensor == 1
    assert data.operating_mode == OperatingMode.SOLDERING
    assert data.estimated_power == 7.0
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
        b"\x0a\x00",
        b"\x0a\x00",
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
    assert settings.get("accel_warn_counter") == 10
    assert settings.get("pd_warn_counter") == 10
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


async def test_get_settings_specific(mock_bleak_client: AsyncMock):
    """Test get_settings for specific settings."""

    mock_bleak_client.read_gatt_char.side_effect = [
        b"@\x01",
        b"\x96\x00",
        b"\x05\x00",
        b"\x01\x00",
    ]

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    settings = await client.get_settings(
        [
            CharSetting.SETPOINT_TEMP,
            CharSetting.SLEEP_TEMP,
            CharSetting.SLEEP_TIMEOUT,
            15,
        ]
    )
    assert settings.get("setpoint_temp") == 320
    assert settings.get("sleep_temp") == 150
    assert settings.get("sleep_timeout") == 5
    assert settings.get("temp_unit") == TempUnit.FAHRENHEIT
    assert len(settings) == 4
    mock_bleak_client.read_gatt_char.assert_awaited()
    assert mock_bleak_client.read_gatt_char.call_count == 4


async def test_get_settings_communication_error(mock_bleak_client: AsyncMock):
    """Test get_settings with communication error."""

    mock_bleak_client.read_gatt_char.side_effect = BleakError

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    with pytest.raises(CommunicationError):
        await client.get_settings()


async def test_read_success(mock_bleak_client: AsyncMock):
    """Test read function success."""

    mock_bleak_client.read_gatt_char.return_value = b"@\x01"

    client = Pynecil("AA:BB:CC:DD:EE:FF")
    result = await client.read(CharLive.LIVE_TEMP)
    assert result == 320
    mock_bleak_client.read_gatt_char.assert_awaited_once()


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


async def test_write_success(mock_bleak_client: AsyncMock):
    """Test write function."""

    client = Pynecil("AA:BB:CC:DD:EE:FF")

    await client.write(CharSetting.SETPOINT_TEMP, 300)

    mock_bleak_client.write_gatt_char.assert_called_once_with(
        UUID("f6d70000-5a10-4eba-aa55-33e27f9bc533"), b",\x01"
    )


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

"""Types for Pynecil."""

from dataclasses import dataclass
from enum import Enum


class CharLive(Enum):
    """Characteristics from live service."""

    LIVE_TEMP = 0
    SETPOINT_TEMP = 1
    DC_VOLTAGE = 2
    HANDLE_TEMP = 3
    PWMLEVEL = 4
    POWER_SRC = 5
    TIP_RESISTANCE = 6
    UPTIME = 7
    MOVEMENT_TIME = 8
    MAX_TIP_TEMP_ABILITY = 9
    TIP_VOLTAGE = 10
    HALL_SENSOR = 11
    OPERATING_MODE = 12
    ESTIMATED_POWER = 13


class CharSetting(Enum):
    """Characteristics from settings service."""

    SETPOINT_TEMP = 0
    SLEEP_TEMP = 1
    SLEEP_TIMEOUT = 2
    MIN_DC_VOLTAGE_CELLS = 3
    MIN_VOLLTAGE_PER_CELL = 4
    QC_IDEAL_VOLTAGE = 5
    ORIENTATION_MODE = 6
    ACCEL_SENSITIVITY = 7
    ANIMATION_LOOP = 8
    ANIMATION_SPEED = 9
    AUTOSTART_MODE = 10
    SHUTDOWN_TIME = 11
    COOLING_TEMP_BLINK = 12
    IDLE_SCREEN_DETAILS = 13
    SOLDER_SCREEN_DETAILS = 14
    TEMP_UNIT = 15
    DESC_SCROLL_SPEED = 16
    LOCKING_MODE = 17
    KEEP_AWAKE_PULSE = 18
    KEEP_AWAKE_PULSE_WAIT = 19
    KEEP_AWAKE_PULSE_DURATION = 20
    VOLTAGE_DIV = 21
    BOOST_TEMP = 22
    CALIBRATION_OFFSET = 23
    POWER_LIMIT = 24
    INVERT_BUTTONS = 25
    TEMP_INCREMENT_LONG = 26
    TEMP_INCREMENT_SHORT = 27
    HALL_SENSITIVITY = 28
    ACCEL_WARN_COUNTER = 29
    PD_WARN_COUNTER = 30
    UI_LANGUAGE = 31
    PD_NEGOTIATION_TIMEOUT = 32
    DISPLAY_INVERT = 33
    DISPLAY_BRIGHTNESS = 34
    LOGO_DURATION = 35
    CALIBRATE_CJC = 36
    BLE_ENABLED = 37
    USB_PD_MODE = 38
    SETTINGS_RESET = 98
    SETTINGS_SAVE = 99


class CharBulk(Enum):
    """Characteristics from bulk service.

    Parameters
    ----------
    Enum : int
        Names and IDs of the characteristics in the bulk service.

    """

    LIVE_DATA = 0
    ACCEL_NAME = 1
    BUILD = 2
    DEVICE_SN = 3
    DEVICE_ID = 4


class PowerSource(Enum):
    """Power source types."""

    DC = 0
    QC = 1
    PD_VBUS = 2
    PD = 3


class OperatingMode(Enum):
    """Operating modes."""

    IDLE = 0
    SOLDERING = 1
    BOOST = 2
    SLEEPING = 3
    SETTINGS = 4
    DEBUG = 5


class LanguageCode(Enum):
    """Language Codes."""

    BE = 60301
    BG = 15395
    CS = 36791
    DA = 63942
    DE = 5496
    EL = 5003
    EN = 41431
    ES = 38713
    ET = 18074
    FI = 25411
    FR = 38783
    HR = 49773
    HU = 19902
    IT = 57867
    JA_JP = 2385
    LT = 5183
    NB = 31043
    NL = 22266
    NL_BE = 55046
    PL = 55968
    PT = 56922
    RO = 61480
    RU = 26979
    SK = 13916
    SL = 21931
    SR_CYRL = 41427
    SR_LATN = 61017
    SV = 65456
    TR = 9120
    UK = 29374
    VI = 20758
    YUE_HK = 17119
    ZH_CN = 44731
    ZH_TW = 34289


@dataclass
class DeviceInfoResponse:
    """Response data with information about the Pinecil device."""

    build: str | None = None
    device_id: str | None = None
    address: str | None = None
    device_sn: str | None = None
    name: str | None = None
    is_synced: bool = False


@dataclass
class LiveDataResponse:
    """Live data response class."""

    live_temp: int | None = None
    set_temp: int | None = None
    dc_input: float | None = None
    handle_temp: float | None = None
    power_level: int | None = None
    power_src: PowerSource | None = None
    tip_res: float | None = None
    uptime: int | None = None
    movement: int | None = None
    max_temp: int | None = None
    raw_tip: float | None = None
    hall_sensor: int | None = None
    op_mode: OperatingMode | None = None
    est_power: float | None = None


@dataclass
class SettingsDataResponse:
    """Settings data response class."""

    setpoint_temp: int | None = None
    sleep_temp: int | None = None
    sleep_timeout: int | None = None
    min_dc_voltage_cells: int | None = None
    min_volltage_per_cell: int | None = None
    qc_ideal_voltage: int | None = None
    orientation_mode: int | None = None
    accel_sensitivity: int | None = None
    animation_loop: int | None = None
    animation_speed: int | None = None
    autostart_mode: int | None = None
    shutdown_time: int | None = None
    cooling_temp_blink: int | None = None
    idle_screen_details: int | None = None
    solder_screen_details: int | None = None
    temp_unit: int | None = None
    desc_scroll_speed: int | None = None
    locking_mode: int | None = None
    keep_awake_pulse: int | None = None
    keep_awake_pulse_wait: int | None = None
    keep_awake_pulse_duration: int | None = None
    voltage_div: int | None = None
    boost_temp: int | None = None
    calibration_offset: int | None = None
    power_limit: int | None = None
    invert_buttons: int | None = None
    temp_increment_long: int | None = None
    temp_increment_short: int | None = None
    hall_sensitivity: int | None = None
    accel_warn_counter: int | None = None
    pd_warn_counter: int | None = None
    ui_language: LanguageCode | None = None
    pd_negotiation_timeout: int | None = None
    display_invert: int | None = None
    display_brightness: int | None = None
    logo_duration: int | None = None
    calibrate_cjc: int | None = None
    ble_enabled: int | None = None
    usb_pd_mode: int | None = None
    settings_save: int | None = None
    settings_reset: int | None = None

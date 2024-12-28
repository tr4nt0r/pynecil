"""Types for Pynecil."""

from dataclasses import dataclass
from enum import Enum
from typing import TypedDict


class Characteristic(Enum):
    """Base class for Characteristics."""


class CharLive(Characteristic, Enum):
    """Characteristics from live service."""

    LIVE_TEMP = 0
    SETPOINT_TEMP = 1
    DC_VOLTAGE = 2
    HANDLE_TEMP = 3
    PWM_LEVEL = 4
    POWER_SRC = 5
    TIP_RESISTANCE = 6
    UPTIME = 7
    MOVEMENT_TIME = 8
    MAX_TIP_TEMP_ABILITY = 9
    TIP_VOLTAGE = 10
    HALL_SENSOR = 11
    OPERATING_MODE = 12
    ESTIMATED_POWER = 13


class CharSetting(Characteristic, Enum):
    """Characteristics from settings service."""

    SETPOINT_TEMP = 0
    SLEEP_TEMP = 1
    SLEEP_TIMEOUT = 2
    MIN_DC_VOLTAGE_CELLS = 3
    MIN_VOLTAGE_PER_CELL = 4
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
    KEEP_AWAKE_PULSE_POWER = 18
    KEEP_AWAKE_PULSE_DELAY = 19
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


class CharBulk(Characteristic, Enum):
    """Characteristics from bulk service."""

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


class BatteryType(Enum):
    """Battery type (cell count)."""

    NO_BATTERY = 0  # DC power supply
    BATTERY_3S = 1
    BATTERY_4S = 2
    BATTERY_5S = 3
    BATTERY_6S = 4


class ScreenOrientationMode(Enum):
    """Screen orientation mode."""

    RIGHT_HANDED = 0
    LEFT_HANDED = 1
    AUTO = 2


class AnimationSpeed(Enum):
    """Animation speed."""

    OFF = 0
    SLOW = 1
    MEDIUM = 2
    FAST = 3


class AutostartMode(Enum):
    """Autostart mode."""

    DISABLED = 0
    SOLDERING = 1
    SLEEPING = 2
    IDLE = 3


class TempUnit(Enum):
    """Temperature unit."""

    CELSIUS = 0
    FAHRENHEIT = 1


class ScrollSpeed(Enum):
    """Description scroll speed."""

    SLOW = 0
    FAST = 1


class LockingMode(Enum):
    """Locking mode."""

    OFF = 0
    BOOST_ONLY = 1
    FULL_LOCKING = 2


class LogoDuration(Enum):
    """Logo duration."""

    OFF = 0
    SECONDS_1 = 1
    SECONDS_2 = 2
    SECONDS_3 = 3
    SECONDS_4 = 4
    SECONDS_5 = 5
    LOOP = 6


@dataclass
class DeviceInfoResponse:
    """Response data with information about the Pinecil device.

    Attributes
    ----------
    build: str | None
        ironOS build version of the device (e.g. 2.22)
    device_id:  str | None
        Identifier of the device
    address: str | None
        Bluetooth address of the device
    device_sn: str | None
        Serial number of the device
    name: str | None
        Name of the device

    """

    build: str | None = None
    device_id: str | None = None
    address: str | None = None
    device_sn: str | None = None
    name: str | None = None
    is_synced: bool = False


@dataclass
class LiveDataResponse:
    """Live data response class.

    Attributes
    ----------
    live_temp: int | None
        Temperature of the tip (in °C)
    setpoint_temp: int | None
        Setpoint temperature (in °C)
    dc_voltage: float | None
        DC input voltage
    handle_temp: float | None
        Handle temperature (in °C)
    pwm_level: int | None
        Power level (0-100%)
    power_src: PowerSource | None
        Power source (e.g. USB-PD/QC or DC)
    tip_resistance: float | None
        Resistance of the tip (in Ω)
    uptime: float | None
        Uptime of the device (in seconds)
    movement_time: float | None
        Last movement time (in seconds)
    max_tip_temp_ability: int | None
        Maximum temperature supported by the tip (in °C)
    tip_voltage: int | None
        Raw tip voltage (in μV)
    hall_sensor: int | None
        Hall effect strength (if hall sensor is installed)
    operating_mode: OperatingMode | None
        Current operating mode of the device (e.g. soldering, idle...)
    estimated_power: float | None
        Estimated power usage (in Watt)

    """

    live_temp: int | None = None
    setpoint_temp: int | None = None
    dc_voltage: float | None = None
    handle_temp: float | None = None
    pwm_level: int | None = None
    power_src: PowerSource | None = None
    tip_resistance: float | None = None
    uptime: float | None = None
    movement_time: float | None = None
    max_tip_temp_ability: int | None = None
    tip_voltage: int | None = None
    hall_sensor: int | None = None
    operating_mode: OperatingMode | None = None
    estimated_power: float | None = None


class SettingsDataResponse(TypedDict, total=False):
    """Settings data response class.

    Attributes
    ----------
    setpoint_temp: int | None
        Setpoint temperature (in °C, 10-450)
    sleep_temp: int | None
        Temperature to drop to in sleep mode (in °C, 10-450)
    sleep_timeout: int | None
        timeout till sleep mode (in minutes , 0-15)
    min_dc_voltage_cells: BatteryType | None
        Voltage to cut out at for under voltage when powered by DC jack (0=DC, 1=3S, 2=4S, 3=5S, 4=6S)
    min_voltage_per_cell: float | None
        Minimum allowed voltage per cell (in V, 2.4-3.8, step=0.1)
    qc_ideal_voltage: float | None
        QC3.0 maximum voltage (9.0-22.0V, step=0.1)
    orientation_mode: ScreenOrientationMode | None
        Screen orientation (right-handed, left-handed, Auto)
    accel_sensitivity: int | None
        Motion sensitivity (0-9)
    animation_loop: bool | None
        Animation loop switch
    animation_speed: AnimationSpeed | None
        Animation speed (off, slow, medium, fast)
    autostart_mode: AutostartMode | None
        Mode to enter on start-up (disabled, soldering, sleeping, idle)
    shutdown_time: int | None
        Time until unit shuts down if not moved (in seconds, 0-60)
    cooling_temp_blink: bool | None
        Blink temperature on the cool down screen until its <50C
    idle_screen_details: bool | None
        Show details on idle screen
    solder_screen_details: bool | None
        Show details on soldering screen
    temp_unit: TempUnit | None
        Temperature unit (0=Celsius, 1=Fahrenheit)
    desc_scroll_speed: ScrollSpeed | None
        Description scroll speed (0=slow, 1=fast)
    locking_mode: LockingMode | None
        Allow locking buttons (off, boost mode only, full locking)
    keep_awake_pulse_power: float | None
        Intensity of power of keep-awake-pulse in W (0-9.9)
    keep_awake_pulse_delay: int | None
        Delay before keep-awake-pulse is triggered (1-9 x 2.5s)
    keep_awake_pulse_duration: int | None
        Keep-awake-pulse duration (1-9 x 250ms)
    voltage_div: int | None
        Voltage divisor factor (360-900)
    boost_temp: int | None
        Boost mode set point temperature (in °C, 0-450)
    calibration_offset: int | None
        Calibration offset for the installed tip (in µV, 100-2500)
    power_limit: float | None
        Maximum power allowed to output (in W, 0-12W, step=0.1)
    invert_buttons: bool | None
        Change the plus and minus button assigment
    temp_increment_long: int | None
        Temperature-change-increment on long button press in degree (5-90)
    temp_increment_short: int | None
        Temperature-change-increment on short button press in degree (1-50)
    hall_sensitivity: int | None
        Hall effect sensor sensitivity (0-9)
    accel_warn_counter: int | None
        Warning counter when accelerometer could not be detected (0-9)
    pd_warn_counter: int | None
        Warning counter when PD interface could not be detected (0-9)
    ui_language: LanguageCode | None
        Hashed integer of language code
    pd_negotiation_timeout: float | None
        Power delivery negotiation timeout in seconds (0-5.0, step=0.1)
    display_invert: bool | None
        Invert colors of display
    display_brightness: int | None
        Display brightness (1-5)
    logo_duration: LogoDuration | None
        Boot logo duration (off, 1-5seconds, loop ∞)
    calibrate_cjc: bool | None
        Enable CJC calibration at next boot
    ble_enabled: bool | None
        Disable BLE
    usb_pd_mode: bool | None
        PPS & EPR USB Power delivery mode
    settings_save: bool | None
        Save settings to flash
    settings_reset: bool | None
        Reset settings to default values

    """

    setpoint_temp: int | None
    sleep_temp: int | None
    sleep_timeout: int | None
    min_dc_voltage_cells: BatteryType | None
    min_voltage_per_cell: float | None
    qc_ideal_voltage: float | None
    orientation_mode: ScreenOrientationMode | None
    accel_sensitivity: int | None
    animation_loop: bool | None
    animation_speed: AnimationSpeed | None
    autostart_mode: AutostartMode | None
    shutdown_time: int | None
    cooling_temp_blink: bool | None
    idle_screen_details: bool | None
    solder_screen_details: bool | None
    temp_unit: TempUnit | None
    desc_scroll_speed: ScrollSpeed | None
    locking_mode: LockingMode | None
    keep_awake_pulse_power: float | None
    keep_awake_pulse_delay: int | None
    keep_awake_pulse_duration: int | None
    voltage_div: int | None
    boost_temp: int | None
    calibration_offset: int | None
    power_limit: float | None
    invert_buttons: bool | None
    temp_increment_long: int | None
    temp_increment_short: int | None
    hall_sensitivity: int | None
    accel_warn_counter: int | None
    pd_warn_counter: int | None
    ui_language: LanguageCode | None
    pd_negotiation_timeout: float | None
    display_invert: bool | None
    display_brightness: int | None
    logo_duration: LogoDuration | None
    calibrate_cjc: bool | None
    ble_enabled: bool | None
    usb_pd_mode: bool | None
    settings_save: bool | None
    settings_reset: bool | None

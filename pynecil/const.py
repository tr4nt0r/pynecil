"""Constants for Pynecil."""

from uuid import UUID

SVC_UUID_BULK = UUID("9eae1000-9d0d-48c5-aa55-33e27f9bc533")
CHAR_UUID_BULK_LIVE_DATA = UUID("9eae1001-9d0d-48c5-aa55-33e27f9bc533")
CHAR_UUID_BULK_ACCEL_NAME = UUID("9eae1002-9d0d-48c5-aa55-33e27f9bc533")
CHAR_UUID_BULK_BUILD = UUID("9eae1003-9d0d-48c5-aa55-33e27f9bc533")
CHAR_UUID_BULK_DEVICE_SN = UUID("9eae1004-9d0d-48c5-aa55-33e27f9bc533")
CHAR_UUID_BULK_DEVICE_ID = UUID("9eae1005-9d0d-48c5-aa55-33e27f9bc533")

SVC_UUID_LIVE = UUID("d85ef000-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_LIVE_TEMP = UUID("d85ef001-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_SETPOINT_TEMP = UUID("d85ef002-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_DC_VOLTAGE = UUID("d85ef003-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_HANDLE_TEMP = UUID("d85ef004-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_PWM_LEVEL = UUID("d85ef005-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_POWER_SRC = UUID("d85ef006-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_TIP_RESISTANCE = UUID("d85ef007-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_UPTIME = UUID("d85ef008-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_MOVEMENT_TIME = UUID("d85ef009-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_MAX_TIP_TEMP_ABILITY = UUID("d85ef00a-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_TIP_VOLTAGE = UUID("d85ef00b-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_HALL_SENSOR = UUID("d85ef00c-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_OPERATING_MODE = UUID("d85ef00d-168e-4a71-aa55-33e27f9bc533")
CHAR_UUID_LIVE_ESTIMATED_POWER = UUID("d85ef00e-168e-4a71-aa55-33e27f9bc533")

SVC_UUID_SETTINGS = UUID("f6d80000-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_SAVE = UUID("f6d7ffff-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_RESET = UUID("f6d7fffe-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_SETPOINT_TEMP = UUID("f6d70000-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_SLEEP_TEMP = UUID("f6d70001-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_SLEEP_TIMEOUT = UUID("f6d70002-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_MIN_DC_VOLTAGE_CELLS = UUID("f6d70003-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_MIN_VOLTAGE_PER_CELL = UUID("f6d70004-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_QC_IDEAL_VOLTAGE = UUID("f6d70005-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_ORIENTATION_MODE = UUID("f6d70006-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_ACCEL_SENSITIVITY = UUID("f6d70007-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_ANIMATION_LOOP = UUID("f6d70008-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_ANIMATION_SPEED = UUID("f6d70009-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_AUTOSTART_MODE = UUID("f6d7000a-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_SHUTDOWN_TIME = UUID("f6d7000b-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_COOLING_TEMP_BLINK = UUID("f6d7000c-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_IDLE_SCREEN_DETAILS = UUID("f6d7000d-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_SOLDER_SCREEN_DETAILS = UUID("f6d7000e-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_TEMP_UNIT = UUID("f6d7000f-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_DESC_SCROLL_SPEED = UUID("f6d70010-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_LOCKING_MODE = UUID("f6d70011-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_KEEP_AWAKE_PULSE_POWER = UUID("f6d70012-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_KEEP_AWAKE_PULSE_DELAY = UUID("f6d70013-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_KEEP_AWAKE_PULSE_DURATION = UUID(
    "f6d70014-5a10-4eba-aa55-33e27f9bc533"
)
CHAR_UUID_SETTINGS_VOLTAGE_DIV = UUID("f6d70015-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_BOOST_TEMP = UUID("f6d70016-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_CALIBRATION_OFFSET = UUID("f6d70017-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_POWER_LIMIT = UUID("f6d70018-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_INVERT_BUTTONS = UUID("f6d70019-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_TEMP_INCREMENT_LONG = UUID("f6d7001a-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_TEMP_INCREMENT_SHORT = UUID("f6d7001b-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_HALL_SENSITIVITY = UUID("f6d7001c-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_ACCEL_WARN_COUNTER = UUID("f6d7001d-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_PD_WARN_COUNTER = UUID("f6d7001e-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_UI_LANGUAGE = UUID("f6d7001f-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_PD_NEGOTIATION_TIMEOUT = UUID("f6d70020-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_DISPLAY_INVERT = UUID("f6d70021-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_DISPLAY_BRIGHTNESS = UUID("f6d70022-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_LOGO_DURATION = UUID("f6d70023-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_CALIBRATE_CJC = UUID("f6d70024-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_BLE_ENABLED = UUID("f6d70025-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_USB_PD_MODE = UUID("f6d70026-5a10-4eba-aa55-33e27f9bc533")

# added in IronOS 2.23
CHAR_UUID_SETTINGS_HALL_SLEEP_TIME = UUID("f6d70035-5a10-4eba-aa55-33e27f9bc533")
CHAR_UUID_SETTINGS_TIP_TYPE = UUID("f6d70036-5a10-4eba-aa55-33e27f9bc533")

GITHUB_LATEST_RELEASES_URL = "https://api.github.com/repos/Ralim/IronOS/releases/latest"

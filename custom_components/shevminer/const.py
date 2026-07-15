"""Constants for the ShevMiner integration."""

DOMAIN = "shevminer"

CONF_HOST = "host"
CONF_PORT = "port"
CONF_PASSWORD = "password"
CONF_API_KEY = "api_key"

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 10

ATTR_MINER_STATE = "miner_state"
ATTR_THROTTLED = "throttled"
ATTR_MINER_TYPE = "miner_type"
ATTR_FIRMWARE = "firmware"
ATTR_MODEL = "model"
ATTR_SERIAL = "serial"
ATTR_IP = "ip"
ATTR_MAC = "mac"
ATTR_HOSTNAME = "hostname"
ATTR_UPTIME = "uptime"

SENSOR_HASHRATE_REALTIME = "hashrate_realtime"
SENSOR_HASHRATE_AVERAGE = "hashrate_average"
SENSOR_HASHRATE_NOMINAL = "hashrate_nominal"
SENSOR_POWER_CONSUMPTION = "power_consumption"
SENSOR_POWER_EFFICIENCY = "power_efficiency"
SENSOR_HW_ERRORS = "hw_errors"
SENSOR_HW_ERRORS_PERCENT = "hw_errors_percent"
SENSOR_CHIP_TEMP = "chip_temp"
SENSOR_PCB_TEMP = "pcb_temp"
SENSOR_FAN_DUTY = "fan_duty"
SENSOR_RESTART_COUNT = "restart_count"
SENSOR_MINER_STATE = "miner_state"

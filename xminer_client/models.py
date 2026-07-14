from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class TempRange:
    min: int
    max: int


@dataclass
class BoardStatus:
    state: str
    description: Optional[str] = None


@dataclass
class Fan:
    id: int
    rpm: int
    status: str
    max_rpm: int


@dataclass
class FanSettings:
    mode: dict[str, Any]


@dataclass
class Cooling:
    fan_num: int
    fans: list[Fan] = field(default_factory=list)
    settings: FanSettings = field(default_factory=lambda: FanSettings(mode={}))
    fan_duty: int = 0


@dataclass
class PoolStats:
    id: int
    url: str
    pool_type: str
    user: str
    status: str
    asic_boost: bool
    diff: str
    accepted: int
    rejected: int
    stale: int
    ls_diff: float
    ls_time: str
    diffa: float
    ping: int


@dataclass
class MinerStatus:
    miner_state: str
    throttled: int
    miner_state_time: int
    description: Optional[str] = None
    failure_code: Optional[int] = None


@dataclass
class AntmBoard:
    id: int
    frequency: float
    voltage: int
    power_consumption: int
    hashrate_ideal: float
    hashrate_rt: float
    hashrate_percentage: float
    hr_error: float
    hw_errors: int
    pcb_temp: TempRange
    chip_temp: TempRange
    chip_statuses: dict[str, int]
    status: BoardStatus
    inlet_water_temp: Optional[int] = None
    outlet_water_temp: Optional[int] = None


@dataclass
class AntmPsuTemps:
    llc1_temp: Optional[int] = None
    llc2_temp: Optional[int] = None
    pfc_temp: Optional[int] = None


@dataclass
class AntmPsuInfo:
    psu_power_metering: Optional[bool] = None
    temps: Optional[AntmPsuTemps] = None


@dataclass
class AntmMinerStats:
    miner_status: Optional[MinerStatus] = None
    miner_type: str = ""
    hr_stock: float = 0.0
    average_hashrate: float = 0.0
    instant_hashrate: float = 0.0
    hr_realtime: float = 0.0
    hr_nominal: float = 0.0
    hr_average: float = 0.0
    pcb_temp: Optional[TempRange] = None
    chip_temp: Optional[TempRange] = None
    power_consumption: int = 0
    power_usage: int = 0
    power_efficiency: float = 0.0
    hw_errors_percent: float = 0.0
    hr_error: float = 0.0
    hw_errors: int = 0
    devfee_percent: float = 0.0
    devfee: float = 0.0
    pools: list[PoolStats] = field(default_factory=list)
    cooling: Optional[Cooling] = None
    chains: list[AntmBoard] = field(default_factory=list)
    found_blocks: int = 0
    best_share: int = 0
    restart_count: int = 0
    psu: Optional[AntmPsuInfo] = None


@dataclass
class Summary:
    miner: Optional[AntmMinerStats] = None


@dataclass
class FwInfo:
    fw_name: str
    fw_version: str
    platform: str
    install_type: str
    build_time: str
    build_name: Optional[str] = None
    build_uuid: Optional[str] = None


@dataclass
class NetworkStatus:
    mac: str
    ip: str
    netmask: str
    gateway: str
    dns: list[str]
    hostname: str
    dhcp: Optional[bool] = None


@dataclass
class SystemInfo:
    os: str
    miner_name: str
    file_system_version: str
    network_status: NetworkStatus
    uptime: str
    mem_total: int = 0
    mem_free: int = 0
    mem_free_percent: int = 0
    mem_buf: int = 0
    mem_buf_percent: int = 0


@dataclass
class InfoJson:
    fw_name: str
    fw_version: str
    platform: str
    install_type: str
    build_time: str
    miner: str
    model: str
    algorithm: str
    hr_measure: str
    system: SystemInfo
    serial: str
    build_name: Optional[str] = None
    build_uuid: Optional[str] = None


@dataclass
class ModelInfoBoard:
    chips_per_chain: int
    chips_per_domain: int
    num_chains: int
    topology: dict[str, Any]


@dataclass
class Overclock:
    max_voltage: int
    min_voltage: int
    default_voltage: int
    max_freq: int
    min_freq: int
    default_freq: int
    warn_freq: int
    max_voltage_stock_psu: int
    power_metering: bool
    max_power_limit: int


@dataclass
class CoolingConsts:
    min_fan_pwm: int
    min_target_temp: int
    max_target_temp: int
    fan_min_count: Optional[dict[str, int]] = None


@dataclass
class MinerModelInfo:
    full_name: str
    model: str
    algorithm: str
    series: str
    platform: str
    install_type: str
    hr_measure: str
    serial: str
    chain: ModelInfoBoard
    cooling: CoolingConsts
    overclock: Overclock


@dataclass
class AutotunePresetsItem:
    name: str
    pretty: str
    status: str
    modded_psu_required: bool


@dataclass
class GlobalsRaw:
    freq: Optional[int] = None
    volt: Optional[int] = None


@dataclass
class BoardRaw:
    freq: Optional[int] = None
    chips: Optional[list[int]] = None
    disabled: Optional[bool] = None


@dataclass
class PresetSwitcherRaw:
    enabled: Optional[bool] = None
    check_time: Optional[int] = None
    decrease_temp: Optional[int] = None
    rise_temp: Optional[int] = None
    power_delta: Optional[int] = None
    power_delta_unit: Optional[str] = None
    top_preset: Optional[str] = None
    min_preset: Optional[str] = None
    autochange_top_preset: Optional[bool] = None
    ignore_fan_speed: Optional[bool] = None


@dataclass
class OverclockSettingsRaw:
    chains: Optional[list[BoardRaw]] = None
    globals: Optional[GlobalsRaw] = None
    modded_psu: Optional[bool] = None
    preset: Optional[str] = None
    preset_switcher: Optional[PresetSwitcherRaw] = None


@dataclass
class CoolingSettingsRaw:
    fan_min_duty: Optional[int] = None
    fan_max_duty: Optional[int] = None
    fan_min_count: Optional[int] = None
    min_startup_water_temp: Optional[int] = None
    mode: Optional[dict[str, Any]] = None


@dataclass
class AdvancedSettingsRaw:
    asic_boost: Optional[bool] = None
    auto_chip_throttling: Optional[bool] = None
    automatic_pause_on_boot: Optional[bool] = None
    bitmain_disable_volt_comp: Optional[bool] = None
    disable_chain_break_protection: Optional[bool] = None
    disable_restart_unbalanced: Optional[bool] = None
    disable_volt_checks: Optional[bool] = None
    downscale_preset_on_failure: Optional[bool] = None
    ignore_broken_sensors: Optional[bool] = None
    ignore_chip_sensors: Optional[bool] = None
    keep_hashing_when_offline: Optional[bool] = None
    max_restart_attempts: Optional[int] = None
    max_startup_delay_time: Optional[int] = None
    min_operational_chains: Optional[int] = None
    min_startup_delay_time: Optional[int] = None
    power_limit: Optional[int] = None
    quick_start: Optional[bool] = None
    quiet_mode: Optional[bool] = None
    restart_hashrate: Optional[int] = None
    restart_temp: Optional[int] = None
    restore_miner_state_on_reboot: Optional[bool] = None
    retune_on_chain_break: Optional[bool] = None
    tuner_bad_chip_hr_threshold: Optional[int] = None


@dataclass
class Pool:
    url: str
    user: str
    pass_: str


@dataclass
class MinerConfigRaw:
    pools: Optional[list[Pool]] = None
    cooling: Optional[CoolingSettingsRaw] = None
    misc: Optional[AdvancedSettingsRaw] = None
    overclock: Optional[OverclockSettingsRaw] = None


@dataclass
class NetworkConfFile:
    hostname: str
    dhcp: bool
    ipaddress: str
    netmask: str
    gateway: str
    dnsservers: list[str]


@dataclass
class RegionalSettings:
    timezone: dict[str, str]


@dataclass
class UiSettings:
    consts: Optional[dict[str, Any]] = None
    dark_side_pane: Optional[bool] = None
    disable_animation: Optional[bool] = None
    locale: Optional[str] = None
    theme: Optional[str] = None
    timezone: Optional[str] = None


@dataclass
class ViewConfig:
    miner: MinerConfigRaw
    ui: UiSettings
    regional: RegionalSettings
    network: NetworkConfFile
    layout: Optional[dict[str, Any]] = None
    password: Optional[dict[str, str]] = None


@dataclass
class SaveConfigResult:
    restart_required: bool
    reboot_required: bool


@dataclass
class StatusPane:
    miner_state: str
    throttled: int
    miner_state_time: int
    restart_required: bool
    reboot_required: bool
    find_miner: bool
    unlocked: bool
    description: Optional[str] = None
    failure_code: Optional[int] = None
    unlock_timeout: Optional[int] = None
    warranty: Optional[str] = None


@dataclass
class RebootAfter:
    after: int


@dataclass
class WarrantyStatus:
    success: bool
    warranty: Optional[str] = None


@dataclass
class ApiKeysJsonItem:
    key: str
    description: str


@dataclass
class AuthCheck:
    unlock_timeout: Optional[int] = None


@dataclass
class ThrottleSettings:
    percent: int


@dataclass
class SwitchPoolQuery:
    pool_id: int


@dataclass
class MetricsData:
    hashrate: float
    pcb_max_temp: int
    chip_max_temp: int
    fan_duty: int
    power_consumption: int


@dataclass
class MetricsReply:
    timezone: str
    metrics: list[dict[str, Any]]
    annotations: list[dict[str, Any]]


@dataclass
class PerfSummary:
    preset_switcher: PresetSwitcherRaw
    current_preset: Optional[AutotunePresetsItem] = None


@dataclass
class FactoryInfoBoard:
    id: int
    board_model: str
    serial: str
    chip_bin: int
    freq: int
    volt: int
    hashrate: float


@dataclass
class FactoryInfoReply:
    chains: Optional[list[FactoryInfoBoard]] = None
    has_pics: Optional[bool] = None
    hr_stock: Optional[float] = None
    psu_model: Optional[str] = None
    psu_serial: Optional[str] = None


@dataclass
class LocateMinerStatus:
    is_enabled: bool

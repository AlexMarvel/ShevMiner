from __future__ import annotations

from typing import Any, Optional

import requests

from .models import (
    AntmMinerStats,
    ApiKeysJsonItem,
    AuthCheck,
    AutotunePresetsItem,
    BoardStatus,
    Cooling,
    FactoryInfoBoard,
    FactoryInfoReply,
    Fan,
    FanSettings,
    FwInfo,
    GlobalsRaw,
    InfoJson,
    LocateMinerStatus,
    MinerModelInfo,
    MinerStatus,
    ModelInfoBoard,
    NetworkStatus,
    Overclock,
    CoolingConsts,
    PerfSummary,
    PoolStats,
    PresetSwitcherRaw,
    RebootAfter,
    SaveConfigResult,
    StatusPane,
    Summary,
    SystemInfo,
    TempRange,
    WarrantyStatus,
)


class XMinerError(Exception):
    def __init__(self, message: str, status_code: int = 0, body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class XMinerClient:
    def __init__(
        self,
        host: str = "192.168.1.147",
        port: int = 80,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 10,
        verify_ssl: bool = True,
    ):
        scheme = "https" if port == 443 else "http"
        self.base_url = f"{scheme}://{host}:{port}/api/v1"
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self._api_key = api_key
        self._token = token

    @property
    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        elif self._api_key:
            h["x-api-key"] = self._api_key
        return h

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Optional[dict[str, Any]] = None,
        files: Optional[dict[str, Any]] = None,
        data: Optional[dict[str, Any]] = None,
        auth: bool = True,
    ) -> Any:
        url = f"{self.base_url}{path}"
        headers = dict(self._headers) if auth else {}
        if json_body is not None and files is None:
            headers["Content-Type"] = "application/json"

        try:
            resp = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json_body if json_body is not None and files is None else None,
                params=params,
                files=files,
                data=data,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        except requests.exceptions.RequestException as exc:
            raise XMinerError(str(exc)) from exc

        if resp.status_code >= 400:
            try:
                body = resp.json()
                err_msg = body.get("err", str(body))
            except Exception:
                body = resp.text
                err_msg = body
            raise XMinerError(err_msg, resp.status_code, body)

        if resp.status_code == 204 or not resp.content:
            return None

        ct = resp.headers.get("content-type", "")
        if "application/json" in ct:
            return resp.json()
        return resp.content

    @staticmethod
    def _unwrap(d: Any, key: str) -> Any:
        if d is None:
            return None
        return d.get(key, d)

    @staticmethod
    def _temp_range(d: Optional[dict]) -> Optional[TempRange]:
        if d is None:
            return None
        return TempRange(min=d["min"], max=d["max"])

    @staticmethod
    def _board_status(d: Optional[dict]) -> Optional[BoardStatus]:
        if d is None:
            return None
        return BoardStatus(state=d["state"], description=d.get("description"))

    @staticmethod
    def _fan(d: dict) -> Fan:
        return Fan(id=d["id"], rpm=d["rpm"], status=d["status"], max_rpm=d["max_rpm"])

    @staticmethod
    def _cooling(d: Optional[dict]) -> Optional[Cooling]:
        if d is None:
            return None
        fans = [XMinerClient._fan(f) for f in d.get("fans", [])]
        settings = FanSettings(mode=d.get("settings", {}).get("mode", {}))
        return Cooling(
            fan_num=d["fan_num"],
            fans=fans,
            settings=settings,
            fan_duty=d["fan_duty"],
        )

    @staticmethod
    def _pool_stats(d: dict) -> PoolStats:
        return PoolStats(
            id=d["id"],
            url=d["url"],
            pool_type=d["pool_type"],
            user=d["user"],
            status=d["status"],
            asic_boost=d["asic_boost"],
            diff=d["diff"],
            accepted=d["accepted"],
            rejected=d["rejected"],
            stale=d["stale"],
            ls_diff=d["ls_diff"],
            ls_time=d["ls_time"],
            diffa=d["diffa"],
            ping=d["ping"],
        )

    @staticmethod
    def _miner_status(d: Optional[dict]) -> Optional[MinerStatus]:
        if d is None:
            return None
        return MinerStatus(
            miner_state=d["miner_state"],
            throttled=d["throttled"],
            miner_state_time=d["miner_state_time"],
            description=d.get("description"),
            failure_code=d.get("failure_code"),
        )

    @staticmethod
    def _miner_stats(d: Optional[dict]) -> Optional[AntmMinerStats]:
        if d is None:
            return None
        return AntmMinerStats(
            miner_status=XMinerClient._miner_status(d.get("miner_status")),
            miner_type=d["miner_type"],
            hr_stock=d["hr_stock"],
            average_hashrate=d["average_hashrate"],
            instant_hashrate=d["instant_hashrate"],
            hr_realtime=d["hr_realtime"],
            hr_nominal=d["hr_nominal"],
            hr_average=d["hr_average"],
            pcb_temp=XMinerClient._temp_range(d.get("pcb_temp")),
            chip_temp=XMinerClient._temp_range(d.get("chip_temp")),
            power_consumption=d["power_consumption"],
            power_usage=d["power_usage"],
            power_efficiency=d["power_efficiency"],
            hw_errors_percent=d["hw_errors_percent"],
            hr_error=d["hr_error"],
            hw_errors=d["hw_errors"],
            devfee_percent=d["devfee_percent"],
            devfee=d["devfee"],
            pools=[XMinerClient._pool_stats(p) for p in d.get("pools", [])],
            cooling=XMinerClient._cooling(d.get("cooling")),
            found_blocks=d.get("found_blocks", 0),
            best_share=d.get("best_share", 0),
            restart_count=d.get("restart_count", 0),
        )

    @staticmethod
    def _network_status(d: dict) -> NetworkStatus:
        return NetworkStatus(
            mac=d["mac"],
            ip=d["ip"],
            netmask=d["netmask"],
            gateway=d["gateway"],
            dns=d["dns"],
            hostname=d["hostname"],
            dhcp=d.get("dhcp"),
        )

    @staticmethod
    def _fw_info(d: dict) -> FwInfo:
        return FwInfo(
            fw_name=d["fw_name"],
            fw_version=d["fw_version"],
            platform=d["platform"],
            install_type=d["install_type"],
            build_time=d["build_time"],
            build_name=d.get("build_name"),
            build_uuid=d.get("build_uuid"),
        )

    @staticmethod
    def _info_json(d: dict) -> InfoJson:
        sys_d = d["system"]
        return InfoJson(
            **XMinerClient._fw_info(d).__dict__,
            miner=d["miner"],
            model=d["model"],
            algorithm=d["algorithm"],
            hr_measure=d["hr_measure"],
            system=SystemInfo(
                os=sys_d["os"],
                miner_name=sys_d["miner_name"],
                file_system_version=sys_d["file_system_version"],
                network_status=XMinerClient._network_status(sys_d["network_status"]),
                uptime=sys_d["uptime"],
                mem_total=sys_d.get("mem_total", 0),
                mem_free=sys_d.get("mem_free", 0),
                mem_free_percent=sys_d.get("mem_free_percent", 0),
                mem_buf=sys_d.get("mem_buf", 0),
                mem_buf_percent=sys_d.get("mem_buf_percent", 0),
            ),
            serial=d["serial"],
        )

    @staticmethod
    def _overclock(d: dict) -> Overclock:
        return Overclock(
            max_voltage=d["max_voltage"],
            min_voltage=d["min_voltage"],
            default_voltage=d["default_voltage"],
            max_freq=d["max_freq"],
            min_freq=d["min_freq"],
            default_freq=d["default_freq"],
            warn_freq=d["warn_freq"],
            max_voltage_stock_psu=d["max_voltage_stock_psu"],
            power_metering=d["power_metering"],
            max_power_limit=d["max_power_limit"],
        )

    @staticmethod
    def _cooling_consts(d: dict) -> CoolingConsts:
        return CoolingConsts(
            min_fan_pwm=d["min_fan_pwm"],
            min_target_temp=d["min_target_temp"],
            max_target_temp=d["max_target_temp"],
            fan_min_count=d.get("fan_min_count"),
        )

    @staticmethod
    def _model_info(d: dict) -> MinerModelInfo:
        chain_d = d["chain"]
        return MinerModelInfo(
            full_name=d["full_name"],
            model=d["model"],
            algorithm=d["algorithm"],
            series=d["series"],
            platform=d["platform"],
            install_type=d["install_type"],
            hr_measure=d["hr_measure"],
            serial=d["serial"],
            chain=ModelInfoBoard(
                chips_per_chain=chain_d["chips_per_chain"],
                chips_per_domain=chain_d["chips_per_domain"],
                num_chains=chain_d["num_chains"],
                topology=chain_d["topology"],
            ),
            cooling=XMinerClient._cooling_consts(d["cooling"]),
            overclock=XMinerClient._overclock(d["overclock"]),
        )

    @staticmethod
    def _preset_switcher(d: Optional[dict]) -> Optional[PresetSwitcherRaw]:
        if d is None:
            return None
        return PresetSwitcherRaw(
            enabled=d.get("enabled"),
            check_time=d.get("check_time"),
            decrease_temp=d.get("decrease_temp"),
            rise_temp=d.get("rise_temp"),
            power_delta=d.get("power_delta"),
            power_delta_unit=d.get("power_delta_unit"),
            top_preset=d.get("top_preset"),
            min_preset=d.get("min_preset"),
            autochange_top_preset=d.get("autochange_top_preset"),
            ignore_fan_speed=d.get("ignore_fan_speed"),
        )

    @staticmethod
    def _status_pane(d: dict) -> StatusPane:
        return StatusPane(
            miner_state=d["miner_state"],
            throttled=d["throttled"],
            miner_state_time=d["miner_state_time"],
            restart_required=d["restart_required"],
            reboot_required=d["reboot_required"],
            find_miner=d.get("find_miner", False),
            unlocked=d["unlocked"],
            description=d.get("description"),
            failure_code=d.get("failure_code"),
            unlock_timeout=d.get("unlock_timeout"),
            warranty=d.get("warranty"),
        )

    @staticmethod
    def _autotune_preset(d: dict) -> AutotunePresetsItem:
        return AutotunePresetsItem(
            name=d["name"],
            pretty=d["pretty"],
            status=d["status"],
            modded_psu_required=d["modded_psu_required"],
        )

    @staticmethod
    def _factory_info(d: dict) -> FactoryInfoReply:
        chains = None
        if d.get("chains"):
            chains = [
                FactoryInfoBoard(
                    id=c["id"],
                    board_model=c["board_model"],
                    serial=c["serial"],
                    chip_bin=c["chip_bin"],
                    freq=c["freq"],
                    volt=c["volt"],
                    hashrate=c["hashrate"],
                )
                for c in d["chains"]
            ]
        return FactoryInfoReply(
            chains=chains,
            has_pics=d.get("has_pics"),
            hr_stock=d.get("hr_stock"),
            psu_model=d.get("psu_model"),
            psu_serial=d.get("psu_serial"),
        )

    # ── Auth ──────────────────────────────────────────────────

    def unlock(self, password: str) -> str:
        data = self._request("POST", "/unlock", json_body={"pw": password}, auth=False)
        token = data["token"]
        self._token = token
        return token

    def auth_check(self) -> AuthCheck:
        data = self._request("GET", "/auth-check")
        return AuthCheck(unlock_timeout=data.get("unlock_timeout"))

    def lock(self) -> None:
        self._request("POST", "/lock")

    def lock_others(self, password: str) -> None:
        self._request("POST", "/lock/others", json_body={"pw": password})

    # ── Info / Status (no auth required) ──────────────────────

    def get_info(self) -> InfoJson:
        data = self._request("GET", "/info", auth=False)
        return self._info_json(data)

    def get_model(self) -> MinerModelInfo:
        data = self._request("GET", "/model", auth=False)
        return self._model_info(data)

    def get_status(self) -> StatusPane:
        data = self._request("GET", "/status", auth=False)
        return self._status_pane(data)

    def get_summary(self) -> Summary:
        data = self._request("GET", "/summary", auth=False)
        miner = self._miner_stats(data.get("miner"))
        return Summary(miner=miner)

    def get_ui(self) -> dict[str, Any]:
        return self._request("GET", "/ui", auth=False)

    def get_layout(self) -> Optional[dict[str, Any]]:
        return self._request("GET", "/layout", auth=False)

    def get_perf_summary(self) -> PerfSummary:
        data = self._request("GET", "/perf-summary", auth=False)
        current = None
        cp = data.get("current_preset")
        if cp:
            current = self._autotune_preset(cp)
        ps = self._preset_switcher(data["preset_switcher"])
        return PerfSummary(
            preset_switcher=ps if ps is not None else PresetSwitcherRaw(),
            current_preset=current,
        )

    def get_boards(self) -> list[dict[str, Any]]:
        return self._request("GET", "/boards", auth=False)

    def get_chains_factory_info(self) -> FactoryInfoReply:
        data = self._request("GET", "/chains/factory-info", auth=False)
        return self._factory_info(data)

    # ── Mining control ────────────────────────────────────────

    def mining_start(self) -> None:
        self._request("POST", "/mining/start")

    def mining_stop(self) -> None:
        self._request("POST", "/mining/stop")

    def mining_restart(self) -> None:
        self._request("POST", "/mining/restart")

    def mining_resume(self) -> None:
        self._request("POST", "/mining/resume")

    def mining_pause(self) -> None:
        self._request("POST", "/mining/pause")

    def mining_switch_pool(self, pool_id: int) -> None:
        self._request("POST", "/mining/switch-pool", json_body={"pool_id": pool_id})

    def mining_throttle(self, percent: int) -> None:
        if not 20 <= percent <= 100:
            raise ValueError("percent must be 20-100")
        self._request("POST", "/mining/throttle", json_body={"percent": percent})

    # ── Autotune ──────────────────────────────────────────────

    def get_autotune_presets(self) -> list[AutotunePresetsItem]:
        data = self._request("GET", "/autotune/presets")
        return [self._autotune_preset(p) for p in data]

    def autotune_reset(self, presets: list[str], restart: bool = False) -> None:
        self._request(
            "POST", "/autotune/reset", json_body={"presets": presets, "restart": restart}
        )

    def autotune_reset_all(self, restart: bool = False) -> None:
        self._request("POST", "/autotune/reset-all", json_body={"restart": restart})

    # ── Settings ──────────────────────────────────────────────

    def get_settings(self) -> dict[str, Any]:
        return self._request("GET", "/settings")

    def save_settings(self, config: dict[str, Any]) -> SaveConfigResult:
        data = self._request("POST", "/settings", json_body=config)
        return SaveConfigResult(
            restart_required=data["restart_required"],
            reboot_required=data["reboot_required"],
        )

    def settings_backup(self) -> bytes:
        return self._request("POST", "/settings/backup")

    def settings_restore(self, file_path: str) -> RebootAfter:
        with open(file_path, "rb") as f:
            data = self._request("POST", "/settings/restore", files={"file": f})
        return RebootAfter(after=data["after"])

    def settings_factory_reset(self) -> RebootAfter:
        data = self._request("POST", "/settings/factory-reset")
        return RebootAfter(after=data["after"])

    # ── Firmware ──────────────────────────────────────────────

    def firmware_update(self, file_path: str, keep_settings: Optional[bool] = None) -> RebootAfter:
        with open(file_path, "rb") as f:
            files = {"file": f}
            form_data = {}
            if keep_settings is not None:
                form_data["keep_settings"] = "true" if keep_settings else "false"
            data = self._request("POST", "/firmware/update", files=files, data=form_data or None)
        return RebootAfter(after=data["after"])

    def firmware_remove(self, remove_stock_logs: bool = False) -> RebootAfter:
        data = self._request(
            "POST", "/firmware/remove", json_body={"remove_stock_logs": remove_stock_logs}
        )
        return RebootAfter(after=data["after"])

    # ── System ────────────────────────────────────────────────

    def system_reboot(self) -> RebootAfter:
        data = self._request("POST", "/system/reboot")
        return RebootAfter(after=data["after"])

    # ── Logs ──────────────────────────────────────────────────

    LOG_TYPES = {"status", "miner", "autotune", "pool", "hwscan", "system", "messages", "api", "*"}

    def get_logs(self, log_type: str) -> str:
        data = self._request("GET", f"/logs/{log_type}", auth=False)
        if isinstance(data, bytes):
            return data.decode("utf-8", errors="replace")
        return str(data)

    def clear_logs(self, log_type: str) -> None:
        self._request("POST", f"/logs/{log_type}/clear")

    # ── Notes ─────────────────────────────────────────────────

    def get_notes(self) -> dict[str, str]:
        return self._request("GET", "/notes", auth=False)

    def get_note(self, key: str) -> str:
        data = self._request("GET", f"/notes/{key}", auth=False)
        return data.get("value", "") if isinstance(data, dict) else str(data)

    def create_note(self, key: str, value: str) -> None:
        self._request("POST", "/notes", json_body={"key": key, "value": value})

    def update_note(self, key: str, value: str) -> None:
        self._request("PUT", f"/notes/{key}", json_body={"value": value})

    def delete_note(self, key: str) -> None:
        self._request("DELETE", f"/notes/{key}")

    # ── API Keys ──────────────────────────────────────────────

    def get_apikeys(self) -> list[ApiKeysJsonItem]:
        data = self._request("GET", "/apikeys")
        return [ApiKeysJsonItem(key=item["key"], description=item["description"]) for item in data]

    def add_apikey(self, key: str, description: str) -> str:
        data = self._request(
            "POST", "/apikeys", json_body={"key": key, "description": description}
        )
        return data.get("status", "")

    def delete_apikey(self, key: str) -> None:
        self._request("POST", "/apikeys/delete", json_body={"key": key})

    # ── Warranty ──────────────────────────────────────────────

    def activate_warranty(self) -> WarrantyStatus:
        data = self._request("POST", "/activate-warranty")
        return WarrantyStatus(success=data["success"], warranty=data.get("warranty"))

    def cancel_warranty(self) -> WarrantyStatus:
        data = self._request("POST", "/cancel-warranty")
        return WarrantyStatus(success=data["success"], warranty=data.get("warranty"))

    # ── Metrics ───────────────────────────────────────────────

    def get_metrics(
        self, time_slice: Optional[int] = None, step: Optional[int] = None
    ) -> dict[str, Any]:
        params = {}
        if time_slice is not None:
            params["time_slice"] = time_slice
        if step is not None:
            params["step"] = step
        return self._request("GET", "/metrics", params=params or None, auth=False)

    # ── Locate / Find ─────────────────────────────────────────

    def locate_miner(self) -> LocateMinerStatus:
        data = self._request("POST", "/locate-miner", auth=False)
        return LocateMinerStatus(is_enabled=data["is_enabled"])

    def find_miner(self) -> Optional[dict[str, Any]]:
        return self._request("POST", "/find-miner", auth=False)

    # ── Context manager ───────────────────────────────────────

    def __enter__(self) -> "XMinerClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

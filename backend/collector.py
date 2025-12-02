"""
TEMS log collector helpers for Redfish/IPMI.

Normalized log schema:
{
    "timestamp": datetime,
    "host": str,
    "vendor": str,
    "service": str,
    "severity": str,
    "message": str,
}

This module keeps network calls minimal and focuses on shaping data for
downstream analysis. Replace stubs with real Redfish/IPMI calls when ready.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

NormalizedLog = Dict[str, Any]


def normalize_log(
    *,
    timestamp: datetime,
    host: str,
    vendor: str,
    service: str,
    severity: str,
    message: str,
) -> NormalizedLog:
    return {
        "timestamp": timestamp,
        "host": host,
        "vendor": vendor,
        "service": service,
        "severity": severity,
        "message": message,
    }


async def fetch_redfish_logs(
    bmc_host: str,
    username: str,
    password: str,
    vendor: str,
    system_path: str = "/Systems/1",
    log_path: str = "/Systems/1/LogServices/SEL/Entries",
) -> List[NormalizedLog]:
    """Fetch Redfish log entries and normalize.

    Replace the endpoint paths per vendor if 다름 (예: iLO IML: /Systems/1/LogServices/IEL/Entries,
    iDRAC Lifecycle: /Systems/System.Embedded.1/LogServices/Lclog/Entries).
    """
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        system_url = f"https://{bmc_host}/redfish/v1{system_path}"
        logs_url = f"https://{bmc_host}/redfish/v1{log_path}"
        await client.get(system_url, auth=(username, password))  # priming / auth check
        res = await client.get(logs_url, auth=(username, password))
        res.raise_for_status()
        data = res.json()

    entries = data.get("Members", [])
    normalized: List[NormalizedLog] = []
    for e in entries:
        ts = e.get("Created") or e.get("DateTime") or datetime.utcnow().isoformat()
        msg = e.get("Message") or e.get("OemRecordFormat") or str(e)
        sev = e.get("Severity") or e.get("EntryType") or "INFO"
        comp = e.get("SensorType") or e.get("OriginOfCondition") or "log"
        normalized.append(
            normalize_log(
                timestamp=datetime.fromisoformat(ts.replace("Z", "+00:00")),
                host=bmc_host,
                vendor=vendor,
                service=str(comp),
                severity=str(sev),
                message=str(msg),
            )
        )
    return normalized


def parse_ipmi_sel(sel_output: str, *, host: str, vendor: str, service: str = "ipmi") -> List[NormalizedLog]:
    """Parse ipmitool sel elist output into normalized logs.

    Expected line example:
    1 | 09/13/2024 | 12:34:56 | Critical | PSU1 input lost
    """
    normalized: List[NormalizedLog] = []
    for line in sel_output.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 5:
            continue
        _, date_str, time_str, sev, msg = parts[:5]
        try:
            ts = datetime.strptime(f"{date_str} {time_str}", "%m/%d/%Y %H:%M:%S")
        except Exception:
            ts = datetime.utcnow()
        normalized.append(
            normalize_log(
                timestamp=ts,
                host=host,
                vendor=vendor,
                service=service,
                severity=sev,
                message=msg,
            )
        )
    return normalized


def parse_ipmi_sensor(sensor_output: str, *, host: str, vendor: str, service: str = "sensor") -> List[NormalizedLog]:
    """Parse ipmitool sensor output into normalized logs (as metric-like events)."""
    normalized: List[NormalizedLog] = []
    for line in sensor_output.splitlines():
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 2:
            continue
        name, reading = parts[:2]
        msg = f"{name}: {reading}"
        normalized.append(
            normalize_log(
                timestamp=datetime.utcnow(),
                host=host,
                vendor=vendor,
                service=service,
                severity="INFO",
                message=msg,
            )
        )
    return normalized


# Convenience wrapper to decide Redfish vs IPMI
async def collect_logs(
    *,
    vendor: str,
    bmc_host: str,
    username: str,
    password: str,
    prefer_redfish: bool = True,
) -> List[NormalizedLog]:
    if prefer_redfish:
        try:
            return await fetch_redfish_logs(bmc_host, username, password, vendor)
        except Exception:
            # Fallback to IPMI if Redfish fails
            pass
    # Placeholder: replace with actual ipmitool invocation and parsing
    sel_mock = "1 | 09/13/2024 | 12:34:56 | Critical | PSU1 input lost"
    return parse_ipmi_sel(sel_mock, host=bmc_host, vendor=vendor)

from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


class ServerInput(BaseModel):
    vendor: Literal["hpe", "dell", "lenovo", "supermicro", "other", "all"]
    bmc_host: str
    username: str
    password: str


class HardwareInfo(BaseModel):
    model: str
    serial: str
    firmware: Optional[str] = None
    power_state: Optional[str] = None
    last_boot: Optional[datetime] = None


class LogEntry(BaseModel):
    timestamp: datetime
    severity: str
    message: str
    component: Optional[str] = None
    host: Optional[str] = None
    vendor: Optional[str] = None


class Analysis(BaseModel):
    risk_score: float = Field(ge=0, le=1)
    summary: str
    insights: list[str]


class ConnectResponse(BaseModel):
    vendor: str
    hardware: HardwareInfo
    logs: list[LogEntry]
    analysis: Analysis


class AnalyzeRequest(BaseModel):
    vendor: Literal["hpe", "dell", "lenovo", "supermicro", "other", "all"] = "all"
    bmc_host: Optional[str] = None


app = FastAPI(title="Hardware Monitoring API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


STATIC_DIR = Path(__file__).resolve().parents[2]
if STATIC_DIR.exists():
    app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui/index.html")


def mock_hardware(vendor: str) -> HardwareInfo:
    now = datetime.utcnow()
    return HardwareInfo(
        model=f"{vendor.upper()}-Server-GenX",
        serial="SN123456",
        firmware="2.0.1",
        power_state="On",
        last_boot=now,
    )


def mock_logs(vendor: str, host: Optional[str] = None) -> list[LogEntry]:
    now = datetime.utcnow()
    source = host or f"{vendor}-bmc"
    return [
        LogEntry(timestamp=now, severity="INFO", message=f"[{vendor}] system OK", component="BMC", host=source, vendor=vendor),
        LogEntry(timestamp=now, severity="WARN", message="Fan 2 speed above threshold", component="Cooling", host=source, vendor=vendor),
        LogEntry(timestamp=now, severity="ERROR", message="PSU input unstable", component="Power", host=source, vendor=vendor),
        LogEntry(timestamp=now, severity="INFO", message="Periodic telemetry sync", component="Agent", host=source, vendor=vendor),
        LogEntry(timestamp=now, severity="WARN", message="Disk SMART pre-fail flagged", component="Storage", host=source, vendor=vendor),
    ]


def analyze_logs(logs: list[LogEntry]) -> Analysis:
    if not logs:
        return Analysis(risk_score=0, summary="No data", insights=["No logs to analyze"])
    crit = sum(1 for l in logs if l.severity.upper() in {"ERROR", "CRITICAL", "FATAL"})
    warn = sum(1 for l in logs if l.severity.upper() == "WARN")
    score = min(0.2 * crit + 0.05 * warn, 1.0)
    summary = "Stable" if score < 0.3 else "Investigate power/cooling"
    notes = [f"{crit} critical/error", f"{warn} warnings"]
    return Analysis(risk_score=score, summary=summary, insights=notes)


@app.post("/api/connect", response_model=ConnectResponse)
async def connect(payload: ServerInput) -> ConnectResponse:
    try:
        if payload.vendor == "all":
            vendors = ["hpe", "dell", "lenovo", "supermicro", "other"]
            logs: list[LogEntry] = []
            for v in vendors:
                logs.extend(mock_logs(v, host=f"{v}-demo"))
            hardware = mock_hardware("all")
        else:
            hardware = mock_hardware(payload.vendor)
            logs = mock_logs(payload.vendor, host=payload.bmc_host)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="BMC auth failed")
    except httpx.RequestError:
        raise HTTPException(status_code=504, detail="BMC connection failed")

    return ConnectResponse(
        vendor=payload.vendor,
        hardware=hardware,
        logs=logs,
        analysis=analyze_logs(logs),
    )


@app.post("/api/analyze")
async def analyze_endpoint(payload: AnalyzeRequest) -> dict:
    try:
        vendors = (
            ["hpe", "dell", "lenovo", "supermicro", "other"]
            if payload.vendor == "all"
            else [payload.vendor]
        )
        all_logs: list[LogEntry] = []
        for v in vendors:
            all_logs.extend(mock_logs(v, host=payload.bmc_host or f"{v}-demo"))
        result = analyze_logs(all_logs)
        return {
            "vendor": payload.vendor,
            "risk_score": result.risk_score,
            "summary": result.summary,
            "insights": result.insights,
            "evidence": [f"[{l.vendor}@{l.host}] {l.severity}: {l.message}" for l in all_logs[:10]],
            "count": len(all_logs),
        }
    except Exception:
        raise HTTPException(status_code=500, detail="analysis_failed")

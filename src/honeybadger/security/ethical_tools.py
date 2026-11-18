import importlib
import logging
from typing import Any, Dict, List, Optional

from honeybadger.brain.ollama_brain import ask_honeybadger

logger = logging.getLogger(__name__)


def _safe_import(module_name: str) -> Any:
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise RuntimeError(f"Required module {module_name} is not installed.") from exc


def network_monitor(interface: Optional[str] = None, timeout: int = 10) -> Dict[str, Any]:
    psutil = _safe_import("psutil")
    scapy = _safe_import("scapy.all")

    stats = psutil.net_io_counters(pernic=True)
    net_data = {}
    if interface:
        net_data[interface] = stats.get(interface)
    else:
        for name, item in stats.items():
            net_data[name] = {
                "bytes_sent": item.bytes_sent,
                "bytes_recv": item.bytes_recv,
                "packets_sent": item.packets_sent,
                "packets_recv": item.packets_recv,
            }

    packets = scapy.sniff(iface=interface, timeout=timeout, count=50)
    proto_counts: Dict[str, int] = {}
    for packet in packets:
        proto = packet.__class__.__name__
        proto_counts[proto] = proto_counts.get(proto, 0) + 1

    summary = {
        "interface_summary": net_data,
        "packet_counts": proto_counts,
        "packet_sample_count": len(packets),
    }
    return summary


def vulnerability_scan(target: str) -> Dict[str, Any]:
    tenable = _safe_import("tenable.io")
    os = _safe_import("os")

    access_key = os.getenv("TENABLE_ACCESS_KEY", "")
    secret_key = os.getenv("TENABLE_SECRET_KEY", "")
    if not access_key or not secret_key:
        raise RuntimeError("TENABLE_ACCESS_KEY and TENABLE_SECRET_KEY must be configured.")

    tio = tenable.TenableIO(access_key=access_key, secret_key=secret_key)
    host_info = None
    try:
        for host in tio.hosts.list():
            if target in {host.get("hostname"), host.get("name"), host.get("ipv4")}:  # type: ignore
                host_info = host
                break
    except Exception as exc:
        raise RuntimeError("Failed to query Tenable hosts.") from exc

    if not host_info:
        return {
            "target": target,
            "found": False,
            "summary": "No host asset was found in Tenable for the requested target.",
        }

    host_id = host_info.get("id")
    vulnerabilities = []
    try:
        vulns = tio.analysis.vulnerabilities(hosts=[host_id], num_assets=1)
        for record in vulns.get("vulnerabilities", [])[:10]:
            vulnerabilities.append(
                {
                    "plugin_name": record.get("plugin_name"),
                    "severity": record.get("severity"),
                    "count": record.get("count"),
                }
            )
    except Exception:
        vulnerabilities = []

    prompt = (
        "Analyze the following security scan results and provide a concise risk summary. "
        "Focus on the most critical vulnerabilities and recommended next steps.\n"
        f"Target: {target}\n"
        f"Host ID: {host_id}\n"
        f"Vulnerabilities: {vulnerabilities[:5]}"
    )
    analysis = ask_honeybadger(prompt, model="security")

    return {
        "target": target,
        "host": host_info,
        "vulnerabilities": vulnerabilities,
        "analysis": analysis,
    }

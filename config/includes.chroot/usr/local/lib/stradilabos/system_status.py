#!/usr/bin/python3
"""Stato del sistema in sola lettura per il Benvenuto e l'hub StradiLab.

Restituisce in italiano la versione di StradilabOS, la serie di aggiornamenti
applicata e la data dell'ultimo controllo, senza privilegi e senza invocare
operazioni tecniche. È usato soltanto in lettura: il pulsante «Controlla ora»
lancia il client di aggiornamento tramite polkit, come per il Centro App.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

VERSION_FILE = Path("/usr/local/share/stradilabos/version.json")
UPDATE_SERIAL = Path("/var/lib/stradilabos/update-serial")
UPDATE_LOG = Path("/var/log/stradilabos-update.log")
TIMER_UNIT = "stradilabos-update.timer"


def read_version() -> str:
    """Versione leggibile di StradilabOS (es. 0.3.0-dev)."""
    try:
        data = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
        version = data.get("version")
        if version:
            return str(version)
    except (OSError, TypeError, json.JSONDecodeError):
        pass
    return "0.3"


def read_serial() -> str:
    """Serie di aggiornamento già applicata (stringa vuota se assente)."""
    try:
        value = UPDATE_SERIAL.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
    return re.sub(r"[^0-9]", "", value)


def _last_trigger(label: str) -> str:
    """Traduce l'epoca in secondi restituita da systemd in data locale."""
    try:
        value = int(label)
    except (TypeError, ValueError):
        return ""
    if value <= 0:
        return ""
    try:
        moment = datetime.fromtimestamp(value)
        return moment.strftime("%d/%m/%Y %H:%M")
    except (OSError, ValueError, OverflowError):
        return ""


def read_last_check() -> str:
    """Data dell'ultimo controllo aggiornamenti, o stringa vuota."""
    try:
        result = subprocess.run(
            [
                "systemctl",
                "show",
                TIMER_UNIT,
                "--property=LastTriggerUSec",
                "--value",
                "--timestamp=unix",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        result = None
    if result is not None and result.returncode == 0:
        match = re.search(r"@?(\d+)(?:\.\d+)?", result.stdout)
        if match:
            stamp = _last_trigger(match.group(1))
            if stamp:
                return stamp

    # In assenza di systemd (rarissimo) o con timer mai scattato, prova il log.
    try:
        lines = UPDATE_LOG.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    for line in reversed(lines):
        match = re.match(r"^\[(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2})\]", line)
        if match:
            date_text, time_text = match.group(1), match.group(2)
            try:
                moment = datetime.strptime(f"{date_text} {time_text}", "%Y-%m-%d %H:%M:%S")
                return moment.strftime("%d/%m/%Y %H:%M")
            except ValueError:
                return f"{date_text} {time_text}"
    return ""


def status_label() -> str:
    """Riga di stato completa, in italiano, pronta per la UI."""
    parts = [f"StradiLabOS {read_version()}"]
    serial = read_serial()
    if serial:
        parts.append(f"aggiornamenti serie {serial}")
    last = read_last_check()
    if last:
        parts.append(f"ultimo controllo {last}")
    return " · ".join(parts)

#!/usr/bin/python3
"""Salva nel sistema installato gli indirizzi scelti in Calamares."""

from __future__ import annotations

import json
from pathlib import Path

import libcalamares

ALLOWED_PROFILES = {"artistico", "musicale", "liuteria", "moda", "arredo"}
ALLOWED_DEVICE_MODES = {"personal", "shared"}


def pretty_name() -> str:
    return "Configurazione dell'indirizzo scolastico"


def pretty_status_message() -> str:
    return "Preparazione delle applicazioni per l'indirizzo scelto…"


def run():
    selected = libcalamares.globalstorage.value("packagechooser_profiles") or ""
    profiles = [
        profile.strip()
        for profile in str(selected).split(",")
        if profile.strip() in ALLOWED_PROFILES
    ]
    profiles = list(dict.fromkeys(profiles))
    if not profiles:
        return (
            "Indirizzo non selezionato",
            "Scegli almeno un indirizzo scolastico prima di continuare.",
        )

    device_mode = str(
        libcalamares.globalstorage.value("packagechooser_device") or ""
    ).strip()
    if device_mode not in ALLOWED_DEVICE_MODES:
        return (
            "Tipo di computer non selezionato",
            "Indica se il PC è personale oppure condiviso prima di continuare.",
        )

    root_mount = libcalamares.globalstorage.value("rootMountPoint")
    if not root_mount:
        return (
            "Sistema di destinazione non disponibile",
            "Non è possibile salvare il profilo StradilabOS nel nuovo sistema.",
        )

    state = {
        "schema_version": 1,
        "profiles": profiles,
        "device_mode": device_mode,
        "source": "calamares",
    }
    targets = (
        Path(str(root_mount)) / "etc/skel/.config/stradilabos/profiles.json",
        Path(str(root_mount)) / "etc/stradilabos/default-profiles.json",
    )
    try:
        for target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    except OSError as error:
        libcalamares.utils.warning(f"Cannot save StradilabOS profiles: {error}")
        return (
            "Profilo non salvato",
            "L'installazione non riesce a memorizzare l'indirizzo scelto.",
        )

    libcalamares.job.setprogress(1.0)
    return None

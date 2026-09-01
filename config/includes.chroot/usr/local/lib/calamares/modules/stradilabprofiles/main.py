#!/usr/bin/python3
"""Salva nel sistema installato ruolo, indirizzo e modalità d'uso."""

from __future__ import annotations

import json
from pathlib import Path

import libcalamares

ADDRESS_PROFILES = ("artistico", "musicale", "liuteria", "moda", "arredo")
ALLOWED_SELECTIONS = {*ADDRESS_PROFILES, "docente", "segreteria", "base"}
ALLOWED_DEVICE_MODES = {"personal", "shared"}
ALLOWED_WORKSPACE_MODES = {"first-boot", "later"}


def pretty_name() -> str:
    return "Configurazione del profilo d'uso"


def pretty_status_message() -> str:
    return "Preparazione di StradiLabOS per il profilo scelto…"


def run():
    selected = libcalamares.globalstorage.value("packagechooser_profiles") or ""
    selections = [
        value.strip()
        for value in str(selected).split(",")
        if value.strip() in ALLOWED_SELECTIONS
    ]
    if not selections:
        return (
            "Profilo d'uso non selezionato",
            "Indica se il sistema sarà usato da uno studente, un docente, "
            "dalla segreteria oppure con la sola dotazione base.",
        )

    selection = selections[0]
    if selection in ADDRESS_PROFILES:
        role = "student"
        profiles = [selection]
    elif selection == "docente":
        role = "teacher"
        profiles = list(ADDRESS_PROFILES)
    elif selection == "segreteria":
        role = "staff"
        profiles = []
    else:
        role = "base"
        profiles = []

    device_mode = str(
        libcalamares.globalstorage.value("packagechooser_device") or ""
    ).strip()
    if device_mode not in ALLOWED_DEVICE_MODES:
        return (
            "Tipo di computer non selezionato",
            "Indica se il PC è personale oppure condiviso prima di continuare.",
        )

    workspace_mode = str(
        libcalamares.globalstorage.value("packagechooser_workspace") or ""
    ).strip()
    if workspace_mode not in ALLOWED_WORKSPACE_MODES:
        return (
            "Google Workspace non configurato",
            "Scegli se accedere a Workspace al primo avvio oppure in seguito.",
        )

    root_mount = libcalamares.globalstorage.value("rootMountPoint")
    if not root_mount:
        return (
            "Sistema di destinazione non disponibile",
            "Non è possibile salvare il profilo StradiLabOS nel nuovo sistema.",
        )

    state = {
        "schema_version": 2,
        "role": role,
        "profiles": profiles,
        "device_mode": device_mode,
        "workspace_onboarding": workspace_mode,
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

        # Il programma di installazione serve solo nella sessione Live. Dopo
        # la copia sul disco i suoi launcher sarebbero inutili e confondenti.
        for relative_path in (
            "usr/share/applications/calamares.desktop",
            "usr/share/applications/calamares-install-debian.desktop",
            "usr/local/share/applications/calamares-install-debian.desktop",
            "etc/skel/Desktop/calamares.desktop",
            "etc/skel/Desktop/install-debian.desktop",
        ):
            (Path(str(root_mount)) / relative_path).unlink(missing_ok=True)
    except OSError as error:
        libcalamares.utils.warning(f"Cannot save StradilabOS profiles: {error}")
        return (
            "Profilo non salvato",
            "L'installazione non riesce a memorizzare l'indirizzo scelto.",
        )

    libcalamares.job.setprogress(1.0)
    return None

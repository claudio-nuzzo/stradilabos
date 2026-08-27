#!/usr/bin/env python3
"""Controlli statici eseguibili sia su macOS sia nella pipeline Linux."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROOT = ROOT / "config/includes.chroot"
SHARE = CHROOT / "usr/local/share/stradilabos"
APPLICATIONS = CHROOT / "usr/local/share/applications"
PACKAGE_RE = re.compile(r"^[a-z0-9][a-z0-9+.-]*$")
FLATPAK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ADDRESS_PROFILES = {"artistico", "musicale", "liuteria", "moda", "arredo"}
BRAND_COLORS = {
    "#16130f",
    "#645e55",
    "#7a9fd4",
    "#7dab7e",
    "#9b2335",
    "#c4906a",
    "#d4839f",
    "#d4a85a",
    "#ded8ce",
    "#f6f4ef",
}


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_catalog(errors: list[str]) -> None:
    catalog = json.loads((SHARE / "apps.json").read_text(encoding="utf-8"))
    apps = catalog.get("apps", [])
    require(bool(apps), "Il catalogo app è vuoto.", errors)
    ids = [app.get("id") for app in apps]
    require(len(ids) == len(set(ids)), "Il catalogo contiene ID duplicati.", errors)
    for app in apps:
        require(app.get("url", "").startswith("https://"), f"URL non HTTPS: {app}", errors)
        require(bool(app.get("title")), f"Titolo mancante: {app}", errors)
    workspace_apps = {
        "workspace-login",
        "google-classroom",
        "google-drive",
        "gmail",
        "google-meet",
        "google-calendar",
        "google-documenti",
        "google-fogli",
        "google-presentazioni",
        "google-moduli",
    }
    require(
        workspace_apps.issubset(set(ids)),
        "La dotazione Google Workspace è incompleta.",
        errors,
    )
    for app in apps:
        if app.get("id") in workspace_apps:
            require(
                app.get("icon") == "stradilabos-workspace",
                f"Icona Workspace non coordinata: {app.get('id')}",
                errors,
            )

    generated = list(APPLICATIONS.glob("stradilabos-web-*.desktop"))
    require(len(generated) == len(apps), "Numero launcher diverso dal catalogo.", errors)
    for desktop in generated:
        text = desktop.read_text(encoding="utf-8")
        require("Terminal=false" in text, f"Launcher non grafico: {desktop.name}", errors)
        require("Exec=stradilabos-open-app" in text, f"Exec non valido: {desktop.name}", errors)


def validate_packs(errors: list[str]) -> None:
    packs = json.loads((SHARE / "packs.json").read_text(encoding="utf-8"))["packs"]
    ids = [pack["id"] for pack in packs]
    require(len(ids) == len(set(ids)), "ID raccolta duplicati.", errors)
    require(ADDRESS_PROFILES.issubset(set(ids)), "Manca un indirizzo scolastico.", errors)
    included_packages: set[str] = set()
    for package_list in (ROOT / "config/package-lists").glob("*.list.chroot"):
        for line in package_list.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                included_packages.add(value)
    for pack in packs:
        require(bool(pack["packages"]), f"Raccolta vuota: {pack['id']}", errors)
        for package in pack["packages"]:
            require(bool(PACKAGE_RE.fullmatch(package)), f"Pacchetto non valido: {package}", errors)
            require(
                package in included_packages,
                f"Pacchetto {package} non incluso nella ISO ({pack['id']}).",
                errors,
            )
        for app_id in pack.get("flatpaks", []):
            require(bool(FLATPAK_RE.fullmatch(app_id)), f"Flatpak non valido: {app_id}", errors)


def validate_code(errors: list[str]) -> None:
    python_files = [
        *ROOT.glob("scripts/*.py"),
        *(CHROOT / "usr/local/lib/stradilabos").glob("*.py"),
        *(CHROOT / "usr/local/lib/calamares/modules").glob("*/main.py"),
    ]
    for path in python_files:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        require(result.returncode == 0, f"Python non valido in {path}: {result.stderr}", errors)

    shell_files = [
        *ROOT.glob("auto/*"),
        *ROOT.glob("scripts/*.sh"),
        *ROOT.glob("config/hooks/live/*.hook.chroot"),
        *(CHROOT / "usr/local/bin").glob("*"),
    ]
    for path in shell_files:
        result = subprocess.run(
            ["sh", "-n", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        require(result.returncode == 0, f"Shell non valida in {path}: {result.stderr}", errors)


def validate_branding(errors: list[str]) -> None:
    branding = CHROOT / "etc/calamares/branding/stradilabos"
    descriptor = branding / "branding.desc"
    slideshow = branding / "show.qml"
    require(descriptor.exists(), "Branding Calamares assente.", errors)
    require((branding / "stradilabos.svg").exists(), "Logo Calamares assente.", errors)
    require(slideshow.exists(), "Presentazione Calamares assente.", errors)
    if descriptor.exists():
        text = descriptor.read_text(encoding="utf-8")
        require(
            re.search(r'^slideshow:\s*["\']show\.qml["\']\s*$', text, re.MULTILINE)
            is not None,
            "Il branding Calamares non collega show.qml.",
            errors,
        )
    if slideshow.exists():
        text = slideshow.read_text(encoding="utf-8")
        require("Presentation" in text, "Presentazione Calamares non valida.", errors)
    wallpaper = CHROOT / "usr/share/backgrounds/stradilabos/stradilabos-wallpaper-v2.png"
    require(wallpaper.exists(), "Sfondo StradilabOS assente.", errors)
    theme = CHROOT / "usr/share/icons/StradiLab"
    require((theme / "index.theme").exists(), "Tema icone StradilabOS assente.", errors)
    require(
        (theme / "scalable/places/user-home.svg").exists(),
        "Icone del desktop StradilabOS assenti.",
        errors,
    )
    require(
        (CHROOT / "usr/local/share/icons/hicolor/scalable/apps/stradilabos-workspace.svg").exists(),
        "Icona Workspace StradilabOS assente.",
        errors,
    )
    branded_files = [
        *branding.glob("*.svg"),
        *branding.glob("*.qml"),
        *(CHROOT / "usr/local/share/icons/hicolor/scalable/apps").glob("*.svg"),
        *(theme / "scalable").glob("**/*.svg"),
        CHROOT / "usr/local/lib/stradilabos/welcome.py",
    ]
    for path in branded_files:
        colors = {
            color.casefold()
            for color in re.findall(r"#[0-9a-fA-F]{6}", path.read_text(encoding="utf-8"))
        }
        unknown = colors - BRAND_COLORS
        require(
            not unknown,
            f"Colori fuori palette in {path.name}: {', '.join(sorted(unknown))}",
            errors,
        )


def validate_installer(errors: list[str]) -> None:
    chooser = CHROOT / "etc/calamares/modules/stradilabos-profiles.conf"
    require(chooser.exists(), "Scelta dell'indirizzo in Calamares assente.", errors)
    if chooser.exists():
        text = chooser.read_text(encoding="utf-8")
        configured = set(re.findall(r"^\s*- id: ([a-z0-9-]+)$", text, re.MULTILINE))
        require(
            configured == ADDRESS_PROFILES,
            "Gli indirizzi di Calamares non coincidono con i profili.",
            errors,
        )
    device_chooser = CHROOT / "etc/calamares/modules/stradilabos-device.conf"
    require(device_chooser.exists(), "Scelta PC personale/condiviso assente.", errors)
    if device_chooser.exists():
        text = device_chooser.read_text(encoding="utf-8")
        modes = set(re.findall(r"^\s*- id: ([a-z0-9-]+)$", text, re.MULTILINE))
        require(modes == {"personal", "shared"}, "Modalità d'uso non valide.", errors)
    module = CHROOT / "usr/local/lib/calamares/modules/stradilabprofiles"
    require((module / "module.desc").exists(), "Modulo profili Calamares assente.", errors)
    require((module / "main.py").exists(), "Backend profili Calamares assente.", errors)
    hook = ROOT / "config/hooks/live/010-stradilabos-branding.hook.chroot"
    hook_text = hook.read_text(encoding="utf-8")
    require("packagechooser@profiles" in hook_text, "Pagina indirizzo non attivata.", errors)
    require("packagechooser@device" in hook_text, "Pagina uso del PC non attivata.", errors)
    require("stradilabprofiles" in hook_text, "Salvataggio profilo non attivato.", errors)


def main() -> int:
    errors: list[str] = []
    validate_catalog(errors)
    validate_packs(errors)
    validate_code(errors)
    validate_branding(errors)
    validate_installer(errors)
    if errors:
        print("Controlli non superati:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Controlli StradilabOS superati.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

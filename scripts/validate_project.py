#!/usr/bin/env python3
"""Controlli statici eseguibili sia su macOS sia nella pipeline Linux."""

from __future__ import annotations

import json
import os
import re
import struct
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHROOT = ROOT / "config/includes.chroot"
SHARE = CHROOT / "usr/local/share/stradilabos"
GUIDE = SHARE / "guide"
APPLICATIONS = CHROOT / "usr/local/share/applications"
PACKAGE_RE = re.compile(r"^[a-z0-9][a-z0-9+.-]*$")
FLATPAK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
ADDRESS_PROFILES = {"artistico", "musicale", "liuteria", "moda", "arredo"}
USER_PROFILE_OPTIONS = {"docente", "segreteria", "base"}
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
    "#ffffff",
    # Toni profondi dei cinque accenti, per testo e badge sull'avorio.
    "#b83864",
    "#477348",
    "#88621d",
    "#3368b5",
    "#915b33",
    # Blu navy della palette StradiLab (docs/BRAND-STRADILAB.md), usato per
    # il pannello scuro del requisito D.
    "#1b3a6b",
    "#2c4a6e",
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
    for login_id in ("workspace-login", "google-classroom"):
        login = next((app for app in apps if app.get("id") == login_id), {})
        login_url = login.get("url", "")
        require("/ServiceLogin?" in login_url, f"Accesso Workspace fragile: {login_id}", errors)
        require("hd=istitutostradivari.it" in login_url, f"Dominio assente: {login_id}", errors)
        require("hl=it" in login_url, f"Lingua italiana assente: {login_id}", errors)

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
    mapped_profiles: set[str] = set()
    included_packages: set[str] = set()
    for package_list in (ROOT / "config/package-lists").glob("*.list.chroot"):
        for line in package_list.read_text(encoding="utf-8").splitlines():
            value = line.strip()
            if value and not value.startswith("#"):
                included_packages.add(value)
    for pack in packs:
        profiles = pack.get("profiles", [pack["id"]])
        require(
            set(profiles).issubset(ADDRESS_PROFILES),
            f"Profilo non valido nella raccolta {pack['id']}.",
            errors,
        )
        mapped_profiles.update(profiles)
        require(bool(pack["packages"]), f"Raccolta vuota: {pack['id']}", errors)
        for package in pack["packages"]:
            require(bool(PACKAGE_RE.fullmatch(package)), f"Pacchetto non valido: {package}", errors)
            require(
                package not in included_packages,
                f"Pacchetto specialistico {package} incorporato nella ISO base ({pack['id']}).",
                errors,
            )
        for app_id in pack.get("flatpaks", []):
            require(bool(FLATPAK_RE.fullmatch(app_id)), f"Flatpak non valido: {app_id}", errors)
    require(
        ADDRESS_PROFILES.issubset(mapped_profiles),
        "Non tutti gli indirizzi hanno una raccolta consigliata.",
        errors,
    )

    # Le raccolte specialistiche devono essere scaricate dal Centro App e non
    # reintrodotte di nascosto da un hook di live-build.
    for hook in (ROOT / "config/hooks/live").glob("*.hook.chroot"):
        hook_text = hook.read_text(encoding="utf-8")
        require(
            "flatpak install" not in hook_text,
            f"Flatpak specialistico incorporato nella ISO base: {hook.name}",
            errors,
        )

    fashion_launcher = APPLICATIONS / "stradilabos-cad-moda.desktop"
    require(fashion_launcher.exists(), "Launcher CAD Moda assente.", errors)
    if fashion_launcher.exists():
        require(
            "NoDisplay=true" in fashion_launcher.read_text(encoding="utf-8"),
            "Il CAD Moda appare prima di essere installato.",
            errors,
        )
    backend = (CHROOT / "usr/local/lib/stradilabos/install_pack.py").read_text(
        encoding="utf-8"
    )
    require(
        "FLATPAK_LAUNCHERS" in backend
        and 'replace("\\nNoDisplay=true\\n", "\\n")' in backend,
        "Il Centro App non rende visibile il CAD Moda dopo l'installazione.",
        errors,
    )


def validate_guides(errors: list[str]) -> None:
    """Verifica che le guide offline restino navigabili e coprano le app GUI."""
    index = GUIDE / "index.html"
    require(index.exists(), "Indice delle guide assente.", errors)
    if index.exists():
        index_text = index.read_text(encoding="utf-8")
        require("['<section" not in index_text, "Indice guide con una lista Python visibile.", errors)
        for section in (
            "base",
            "artistico",
            "scenografia",
            "video",
            "musicale",
            "liuteria",
            "moda",
            "arredo",
            "accessibilita",
        ):
            require(
                f'id="{section}"' in index_text,
                f"Sezione guide assente: {section}.",
                errors,
            )

    # I due pacchetti seguenti non espongono un'app grafica autonoma: sono
    # rispettivamente una banca suoni e il motore di sintesi usato da Orca.
    aliases = {"musescore3": "musescore", "io.seamly.seamly2d": "seamly2d"}
    technical = {"fluid-soundfont-gm", "espeak-ng"}
    packs = json.loads((SHARE / "packs.json").read_text(encoding="utf-8"))["packs"]
    expected = {
        aliases.get(name, name)
        for pack in packs
        for name in [*pack["packages"], *pack.get("flatpaks", [])]
        if name not in technical
    }
    for app_id in expected:
        path = GUIDE / f"{app_id}.html"
        require(path.exists(), f"Guida mancante per l'app: {app_id}.", errors)
        if path.exists():
            text = path.read_text(encoding="utf-8")
            for heading in (
                "A cosa serve a scuola",
                "Come si apre",
                "I primi 5 passi",
                "Tre problemi comuni",
                "Per imparare di più",
            ):
                require(heading in text, f"Formato incompleto nella guida {app_id}: {heading}.", errors)


def validate_updates(errors: list[str]) -> None:
    """Il canale deve aggiornare anche un PC già installato, senza una ISO."""
    client = CHROOT / "usr/local/bin/stradilabos-update"
    mirror = ROOT / "updates/stradilabos-update"
    require(client.exists() and mirror.exists(), "Client aggiornamenti o copia canale assente.", errors)
    if client.exists() and mirror.exists():
        require(
            client.read_text(encoding="utf-8") == mirror.read_text(encoding="utf-8"),
            "Client aggiornamenti e copia nel canale non sono identici.",
            errors,
        )
    version = ROOT / "updates/version.txt"
    require(version.read_text(encoding="utf-8").strip().isdigit(), "Serie aggiornamenti non numerica.", errors)
    require(
        version.read_text(encoding="utf-8").strip() == "6",
        "La configurazione guidata di Google Chrome deve essere pubblicata nella serie 6.",
        errors,
    )
    payload = ROOT / "updates/update.sh"
    require(payload.exists(), "Payload aggiornamenti assente.", errors)
    if payload.exists():
        text = payload.read_text(encoding="utf-8")
        for fragment in (
            "sync_0_3_interface",
            "repair_existing_panel_profiles",
            "stradilabos-repair-panel --force",
            "runuser",
            "SOURCE_ARCHIVE_URL",
            "install_security_updates",
            "usr/share/grub/themes/stradilabos",
            "update-grub",
            "xfce4-power-manager-plugins",
            "xfce4-pulseaudio-plugin",
            "stradilabos-wallpaper-contrast --once",
            "usr/share/backgrounds/stradilabos",
            "stradilabos-install-chrome",
            "nessuna reinstallazione necessaria",
        ):
            require(fragment in text, f"Payload cumulativo incompleto: {fragment}.", errors)
    update_ui = CHROOT / "usr/local/bin/stradilabos-update-ui"
    update_desktop = CHROOT / "usr/local/share/applications/stradilabos-update.desktop"
    require(update_ui.exists(), "Interfaccia grafica degli aggiornamenti assente.", errors)
    require(os.access(update_ui, os.X_OK), "Interfaccia aggiornamenti non eseguibile.", errors)
    require(update_desktop.exists(), "Voce Aggiornamenti nel menu principale assente.", errors)
    if update_desktop.exists():
        desktop_text = update_desktop.read_text(encoding="utf-8")
        require(
            "Name=Aggiornamenti StradiLabOS" in desktop_text
            and "Exec=stradilabos-update-ui" in desktop_text,
            "Voce Aggiornamenti nel menu non valida.",
            errors,
        )


def validate_code(errors: list[str]) -> None:
    python_files = [
        *ROOT.glob("scripts/*.py"),
        *(CHROOT / "usr/local/lib/stradilabos").glob("*.py"),
        *(CHROOT / "usr/local/lib/calamares/modules").glob("*/main.py"),
    ]
    local_commands = [
        path for path in (CHROOT / "usr/local/bin").glob("*") if path.is_file()
    ]
    for path in local_commands:
        require(
            os.access(path, os.X_OK),
            f"Comando installato senza permesso di esecuzione: {path}.",
            errors,
        )
        try:
            with path.open(encoding="utf-8") as command_file:
                first_line = command_file.readline()
        except (OSError, UnicodeDecodeError) as error:
            errors.append(f"Comando non leggibile in {path}: {error}")
            continue
        if first_line.startswith("#!") and "python" in first_line:
            python_files.append(path)
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
        *ROOT.glob("config/hooks/live/*.hook.*"),
        *[
            path
            for path in local_commands
            if path not in python_files
        ],
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
        app_icon_names = re.findall(r'appIcons \+ "([^"]+)"', text)
        theme_icon_names = re.findall(r'themeIcons \+ "([^"]+)"', text)
        for name in app_icon_names:
            require(
                (CHROOT / "usr/local/share/icons/hicolor/scalable/apps" / name).exists(),
                f"Icona della presentazione assente: {name}",
                errors,
            )
        for name in theme_icon_names:
            require(
                (CHROOT / "usr/share/icons/StradiLab/scalable" / name).exists(),
                f"Icona del tema assente nella presentazione: {name}",
                errors,
            )
    wallpaper = CHROOT / "usr/share/backgrounds/stradilabos/stradilabos-wallpaper-v3.png"
    require(wallpaper.exists(), "Sfondo StradilabOS assente.", errors)
    for visible_name, target in (
        ("StradiLabOS-Crema.png", "stradilabos-wallpaper-v2.png"),
        ("StradiLabOS-Onde.png", "stradilabos-wallpaper-v3.png"),
    ):
        alias = wallpaper.parent / visible_name
        require(
            alias.is_symlink() and os.readlink(alias) == target,
            f"Nome visibile dello sfondo non valido: {visible_name}.",
            errors,
        )
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
    brand_icons = {
        "stradilabos.svg",
        "stradilabos-app-center.svg",
        "stradilabos-workspace.svg",
        "stradilabos-guide.svg",
        "stradilabos-welcome.svg",
        "stradilabos-scuola.svg",
        "stradilabos-orientamento.svg",
        "stradilabos-update.svg",
    }
    brand_icon_dir = CHROOT / "usr/local/share/icons/hicolor/scalable/apps"
    icon_contents = []
    for name in brand_icons:
        path = brand_icon_dir / name
        require(path.exists(), f"Icona StradiLab assente: {name}", errors)
        if path.exists():
            icon_contents.append(path.read_text(encoding="utf-8"))
    require(
        len(icon_contents) == len(set(icon_contents)),
        "Le icone principali StradiLab non sono visivamente differenziate.",
        errors,
    )
    branded_files = [
        *branding.glob("*.svg"),
        *branding.glob("*.qml"),
        *(CHROOT / "usr/local/share/icons/hicolor/scalable/apps").glob("*.svg"),
        *(theme / "scalable").glob("**/*.svg"),
        CHROOT / "usr/local/lib/stradilabos/welcome.py",
        CHROOT / "usr/local/lib/stradilabos/hub.py",
        CHROOT / "usr/local/lib/stradilabos/app_center.py",
        CHROOT / "etc/skel/.config/gtk-3.0/gtk.css",
        CHROOT / "etc/xdg/gtk-3.0/gtk.css",
        CHROOT / "etc/skel/.config/gtk-4.0/gtk.css",
        CHROOT / "etc/xdg/gtk-4.0/gtk.css",
    ]
    for version in ("3.0", "4.0"):
        require(
            (CHROOT / f"etc/skel/.config/gtk-{version}/gtk.css").read_text(encoding="utf-8")
            == (CHROOT / f"etc/xdg/gtk-{version}/gtk.css").read_text(encoding="utf-8"),
            f"gtk.css di skel e di /etc/xdg divergono (GTK {version}).",
            errors,
        )
    focus_css = (CHROOT / "etc/skel/.config/gtk-3.0/gtk.css").read_text(encoding="utf-8")
    require(
        "outline-color: #9b2335" in focus_css and "#7a9fd4" not in focus_css,
        "L'anello di fuoco deve essere bordeaux: il blu ha contrasto 2,5:1 sull'avorio.",
        errors,
    )
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
            configured == ADDRESS_PROFILES | USER_PROFILE_OPTIONS,
            "I profili d'uso di Calamares sono incompleti.",
            errors,
        )
        require("mode: required" in text, "La scelta del profilo deve essere singola.", errors)
    device_chooser = CHROOT / "etc/calamares/modules/stradilabos-device.conf"
    require(device_chooser.exists(), "Scelta PC personale/condiviso assente.", errors)
    if device_chooser.exists():
        text = device_chooser.read_text(encoding="utf-8")
        modes = set(re.findall(r"^\s*- id: ([a-z0-9-]+)$", text, re.MULTILINE))
        require(modes == {"personal", "shared"}, "Modalità d'uso non valide.", errors)
    workspace_chooser = CHROOT / "etc/calamares/modules/stradilabos-workspace.conf"
    require(workspace_chooser.exists(), "Scelta Google Workspace assente.", errors)
    if workspace_chooser.exists():
        text = workspace_chooser.read_text(encoding="utf-8")
        modes = set(re.findall(r"^\s*- id: ([a-z0-9-]+)$", text, re.MULTILINE))
        require(
            modes == {"first-boot", "later"},
            "Modalità Google Workspace non valide.",
            errors,
        )
        require(
            "@istitutostradivari.it" in text,
            "Il dominio Workspace non è indicato nell'installatore.",
            errors,
        )
    module = CHROOT / "usr/local/lib/calamares/modules/stradilabprofiles"
    require((module / "module.desc").exists(), "Modulo profili Calamares assente.", errors)
    require((module / "main.py").exists(), "Backend profili Calamares assente.", errors)
    hook = ROOT / "config/hooks/live/010-stradilabos-branding.hook.chroot"
    hook_text = hook.read_text(encoding="utf-8")
    require("packagechooser@profiles" in hook_text, "Pagina indirizzo non attivata.", errors)
    require("packagechooser@device" in hook_text, "Pagina uso del PC non attivata.", errors)
    require("packagechooser@workspace" in hook_text, "Pagina Workspace non attivata.", errors)
    require("stradilabprofiles" in hook_text, "Salvataggio profilo non attivato.", errors)
    backend_text = (module / "main.py").read_text(encoding="utf-8")
    for launcher in (
        "usr/share/applications/calamares.desktop",
        "usr/share/applications/calamares-install-debian.desktop",
        "usr/local/share/applications/calamares-install-debian.desktop",
    ):
        require(
            launcher in backend_text,
            f"Il launcher dell'installatore resta sul sistema: {launcher}",
            errors,
        )


def png_size(path: Path) -> tuple[int, int] | None:
    try:
        header = path.read_bytes()[:24]
    except OSError:
        return None
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return struct.unpack(">II", header[16:24])


def validate_system_branding(errors: list[str]) -> None:
    os_release = CHROOT / "usr/lib/os-release"
    require(os_release.exists(), "Identità StradilabOS in os-release assente.", errors)
    if os_release.exists():
        text = os_release.read_text(encoding="utf-8")
        require('NAME="StradiLabOS"' in text, "Nome OS non personalizzato.", errors)
        require('ID=stradilabos' in text, "ID OS non personalizzato.", errors)
        require('ID_LIKE=debian' in text, "Compatibilità Debian non dichiarata.", errors)

    boot_image = ROOT / "config/branding/stradilabos-boot-800x600.png"
    require(
        png_size(boot_image) == (800, 600),
        "Sfondo di avvio GRUB assente o non 800×600.",
        errors,
    )
    binary_hook = ROOT / "config/hooks/live/090-stradilabos-binary-branding.hook.binary"
    require(binary_hook.exists(), "Hook di branding della ISO assente.", errors)
    if binary_hook.exists():
        text = binary_hook.read_text(encoding="utf-8")
        require("Prova StradiLabOS" in text, "Menu Live non rinominato.", errors)
        require("StradiLabOS 0.3" in text, "Metadati ISO non personalizzati.", errors)
    live_theme = ROOT / "config/branding/grub-live-theme.txt"
    require(live_theme.exists(), "Tema del menu Live assente.", errors)
    if live_theme.exists():
        text = live_theme.read_text(encoding="utf-8")
        require(not re.search(r"@[A-Z0-9_]+@", text), "Tema Live con segnaposto irrisolti.", errors)

    plymouth = CHROOT / "usr/share/plymouth/themes/stradilabos"
    require((plymouth / "stradilabos.plymouth").exists(), "Tema Plymouth assente.", errors)
    require((plymouth / "stradilabos.script").exists(), "Script Plymouth assente.", errors)
    require(png_size(plymouth / "background.png") == (1280, 720), "Sfondo Plymouth non valido.", errors)
    require(png_size(plymouth / "logo.png") is not None, "Logo Plymouth non valido.", errors)
    if (plymouth / "stradilabos.script").exists():
        text = (plymouth / "stradilabos.script").read_text(encoding="utf-8")
        for callback in (
            "SetMessageFunction",
            "SetDisplayPasswordFunction",
            "SetDisplayQuestionFunction",
            "SetDisplayNormalFunction",
        ):
            require(callback in text, f"Plymouth non gestisce {callback}.", errors)

    greeter = CHROOT / "etc/lightdm/lightdm-gtk-greeter.conf.d/60-stradilabos.conf"
    require(greeter.exists(), "Branding della schermata di accesso assente.", errors)
    if greeter.exists():
        greeter_text = greeter.read_text(encoding="utf-8")
        require(
            "stradilabos-wallpaper-v3.png" in greeter_text,
            "Sfondo StradilabOS non applicato alla schermata di accesso.",
            errors,
        )
        require(
            "theme-name=StradiLab" in greeter_text,
            "Schermata di accesso fuori dal tema StradiLab.",
            errors,
        )

    lightdm_hardware = (
        CHROOT / "etc/lightdm/lightdm.conf.d/50-stradilabos-hardware.conf"
    )
    require(
        lightdm_hardware.exists(),
        "Compatibilità LightDM con GPU virtuali e datate assente.",
        errors,
    )
    if lightdm_hardware.exists():
        text = lightdm_hardware.read_text(encoding="utf-8")
        require(
            re.search(r"^\s*logind-check-graphical\s*=\s*false\s*$", text, re.MULTILINE)
            is not None,
            "LightDM può restare bloccato in attesa di CanGraphical.",
            errors,
        )

    panel_paths = (
        CHROOT / "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml",
        CHROOT / "etc/xdg/xfce4/panel/default.xml",
    )
    for panel in panel_paths:
        require(panel.exists(), f"Pannello Xfce StradilabOS assente: {panel}.", errors)
        if not panel.exists():
            continue
        try:
            root = ET.parse(panel).getroot()
        except ET.ParseError as error:
            errors.append(f"Pannello Xfce non valido: {error}")
            continue
        panels = root.find("./property[@name='panels']")
        plugins = root.find("./property[@name='plugins']")
        require(panels is not None, f"Elenco pannelli assente: {panel}.", errors)
        require(plugins is not None, f"Elenco plugin assente: {panel}.", errors)
        if panels is None or plugins is None:
            continue

        children = list(panels)
        panel_ids = [
            child.get("value")
            for child in children
            if child.tag == "value" and child.get("type") == "int"
        ]
        require(panel_ids == ["1"], f"Serve una sola barra applicazioni: {panel}.", errors)
        value_positions = [index for index, child in enumerate(children) if child.tag == "value"]
        definition_positions = [
            index
            for index, child in enumerate(children)
            if child.tag == "property" and child.get("name", "").startswith("panel-")
        ]
        require(
            bool(value_positions and definition_positions)
            and max(value_positions) < min(definition_positions),
            f"Gli ID dei pannelli non precedono le definizioni (errore plugin null): {panel}.",
            errors,
        )
        plugin_definitions = {
            child.get("name"): child.get("value")
            for child in plugins
            if child.tag == "property"
        }
        required_plugins = {
            "whiskermenu",
            "tasklist",
            "separator",
            "systray",
            "notification-plugin",
            "power-manager-plugin",
            "pulseaudio",
            "clock",
            "actions",
        }
        require(
            required_plugins.issubset(set(plugin_definitions.values())),
            f"Controlli nativi della barra incompleti: {panel}.",
            errors,
        )
        for panel_id in panel_ids:
            definition = panels.find(f"./property[@name='panel-{panel_id}']")
            require(definition is not None, f"Definizione panel-{panel_id} assente: {panel}.", errors)
            if definition is None:
                continue
            plugin_ids = definition.find("./property[@name='plugin-ids']")
            require(plugin_ids is not None, f"Plugin di panel-{panel_id} assenti: {panel}.", errors)
            if plugin_ids is None:
                continue
            position = definition.find("./property[@name='position']")
            require(
                position is not None and position.get("value", "").startswith("p=12;"),
                f"La barra non è ancorata in basso: {panel}.",
                errors,
            )
            for value in plugin_ids.findall("./value"):
                plugin_id = value.get("value")
                require(
                    bool(plugin_definitions.get(f"plugin-{plugin_id}")),
                    f"Plugin {plugin_id} senza nome in panel-{panel_id}: {panel}.",
                    errors,
                )
        actions = plugins.find("./property[@name='plugin-13']")
        action_items = (
            {value.get("value") for value in actions.findall("./property[@name='items']/value")}
            if actions is not None
            else set()
        )
        for action in (
            "+lock-screen",
            "+switch-user",
            "+restart",
            "+shutdown",
            "+logout-dialog",
        ):
            require(action in action_items, f"Azione di sessione assente ({action}): {panel}.", errors)

    panel = panel_paths[0]
    if panel.exists():
        text = panel.read_text(encoding="utf-8")
        require("stradilabos-workspace.desktop" in text, "Workspace non è nel pannello.", errors)
        require("xfce4-terminal" not in text, "Il terminale compare nel pannello utente.", errors)
        launcher_names = re.findall(r'value="([^"]+\.desktop)"', text)
        for launcher_name in launcher_names:
            matches = list((CHROOT / "etc/skel/.config/xfce4/panel").glob(f"launcher-*/{launcher_name}"))
            require(bool(matches), f"Launcher del pannello assente: {launcher_name}", errors)
            for launcher in matches:
                launcher_text = launcher.read_text(encoding="utf-8")
                require("Terminal=false" in launcher_text, f"Launcher non grafico: {launcher_name}", errors)
                require(
                    re.search(r"(?<!%)%(?!%)", launcher_text) is None,
                    f"Percentuale non protetta nel launcher: {launcher_name}",
                    errors,
                )

    panel_repair = CHROOT / "usr/local/bin/stradilabos-repair-panel"
    require(panel_repair.exists(), "Riparazione automatica dei pannelli assente.", errors)
    require(os.access(panel_repair, os.X_OK), "Riparazione pannelli non eseguibile.", errors)
    panel_autostart = CHROOT / "etc/xdg/autostart/stradilabos-repair-panel.desktop"
    require(panel_autostart.exists(), "Avvio della riparazione pannelli assente.", errors)
    if panel_autostart.exists():
        require(
            "Exec=stradilabos-repair-panel" in panel_autostart.read_text(encoding="utf-8"),
            "Autostart della riparazione pannelli errato.",
            errors,
        )

    contrast = CHROOT / "usr/local/bin/stradilabos-wallpaper-contrast"
    contrast_autostart = CHROOT / "etc/xdg/autostart/stradilabos-wallpaper-contrast.desktop"
    require(contrast.exists(), "Contrasto automatico dello sfondo assente.", errors)
    require(os.access(contrast, os.X_OK), "Contrasto automatico non eseguibile.", errors)
    require(contrast_autostart.exists(), "Avvio del contrasto automatico assente.", errors)
    if contrast.exists():
        contrast_text = contrast.read_text(encoding="utf-8")
        for fragment in ("relative_luminance", "light-wallpaper", "dark-wallpaper", "XfdesktopIconView.view"):
            require(fragment in contrast_text, f"Contrasto automatico incompleto: {fragment}.", errors)

    live_config = CHROOT / "etc/live/config.conf.d/stradilabos.conf"
    require(live_config.exists(), "Nome utente Live personalizzato assente.", errors)
    if live_config.exists():
        text = live_config.read_text(encoding="utf-8")
        require(
            'LIVE_USER_FULLNAME="StradiLabOS Live"' in text,
            "Nome completo dell'utente Live non personalizzato.",
            errors,
        )

    grub_config = CHROOT / "etc/default/grub.d/60-stradilabos.cfg"
    require(grub_config.exists(), "Configurazione GRUB installata assente.", errors)
    if grub_config.exists():
        text = grub_config.read_text(encoding="utf-8")
        require('GRUB_DISTRIBUTOR="StradiLabOS"' in text, "GRUB conserva il nome Debian.", errors)
        require(
            'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=3"' in text,
            "Avvio grafico o filtro dei messaggi firmware non configurato in GRUB.",
            errors,
        )
    grub_theme = CHROOT / "usr/share/grub/themes/stradilabos/theme.txt"
    require(grub_theme.exists(), "Tema GRUB installato assente.", errors)
    if grub_theme.exists():
        require(
            'terminal-box: "0"' not in grub_theme.read_text(encoding="utf-8"),
            "Il tema GRUB contiene ancora il pattern pixmap non valido.",
            errors,
        )
    require(
        "quiet splash loglevel=3" in (ROOT / "auto/config").read_text(encoding="utf-8"),
        "Il menu Live non filtra i messaggi ACPI non critici.",
        errors,
    )

    policy = CHROOT / "etc/chromium/policies/managed/stradilabos-workspace.json"
    require(policy.exists(), "Criterio Workspace del browser assente.", errors)
    if policy.exists():
        try:
            data = json.loads(policy.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            errors.append(f"Criterio Chromium non valido: {error}")
        else:
            require(
                data.get("AllowedDomainsForApps") == "istitutostradivari.it",
                "Il browser non limita Workspace al dominio scolastico.",
                errors,
            )
            require(
                data.get("TranslateEnabled") is False,
                "Il popup automatico di traduzione non è disattivato.",
                errors,
            )
            require(
                data.get("PasswordManagerEnabled") is False,
                "Il browser può salvare password senza un portachiavi cifrato.",
                errors,
            )

    opener = CHROOT / "usr/local/bin/stradilabos-open-app"
    require(
        "--password-store=basic" in opener.read_text(encoding="utf-8"),
        "Le web app possono aprire una richiesta tecnica del portachiavi.",
        errors,
    )

    welcome = CHROOT / "usr/local/lib/stradilabos/welcome.py"
    welcome_text = welcome.read_text(encoding="utf-8")
    require("GTK_ARGV" in welcome_text, "Le opzioni del Benvenuto arrivano ancora a GTK.", errors)
    require("AUTOSTART_MODE" in welcome_text, "L'avvio iniziale non è controllabile.", errors)
    require("Gtk.PolicyType.ALWAYS" in welcome_text, "La lista degli indirizzi non mostra lo scorrimento.", errors)
    require("monitor.get_workarea()" in welcome_text, "Il Benvenuto ignora l'area utile dello schermo.", errors)
    require("set_vhomogeneous(False)" in welcome_text, "Le pagine del Benvenuto impongono ancora l'altezza massima.", errors)
    require("home_scroller" in welcome_text, "Il Benvenuto non scorre sugli schermi piccoli.", errors)
    require("profile_scroller" in welcome_text, "La scelta profilo non scorre sugli schermi piccoli.", errors)
    require("stradilabos-wifi" in welcome_text, "Il Benvenuto apre ancora l'editor Wi-Fi tecnico.", errors)
    require("2 · Scarica Chrome e accedi" in welcome_text, "Installazione Chrome assente dal Benvenuto.", errors)
    require("Attiva la sincronizzazione" in welcome_text, "Guida alla sincronizzazione Chrome assente.", errors)
    require("CHROME_SETUP_DONE.exists()" in welcome_text, "Il Benvenuto conferma Chrome senza verifica utente.", errors)
    chrome_installer = CHROOT / "usr/local/bin/stradilabos-install-chrome"
    require(chrome_installer.exists(), "Installatore guidato di Google Chrome assente.", errors)
    require(os.access(chrome_installer, os.X_OK), "Installatore Google Chrome non eseguibile.", errors)
    if chrome_installer.exists():
        chrome_installer_text = chrome_installer.read_text(encoding="utf-8")
        for fragment in ("amd64", "arm64", "dl.google.com", "dpkg-deb", "apt-get install"):
            require(fragment in chrome_installer_text, f"Installatore Chrome incompleto: {fragment}.", errors)
    wifi = CHROOT / "usr/local/bin/stradilabos-wifi"
    require(wifi.exists(), "Selettore Wi-Fi StradiLabOS assente.", errors)
    require(os.access(wifi, os.X_OK), "Selettore Wi-Fi StradiLabOS non eseguibile.", errors)

    app_center_text = (CHROOT / "usr/local/lib/stradilabos/app_center.py").read_text(
        encoding="utf-8"
    )
    require("APP_CENTER_CSS" in app_center_text, "Centro App non coordinato al brand.", errors)
    require("#9b2335" in app_center_text, "Palette StradiLab assente dal Centro App.", errors)
    require("code == 126" in app_center_text, "Annullare la password appare come errore.", errors)
    require("Operazione annullata" in app_center_text, "Messaggio di annullamento assente.", errors)

    polkit_policy = CHROOT / "usr/share/polkit-1/actions/org.stradilab.stradilabos.policy"
    require(polkit_policy.exists(), "Descrizione grafica dell'autorizzazione assente.", errors)
    if polkit_policy.exists():
        try:
            ET.parse(polkit_policy)
        except ET.ParseError as error:
            errors.append(f"PolicyKit non valido: {error}")
        policy_text = polkit_policy.read_text(encoding="utf-8")
        require(
            "org.freedesktop.policykit.exec.path" in policy_text,
            "Il Centro App non usa la propria richiesta di autorizzazione.",
            errors,
        )
        require(
            "/usr/local/bin/stradilabos-install-chrome" in policy_text,
            "Installazione Chrome priva di autorizzazione PolicyKit dedicata.",
            errors,
        )

    tmpfiles = CHROOT / "usr/lib/tmpfiles.d/stradilabos-lightdm.conf"
    require(tmpfiles.exists(), "Creazione persistente della directory LightDM assente.", errors)

    theme_script = CHROOT / "usr/local/bin/stradilabos-apply-theme"
    theme_text = theme_script.read_text(encoding="utf-8")
    for fragment in (
        "xrandr --query",
        "monitor$output",
        "/general/button_layout",
        "/general/borderless_maximize",
        "/general/titleless_maximize",
    ):
        require(fragment in theme_text, f"Tema dinamico incompleto: {fragment}", errors)

    wm_guard = CHROOT / "usr/local/bin/stradilabos-window-manager-guard"
    require(wm_guard.exists(), "Guardia del gestore delle finestre assente.", errors)
    if wm_guard.exists():
        require(
            os.access(wm_guard, os.X_OK),
            "Guardia del gestore delle finestre non eseguibile.",
            errors,
        )
        guard_text = wm_guard.read_text(encoding="utf-8")
        for fragment in (
            "--vblank=off",
            "--compositor=off",
            "Greybird",
            "max_attempts=3",
            "logger -t",
            "inizializzazione preventiva di xfwm4",
            "disable_compositing",
            "/general/use_compositing",
        ):
            require(fragment in guard_text, f"Guardia finestre incompleta: {fragment}", errors)
    wm_autostart = CHROOT / "etc/xdg/autostart/stradilabos-window-manager.desktop"
    require(wm_autostart.exists(), "Avvio automatico della guardia finestre assente.", errors)
    if wm_autostart.exists():
        autostart_text = wm_autostart.read_text(encoding="utf-8")
        require(
            "Exec=stradilabos-window-manager-guard" in autostart_text,
            "La guardia finestre non viene avviata dalla sessione.",
            errors,
        )
        require("OnlyShowIn=XFCE;" in autostart_text, "Guardia finestre non limitata a Xfce.", errors)
    wm_diagnostics = CHROOT / "usr/local/bin/stradilabos-window-diagnostics"
    require(wm_diagnostics.exists(), "Diagnostica finestre assente.", errors)
    wm_test = ROOT / "scripts/test_window_manager_xvfb.sh"
    require(wm_test.exists(), "Prova runtime del gestore delle finestre assente.", errors)

    window_theme = ROOT / "config/hooks/live/012-stradilabos-window-theme.hook.chroot"
    require(window_theme.exists(), "Tema finestre StradiLab assente.", errors)
    if window_theme.exists():
        text = window_theme.read_text(encoding="utf-8")
        require("/usr/share/themes/StradiLab" in text, "Tema finestre non installato.", errors)
        require("active_color_1" in text, "Accento bordeaux delle finestre assente.", errors)
        require(
            "WhiteSur-Light" in text and "WhiteSur-Dark" in text,
            "Il tema WhiteSur non riceve le regole StradiLab al build.",
            errors,
        )

    for variant in ("WhiteSur-Light", "WhiteSur-Dark"):
        theme = CHROOT / "usr/share/themes" / variant
        require((theme / "index.theme").exists(), f"Tema {variant} assente.", errors)
        require((theme / "xfwm4/themerc").exists(), f"Tema xfwm4 {variant} assente.", errors)
        require((theme / "LICENSE.WhiteSur").exists(), f"Licenza {variant} assente.", errors)
    whitesur_icons = CHROOT / "usr/share/icons/WhiteSur"
    require((whitesur_icons / "index.theme").exists(), "Tema icone WhiteSur assente.", errors)
    if (whitesur_icons / "index.theme").exists():
        icons_text = (whitesur_icons / "index.theme").read_text(encoding="utf-8")
        require("Inherits=StradiLab," in icons_text, "WhiteSur non eredita le icone StradiLab.", errors)
    require((whitesur_icons / "COPYING").exists(), "Licenza WhiteSur Icon Theme assente.", errors)

    for relative in (
        "etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml",
        "etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml",
        "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml",
        "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml",
    ):
        path = CHROOT / relative
        try:
            ET.parse(path)
        except ET.ParseError as error:
            errors.append(f"Configurazione tema non valida ({relative}): {error}")
        text = path.read_text(encoding="utf-8")
        require('value="WhiteSur-Light"' in text, f"Tema WhiteSur non scelto: {relative}", errors)
    for relative in (
        "etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml",
        "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xsettings.xml",
    ):
        text = (CHROOT / relative).read_text(encoding="utf-8")
        require('value="WhiteSur"' in text, f"Icone WhiteSur non scelte: {relative}", errors)
    xfwm_defaults = (
        CHROOT
        / "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml"
    ).read_text(encoding="utf-8")
    require('name="borderless_maximize" type="bool" value="false"' in xfwm_defaults,
            "Le finestre massimizzate possono perdere i bordi.", errors)
    require('name="titleless_maximize" type="bool" value="false"' in xfwm_defaults,
            "Le finestre massimizzate possono perdere il titolo.", errors)
    require('name="use_compositing" type="bool" value="false"' in xfwm_defaults,
            "Il compositore di xfwm4 può riattivarsi anche se la guardia lo spegne.", errors)
    require('name="button_layout" type="string" value="CHM|O"' in xfwm_defaults,
            "I controlli semaforo non sono a sinistra.", errors)

    branding_hook = ROOT / "config/hooks/live/010-stradilabos-branding.hook.chroot"
    branding_text = branding_hook.read_text(encoding="utf-8")
    for launcher in (
        "xfce4-terminal.desktop",
        "xfce4-terminal-settings.desktop",
        "xfce4-terminal-emulator.desktop",
    ):
        require(launcher in branding_text, f"Voce terminale non nascosta: {launcher}", errors)

    packages = (ROOT / "config/package-lists/stradilabos-core.list.chroot").read_text(
        encoding="utf-8"
    )
    for package in (
        "lightdm-gtk-greeter",
        "plymouth",
        "plymouth-themes",
        "plymouth-label",
        "greybird-gtk-theme",
        "mate-polkit",
        "usbutils",
        "xfce4-terminal",
        "x11-utils",
        "libnotify-bin",
        "xfce4-power-manager-plugins",
        "xfce4-pulseaudio-plugin",
    ):
        require(
            re.search(rf"^{re.escape(package)}$", packages, re.MULTILINE) is not None,
            f"Pacchetto grafico obbligatorio assente: {package}.",
            errors,
        )
    for forbidden in (
        "task-xfce-desktop",
        "task-italian",
        "task-italian-desktop",
        "libreoffice",
        "gnome-software",
        "gnome-software-plugin-flatpak",
        "firmware-linux",
        "firmware-misc-nonfree",
    ):
        require(
            re.search(rf"^{re.escape(forbidden)}$", packages, re.MULTILINE) is None,
            f"Metapacchetto pesante ancora nella base: {forbidden}.",
            errors,
        )


def main() -> int:
    errors: list[str] = []
    validate_catalog(errors)
    validate_packs(errors)
    validate_guides(errors)
    validate_updates(errors)
    validate_code(errors)
    validate_branding(errors)
    validate_installer(errors)
    validate_system_branding(errors)
    if errors:
        print("Controlli non superati:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("Controlli StradiLabOS superati.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

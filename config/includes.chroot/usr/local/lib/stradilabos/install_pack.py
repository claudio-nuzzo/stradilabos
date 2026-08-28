#!/usr/bin/python3
"""Backend privilegiato del Centro App StradilabOS."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

CATALOG = Path("/usr/local/share/stradilabos/packs.json")
SAFE_PACKAGE = re.compile(r"^[a-z0-9][a-z0-9+.-]*$")
SAFE_FLATPAK = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
FLATPAK_LAUNCHERS = {
    "io.seamly.seamly2d": Path(
        "/usr/local/share/applications/stradilabos-cad-moda.desktop"
    ),
}


def fail(message: str, code: int = 2) -> int:
    print(message, file=sys.stderr, flush=True)
    return code


def main(argv: list[str]) -> int:
    if os.geteuid() != 0:
        return fail("Questa operazione richiede l'autorizzazione di amministratore.")
    if not argv:
        return fail("Nessun pacchetto didattico selezionato.")

    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    known = {pack["id"]: pack for pack in data["packs"]}
    unknown = [pack_id for pack_id in argv if pack_id not in known]
    if unknown:
        return fail("Selezione non riconosciuta: " + ", ".join(unknown))

    packages: list[str] = []
    flatpaks: list[str] = []
    for pack_id in argv:
        packages.extend(known[pack_id]["packages"])
        flatpaks.extend(known[pack_id].get("flatpaks", []))
    packages = sorted(set(packages))
    flatpaks = sorted(set(flatpaks))

    if not packages and not flatpaks:
        return fail("La raccolta selezionata è vuota.")
    if any(not SAFE_PACKAGE.fullmatch(name) for name in packages):
        return fail("Il catalogo contiene un nome di pacchetto non valido.")
    if any(not SAFE_FLATPAK.fullmatch(name) for name in flatpaks):
        return fail("Il catalogo contiene un identificativo Flatpak non valido.")

    env = os.environ.copy()
    env["DEBIAN_FRONTEND"] = "noninteractive"
    print("Aggiornamento del catalogo software…", flush=True)
    update = subprocess.run(["apt-get", "update"], env=env, check=False)
    if update.returncode:
        return fail(
            "Impossibile aggiornare il catalogo. Controlla la connessione Internet.",
            update.returncode,
        )

    if packages:
        print("Installazione delle applicazioni Debian…", flush=True)
        install = subprocess.run(
            ["apt-get", "install", "--yes", "--no-install-recommends", *packages],
            env=env,
            check=False,
        )
        if install.returncode:
            return fail("Installazione Debian non completata.", install.returncode)

    if flatpaks:
        print("Installazione delle applicazioni specialistiche…", flush=True)
        remote = subprocess.run(
            [
                "flatpak",
                "remote-add",
                "--system",
                "--if-not-exists",
                "flathub",
                "https://dl.flathub.org/repo/flathub.flatpakrepo",
            ],
            env=env,
            check=False,
        )
        if remote.returncode:
            return fail("Impossibile configurare il catalogo Flathub.", remote.returncode)
        install_flatpak = subprocess.run(
            [
                "flatpak",
                "install",
                "--system",
                "--noninteractive",
                "flathub",
                *flatpaks,
            ],
            env=env,
            check=False,
        )
        if install_flatpak.returncode:
            return fail("Installazione specialistica non completata.", install_flatpak.returncode)

        # I launcher specialistici restano nascosti finché la relativa app non
        # è davvero presente. Dopo il download diventano normali voci del menu.
        for app_id in flatpaks:
            launcher = FLATPAK_LAUNCHERS.get(app_id)
            if not launcher or not launcher.exists():
                continue
            launcher_text = launcher.read_text(encoding="utf-8")
            launcher.write_text(
                launcher_text.replace("\nNoDisplay=true\n", "\n"),
                encoding="utf-8",
            )
        subprocess.run(
            ["update-desktop-database", "/usr/local/share/applications"],
            check=False,
        )

    print("Applicazioni installate correttamente.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

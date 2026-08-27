#!/usr/bin/env python3
"""Sincronizza progetti.json con il catalogo e i launcher di StradilabOS."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(
    "/Users/claudionuzzo/Dev/stradilab/stradilab home/progetti.json"
)
SHARE_DIR = (
    PROJECT_ROOT
    / "config/includes.chroot/usr/local/share/stradilabos"
)
DESKTOP_DIR = (
    PROJECT_ROOT
    / "config/includes.chroot/usr/local/share/applications"
)

INSTITUTIONAL_APPS = [
    {
        "id": "stradilab-home",
        "title": "StradiLab",
        "description": "Lo spazio di sperimentazione didattica digitale dell'IIS Stradivari.",
        "url": "https://stradilab.org",
        "audience": ["tutti"],
        "category": "StradiLab",
        "source": "istituto",
    },
    {
        "id": "istituto",
        "title": "Sito dell'Istituto",
        "description": "Notizie, didattica, organizzazione e informazioni ufficiali.",
        "url": "https://www.istitutostradivari.edu.it/",
        "audience": ["tutti"],
        "category": "Scuola",
        "source": "istituto",
        "icon": "istituto-stradivari",
    },
    {
        "id": "circolari",
        "title": "Circolari",
        "description": "Le comunicazioni ufficiali rivolte a studenti, famiglie e personale.",
        "url": "https://www.istitutostradivari.edu.it/comunicati",
        "audience": ["tutti"],
        "category": "Scuola",
        "source": "istituto",
    },
    {
        "id": "mastercom",
        "title": "MasterCom — Registro elettronico",
        "description": "Accesso diretto al registro elettronico dell'IIS Stradivari.",
        "url": "https://stradivari-cr.registroelettronico.com/mastercom/index.php",
        "audience": ["docenti", "studenti", "famiglie"],
        "category": "Scuola",
        "source": "mastercom",
        "icon": "mastercom",
    },
    {
        "id": "servizi-famiglie",
        "title": "Servizi per famiglie e studenti",
        "description": "Libri, modulistica, registro, pagamenti e servizi di orientamento.",
        "url": "https://www.istitutostradivari.edu.it/servizi-famiglie",
        "audience": ["studenti", "famiglie"],
        "category": "Scuola",
        "source": "istituto",
    },
    {
        "id": "servizi-personale",
        "title": "Servizi per il personale",
        "description": "Modulistica, segreteria digitale, registro e strumenti di lavoro.",
        "url": "https://www.istitutostradivari.edu.it/servizi-personale",
        "audience": ["docenti", "personale"],
        "category": "Scuola",
        "source": "istituto",
    },
    {
        "id": "unica",
        "title": "Piattaforma Unica",
        "description": "Servizi del Ministero per studenti e famiglie.",
        "url": "https://unica.istruzione.gov.it/",
        "audience": ["studenti", "famiglie"],
        "category": "Scuola",
        "source": "mim",
    },
    {
        "id": "workspace-login",
        "title": "Accedi a Google Workspace",
        "description": "Accesso con l'account istituzionale, condiviso tra tutte le app Google.",
        "url": "https://accounts.google.com/AccountChooser?continue=https%3A%2F%2Fclassroom.google.com%2F&hd=istitutostradivari.it",
        "audience": ["docenti", "studenti", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "google-classroom",
        "title": "Google Classroom",
        "description": "Corsi, materiali, compiti e comunicazioni delle classi.",
        "url": "https://classroom.google.com/",
        "audience": ["docenti", "studenti"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "google-drive",
        "title": "Google Drive",
        "description": "File e cartelle dell'account istituzionale.",
        "url": "https://drive.google.com/",
        "audience": ["docenti", "studenti", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "gmail",
        "title": "Posta istituzionale",
        "description": "Gmail con l'account dell'Istituto Stradivari.",
        "url": "https://mail.google.com/",
        "audience": ["docenti", "studenti", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "google-meet",
        "title": "Google Meet",
        "description": "Videolezioni, colloqui e riunioni online.",
        "url": "https://meet.google.com/",
        "audience": ["docenti", "studenti", "famiglie", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "google-calendar",
        "title": "Google Calendar",
        "description": "Calendari, lezioni, appuntamenti, riunioni e scadenze.",
        "url": "https://calendar.google.com/",
        "audience": ["docenti", "studenti", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "google-documenti",
        "title": "Google Documenti",
        "description": "Crea e modifica documenti collaborativi con l'account istituzionale.",
        "url": "https://docs.google.com/document/",
        "audience": ["docenti", "studenti", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "google-fogli",
        "title": "Google Fogli",
        "description": "Fogli di calcolo collaborativi per attività e laboratori.",
        "url": "https://docs.google.com/spreadsheets/",
        "audience": ["docenti", "studenti", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "google-presentazioni",
        "title": "Google Presentazioni",
        "description": "Presentazioni collaborative per lezioni, progetti e portfolio.",
        "url": "https://docs.google.com/presentation/",
        "audience": ["docenti", "studenti", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "google-moduli",
        "title": "Google Moduli",
        "description": "Questionari, verifiche, raccolta dati e iscrizioni.",
        "url": "https://docs.google.com/forms/",
        "audience": ["docenti", "studenti", "personale"],
        "category": "Workspace",
        "source": "google",
    },
    {
        "id": "freesewing",
        "title": "FreeSewing — Cartamodelli su misura",
        "description": "Crea e personalizza cartamodelli nel browser partendo dalle misure.",
        "url": "https://freesewing.eu/editor/",
        "audience": ["docenti", "studenti"],
        "category": "Moda",
        "source": "freesewing",
        "icon": "fashion-cad",
    },
]


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", normalized.casefold()).strip("-")
    return slug or "app"


def desktop_quote(value: str) -> str:
    value = value.replace("%", "%%")
    for original, escaped in (("\\", "\\\\"), ('"', '\\"'), ("$", "\\$"), ("`", "\\`")):
        value = value.replace(original, escaped)
    return f'"{value}"'


def project_to_app(project: dict) -> dict:
    return {
        "id": slugify(project["titolo"]),
        "title": project["titolo"],
        "description": project.get("breve") or project.get("desc") or "App StradiLab",
        "url": project["url"],
        "audience": [project.get("destinatari", "tutti")],
        "category": "Orientamento" if project.get("colore") == "vetrina" else "StradiLab",
        "source": "stradilab",
        "icon": "stradilabos",
        "access": project.get("accesso", "libero"),
        "updated": project.get("aggiornato"),
    }


def desktop_entry(app: dict) -> str:
    keywords = ";".join(("StradiLab", app["category"], *app["audience"])) + ";"
    return "\n".join(
        (
            "[Desktop Entry]",
            "Type=Application",
            "Version=1.0",
            f"Name={app['title']}",
            f"Comment={app['description']}",
            f"Exec=stradilabos-open-app {desktop_quote(app['url'])} {desktop_quote(app['id'])}",
            "TryExec=stradilabos-open-app",
            f"Icon={app.get('icon', 'stradilabos')}",
            "Terminal=false",
            "Categories=Education;Network;",
            f"Keywords={keywords}",
            f"X-StradilabOS-Category={app['category']}",
            "StartupNotify=true",
            "",
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    args = parser.parse_args()

    source_data = json.loads(args.source.read_text(encoding="utf-8"))
    projects = [
        project_to_app(project)
        for project in source_data
        if project.get("attivo") is True
        and isinstance(project.get("url"), str)
        and urlparse(project["url"]).scheme == "https"
    ]

    by_url = {app["url"].rstrip("/"): app for app in INSTITUTIONAL_APPS}
    for app in projects:
        by_url.setdefault(app["url"].rstrip("/"), app)
    apps = list(by_url.values())

    ids: set[str] = set()
    for app in apps:
        base = app["id"]
        suffix = 2
        while app["id"] in ids:
            app["id"] = f"{base}-{suffix}"
            suffix += 1
        ids.add(app["id"])

    SHARE_DIR.mkdir(parents=True, exist_ok=True)
    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    catalog = {
        "schema_version": 1,
        "generated_from": str(args.source),
        "apps": apps,
    }
    (SHARE_DIR / "apps.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    for old_entry in DESKTOP_DIR.glob("stradilabos-web-*.desktop"):
        old_entry.unlink()
    for app in apps:
        path = DESKTOP_DIR / f"stradilabos-web-{app['id']}.desktop"
        path.write_text(desktop_entry(app), encoding="utf-8")

    print(f"Sincronizzate {len(projects)} app StradiLab e {len(apps)} voci totali.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

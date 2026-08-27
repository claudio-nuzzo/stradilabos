#!/usr/bin/python3
"""Centro App grafico con pacchetti curati per area didattica."""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import GLib, Gtk  # noqa: E402

CATALOG = Path("/usr/local/share/stradilabos/packs.json")
BACKEND = "/usr/local/lib/stradilabos/install_pack.py"
PROFILE_STATE = Path.home() / ".config/stradilabos/profiles.json"


def is_live() -> bool:
    if Path("/run/live/medium").exists():
        return True
    try:
        return "boot=live" in Path("/proc/cmdline").read_text(encoding="utf-8")
    except OSError:
        return False


def selected_profiles() -> set[str]:
    try:
        values = json.loads(PROFILE_STATE.read_text(encoding="utf-8"))["profiles"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return set()
    return {value for value in values if isinstance(value, str)}


def selected_role() -> str:
    try:
        role = json.loads(PROFILE_STATE.read_text(encoding="utf-8")).get("role")
    except (OSError, TypeError, json.JSONDecodeError):
        return "student" if selected_profiles() else "base"
    return role if role in {"student", "teacher", "staff", "base"} else "base"


def package_installed(package: str) -> bool:
    result = subprocess.run(
        ["dpkg-query", "-W", "-f=${db:Status-Status}", package],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "installed"


def flatpak_installed(app_id: str) -> bool:
    result = subprocess.run(
        ["flatpak", "info", "--system", app_id],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


class AppCenterWindow(Gtk.ApplicationWindow):
    def __init__(self, application: Gtk.Application):
        super().__init__(application=application, title="Centro App StradilabOS")
        self.set_default_size(820, 660)
        self.set_icon_name("stradilabos-app-center")
        self.packs = json.loads(CATALOG.read_text(encoding="utf-8"))["packs"]
        self.profiles = selected_profiles()
        self.role = selected_role()
        self.recommended = {
            pack["id"]
            for pack in self.packs
            if self.profiles.intersection(pack.get("profiles", [pack["id"]]))
        }
        self.live_session = is_live()
        self.checks: dict[str, Gtk.CheckButton] = {}

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_border_width(20)
        title = Gtk.Label(label="App e raccolte StradilabOS", xalign=0)
        title.set_markup("<span size='xx-large' weight='bold'>App e raccolte StradilabOS</span>")
        role_note = {
            "teacher": "Profilo docente: sono consigliate le raccolte di tutti gli indirizzi.",
            "staff": "Profilo segreteria: nessuna raccolta specialistica è obbligatoria.",
            "base": "Installazione base: scegli soltanto ciò che vuoi aggiungere.",
            "student": "Le raccolte del tuo indirizzo sono già selezionate.",
        }[self.role]
        copy = Gtk.Label(
            label=(
                "La chiavetta resta leggera: dopo l'installazione connettiti a Internet "
                f"e scarica soltanto gli strumenti utili. {role_note}"
                if not self.live_session
                else "Qui trovi le raccolte disponibili. Per mantenere leggera la "
                "chiavetta, potrai scaricarle dopo aver installato StradilabOS."
            ),
            xalign=0,
        )
        copy.set_line_wrap(True)
        root.pack_start(title, False, False, 0)
        root.pack_start(copy, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        listing = Gtk.ListBox()
        listing.set_selection_mode(Gtk.SelectionMode.NONE)
        for pack in self.packs:
            listing.add(self.pack_row(pack))
        scroller.add(listing)
        root.pack_start(scroller, True, True, 0)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.status = Gtk.Label(label="", xalign=0)
        profile_button = Gtk.Button(label="Cambia profilo d'uso")
        profile_button.connect("clicked", self.change_profile)
        self.install_button = Gtk.Button(label="Scarica e installa le app selezionate")
        self.install_button.get_style_context().add_class("suggested-action")
        self.install_button.connect("clicked", self.start_install)
        self.install_button.set_sensitive(not self.live_session)
        if self.live_session:
            self.status.set_text("Disponibile dopo l'installazione")
        footer.pack_start(profile_button, False, False, 0)
        footer.pack_start(self.status, True, True, 0)
        footer.pack_end(self.install_button, False, False, 0)
        root.pack_end(footer, False, False, 0)
        self.add(root)

    def pack_row(self, pack: dict) -> Gtk.ListBoxRow:
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_border_width(12)

        installed = all(package_installed(name) for name in pack["packages"]) and all(
            flatpak_installed(app_id) for app_id in pack.get("flatpaks", [])
        )
        check = Gtk.CheckButton()
        check.set_active(pack["id"] in self.recommended and not installed)
        check.set_sensitive(not installed and not self.live_session)
        self.checks[pack["id"]] = check

        text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        title = Gtk.Label(label=pack["title"], xalign=0)
        title.set_markup(f"<b>{GLib.markup_escape_text(pack['title'])}</b>")
        description = Gtk.Label(label=pack["description"], xalign=0)
        description.set_line_wrap(True)
        software_names = [*pack["packages"], *pack.get("flatpaks", [])]
        packages = Gtk.Label(label=" · ".join(software_names), xalign=0)
        packages.get_style_context().add_class("dim-label")
        text.pack_start(title, False, False, 0)
        text.pack_start(description, False, False, 0)
        text.pack_start(packages, False, False, 0)

        state_parts = []
        if pack["id"] in self.recommended:
            state_parts.append("Consigliato per te")
        state_parts.append("Già presente" if installed else "Da installare")
        state = Gtk.Label(label=" · ".join(state_parts))
        state.get_style_context().add_class("dim-label")
        box.pack_start(check, False, False, 0)
        box.pack_start(text, True, True, 0)
        box.pack_end(state, False, False, 0)
        row.add(box)
        return row

    def change_profile(self, *_args) -> None:
        try:
            subprocess.Popen(["stradilabos-welcome", "--profiles"])
        except OSError as error:
            self.show_message(
                Gtk.MessageType.ERROR,
                "Impossibile aprire la configurazione",
                str(error),
            )

    def start_install(self, *_args) -> None:
        if self.live_session:
            self.show_message(
                Gtk.MessageType.INFO,
                "Installa prima StradilabOS",
                "Le raccolte specialistiche si scaricano sul disco dopo l'installazione.",
            )
            return
        selected = [pack_id for pack_id, check in self.checks.items() if check.get_active()]
        if not selected:
            self.show_message(
                Gtk.MessageType.INFO,
                "Nessuna raccolta selezionata",
                "Scegli almeno una raccolta non ancora presente.",
            )
            return

        self.install_button.set_sensitive(False)
        self.status.set_text("In attesa dell'autorizzazione…")
        thread = threading.Thread(target=self.install_worker, args=(selected,), daemon=True)
        thread.start()

    def install_worker(self, selected: list[str]) -> None:
        try:
            process = subprocess.Popen(
                ["pkexec", BACKEND, *selected],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            assert process.stdout is not None
            for line in process.stdout:
                text = line.strip()
                if text:
                    GLib.idle_add(self.status.set_text, text[-140:])
            code = process.wait()
        except OSError as error:
            GLib.idle_add(self.install_finished, 1, str(error))
            return
        GLib.idle_add(self.install_finished, code, "")

    def install_finished(self, code: int, detail: str) -> bool:
        self.install_button.set_sensitive(True)
        if code == 0:
            self.status.set_text("Installazione completata.")
            self.show_message(
                Gtk.MessageType.INFO,
                "Applicazioni installate",
                "Le nuove applicazioni sono disponibili nel menu.",
            )
        else:
            self.status.set_text("Installazione non completata.")
            self.show_message(
                Gtk.MessageType.ERROR,
                "Installazione non completata",
                detail or "Controlla la connessione Internet e riprova.",
            )
        return False

    def show_message(self, message_type, title: str, detail: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=message_type,
            buttons=Gtk.ButtonsType.CLOSE,
            text=title,
        )
        dialog.format_secondary_text(detail)
        dialog.run()
        dialog.destroy()


class AppCenterApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.stradilab.StradilabOS.AppCenter")

    def do_activate(self) -> None:
        window = self.props.active_window or AppCenterWindow(self)
        window.show_all()
        window.present()


if __name__ == "__main__":
    raise SystemExit(AppCenterApplication().run(sys.argv))

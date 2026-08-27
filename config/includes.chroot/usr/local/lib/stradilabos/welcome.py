#!/usr/bin/python3
"""Configurazione iniziale e schermata di benvenuto di StradilabOS."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

CONFIG_DIR = Path.home() / ".config" / "stradilabos"
WELCOME_STATE = CONFIG_DIR / "welcome-seen"
PROFILE_STATE = CONFIG_DIR / "profiles.json"
PACKS_CATALOG = Path("/usr/local/share/stradilabos/packs.json")
ADDRESS_IDS = ("artistico", "musicale", "liuteria", "moda", "arredo")
WORKSPACE_LOGIN = (
    "https://accounts.google.com/AccountChooser?"
    "continue=https%3A%2F%2Fclassroom.google.com%2F&"
    "hd=istitutostradivari.it"
)

CSS = b"""
window { background: #f6f4ef; }
.wrap { padding: 30px; }
.brand { color: #9b2335; font-size: 13px; font-weight: 700; }
.title { color: #16130f; font-size: 30px; font-weight: 700; }
.copy { color: #5d574f; font-size: 14px; }
.action { background: #ffffff; border: 1px solid #ded8ce; border-radius: 12px; padding: 13px; }
.action:hover { border-color: #9b2335; }
.primary { background: #9b2335; color: #ffffff; border-radius: 12px; padding: 13px; }
.profile-row { background: #ffffff; border: 1px solid #ded8ce; border-radius: 10px; padding: 12px; }
"""


def is_live() -> bool:
    if Path("/run/live/medium").exists():
        return True
    try:
        return "boot=live" in Path("/proc/cmdline").read_text(encoding="utf-8")
    except OSError:
        return False


def load_packs() -> list[dict]:
    try:
        packs = json.loads(PACKS_CATALOG.read_text(encoding="utf-8"))["packs"]
    except (OSError, KeyError, json.JSONDecodeError):
        return []
    by_id = {pack.get("id"): pack for pack in packs}
    return [by_id[pack_id] for pack_id in ADDRESS_IDS if pack_id in by_id]


def load_profiles() -> list[str]:
    try:
        profiles = json.loads(PROFILE_STATE.read_text(encoding="utf-8"))["profiles"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return []
    allowed = set(ADDRESS_IDS)
    return list(dict.fromkeys(value for value in profiles if value in allowed))


def load_device_mode() -> str:
    try:
        mode = json.loads(PROFILE_STATE.read_text(encoding="utf-8"))["device_mode"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return "shared" if is_live() else "personal"
    return mode if mode in {"personal", "shared"} else "personal"


class WelcomeWindow(Gtk.ApplicationWindow):
    def __init__(self, application: Gtk.Application):
        super().__init__(application=application, title="Benvenuto in StradilabOS")
        self.set_default_size(780, 690)
        self.set_resizable(False)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("stradilabos")
        self.packs = load_packs()
        self.profiles = load_profiles()
        self.device_mode = load_device_mode()
        self.profile_checks: dict[str, Gtk.CheckButton] = {}

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.add_named(self.build_home_page(), "home")
        self.stack.add_named(self.build_profile_page(), "profiles")
        self.add(self.stack)

        force_profiles = "--profiles" in sys.argv
        needs_profile = not is_live() and not self.profiles
        self.stack.set_visible_child_name("profiles" if force_profiles or needs_profile else "home")

    def heading(self, title_text: str, copy_text: str) -> tuple[Gtk.Label, Gtk.Label, Gtk.Label]:
        brand = Gtk.Label(label="STRADILAB · IIS ANTONIO STRADIVARI", xalign=0)
        brand.get_style_context().add_class("brand")
        title = Gtk.Label(label=title_text, xalign=0)
        title.get_style_context().add_class("title")
        copy = Gtk.Label(label=copy_text, xalign=0)
        copy.set_line_wrap(True)
        copy.get_style_context().add_class("copy")
        return brand, title, copy

    def build_home_page(self) -> Gtk.Widget:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        root.get_style_context().add_class("wrap")
        live_session = is_live()
        brand, title, copy = self.heading(
            "Prova o installa StradilabOS" if live_session else "Benvenuto in StradilabOS",
            (
                "Puoi provarlo senza modificare il computer oppure avviare subito "
                "l'installazione grafica."
                if live_session
                else "Un ambiente leggero per studiare, creare e usare i servizi della scuola."
            ),
        )
        self.profile_summary = Gtk.Label(xalign=0)
        self.profile_summary.get_style_context().add_class("brand")
        self.update_profile_summary()

        for widget in (brand, title, copy, self.profile_summary):
            root.pack_start(widget, False, False, 0)

        if live_session and shutil.which("calamares-install-debian"):
            root.pack_start(
                self.action(
                    "Installa StradilabOS sul computer",
                    "L'installatore chiederà l'indirizzo e il tipo di utilizzo del PC",
                    ["calamares-install-debian"],
                    primary=True,
                ),
                False,
                False,
                3,
            )

        root.pack_start(
            self.action(
                "Accedi a Google Workspace",
                "Un solo accesso istituzionale per Classroom, Drive, Gmail, Meet e le altre app",
                ["stradilabos-open-app", WORKSPACE_LOGIN, "workspace-login"],
                primary=not live_session,
            ),
            False,
            False,
            3,
        )
        root.pack_start(
            self.action("Apri StradiLab", "Web app e servizi della scuola", ["stradilabos-hub"]),
            False,
            False,
            0,
        )
        root.pack_start(
            self.action("Connettiti a Internet", "Scegli o configura una rete Wi-Fi", ["nm-connection-editor"]),
            False,
            False,
            0,
        )
        root.pack_start(
            self.callback_action(
                "Scegli o cambia indirizzo",
                "Personalizza le applicazioni per Artistico, Musicale, Liuteria, Moda o Arredo",
                self.show_profiles,
            ),
            False,
            False,
            0,
        )
        root.pack_start(
            self.action("Centro App", "Controlla e aggiungi le raccolte didattiche", ["stradilabos-app-center"]),
            False,
            False,
            0,
        )
        root.pack_start(
            self.action("Apri i tuoi file", "Documenti, chiavette e dischi esterni", ["thunar"]),
            False,
            False,
            0,
        )

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.skip = Gtk.CheckButton(label="Non mostrare questa schermata al prossimo accesso")
        self.skip.set_sensitive(not live_session)
        close = Gtk.Button(label="Continua senza installare" if live_session else "Chiudi")
        close.connect("clicked", self.close_and_save)
        footer.pack_start(self.skip, True, True, 0)
        footer.pack_end(close, False, False, 0)
        root.pack_end(footer, False, False, 3)
        return root

    def build_profile_page(self) -> Gtk.Widget:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.get_style_context().add_class("wrap")
        brand, title, copy = self.heading(
            "Per quale indirizzo userai questo PC?",
            (
                "Puoi sceglierne più di uno, per esempio per un laboratorio condiviso. "
                "StradilabOS evidenzierà le raccolte consigliate."
            ),
        )
        root.pack_start(brand, False, False, 0)
        root.pack_start(title, False, False, 0)
        root.pack_start(copy, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        listing = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for pack in self.packs:
            check = Gtk.CheckButton()
            check.set_active(pack["id"] in self.profiles)
            self.profile_checks[pack["id"]] = check

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            row.get_style_context().add_class("profile-row")
            text = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            name = Gtk.Label(xalign=0)
            name.set_markup(f"<b>{GLib.markup_escape_text(pack['title'])}</b>")
            description = Gtk.Label(label=pack["description"], xalign=0)
            description.set_line_wrap(True)
            text.pack_start(name, False, False, 0)
            text.pack_start(description, False, False, 0)
            row.pack_start(check, False, False, 0)
            row.pack_start(text, True, True, 0)
            listing.pack_start(row, False, False, 0)
        scroller.add(listing)
        root.pack_start(scroller, True, True, 0)

        mode_title = Gtk.Label(xalign=0)
        mode_title.set_markup("<b>Questo computer sarà:</b>")
        root.pack_start(mode_title, False, False, 0)
        modes = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        self.personal_mode = Gtk.RadioButton.new_with_label_from_widget(
            None, "Personale o assegnato — conserva l'accesso Workspace"
        )
        self.shared_mode = Gtk.RadioButton.new_with_label_from_widget(
            self.personal_mode, "Condiviso — cancella l'accesso all'uscita"
        )
        self.shared_mode.set_active(self.device_mode == "shared")
        self.personal_mode.set_active(self.device_mode == "personal")
        modes.pack_start(self.personal_mode, False, False, 0)
        modes.pack_start(self.shared_mode, False, False, 0)
        root.pack_start(modes, False, False, 0)

        note_text = (
            "Nella modalità live la scelta vale fino allo spegnimento; durante "
            "l'installazione potrai confermarla o cambiarla."
            if is_live()
            else "Potrai cambiare questa scelta in qualsiasi momento dal Centro App."
        )
        note = Gtk.Label(label=note_text, xalign=0)
        note.set_line_wrap(True)
        note.get_style_context().add_class("copy")
        root.pack_start(note, False, False, 0)

        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        if self.profiles or is_live():
            back = Gtk.Button(label="Indietro")
            back.connect("clicked", lambda _button: self.stack.set_visible_child_name("home"))
            footer.pack_start(back, False, False, 0)
        save = Gtk.Button(label="Salva e continua")
        save.get_style_context().add_class("suggested-action")
        save.connect("clicked", self.save_profiles)
        footer.pack_end(save, False, False, 0)
        root.pack_end(footer, False, False, 0)
        return root

    def update_profile_summary(self) -> None:
        titles = {pack["id"]: pack["title"] for pack in self.packs}
        selected = [titles[value] for value in self.profiles if value in titles]
        label = " · ".join(selected) if selected else "Profilo non ancora scelto"
        device = "PC CONDIVISO" if self.device_mode == "shared" else "PC PERSONALE"
        self.profile_summary.set_text(f"IL TUO PROFILO: {label.upper()} · {device}")

    def show_profiles(self, *_args) -> None:
        for pack_id, check in self.profile_checks.items():
            check.set_active(pack_id in self.profiles)
        self.shared_mode.set_active(self.device_mode == "shared")
        self.personal_mode.set_active(self.device_mode == "personal")
        self.stack.set_visible_child_name("profiles")

    def save_profiles(self, *_args) -> None:
        selected = [
            pack_id
            for pack_id in ADDRESS_IDS
            if self.profile_checks.get(pack_id)
            and self.profile_checks[pack_id].get_active()
        ]
        if not selected:
            self.message(
                "Scegli almeno un indirizzo",
                "Per continuare seleziona una o più raccolte didattiche.",
                Gtk.MessageType.INFO,
            )
            return
        device_mode = "shared" if self.shared_mode.get_active() else "personal"
        state = {
            "schema_version": 1,
            "profiles": selected,
            "device_mode": device_mode,
            "source": "welcome",
        }
        try:
            PROFILE_STATE.parent.mkdir(parents=True, exist_ok=True)
            temporary = PROFILE_STATE.with_suffix(".tmp")
            temporary.write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(PROFILE_STATE)
        except OSError as error:
            self.message("Impossibile salvare il profilo", str(error))
            return
        self.profiles = selected
        self.device_mode = device_mode
        self.update_profile_summary()
        self.stack.set_visible_child_name("home")

    def action(
        self, title: str, subtitle: str, command: list[str], primary: bool = False
    ) -> Gtk.Button:
        return self.callback_action(
            title,
            subtitle,
            lambda *_args: self.launch(command),
            primary=primary,
        )

    def callback_action(self, title: str, subtitle: str, callback, primary: bool = False) -> Gtk.Button:
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.get_style_context().add_class("primary" if primary else "action")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label = Gtk.Label(xalign=0)
        label.set_markup(f"<b>{GLib.markup_escape_text(title)}</b>")
        detail = Gtk.Label(label=subtitle, xalign=0)
        detail.set_line_wrap(True)
        box.pack_start(label, False, False, 0)
        box.pack_start(detail, False, False, 0)
        button.add(box)
        button.connect("clicked", callback)
        return button

    def launch(self, command: list[str]) -> None:
        if not shutil.which(command[0]):
            self.message("Funzione non disponibile", f"Non trovo {command[0]} in questo sistema.")
            return
        try:
            subprocess.Popen(command)
        except OSError as error:
            self.message("Impossibile avviare l'applicazione", str(error))

    def message(self, title: str, detail: str, message_type=Gtk.MessageType.ERROR) -> None:
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

    def close_and_save(self, *_args) -> None:
        if self.skip.get_active() and not is_live():
            WELCOME_STATE.parent.mkdir(parents=True, exist_ok=True)
            WELCOME_STATE.touch()
        self.close()


class WelcomeApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.stradilab.StradilabOS.Welcome")

    def do_activate(self) -> None:
        already_configured = WELCOME_STATE.exists() and PROFILE_STATE.exists()
        if "--autostart" in sys.argv and already_configured and not is_live():
            self.quit()
            return
        window = self.props.active_window or WelcomeWindow(self)
        window.show_all()
        window.present()


if __name__ == "__main__":
    raise SystemExit(WelcomeApplication().run(sys.argv))

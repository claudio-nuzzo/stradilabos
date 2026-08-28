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
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

FORCE_PROFILES = "--profiles" in sys.argv
AUTOSTART_MODE = "--autostart" in sys.argv
GTK_ARGV = [
    argument
    for argument in sys.argv
    if argument not in {"--profiles", "--autostart"}
]

CONFIG_DIR = Path.home() / ".config" / "stradilabos"
WELCOME_STATE = CONFIG_DIR / "welcome-seen"
PROFILE_STATE = CONFIG_DIR / "profiles.json"
PACKS_CATALOG = Path("/usr/local/share/stradilabos/packs.json")
ADDRESS_IDS = ("artistico", "musicale", "liuteria", "moda", "arredo")
ROLE_IDS = ("student", "teacher", "staff", "base")
ROLE_LABELS = {
    "student": "Studente",
    "teacher": "Docente · tutti gli indirizzi",
    "staff": "Personale di segreteria",
    "base": "Installazione base",
}
WORKSPACE_LOGIN = (
    "https://accounts.google.com/ServiceLogin?service=classroom&"
    "continue=https%3A%2F%2Fclassroom.google.com%2F&"
    "hd=istitutostradivari.it&hl=it"
)

CSS = b"""
window { background: #f6f4ef; }
.wrap { padding: 32px; }
.brand { color: #9b2335; font-size: 13px; font-weight: 700; }
.title { color: #16130f; font-size: 32px; font-weight: 700; }
.copy { color: #645e55; font-size: 15px; }
.action {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #ded8ce;
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 2px 8px rgba(22, 19, 15, 0.08);
}
.action:hover { border-color: #9b2335; background: rgba(255, 255, 255, 0.92); }
.primary {
  background: #9b2335;
  color: #f6f4ef;
  border-radius: 16px;
  padding: 14px;
  box-shadow: 0 3px 10px rgba(155, 35, 53, 0.22);
}
.profile-row {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid #ded8ce;
  border-radius: 14px;
  padding: 13px;
}
button { min-height: 34px; }
check, radio { min-width: 20px; min-height: 20px; }
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


def load_role() -> str:
    try:
        state = json.loads(PROFILE_STATE.read_text(encoding="utf-8"))
    except (OSError, TypeError, json.JSONDecodeError):
        return "student" if load_profiles() else "base"
    role = state.get("role")
    if role in ROLE_IDS:
        return role
    return "student" if state.get("profiles") else "base"


def load_device_mode() -> str:
    try:
        mode = json.loads(PROFILE_STATE.read_text(encoding="utf-8"))["device_mode"]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return "shared" if is_live() else "personal"
    return mode if mode in {"personal", "shared"} else "personal"


def load_workspace_onboarding() -> str:
    try:
        mode = json.loads(PROFILE_STATE.read_text(encoding="utf-8"))[
            "workspace_onboarding"
        ]
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return "first-boot"
    return mode if mode in {"first-boot", "later"} else "first-boot"


class WelcomeWindow(Gtk.ApplicationWindow):
    def __init__(self, application: Gtk.Application):
        super().__init__(application=application, title="Benvenuto in StradilabOS")
        self.set_default_size(860, 720)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("stradilabos")
        self.packs = load_packs()
        self.role = load_role()
        self.profiles = load_profiles()
        self.device_mode = load_device_mode()
        self.workspace_onboarding = load_workspace_onboarding()
        self.profile_checks: dict[str, Gtk.CheckButton] = {}
        self.role_buttons: dict[str, Gtk.RadioButton] = {}

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

        needs_profile = not is_live() and not PROFILE_STATE.exists()
        self.stack.set_visible_child_name(
            "profiles" if FORCE_PROFILES or needs_profile else "home"
        )

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
                else "Accedi con l'account @istitutostradivari.it, poi scegli le app "
                "utili per il tuo ruolo."
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
                    "Scegli Studente, Docente, Segreteria o la sola installazione base",
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
                "Solo account @istitutostradivari.it · Classroom, Drive, Gmail, Meet e le altre app",
                ["stradilabos-open-app", WORKSPACE_LOGIN, "workspace-login"],
                primary=(
                    not live_session and self.workspace_onboarding == "first-boot"
                ),
            ),
            False,
            False,
            3,
        )
        if not live_session:
            root.pack_start(
                self.action(
                    "Scarica le app consigliate",
                    "Il Centro App segue il profilo scelto; per il download serve Internet",
                    ["stradilabos-app-center"],
                    primary=self.workspace_onboarding == "later",
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
                "Scegli o cambia profilo d'uso",
                "Studente, docente, segreteria oppure installazione base",
                self.show_profiles,
            ),
            False,
            False,
            0,
        )
        if live_session:
            root.pack_start(
                self.action(
                    "Centro App",
                    "Scopri le raccolte che potrai aggiungere dopo l'installazione",
                    ["stradilabos-app-center"],
                ),
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
            "Chi userà questo PC?",
            (
                "Scegli il ruolo. Agli studenti vengono proposte le app del proprio "
                "indirizzo; ai docenti quelle di tutti gli indirizzi. Segreteria e "
                "installazione base restano leggere."
            ),
        )
        root.pack_start(brand, False, False, 0)
        root.pack_start(title, False, False, 0)
        root.pack_start(copy, False, False, 0)

        role_title = Gtk.Label(xalign=0)
        role_title.set_markup("<b>Profilo d'uso:</b>")
        root.pack_start(role_title, False, False, 0)
        role_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        role_group = None
        role_options = (
            ("student", "Studente — scegli il tuo indirizzo"),
            ("teacher", "Docente — raccolte di tutti gli indirizzi"),
            ("staff", "Personale di segreteria — strumenti comuni e servizi scolastici"),
            ("base", "Solo base — nessuna raccolta specialistica preselezionata"),
        )
        for role_id, label in role_options:
            button = Gtk.RadioButton.new_with_label_from_widget(role_group, label)
            if role_group is None:
                role_group = button
            button.set_active(role_id == self.role)
            button.connect("toggled", self.role_changed, role_id)
            self.role_buttons[role_id] = button
            role_box.pack_start(button, False, False, 0)
        root.pack_start(role_box, False, False, 0)

        address_title = Gtk.Label(xalign=0)
        address_title.set_markup("<b>Indirizzo dello studente:</b>")
        root.pack_start(address_title, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.ALWAYS)
        scroller.set_min_content_height(220)
        listing = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        for pack in self.packs:
            check = Gtk.CheckButton()
            check.set_active(pack["id"] in self.profiles)
            check.connect("toggled", self.address_changed, pack["id"])
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
        self.apply_role_to_controls(self.role)

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
        if PROFILE_STATE.exists() or is_live():
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
        if self.role == "teacher":
            label = ROLE_LABELS[self.role]
        elif self.role == "student":
            addresses = " · ".join(selected) if selected else "indirizzo non scelto"
            label = f"{ROLE_LABELS[self.role]} · {addresses}"
        else:
            label = ROLE_LABELS[self.role]
        device = "PC CONDIVISO" if self.device_mode == "shared" else "PC PERSONALE"
        self.profile_summary.set_text(f"IL TUO PROFILO: {label.upper()} · {device}")

    def role_changed(self, button: Gtk.RadioButton, role: str) -> None:
        if button.get_active():
            self.apply_role_to_controls(role)

    def address_changed(self, button: Gtk.CheckButton, pack_id: str) -> None:
        student_button = self.role_buttons.get("student")
        if not button.get_active() or not student_button or not student_button.get_active():
            return
        for other_id, other in self.profile_checks.items():
            if other_id != pack_id:
                other.set_active(False)

    def apply_role_to_controls(self, role: str) -> None:
        if role == "student":
            selected = [check for check in self.profile_checks.values() if check.get_active()]
            for extra in selected[1:]:
                extra.set_active(False)
        for pack_id, check in self.profile_checks.items():
            if role == "teacher":
                check.set_active(True)
            elif role in {"staff", "base"}:
                check.set_active(False)
            check.set_sensitive(role == "student")

    def show_profiles(self, *_args) -> None:
        for pack_id, check in self.profile_checks.items():
            check.set_active(pack_id in self.profiles)
        self.role_buttons[self.role].set_active(True)
        self.apply_role_to_controls(self.role)
        self.shared_mode.set_active(self.device_mode == "shared")
        self.personal_mode.set_active(self.device_mode == "personal")
        self.stack.set_visible_child_name("profiles")

    def save_profiles(self, *_args) -> None:
        role = next(
            (role_id for role_id, button in self.role_buttons.items() if button.get_active()),
            "base",
        )
        if role == "teacher":
            selected = list(ADDRESS_IDS)
        elif role == "student":
            selected = [
                pack_id
                for pack_id in ADDRESS_IDS
                if self.profile_checks.get(pack_id)
                and self.profile_checks[pack_id].get_active()
            ]
        else:
            selected = []
        if role == "student" and len(selected) != 1:
            self.message(
                "Scegli un indirizzo",
                "Per il profilo Studente seleziona un solo indirizzo scolastico.",
                Gtk.MessageType.INFO,
            )
            return
        device_mode = "shared" if self.shared_mode.get_active() else "personal"
        state = {
            "schema_version": 2,
            "role": role,
            "profiles": selected,
            "device_mode": device_mode,
            "workspace_onboarding": self.workspace_onboarding,
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
        self.role = role
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
        if AUTOSTART_MODE and already_configured and not is_live():
            self.quit()
            return
        window = self.props.active_window or WelcomeWindow(self)
        window.show_all()
        window.present()


if __name__ == "__main__":
    raise SystemExit(WelcomeApplication().run(GTK_ARGV))

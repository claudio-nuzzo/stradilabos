#!/usr/bin/python3
"""Configurazione iniziale e schermata di benvenuto di StradilabOS."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gdk, GLib, Gtk  # noqa: E402

try:
    import system_status  # noqa: E402  (stesso albero di StradilabOS)
except ImportError:  # pragma: no cover - difesa in ambienti minimi
    system_status = None

FORCE_PROFILES = "--profiles" in sys.argv
AUTOSTART_MODE = "--autostart" in sys.argv
GTK_ARGV = [
    argument
    for argument in sys.argv
    if argument not in {"--profiles", "--autostart"}
]

CONFIG_DIR = Path.home() / ".config" / "stradilabos"
FIRST_RUN_DONE = CONFIG_DIR / "first-run-done"
PROFILE_STATE = CONFIG_DIR / "profiles.json"
CHROME_SETUP_DONE = CONFIG_DIR / "chrome-setup-done"
PACKS_CATALOG = Path("/usr/local/share/stradilabos/packs.json")
ADDRESS_IDS = ("artistico", "musicale", "liuteria", "moda", "arredo")
ROLE_IDS = ("student", "teacher", "staff", "base")
WORKSPACE_ONBOARDING_MODES = {"first-boot", "later", "completed"}
ROLE_LABELS = {
    "student": "Studente",
    "teacher": "Docente · tutti gli indirizzi",
    "staff": "Personale di segreteria",
    "base": "Installazione base",
}
# L'accesso guidato di Google Workspace apre Gmail (non Classroom): è il
# rilievo n. 2 del collaudo. Il dominio resta vincolato dall'URL e dalla policy
# Chromium AllowedDomainsForApps=istitutostradivari.it.
WORKSPACE_LOGIN = (
    "https://accounts.google.com/ServiceLogin?service=mail&"
    "continue=https%3A%2F%2Fmail.google.com%2F&"
    "hd=istitutostradivari.it&hl=it"
)

CSS = b"""
window { background: #f6f4ef; }
.wrap { padding: 32px; }
.brand { color: #9b2335; font-size: 13px; font-weight: 700; }
.title { color: #16130f; font-size: 32px; font-weight: 700; }
.copy { color: #645e55; font-size: 15px; }
.status { color: #645e55; font-size: 13px; }
.offline { color: #9b2335; font-weight: 700; }
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
    return mode if mode in WORKSPACE_ONBOARDING_MODES else "first-boot"


def store_workspace_onboarding(mode: str) -> None:
    """Aggiorna soltanto lo stato Workspace, preservando il profilo scelto."""
    if mode not in WORKSPACE_ONBOARDING_MODES:
        raise ValueError(f"stato Workspace non valido: {mode}")
    state = json.loads(PROFILE_STATE.read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError("profilo StradiLabOS non valido")
    state["workspace_onboarding"] = mode
    temporary = PROFILE_STATE.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(PROFILE_STATE)


class WelcomeWindow(Gtk.ApplicationWindow):
    def __init__(self, application: Gtk.Application):
        super().__init__(application=application, title="Benvenuto in StradiLabOS")
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() if display else None
        if monitor is None and display and display.get_n_monitors() > 0:
            monitor = display.get_monitor(0)
        if monitor:
            workarea = monitor.get_workarea()
            width = max(560, min(860, workarea.width - 48))
            height = max(480, min(680, workarea.height - 48))
            self.set_default_size(width, height)
        else:
            self.set_default_size(820, 640)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("stradilabos")
        self.packs = load_packs()
        self.role = load_role()
        self.profiles = load_profiles()
        self.device_mode = load_device_mode()
        self.workspace_onboarding = load_workspace_onboarding()
        self.chrome_onboarding_opened = False
        self.profile_checks: dict[str, Gtk.CheckButton] = {}
        self.role_buttons: dict[str, Gtk.RadioButton] = {}

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_hhomogeneous(False)
        self.stack.set_vhomogeneous(False)
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
        connected = self.nm_is_connected()
        brand, title, copy = self.heading(
            "Prova o installa StradiLabOS" if live_session else "Benvenuto in StradiLabOS",
            (
                "Puoi provarlo senza modificare il computer oppure avviare subito "
                "l'installazione grafica."
                if live_session
                else "Collega il computer a Internet, accedi con l'account "
                "@istitutostradivari.it e scegli le app utili per il tuo ruolo."
            ),
        )
        self.profile_summary = Gtk.Label(xalign=0)
        self.profile_summary.get_style_context().add_class("brand")
        self.update_profile_summary()

        self.status_line = Gtk.Label(label=self.status_text(), xalign=0)
        self.status_line.get_style_context().add_class("status")
        if not connected:
            self.status_line.set_markup(
                f'<span color="#9b2335">{GLib.markup_escape_text(self.status_text())}</span>'
            )

        for widget in (brand, title, copy, self.profile_summary, self.status_line):
            root.pack_start(widget, False, False, 0)

        if live_session and shutil.which("calamares-install-debian"):
            root.pack_start(
                self.action(
                    "Installa StradiLabOS sul computer",
                    "Scegli Studente, Docente, Segreteria o la sola installazione base",
                    self.install_and_check,
                    primary=True,
                ),
                False,
                False,
                3,
            )

        # Passo 1 della prima accensione: la rete. È primaria quando manca la
        # connessione, così l'utente non può avviare nulla di inutile.
        if not connected:
            root.pack_start(
                self.action(
                    "1 · Prima cosa: collegati a Internet",
                    "Senza rete Google Workspace e le app non funzionano",
                    self.open_network_center,
                    primary=True,
                ),
                False,
                False,
                3,
            )
            root.pack_start(
                self.callback_action(
                    "Salta, configuro dopo",
                    "Potrai continuare, ma Google Workspace e il Centro App resteranno inattivi finché non ti colleghi.",
                    self.skip_network,
                ),
                False,
                False,
                0,
            )
        else:
            root.pack_start(
                self.action(
                    "Rete: connesso",
                    "Puoi cambiare o configurare una rete in ogni momento",
                    self.open_network_center,
                ),
                False,
                False,
                3,
            )

        # Passo 2 della prima accensione: Google Workspace, se scelto in
        # installazione e solo a rete attiva.
        google_primary = (
            not live_session
            and not CHROME_SETUP_DONE.exists()
            and connected
        )
        chrome_installed = self.chrome_command() is not None
        workspace_completed = CHROME_SETUP_DONE.exists() and chrome_installed
        self.workspace_button = self.action(
            "2 · Chrome e Google Workspace configurati ✓"
            if workspace_completed
            else (
                "2 · Apri Chrome e configura il profilo"
                if chrome_installed
                else "2 · Scarica Chrome e accedi"
            ),
            "Profilo Chrome e accesso condivisi tra Gmail, Classroom, Drive, Meet e le altre app"
            if workspace_completed
            else (
                "Accedi con @istitutostradivari.it e attiva la sincronizzazione"
                if chrome_installed
                else "Installa il browser Google, crea il profilo e attiva la sincronizzazione"
            ),
            self.open_workspace,
            primary=google_primary,
        )
        root.pack_start(
            self.workspace_button,
            False,
            False,
            3,
        )
        if not live_session:
            self.apps_button = self.action(
                "3 · Scarica le app consigliate",
                "Il Centro App segue il profilo scelto; per il download serve Internet",
                ["stradilabos-app-center"],
                primary=(
                    self.workspace_onboarding == "later" or CHROME_SETUP_DONE.exists()
                )
                and connected,
            )
            root.pack_start(
                self.apps_button,
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
        self.status_footer = Gtk.Label(label=self.status_text(), xalign=0)
        self.status_footer.get_style_context().add_class("status")
        check_now = Gtk.Button(label="Controlla aggiornamenti")
        check_now.connect("clicked", self.check_updates)
        close = Gtk.Button(label="Continua senza installare" if live_session else "Chiudi")
        close.connect("clicked", self.close_and_save)
        footer.pack_start(self.status_footer, True, True, 0)
        footer.pack_start(check_now, False, False, 0)
        footer.pack_end(close, False, False, 0)
        footer.set_margin_start(32)
        footer.set_margin_end(32)
        footer.set_margin_top(8)
        footer.set_margin_bottom(18)
        # Su portatili 1366×768 il pannello e le decorazioni riducono l'area
        # utile: il contenuto scorre, mentre aggiornamenti e chiusura restano
        # sempre visibili in un piè di pagina fisso sopra la barra.
        home_scroller = Gtk.ScrolledWindow()
        home_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        home_scroller.add(root)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page.pack_start(home_scroller, True, True, 0)
        page.pack_end(footer, False, False, 0)
        return page

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
        footer.set_margin_start(32)
        footer.set_margin_end(32)
        footer.set_margin_top(8)
        footer.set_margin_bottom(18)
        profile_scroller = Gtk.ScrolledWindow()
        profile_scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        profile_scroller.add(root)
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page.pack_start(profile_scroller, True, True, 0)
        page.pack_end(footer, False, False, 0)
        return page

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
        self, title: str, subtitle: str, command, primary: bool = False
    ) -> Gtk.Button:
        callback = command if callable(command) else (lambda *_args, c=command: self.launch(c))
        return self.callback_action(title, subtitle, callback, primary=primary)

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

    def launch(self, command: list[str]) -> bool:
        if not shutil.which(command[0]):
            self.message("Funzione non disponibile", f"Non trovo {command[0]} in questo sistema.")
            return False
        try:
            subprocess.Popen(command)
        except OSError as error:
            self.message("Impossibile avviare l'applicazione", str(error))
            return False
        return True

    @staticmethod
    def update_action(button: Gtk.Button, title: str, subtitle: str, primary: bool) -> None:
        context = button.get_style_context()
        context.remove_class("action")
        context.remove_class("primary")
        context.add_class("primary" if primary else "action")
        labels = button.get_child().get_children()
        labels[0].set_markup(f"<b>{GLib.markup_escape_text(title)}</b>")
        labels[1].set_text(subtitle)

    def nm_is_connected(self) -> bool:
        """Verifica la connettività di rete senza privilegi, a ogni comparsa."""
        if not shutil.which("nmcli"):
            # Senza nmcli non possiamo verificare: non blocchiamo nulla.
            return True
        try:
            result = subprocess.run(
                ["nmcli", "-t", "-f", "STATE", "general"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                check=False,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.stdout.strip() == "connected"

    def open_network_center(self, *_args) -> None:
        if shutil.which("stradilabos-wifi"):
            self.launch(["stradilabos-wifi"])
        else:
            self.launch(["nm-connection-editor"])

    def skip_network(self, *_args) -> None:
        """Conferma il rinvio senza memorizzare uno stato permanente.

        La rete viene verificata a ogni nuova apertura del Benvenuto, come
        richiesto: il rinvio vale soltanto per questa scelta dell'utente.
        """
        self.message(
            "Puoi configurare la rete più tardi",
            "Continua pure con le altre attività. Quando vorrai usare Google Workspace o scaricare le app, apri il pulsante «Collegati a Internet».",
            Gtk.MessageType.INFO,
        )

    def open_workspace(self, *_args) -> None:
        if not self.nm_is_connected():
            open_nets = self.choice(
                "Prima collega il computer a Internet",
                "Per accedere a Google Workspace serve una connessione. Collega il "
                "computer e poi riprova: la verifica della rete avviene ogni volta.",
                "Apri la scelta della rete",
                "Salta, configuro dopo",
            )
            if open_nets:
                self.open_network_center()
            return

        chrome = self.chrome_command()
        if not chrome:
            if is_live():
                self.message(
                    "Installa prima StradiLabOS",
                    "Nella sessione di prova Chrome scomparirebbe allo spegnimento. "
                    "Installa StradiLabOS sul computer: al primo avvio questo pulsante "
                    "scaricherà Chrome e configurerà l’account.",
                    Gtk.MessageType.INFO,
                )
                return
            accepted = self.choice(
                "Scaricare Google Chrome?",
                "Verrà scaricato dal sito ufficiale Google il pacchetto adatto a questo "
                "computer (circa 130–140 MB). Chrome diventerà il browser predefinito "
                "e aggiungerà il proprio canale per gli aggiornamenti di sicurezza.\n\n"
                "Al primo avvio Google mostrerà i propri Termini di servizio. "
                "Chromium resterà installato soltanto come browser di riserva.",
                "Scarica e installa",
                "Annulla",
            )
            if accepted:
                self.start_chrome_install()
            return

        self.make_chrome_default()
        if CHROME_SETUP_DONE.exists():
            self.launch(["stradilabos-open-app", WORKSPACE_LOGIN, "workspace-login"])
            return

        if self.chrome_onboarding_opened:
            completed = self.choice(
                "Profilo Chrome configurato?",
                "Conferma soltanto dopo avere eseguito in Chrome l’accesso con "
                "l’account @istitutostradivari.it e avere attivato la sincronizzazione.",
                "Sì, ho completato",
                "Non ancora",
            )
            if completed:
                self.complete_workspace_onboarding()
            return

        self.begin_chrome_onboarding()

    @staticmethod
    def chrome_command() -> str | None:
        for command in ("google-chrome-stable", "google-chrome"):
            executable = shutil.which(command)
            if executable:
                return executable
        return None

    def start_chrome_install(self) -> None:
        installer = shutil.which("stradilabos-install-chrome")
        pkexec = shutil.which("pkexec")
        if not installer or not pkexec:
            self.message(
                "Installazione non disponibile",
                "Il programma per installare Chrome non è presente o è incompleto.",
            )
            return
        self.workspace_button.set_sensitive(False)
        self.update_action(
            self.workspace_button,
            "2 · Download e installazione di Chrome in corso…",
            "Attendi il completamento e autorizza l’operazione quando richiesto",
            primary=True,
        )
        threading.Thread(
            target=self.run_chrome_install,
            args=(pkexec, installer),
            daemon=True,
        ).start()

    def run_chrome_install(self, pkexec: str, installer: str) -> None:
        try:
            completed = subprocess.run(
                [pkexec, installer],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            output = completed.stdout.strip()
            returncode = completed.returncode
        except OSError as error:
            output = str(error)
            returncode = 1
        GLib.idle_add(self.finish_chrome_install, returncode, output)

    def finish_chrome_install(self, returncode: int, output: str) -> bool:
        self.workspace_button.set_sensitive(True)
        if returncode in (126, 127):
            self.restore_workspace_action()
            self.message(
                "Installazione annullata",
                "Google Chrome non è stato installato. Puoi riprovare quando vuoi.",
                Gtk.MessageType.INFO,
            )
            return False
        if returncode != 0 or not self.chrome_command():
            self.restore_workspace_action()
            detail = "\n".join(output.splitlines()[-5:]) or "Errore sconosciuto."
            self.message("Chrome non è stato installato", detail)
            return False
        self.make_chrome_default()
        self.begin_chrome_onboarding()
        return False

    def begin_chrome_onboarding(self) -> None:
        proceed = self.choice(
            "Configura un solo profilo Google Chrome",
            "1. In Chrome scegli «Accedi a Chrome».\n"
            "2. Usa l’account @istitutostradivari.it.\n"
            "3. Scegli «Attiva la sincronizzazione» e conferma.\n"
            "4. Torna qui e premi di nuovo il pulsante rosso per confermare.\n\n"
            "Da quel momento Gmail, Classroom, Drive, Meet e le altre web app "
            "StradiLabOS useranno lo stesso account.",
            "Apri Google Chrome",
            "Annulla",
        )
        if not proceed:
            self.restore_workspace_action()
            return
        if not self.launch(["stradilabos-browser", WORKSPACE_LOGIN]):
            self.restore_workspace_action()
            return
        self.chrome_onboarding_opened = True
        self.update_action(
            self.workspace_button,
            "2 · Completa accesso e sincronizzazione in Chrome",
            "Quando hai finito, torna qui e premi per confermare",
            primary=True,
        )

    def make_chrome_default(self) -> None:
        if not self.chrome_command():
            return
        for command in (
            ["xdg-settings", "set", "default-web-browser", "google-chrome.desktop"],
            ["xdg-mime", "default", "google-chrome.desktop", "x-scheme-handler/http"],
            ["xdg-mime", "default", "google-chrome.desktop", "x-scheme-handler/https"],
        ):
            if shutil.which(command[0]):
                subprocess.run(
                    command,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False,
                )

    def restore_workspace_action(self) -> None:
        chrome_installed = self.chrome_command() is not None
        self.update_action(
            self.workspace_button,
            "2 · Apri Chrome e configura il profilo"
            if chrome_installed
            else "2 · Scarica Chrome e accedi",
            "Accedi con @istitutostradivari.it e attiva la sincronizzazione"
            if chrome_installed
            else "Installa il browser Google, crea il profilo e attiva la sincronizzazione",
            primary=self.nm_is_connected() and not is_live(),
        )

    def complete_workspace_onboarding(self) -> None:
        try:
            store_workspace_onboarding("completed")
            CHROME_SETUP_DONE.parent.mkdir(parents=True, exist_ok=True)
            temporary = CHROME_SETUP_DONE.with_suffix(".tmp")
            temporary.write_text("completed\n", encoding="utf-8")
            temporary.replace(CHROME_SETUP_DONE)
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            self.message("Configurazione completata, stato non salvato", str(error))
            return
        self.workspace_onboarding = "completed"
        self.chrome_onboarding_opened = False
        self.update_action(
            self.workspace_button,
            "2 · Chrome e Google Workspace configurati ✓",
            "Profilo Chrome e accesso condivisi tra Gmail, Classroom, Drive, Meet e le altre app",
            primary=False,
        )
        if hasattr(self, "apps_button"):
            self.update_action(
                self.apps_button,
                "3 · Scarica le app consigliate",
                "Il Centro App segue il profilo scelto; per il download serve Internet",
                primary=True,
            )

    def install_and_check(self, *_args) -> None:
        if not shutil.which("calamares-install-debian"):
            self.message(
                "Funzione non disponibile",
                "Non trovo l'installatore in questo sistema.",
            )
            return
        if self.nm_is_connected():
            self.launch(["calamares-install-debian"])
            return
        proceed = self.choice(
            "Collega prima il computer a Internet",
            "L'installazione di StradiLabOS ha bisogno di Internet: senza rete "
            "può fermarsi a metà e non potrà proporre l'accesso a Google Workspace.\n\n"
            "Puoi continuare senza rete: potrai collegarti al primo avvio del "
            "sistema installato.",
            "Procedi senza rete",
            "Configura la rete",
        )
        if proceed:
            self.launch(["calamares-install-debian"])
        else:
            self.open_network_center()

    def check_updates(self, *_args) -> None:
        update_ui = shutil.which("stradilabos-update-ui")
        if not update_ui:
            self.message(
                "Funzione non disponibile",
                "Il controllo degli aggiornamenti non è disponibile in questo sistema.",
            )
            return
        try:
            subprocess.Popen([update_ui])
        except OSError as error:
            self.message("Impossibile avviare la verifica", str(error))

    def status_text(self) -> str:
        base = "StradiLabOS 0.4"
        if system_status is not None:
            try:
                return system_status.status_label()
            except Exception:  # difesa: la riga di stato non blocca il Benvenuto
                pass
        return base

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

    def choice(self, title: str, detail: str, ok_label: str, cancel_label: str) -> bool:
        dialog = Gtk.Dialog(title=title, transient_for=self, modal=True)
        dialog.add_button(cancel_label, Gtk.ResponseType.CANCEL)
        dialog.add_button(ok_label, Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        label = Gtk.Label(label=detail)
        label.set_line_wrap(True)
        label.set_max_width_chars(62)
        box.pack_start(label, True, True, 14)
        box.show_all()
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.OK

    def close_and_save(self, *_args) -> None:
        if not is_live():
            FIRST_RUN_DONE.parent.mkdir(parents=True, exist_ok=True)
            FIRST_RUN_DONE.touch()
        self.close()


class WelcomeApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.stradilab.StradilabOS.Welcome")

    def do_activate(self) -> None:
        already_configured = FIRST_RUN_DONE.exists() and PROFILE_STATE.exists()
        if AUTOSTART_MODE and already_configured and not is_live():
            self.quit()
            return
        window = self.props.active_window or WelcomeWindow(self)
        window.show_all()
        window.present()


if __name__ == "__main__":
    raise SystemExit(WelcomeApplication().run(GTK_ARGV))

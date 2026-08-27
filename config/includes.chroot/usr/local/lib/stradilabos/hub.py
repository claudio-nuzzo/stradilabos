#!/usr/bin/python3
"""Launcher grafico delle web app StradiLab e dei servizi scolastici."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk, Pango  # noqa: E402

CATALOG = Path("/usr/local/share/stradilabos/apps.json")

CATEGORY_COLORS = {
    "StradiLab": "#9b2335",
    "Scuola": "#2f5d62",
    "Workspace": "#375a9e",
    "Orientamento": "#8b5e34",
    "Moda": "#8e3b67",
}

CSS = b"""
window { background: #f6f4ef; }
.hero { background: #16130f; color: #f6f4ef; padding: 22px; }
.hero-title { font-size: 28px; font-weight: 700; }
.hero-copy { color: #d8d2c9; font-size: 14px; }
.toolbar { padding: 12px 18px; background: #eeeae2; }
.app-card { background: #ffffff; border: 1px solid #ded8ce; border-radius: 14px; padding: 14px; }
.app-card:hover { border-color: #9b2335; background: #fffdf9; }
.app-title { color: #16130f; font-size: 16px; font-weight: 700; }
.app-copy { color: #5d574f; font-size: 12px; }
.badge { color: #9b2335; font-size: 11px; font-weight: 700; }
"""


class AppCard(Gtk.FlowBoxChild):
    def __init__(self, app: dict, open_callback):
        super().__init__()
        self.app = app

        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.get_style_context().add_class("app-card")
        button.connect("clicked", lambda _button: open_callback(app))

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=7)
        box.set_size_request(260, 138)

        title = Gtk.Label(label=app["title"], xalign=0)
        title.set_line_wrap(True)
        title.set_max_width_chars(29)
        title.get_style_context().add_class("app-title")

        description = Gtk.Label(label=app["description"], xalign=0, yalign=0)
        description.set_line_wrap(True)
        description.set_lines(3)
        description.set_max_width_chars(36)
        description.set_ellipsize(Pango.EllipsizeMode.END)
        description.get_style_context().add_class("app-copy")

        audience = ", ".join(app.get("audience", ["tutti"]))
        badge = Gtk.Label(
            label=f"{app['category'].upper()}  ·  {audience.upper()}", xalign=0
        )
        badge.get_style_context().add_class("badge")

        box.pack_start(title, False, False, 0)
        box.pack_start(description, True, True, 0)
        box.pack_end(badge, False, False, 0)
        button.add(box)
        self.add(button)


class HubWindow(Gtk.ApplicationWindow):
    def __init__(self, application: Gtk.Application):
        super().__init__(application=application, title="StradiLab")
        self.set_default_size(1080, 720)
        self.set_icon_name("stradilabos")
        self.apps = json.loads(CATALOG.read_text(encoding="utf-8"))["apps"]
        self.cards: list[AppCard] = []

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        root.pack_start(self._hero(), False, False, 0)
        root.pack_start(self._filters(), False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroller.set_border_width(18)

        self.flow = Gtk.FlowBox()
        self.flow.set_valign(Gtk.Align.START)
        self.flow.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flow.set_column_spacing(14)
        self.flow.set_row_spacing(14)
        self.flow.set_min_children_per_line(1)
        self.flow.set_max_children_per_line(4)
        for app in self.apps:
            card = AppCard(app, self.open_app)
            self.cards.append(card)
            self.flow.add(card)

        scroller.add(self.flow)
        root.pack_start(scroller, True, True, 0)
        self.add(root)

    @staticmethod
    def _hero() -> Gtk.Widget:
        hero = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        hero.get_style_context().add_class("hero")
        title = Gtk.Label(label="STRADILAB", xalign=0)
        title.get_style_context().add_class("hero-title")
        copy = Gtk.Label(
            label="App, documenti e servizi dell'IIS Antonio Stradivari in un unico posto.",
            xalign=0,
        )
        copy.get_style_context().add_class("hero-copy")
        hero.pack_start(title, False, False, 0)
        hero.pack_start(copy, False, False, 0)
        return hero

    def _filters(self) -> Gtk.Widget:
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toolbar.get_style_context().add_class("toolbar")

        self.search = Gtk.SearchEntry()
        self.search.set_placeholder_text("Cerca un'app o un servizio…")
        self.search.set_hexpand(True)
        self.search.connect("search-changed", self.apply_filters)

        self.audience = Gtk.ComboBoxText()
        for value, label in (
            ("all", "Tutti gli utenti"),
            ("docenti", "Docenti"),
            ("studenti", "Studenti"),
            ("famiglie", "Famiglie"),
            ("personale", "Personale"),
        ):
            self.audience.append(value, label)
        self.audience.set_active_id("all")
        self.audience.connect("changed", self.apply_filters)

        self.category = Gtk.ComboBoxText()
        self.category.append("all", "Tutte le aree")
        for category in CATEGORY_COLORS:
            self.category.append(category, category)
        self.category.set_active_id("all")
        self.category.connect("changed", self.apply_filters)

        toolbar.pack_start(self.search, True, True, 0)
        toolbar.pack_start(self.audience, False, False, 0)
        toolbar.pack_start(self.category, False, False, 0)
        return toolbar

    def apply_filters(self, *_args) -> None:
        query = self.search.get_text().strip().casefold()
        audience = self.audience.get_active_id() or "all"
        category = self.category.get_active_id() or "all"

        for card in self.cards:
            app = card.app
            haystack = " ".join(
                (app["title"], app["description"], app["category"])
            ).casefold()
            audience_values = app.get("audience", ["tutti"])
            visible = not query or query in haystack
            visible = visible and (
                audience == "all"
                or audience in audience_values
                or "tutti" in audience_values
            )
            visible = visible and (category == "all" or category == app["category"])
            card.set_visible(visible)

    def open_app(self, app: dict) -> None:
        try:
            subprocess.Popen(["stradilabos-open-app", app["url"], app["id"]])
        except OSError as error:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                modal=True,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.CLOSE,
                text="Impossibile aprire l'app",
            )
            dialog.format_secondary_text(str(error))
            dialog.run()
            dialog.destroy()


class HubApplication(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="org.stradilab.StradilabOS.Hub")

    def do_activate(self) -> None:
        window = self.props.active_window or HubWindow(self)
        window.show_all()
        window.present()


if __name__ == "__main__":
    raise SystemExit(HubApplication().run(sys.argv))

from __future__ import annotations

import importlib.util
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from types import SimpleNamespace
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CHROOT = ROOT / "config/includes.chroot"


def load_sync_module():
    path = ROOT / "scripts/sync_stradilab_apps.py"
    spec = importlib.util.spec_from_file_location("sync_stradilab_apps", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_install_module():
    path = CHROOT / "usr/local/lib/stradilabos/install_pack.py"
    spec = importlib.util.spec_from_file_location("install_pack", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = json.loads(
            (CHROOT / "usr/local/share/stradilabos/apps.json").read_text(
                encoding="utf-8"
            )
        )["apps"]

    def test_ids_are_unique(self) -> None:
        ids = [app["id"] for app in self.catalog]
        self.assertEqual(len(ids), len(set(ids)))

    def test_workspace_login_is_domain_scoped_and_in_italian(self) -> None:
        by_id = {app["id"]: app for app in self.catalog}
        for app_id in ("workspace-login", "google-classroom"):
            url = by_id[app_id]["url"]
            self.assertIn("/ServiceLogin?", url)
            self.assertIn("hd=istitutostradivari.it", url)
            self.assertIn("hl=it", url)

    def test_desktop_quoting_escapes_field_codes(self) -> None:
        module = load_sync_module()
        quoted = module.desktop_quote("https://example.test/?next=%2F&value=$HOME")
        self.assertEqual(
            quoted,
            '"https://example.test/?next=%%2F&value=\\$HOME"',
        )


class DesktopDefaultsTests(unittest.TestCase):
    def test_all_xml_defaults_are_well_formed(self) -> None:
        paths = [
            *(
                CHROOT
                / "etc/xdg/xfce4/xfconf/xfce-perchannel-xml"
            ).glob("*.xml"),
            *(
                CHROOT
                / "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml"
            ).glob("*.xml"),
        ]
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path):
                ET.parse(path)

    def test_window_controls_are_always_visible(self) -> None:
        for relative in (
            "etc/xdg/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml",
            "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml",
        ):
            text = (CHROOT / relative).read_text(encoding="utf-8")
            self.assertIn('name="button_layout" type="string" value="O|HMC"', text)
            self.assertIn('name="borderless_maximize" type="bool" value="false"', text)
            self.assertIn('name="titleless_maximize" type="bool" value="false"', text)
            self.assertIn('name="theme" type="string" value="StradiLab"', text)

    def test_wallpaper_supports_named_monitors(self) -> None:
        script = (CHROOT / "usr/local/bin/stradilabos-apply-theme").read_text(
            encoding="utf-8"
        )
        self.assertIn("xrandr --query", script)
        self.assertIn("monitor$output", script)
        self.assertIn("xfdesktop --reload", script)

    def test_graphical_authorization_agent_starts_in_xfce(self) -> None:
        packages = (
            ROOT / "config/package-lists/stradilabos-core.list.chroot"
        ).read_text(encoding="utf-8")
        active = set(re.findall(r"^[a-z0-9][a-z0-9+.-]*$", packages, re.M))
        self.assertIn("mate-polkit", active)
        self.assertNotIn("lxpolkit", active)

    def test_app_center_uses_stradilab_palette(self) -> None:
        app_center = (CHROOT / "usr/local/lib/stradilabos/app_center.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("APP_CENTER_CSS", app_center)
        self.assertIn("#9b2335", app_center)
        self.assertIn("#f6f4ef", app_center)


class LeanBaseTests(unittest.TestCase):
    def test_heavy_task_metapackages_are_absent(self) -> None:
        packages = (
            ROOT / "config/package-lists/stradilabos-core.list.chroot"
        ).read_text(encoding="utf-8")
        active_lines = {
            line.strip()
            for line in packages.splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        forbidden = {
            "task-xfce-desktop",
            "task-italian",
            "task-italian-desktop",
            "libreoffice",
            "gnome-software",
            "gnome-software-plugin-flatpak",
            "firmware-linux",
            "firmware-misc-nonfree",
        }
        self.assertFalse(active_lines & forbidden)

    def test_specialist_packages_remain_download_on_demand(self) -> None:
        base = (
            ROOT / "config/package-lists/stradilabos-core.list.chroot"
        ).read_text(encoding="utf-8")
        base_packages = set(re.findall(r"^[a-z0-9][a-z0-9+.-]*$", base, re.M))
        packs = json.loads(
            (CHROOT / "usr/local/share/stradilabos/packs.json").read_text(
                encoding="utf-8"
            )
        )["packs"]
        optional = {name for pack in packs for name in pack["packages"]}
        self.assertFalse(base_packages & optional)
        for hook in (ROOT / "config/hooks/live").glob("*.hook.chroot"):
            self.assertNotIn("flatpak install", hook.read_text(encoding="utf-8"))

        fashion_launcher = (
            CHROOT
            / "usr/local/share/applications/stradilabos-cad-moda.desktop"
        ).read_text(encoding="utf-8")
        self.assertIn("NoDisplay=true", fashion_launcher)
        backend = (CHROOT / "usr/local/lib/stradilabos/install_pack.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("FLATPAK_LAUNCHERS", backend)

    def test_flatpak_launcher_appears_only_after_successful_install(self) -> None:
        module = load_install_module()
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            catalog = temporary / "packs.json"
            catalog.write_text(
                json.dumps(
                    {
                        "packs": [
                            {
                                "id": "moda",
                                "packages": [],
                                "flatpaks": ["io.seamly.seamly2d"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            launcher = temporary / "stradilabos-cad-moda.desktop"
            launcher.write_text(
                "[Desktop Entry]\nName=CAD Moda\nNoDisplay=true\n",
                encoding="utf-8",
            )
            module.CATALOG = catalog
            module.FLATPAK_LAUNCHERS = {"io.seamly.seamly2d": launcher}
            completed = SimpleNamespace(returncode=0)
            with mock.patch.object(module.os, "geteuid", return_value=0), mock.patch.object(
                module.subprocess, "run", return_value=completed
            ) as run:
                self.assertEqual(module.main(["moda"]), 0)

            self.assertNotIn("NoDisplay=true", launcher.read_text(encoding="utf-8"))
            commands = [call.args[0] for call in run.call_args_list]
            self.assertIn(
                [
                    "flatpak",
                    "install",
                    "--system",
                    "--noninteractive",
                    "flathub",
                    "io.seamly.seamly2d",
                ],
                commands,
            )


if __name__ == "__main__":
    unittest.main()

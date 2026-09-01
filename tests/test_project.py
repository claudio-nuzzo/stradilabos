from __future__ import annotations

import ast
import importlib.util
import json
import os
import subprocess
import tempfile
import re
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
            self.assertIn('name="button_layout" type="string" value="CHM|O"', text)
            self.assertIn('name="borderless_maximize" type="bool" value="false"', text)
            self.assertIn('name="titleless_maximize" type="bool" value="false"', text)
            self.assertIn('name="use_compositing" type="bool" value="false"', text)
            self.assertIn('name="theme" type="string" value="WhiteSur-Light"', text)

    def test_both_panels_have_ordered_ids_and_named_plugins(self) -> None:
        """Previene il plugin “(null)” e la scomparsa della barra inferiore."""
        for relative in (
            "etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml",
            "etc/xdg/xfce4/panel/default.xml",
        ):
            path = CHROOT / relative
            root = ET.parse(path).getroot()
            panels = root.find("./property[@name='panels']")
            plugins = root.find("./property[@name='plugins']")
            self.assertIsNotNone(panels, path)
            self.assertIsNotNone(plugins, path)
            assert panels is not None and plugins is not None

            children = list(panels)
            panel_ids = [
                child.get("value")
                for child in children
                if child.tag == "value" and child.get("type") == "int"
            ]
            self.assertEqual(panel_ids, ["1", "2"], path)
            value_positions = [index for index, child in enumerate(children) if child.tag == "value"]
            panel_positions = [
                index
                for index, child in enumerate(children)
                if child.tag == "property" and child.get("name", "").startswith("panel-")
            ]
            self.assertLess(max(value_positions), min(panel_positions), path)

            definitions = {
                child.get("name"): child.get("value")
                for child in plugins
                if child.tag == "property"
            }
            for panel_id in panel_ids:
                panel = panels.find(f"./property[@name='panel-{panel_id}']")
                self.assertIsNotNone(panel, path)
                assert panel is not None
                plugin_ids = panel.find("./property[@name='plugin-ids']")
                self.assertIsNotNone(plugin_ids, path)
                assert plugin_ids is not None
                for value in plugin_ids.findall("./value"):
                    self.assertTrue(definitions.get(f"plugin-{value.get('value')}"), path)

    def test_panel_repair_replaces_the_broken_personal_layout(self) -> None:
        repair = CHROOT / "usr/local/bin/stradilabos-repair-panel"
        default = CHROOT / "etc/xdg/xfce4/panel/default.xml"
        self.assertTrue(os.access(repair, os.X_OK))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_home = root / "config"
            personal = config_home / "xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml"
            personal.parent.mkdir(parents=True)
            valid_text = default.read_text(encoding="utf-8")
            id_two = '    <value type="int" value="2"/>\n'
            broken_text = valid_text.replace(id_two, "", 1).replace(
                '    <property name="panel-2" type="empty">',
                id_two + '    <property name="panel-2" type="empty">',
                1,
            )
            personal.write_text(broken_text, encoding="utf-8")
            marker = config_home / "stradilabos/panel-layout-v4"
            marker.parent.mkdir(parents=True)
            marker.touch()

            fake_bin = root / "bin"
            fake_bin.mkdir()
            for command in ("xfce4-panel", "xfconf-query", "xfconfd"):
                stub = fake_bin / command
                stub.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
                stub.chmod(0o755)
            environment = {
                **os.environ,
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
                "XDG_CONFIG_HOME": str(config_home),
                "STRADILABOS_PANEL_DEFAULT": str(default),
                "STRADILABOS_PANEL_RESTART_DELAY": "0",
            }
            result = subprocess.run(
                ["sh", str(repair), "--force"], env=environment, check=False
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(personal.read_text(encoding="utf-8"), valid_text)
            self.assertEqual(
                personal.with_name("xfce4-panel.xml.stradilabos-backup").read_text(encoding="utf-8"),
                broken_text,
            )
            self.assertTrue(marker.exists())

    def test_wifi_chooser_handles_escaped_network_names(self) -> None:
        wifi = CHROOT / "usr/local/bin/stradilabos-wifi"
        self.assertTrue(os.access(wifi, os.X_OK))
        tree = ast.parse(wifi.read_text(encoding="utf-8"))
        split_function = next(
            node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "split_nmcli"
        )
        namespace: dict[str, object] = {}
        exec(compile(ast.Module(body=[split_function], type_ignores=[]), str(wifi), "exec"), namespace)
        split_nmcli = namespace["split_nmcli"]
        self.assertEqual(
            split_nmcli(r"*:Aula\:Musica:87:WPA2"),
            ["*", "Aula:Musica", "87", "WPA2"],
        )
        welcome = (CHROOT / "usr/local/lib/stradilabos/welcome.py").read_text(encoding="utf-8")
        self.assertIn('self.launch(["stradilabos-wifi"])', welcome)
        wifi_text = wifi.read_text(encoding="utf-8")
        self.assertIn("STRADILAB · RETE", wifi_text)
        self.assertIn('set_icon_name("network-wireless")', wifi_text)
        self.assertIn("Vuoi scaricare e installare ora", wifi_text)
        self.assertIn("subprocess.Popen([pkexec, updater])", wifi_text)

    def test_built_image_validator_tracks_the_current_desktop_theme(self) -> None:
        text = (ROOT / "scripts/validate_built_image.sh").read_text(encoding="utf-8")
        self.assertIn("usr/share/themes/WhiteSur-Light/xfwm4/themerc", text)
        self.assertIn("usr/share/themes/WhiteSur-Light/gtk-3.0/gtk.css", text)
        self.assertIn("usr/share/icons/WhiteSur/index.theme", text)
        self.assertIn('value="WhiteSur-Light"', text)
        self.assertNotIn("usr/share/themes/StradiLab/xfwm4/themerc", text)

    def test_update_client_applies_a_local_series_once(self) -> None:
        """Un PC già installato applica una serie senza ricostruire una ISO."""
        client = CHROOT / "usr/local/bin/stradilabos-update"
        mirror = ROOT / "updates/stradilabos-update"
        self.assertEqual(client.read_text(encoding="utf-8"), mirror.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            channel = root / "channel"
            channel.mkdir()
            (channel / "version.txt").write_text("42\n", encoding="utf-8")
            marker = root / "payload-runs"
            (channel / "update.sh").write_text(
                '#!/bin/sh\nprintf "ok\\n" >> "$STRADILABOS_TEST_MARKER"\n',
                encoding="utf-8",
            )
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_id = fake_bin / "id"
            fake_id.write_text("#!/bin/sh\nprintf '0\\n'\n", encoding="utf-8")
            fake_id.chmod(0o755)
            state = root / "state"
            log = root / "update.log"
            environment = {
                **os.environ,
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
                "STRADILABOS_UPDATE_BASE_URL": channel.as_uri(),
                "STRADILABOS_UPDATE_STATE_DIR": str(state),
                "STRADILABOS_UPDATE_LOG": str(log),
                "STRADILABOS_TEST_MARKER": str(marker),
            }
            first = subprocess.run(["bash", str(client)], env=environment, check=False)
            second = subprocess.run(["bash", str(client)], env=environment, check=False)

            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 0)
            self.assertEqual((state / "update-serial").read_text(encoding="utf-8").strip(), "42")
            self.assertEqual(marker.read_text(encoding="utf-8").splitlines(), ["ok"])

            # Un payload non riuscito non deve avanzare la serie: il timer lo
            # ritenterà senza chiedere di reinstallare il sistema.
            (channel / "version.txt").write_text("43\n", encoding="utf-8")
            (channel / "update.sh").write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
            failed = subprocess.run(["bash", str(client)], env=environment, check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual((state / "update-serial").read_text(encoding="utf-8").strip(), "42")

    def test_window_manager_guard_is_installed_and_bounded(self) -> None:
        guard = CHROOT / "usr/local/bin/stradilabos-window-manager-guard"
        self.assertTrue(guard.exists())
        self.assertTrue(os.access(guard, os.X_OK))
        text = guard.read_text(encoding="utf-8")
        self.assertIn("--vblank=off", text)
        self.assertIn("--compositor=off", text)
        self.assertIn("Greybird", text)
        self.assertIn("max_attempts=3", text)
        self.assertIn("logger -t", text)
        self.assertIn("notify-send", text)
        self.assertIn("inizializzazione preventiva di xfwm4", text)
        self.assertIn("xfwm4 --replace --compositor=off", text)
        self.assertIn("startup_grace=${STRADILABOS_WM_GRACE:-2}", text)
        self.assertIn("disable_compositing", text)
        self.assertIn("/general/use_compositing", text)
        autostart = (
            CHROOT / "etc/xdg/autostart/stradilabos-window-manager.desktop"
        ).read_text(encoding="utf-8")
        self.assertIn("Exec=stradilabos-window-manager-guard", autostart)
        self.assertIn("OnlyShowIn=XFCE;", autostart)
        packages = (
            ROOT / "config/package-lists/stradilabos-core.list.chroot"
        ).read_text(encoding="utf-8")
        active = set(re.findall(r"^[a-z0-9][a-z0-9+.-]*$", packages, re.M))
        self.assertIn("x11-utils", active)
        self.assertIn("libnotify-bin", active)

    def test_window_manager_runtime_check_exists(self) -> None:
        script = ROOT / "scripts/test_window_manager_xvfb.sh"
        self.assertTrue(script.exists())
        text = script.read_text(encoding="utf-8")
        self.assertIn("_NET_FRAME_EXTENTS", text)
        self.assertIn("stradilabos-window-manager-guard", text)
        for workflow in ("build-iso.yml", "build-arm64.yml"):
            yaml_text = (ROOT / ".github/workflows" / workflow).read_text(
                encoding="utf-8"
            )
            self.assertIn("scripts/test_window_manager_xvfb.sh", yaml_text)
            self.assertIn("scripts/test_panel_xvfb.sh", yaml_text)
            self.assertIn("scripts/test_wifi_xvfb.sh", yaml_text)
            self.assertIn("timeout 60s sh scripts/test_panel_xvfb.sh", yaml_text)
            self.assertIn("timeout 60s sh scripts/test_wifi_xvfb.sh", yaml_text)

        panel_test = ROOT / "scripts/test_panel_xvfb.sh"
        self.assertTrue(os.access(panel_test, os.X_OK))
        panel_test_text = panel_test.read_text(encoding="utf-8")
        self.assertIn("xfce4-panel --disable-wm-check", panel_test_text)
        self.assertIn("plugin_name.*NULL", panel_test_text)

        wifi_test = ROOT / "scripts/test_wifi_xvfb.sh"
        self.assertTrue(os.access(wifi_test, os.X_OK))
        self.assertIn("stradilabos-wifi", wifi_test.read_text(encoding="utf-8"))

    def test_grub_fixes_cover_live_installed_and_ota(self) -> None:
        theme = (CHROOT / "usr/share/grub/themes/stradilabos/theme.txt").read_text(
            encoding="utf-8"
        )
        self.assertNotIn('terminal-box: "0"', theme)
        installed = (CHROOT / "etc/default/grub.d/60-stradilabos.cfg").read_text(
            encoding="utf-8"
        )
        self.assertIn('GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=3"', installed)
        self.assertIn("quiet splash loglevel=3", (ROOT / "auto/config").read_text(encoding="utf-8"))
        self.assertEqual((ROOT / "updates/version.txt").read_text(encoding="utf-8").strip(), "4")
        update = (ROOT / "updates/update.sh").read_text(encoding="utf-8")
        self.assertIn("usr/share/grub/themes/stradilabos", update)
        self.assertIn("update-grub || return 1", update)
        self.assertIn("xfce4-power-manager-plugins", update)
        self.assertIn("xfce4-pulseaudio-plugin", update)
        self.assertIn("repair_existing_panel_profiles", update)
        self.assertIn("stradilabos-repair-panel --force", update)

    def test_container_workflows_fail_on_intermediate_errors(self) -> None:
        workflows = ROOT / ".github/workflows"
        for name in ("build-iso.yml", "build-arm64.yml", "validate-wm-trixie.yml"):
            text = (workflows / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertNotIn("sh -lc '", text)
                self.assertIn("sh -euc '", text)

        validation = (workflows / "validate-wm-trixie.yml").read_text(
            encoding="utf-8"
        )
        self.assertGreaterEqual(validation.count("python3"), 2)

        package_validator = (
            ROOT / "scripts/validate_debian_packages.sh"
        ).read_text(encoding="utf-8")
        self.assertIn("command -v python3", package_validator)

    def test_iso_builds_require_manual_approval(self) -> None:
        for name in ("build-iso.yml", "build-arm64.yml"):
            text = (ROOT / ".github/workflows" / name).read_text(encoding="utf-8")
            with self.subTest(workflow=name):
                self.assertIn("workflow_dispatch:", text)
                self.assertNotRegex(text, r"(?m)^\s{2}push:\s*$")

    def test_xfce_preflight_uses_the_real_autostart_path(self) -> None:
        text = (ROOT / "scripts/preflight_xfce_session.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('"$config_home/autostart"', text)
        self.assertIn("la guardia non è stata avviata dall'autostart Xfce", text)
        self.assertNotIn('"$GUARD" &', text)

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

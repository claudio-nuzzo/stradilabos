#!/bin/sh
set -eu

binary_dir=${1:-binary}
grub_dir=$binary_dir/boot/grub
squashfs=$binary_dir/live/filesystem.squashfs

fail() {
    printf '%s\n' "Controllo ISO fallito: $1" >&2
    exit 1
}

[ -s "$grub_dir/grub.cfg" ] || fail "grub.cfg assente"
[ -s "$grub_dir/splash.png" ] || fail "sfondo GRUB assente"
[ -s "$grub_dir/live-theme/theme.txt" ] || fail "tema GRUB assente"
[ -s "$binary_dir/.disk/info" ] || fail "metadati ISO assenti"
[ -s "$squashfs" ] || fail "filesystem Live assente"

cmp -s config/branding/stradilabos-boot-800x600.png "$grub_dir/splash.png" || \
    fail "lo sfondo GRUB non è quello StradiLabOS"
grep -q "Prova StradiLabOS" "$grub_dir/grub.cfg" || \
    fail "il menu Live conserva il nome Debian"
grep -q "quiet splash loglevel=3" "$grub_dir/grub.cfg" || \
    fail "il menu Live non filtra i messaggi firmware non critici"
grep -q "StradiLabOS 0.3" "$binary_dir/.disk/info" || \
    fail "il supporto non si identifica come StradiLabOS"

os_release=$(unsquashfs -cat "$squashfs" usr/lib/os-release 2>/dev/null) || \
    fail "os-release non leggibile"
printf '%s\n' "$os_release" | grep -q '^NAME="StradiLabOS"$' || \
    fail "il sistema interno non si identifica come StradiLabOS"
printf '%s\n' "$os_release" | grep -q '^ID_LIKE=debian$' || \
    fail "la compatibilità Debian non è dichiarata"

workspace_policy=$(unsquashfs -cat \
    "$squashfs" etc/chromium/policies/managed/stradilabos-workspace.json \
    2>/dev/null) || fail "criterio Workspace assente"
printf '%s\n' "$workspace_policy" | grep -q '"istitutostradivari.it"' || \
    fail "dominio Workspace errato"
printf '%s\n' "$workspace_policy" | grep -q '"TranslateEnabled"[[:space:]]*:[[:space:]]*false' || \
    fail "popup di traduzione non disattivato"
printf '%s\n' "$workspace_policy" | grep -q '"PasswordManagerEnabled"[[:space:]]*:[[:space:]]*false' || \
    fail "salvataggio password non disattivato"

app_opener=$(unsquashfs -cat "$squashfs" usr/local/bin/stradilabos-open-app 2>/dev/null) || \
    fail "avviatore web app assente"
printf '%s\n' "$app_opener" | grep -q -- '--password-store=basic' || \
    fail "le web app possono chiedere il portachiavi"

lightdm_hardware=$(unsquashfs -cat \
    "$squashfs" etc/lightdm/lightdm.conf.d/50-stradilabos-hardware.conf \
    2>/dev/null) || fail "compatibilità LightDM assente"
printf '%s\n' "$lightdm_hardware" | grep -Eq \
    '^[[:space:]]*logind-check-graphical[[:space:]]*=[[:space:]]*false[[:space:]]*$' || \
    fail "LightDM può restare bloccato in attesa di CanGraphical"

plymouth_config=$(unsquashfs -cat "$squashfs" etc/plymouth/plymouthd.conf 2>/dev/null) || \
    fail "configurazione Plymouth assente"
printf '%s\n' "$plymouth_config" | grep -q 'Theme=stradilabos' || \
    fail "tema Plymouth non attivato"

for path in \
    etc/calamares/modules/stradilabos-workspace.conf \
    etc/xdg/autostart/polkit-mate-authentication-agent-1.desktop \
    etc/lightdm/lightdm-gtk-greeter.conf.d/60-stradilabos.conf \
    usr/lib/tmpfiles.d/stradilabos-lightdm.conf \
    usr/share/polkit-1/actions/org.stradilab.stradilabos.policy \
    usr/share/themes/WhiteSur-Light/xfwm4/themerc \
    usr/share/themes/WhiteSur-Light/gtk-3.0/gtk.css \
    usr/share/icons/WhiteSur/index.theme \
    usr/local/bin/stradilabos-window-manager-guard \
    usr/local/bin/stradilabos-window-diagnostics \
    usr/local/bin/stradilabos-repair-panel \
    usr/local/bin/stradilabos-wifi \
    etc/default/grub.d/60-stradilabos.cfg \
    usr/share/grub/themes/stradilabos/theme.txt \
    etc/xdg/autostart/stradilabos-window-manager.desktop \
    etc/xdg/autostart/stradilabos-repair-panel.desktop \
    etc/xdg/autostart/stradilabos-wallpaper-contrast.desktop \
    usr/bin/xprop \
    usr/bin/notify-send \
    usr/bin/xfwm4 \
    etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml \
    usr/share/backgrounds/stradilabos/stradilabos-wallpaper-v3.png \
    usr/local/share/stradilabos/guide/index.html \
    usr/local/share/stradilabos/guide/css/guida.css \
    usr/local/bin/stradilabos-guide \
    usr/local/bin/stradilabos-browser \
    usr/local/bin/stradilabos-update-ui \
    usr/local/bin/stradilabos-wallpaper-contrast \
    usr/local/share/applications/stradilabos-guide.desktop \
    usr/local/share/applications/stradilabos-update.desktop \
    etc/skel/.config/gtk-3.0/stradilabos-desktop-contrast.css \
    usr/share/plymouth/themes/stradilabos/stradilabos.script; do
    unsquashfs -cat "$squashfs" "$path" >/dev/null 2>&1 || \
        fail "file interno assente: $path"
done

installed_grub=$(unsquashfs -cat \
    "$squashfs" etc/default/grub.d/60-stradilabos.cfg \
    2>/dev/null) || fail "configurazione GRUB installata assente"
printf '%s\n' "$installed_grub" | grep -q \
    'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash loglevel=3"' || \
    fail "il sistema installato non filtra i messaggi firmware non critici"

installed_grub_theme=$(unsquashfs -cat \
    "$squashfs" usr/share/grub/themes/stradilabos/theme.txt \
    2>/dev/null) || fail "tema GRUB installato assente"
if printf '%s\n' "$installed_grub_theme" | grep -q 'terminal-box: "0"'; then
    fail "il tema GRUB contiene il pattern pixmap non valido"
fi

greeter_theme=$(unsquashfs -cat \
    "$squashfs" etc/lightdm/lightdm-gtk-greeter.conf.d/60-stradilabos.conf \
    2>/dev/null) || fail "tema del login assente"
printf '%s\n' "$greeter_theme" | grep -q '^theme-name=StradiLab$' || \
    fail "login fuori dal tema StradiLab"

if unsquashfs -ll "$squashfs" 2>/dev/null | \
    grep -q 'var/lib/flatpak/app/io\.seamly\.seamly2d/'; then
    fail "Seamly2D è ancora incorporato nella ISO base"
fi

fashion_launcher=$(unsquashfs -cat \
    "$squashfs" usr/local/share/applications/stradilabos-cad-moda.desktop \
    2>/dev/null) || fail "launcher CAD Moda assente"
printf '%s\n' "$fashion_launcher" | grep -q '^NoDisplay=true$' || \
    fail "il CAD Moda appare prima del download"

polkit_autostart=$(unsquashfs -cat \
    "$squashfs" etc/xdg/autostart/polkit-mate-authentication-agent-1.desktop \
    2>/dev/null) || fail "avvio dell'agente di autorizzazione assente"
printf '%s\n' "$polkit_autostart" | grep -q \
    '^Exec=/usr/libexec/polkit-mate-authentication-agent-1$' || \
    fail "agente di autorizzazione errato"
printf '%s\n' "$polkit_autostart" | grep -q '^NotShowIn=GNOME;KDE;$' || \
    fail "agente di autorizzazione disattivato nelle sessioni grafiche"

xfwm_config=$(unsquashfs -cat \
    "$squashfs" etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfwm4.xml \
    2>/dev/null) || fail "configurazione finestre assente"
printf '%s\n' "$xfwm_config" | grep -q 'value="WhiteSur-Light"' || \
    fail "tema finestre WhiteSur non selezionato"
printf '%s\n' "$xfwm_config" | grep -q 'name="borderless_maximize" type="bool" value="false"' || \
    fail "le finestre massimizzate possono perdere i bordi"

panel_config=$(unsquashfs -cat \
    "$squashfs" etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml \
    2>/dev/null) || fail "configurazione barra applicazioni assente"
printf '%s\n' "$panel_config" | grep -q 'name="position" type="string" value="p=12;' || \
    fail "la barra applicazioni non è ancorata in basso"
printf '%s\n' "$panel_config" | grep -q 'value="actions"' || \
    fail "menu utente e spegnimento assente dalla barra"
printf '%s\n' "$panel_config" | grep -q 'value="+shutdown"' || \
    fail "spegnimento assente dal menu di sessione"

wm_autostart=$(unsquashfs -cat \
    "$squashfs" etc/xdg/autostart/stradilabos-window-manager.desktop \
    2>/dev/null) || fail "avvio della guardia finestre assente"
printf '%s\n' "$wm_autostart" | grep -q '^Exec=stradilabos-window-manager-guard$' || \
    fail "guardia del gestore delle finestre non avviata"

for launcher in \
    xfce4-terminal.desktop \
    xfce4-terminal-settings.desktop \
    xfce4-terminal-emulator.desktop; do
    terminal_entry=$(unsquashfs -cat \
        "$squashfs" "usr/local/share/applications/$launcher" 2>/dev/null) || \
        fail "override del terminale assente: $launcher"
    printf '%s\n' "$terminal_entry" | grep -q '^NoDisplay=true$' || \
        fail "voce terminale ancora visibile: $launcher"
done

printf '%s\n' "Controlli sull'immagine StradiLabOS superati."

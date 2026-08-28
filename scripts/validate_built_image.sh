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
    fail "lo sfondo GRUB non è quello StradilabOS"
grep -q "Prova StradilabOS" "$grub_dir/grub.cfg" || \
    fail "il menu Live conserva il nome Debian"
grep -q "StradilabOS 0.2" "$binary_dir/.disk/info" || \
    fail "il supporto non si identifica come StradilabOS"

os_release=$(unsquashfs -cat "$squashfs" usr/lib/os-release 2>/dev/null) || \
    fail "os-release non leggibile"
printf '%s\n' "$os_release" | grep -q '^NAME="StradilabOS"$' || \
    fail "il sistema interno non si identifica come StradilabOS"
printf '%s\n' "$os_release" | grep -q '^ID_LIKE=debian$' || \
    fail "la compatibilità Debian non è dichiarata"

workspace_policy=$(unsquashfs -cat \
    "$squashfs" etc/chromium/policies/managed/stradilabos-workspace.json \
    2>/dev/null) || fail "criterio Workspace assente"
printf '%s\n' "$workspace_policy" | grep -q '"istitutostradivari.it"' || \
    fail "dominio Workspace errato"

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
    etc/lightdm/lightdm-gtk-greeter.conf.d/60-stradilabos.conf \
    etc/skel/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml \
    usr/share/backgrounds/stradilabos/stradilabos-wallpaper-v2.png \
    usr/share/plymouth/themes/stradilabos/stradilabos.script; do
    unsquashfs -cat "$squashfs" "$path" >/dev/null 2>&1 || \
        fail "file interno assente: $path"
done

printf '%s\n' "Controlli sull'immagine StradilabOS superati."

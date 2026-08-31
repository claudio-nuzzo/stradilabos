#!/bin/bash
# StradilabOS — aggiornamento cumulativo, serie 2 (2026-08-31)
#
# È pensato anche per PC già installati con la 0.2: scarica soltanto il
# materiale pubblicato dal repository ufficiale, aggiorna i file posseduti da
# StradilabOS e non richiede di reinstallare o ricreare l'immagine ISO.
set -u

SOURCE_ARCHIVE_URL="${STRADILABOS_UPDATE_SOURCE_ARCHIVE_URL:-https://codeload.github.com/claudio-nuzzo/stradilabos/tar.gz/refs/heads/main}"
update_tmpdir=$(mktemp -d)
trap 'rm -rf "$update_tmpdir"' EXIT

fetch() {
  # $1 = URL, $2 = file di destinazione
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --connect-timeout 20 -o "$2" "$1"
  else
    wget -q --timeout=20 -O "$2" "$1"
  fi
}

install_cookie_policy() {
  local policy
  policy='{
  "BlockThirdPartyCookies": false,
  "CookiesAllowedForUrls": [
    "https://[*.]google.com",
    "https://[*.]googleusercontent.com",
    "https://[*.]gstatic.com"
  ]
}'

  for dir in /etc/chromium/policies/managed /etc/chromium-browser/policies/managed; do
    mkdir -p "$dir" || return 1
    printf '%s\n' "$policy" > "$dir/stradilabos-cookies.json" || return 1
  done
}

copy_tree() {
  # $1 = origine, $2 = destinazione; non cancella mai file utente.
  [ -d "$1" ] || return 0
  mkdir -p "$2"
  cp -a "$1/." "$2/"
}

sync_0_3_interface() {
  local archive source_root source_file unit file
  archive="$update_tmpdir/stradilabos-main.tar.gz"

  if ! fetch "$SOURCE_ARCHIVE_URL" "$archive"; then
    echo "ERRORE: non riesco a scaricare l'interfaccia 0.3; la serie sarà ritentata." >&2
    return 1
  fi
  if ! tar -xzf "$archive" -C "$update_tmpdir"; then
    echo "ERRORE: archivio dell'interfaccia non valido; la serie sarà ritentata." >&2
    return 1
  fi
  source_root=$(find "$update_tmpdir" -mindepth 1 -maxdepth 1 -type d -name 'stradilabos-*' -print -quit)
  if [ -z "$source_root" ] || [ ! -d "$source_root/config/includes.chroot" ]; then
    echo "ERRORE: struttura dell'archivio inattesa; la serie sarà ritentata." >&2
    return 1
  fi

  # File applicativi e guide: tutti sotto /usr/local sono di StradilabOS.
  copy_tree "$source_root/config/includes.chroot/usr/local" /usr/local || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/themes/WhiteSur-Light" /usr/share/themes/WhiteSur-Light || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/themes/WhiteSur-Dark" /usr/share/themes/WhiteSur-Dark || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/icons/WhiteSur" /usr/share/icons/WhiteSur || return 1
  copy_tree "$source_root/config/includes.chroot/etc/xdg" /etc/xdg || return 1
  copy_tree "$source_root/config/includes.chroot/etc/skel/.config" /etc/skel/.config || return 1

  install -d /etc/apt/apt.conf.d /usr/share/polkit-1/actions || return 1
  for file in 20auto-upgrades 50unattended-upgrades; do
    source_file="$source_root/config/includes.chroot/etc/apt/apt.conf.d/$file"
    [ -f "$source_file" ] && install -m 0644 "$source_file" "/etc/apt/apt.conf.d/$file" || return 1
  done
  source_file="$source_root/config/includes.chroot/usr/share/polkit-1/actions/org.stradilab.stradilabos.policy"
  [ -f "$source_file" ] && install -m 0644 "$source_file" /usr/share/polkit-1/actions/org.stradilab.stradilabos.policy || return 1

  for unit in stradilabos-update.service stradilabos-update.timer; do
    source_file="$source_root/config/includes.chroot/etc/systemd/system/$unit"
    [ -f "$source_file" ] && install -m 0644 "$source_file" "/etc/systemd/system/$unit" || return 1
  done

  if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/local/share/applications || true
  fi
  if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f /usr/local/share/icons/hicolor || true
    gtk-update-icon-cache -f /usr/share/icons/WhiteSur || true
  fi
  if command -v systemctl >/dev/null 2>&1; then
    systemctl daemon-reload || true
    systemctl enable --now stradilabos-update.timer || true
  fi
}

install_security_updates() {
  # Una 0.2 aggiornata riceve anche unattended-upgrades senza interventi
  # manuali. Se il mirror APT è momentaneamente irraggiungibile, l'aggiornamento
  # dell'interfaccia resta valido e APT ritenterà al prossimo controllo.
  command -v apt-get >/dev/null 2>&1 || return 0
  export DEBIAN_FRONTEND=noninteractive
  if apt-get update -qq && apt-get install -y -qq unattended-upgrades; then
    echo "Aggiornamenti di sicurezza Debian attivati."
  else
    echo "ERRORE: unattended-upgrades non installato ora; la serie sarà ritentata." >&2
    return 1
  fi
}

echo "— Serie 2: aggiornamento cumulativo StradilabOS 0.3 —"
install_cookie_policy
sync_0_3_interface || exit 1
install_security_updates || exit 1
echo "Aggiornamento cumulativo completato: nessuna reinstallazione necessaria."

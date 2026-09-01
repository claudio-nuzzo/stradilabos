#!/bin/bash
# StradilabOS — aggiornamento cumulativo, serie 7 (2026-09-01)
#
# È pensato anche per PC già installati con la 0.2: scarica soltanto il
# materiale pubblicato dal repository ufficiale, aggiorna i file posseduti da
# StradilabOS e non richiede di reinstallare o ricreare l'immagine ISO.
set -u

SOURCE_ARCHIVE_URL="${STRADILABOS_UPDATE_SOURCE_ARCHIVE_URL:-https://codeload.github.com/claudio-nuzzo/stradilabos/tar.gz/refs/heads/main}"
WALLPAPER_BASE_URL="${STRADILABOS_WALLPAPER_BASE_URL:-https://raw.githubusercontent.com/claudio-nuzzo/stradilabos/main/config/includes.chroot/usr/share/backgrounds/stradilabos}"
WALLPAPER_INSTALL_DIR="${STRADILABOS_WALLPAPER_INSTALL_DIR:-/usr/share/backgrounds/stradilabos}"
LOCAL_SERIES="${STRADILABOS_UPDATE_LOCAL_SERIAL:-$(cat /var/lib/stradilabos/update-serial 2>/dev/null || echo 0)}"
case "$LOCAL_SERIES" in (*[!0-9]*|'') LOCAL_SERIES=0;; esac
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

install_study_wallpapers() {
  # La serie grafica pesa circa 2 MB: sui PC già alla serie 6 viene scaricata
  # direttamente, senza trasferire di nuovo l'intero repository e gli asset
  # WhiteSur. Gli hash impediscono di installare download troncati o inattesi.
  local expected name downloaded actual
  while read -r expected name; do
    [ -n "$expected" ] || continue
    downloaded="$update_tmpdir/$name"
    if ! fetch "$WALLPAPER_BASE_URL/$name" "$downloaded"; then
      echo "ERRORE: download dello sfondo $name non riuscito; la serie sarà ritentata." >&2
      return 1
    fi
    if command -v sha256sum >/dev/null 2>&1; then
      actual=$(sha256sum "$downloaded" | awk '{print $1}')
    elif command -v shasum >/dev/null 2>&1; then
      actual=$(shasum -a 256 "$downloaded" | awk '{print $1}')
    else
      echo "ERRORE: verifica SHA-256 non disponibile; nessuno sfondo installato." >&2
      return 1
    fi
    if [ "$actual" != "$expected" ]; then
      echo "ERRORE: verifica SHA-256 fallita per $name; nessuno sfondo installato." >&2
      return 1
    fi
  done <<'WALLPAPERS'
78a6a636a0e4c964272ff0d6346c0156a43e11374b5d7ee5fec32a55f8eb5d62 StradiLabOS-Arredo-e-Architettura.jpg
6984911e6c5f0c49d1e7f6b6d7318e1191d278d489c1c49123f89ed1edb093cf StradiLabOS-Liceo-Artistico.jpg
40f3a87bceb4a402578dc3ef7cc9eae31ee456895c2ea9441ce76c2f5a819e4e StradiLabOS-Liceo-Musicale.jpg
3789ea04f8e7a9bc183f21907e745c08d42d2e97ee471c383e65530ec6543d15 StradiLabOS-Liuteria.jpg
e59c99ebef2ed7c24e4c73a6acabcd68be457e980ca89f737a5a9a2f0299d299 StradiLabOS-Moda.jpg
WALLPAPERS

  install -d -m 0755 "$WALLPAPER_INSTALL_DIR" || return 1
  while read -r _ name; do
    [ -n "$name" ] || continue
    install -m 0644 "$update_tmpdir/$name" "$WALLPAPER_INSTALL_DIR/.$name.nuovo" || return 1
    mv -f "$WALLPAPER_INSTALL_DIR/.$name.nuovo" "$WALLPAPER_INSTALL_DIR/$name" || return 1
  done <<'WALLPAPERS'
78a6a636a0e4c964272ff0d6346c0156a43e11374b5d7ee5fec32a55f8eb5d62 StradiLabOS-Arredo-e-Architettura.jpg
6984911e6c5f0c49d1e7f6b6d7318e1191d278d489c1c49123f89ed1edb093cf StradiLabOS-Liceo-Artistico.jpg
40f3a87bceb4a402578dc3ef7cc9eae31ee456895c2ea9441ce76c2f5a819e4e StradiLabOS-Liceo-Musicale.jpg
3789ea04f8e7a9bc183f21907e745c08d42d2e97ee471c383e65530ec6543d15 StradiLabOS-Liuteria.jpg
e59c99ebef2ed7c24e4c73a6acabcd68be457e980ca89f737a5a9a2f0299d299 StradiLabOS-Moda.jpg
WALLPAPERS
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
  local archive source_root source_file unit file client_new
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

  # Il client di aggiornamento si sostituirebbe da solo mentre e' in
  # esecuzione: mai riscriverlo con cp sullo stesso inode. Lo togliamo
  # dall'albero e lo installiamo alla fine con un file nuovo + mv atomico,
  # cosi' il processo in corso continua a leggere la vecchia copia.
  client_new="$source_root/config/includes.chroot/usr/local/bin/stradilabos-update"
  if [ -f "$client_new" ]; then
    mv "$client_new" "$update_tmpdir/stradilabos-update.new"
  fi

  # File applicativi e guide: tutti sotto /usr/local sono di StradilabOS.
  copy_tree "$source_root/config/includes.chroot/usr/local" /usr/local || return 1
  # I launcher desktop eseguono direttamente questi comandi. Rendere espliciti
  # i permessi evita che un bit perso nell'archivio provochi “permesso negato”.
  for file in /usr/local/bin/stradilabos-*; do
    [ -f "$file" ] || continue
    chmod 0755 "$file" || return 1
  done
  for file in \
      /usr/local/bin/stradilabos-browser \
      /usr/local/bin/stradilabos-open-app \
      /usr/local/bin/stradilabos-install-chrome; do
    if [ ! -x "$file" ]; then
      echo "ERRORE: componente Chrome mancante dopo l'aggiornamento: $file" >&2
      return 1
    fi
  done
  if [ -f "$update_tmpdir/stradilabos-update.new" ]; then
    install -m 0755 "$update_tmpdir/stradilabos-update.new" /usr/local/bin/stradilabos-update.nuovo || return 1
    mv -f /usr/local/bin/stradilabos-update.nuovo /usr/local/bin/stradilabos-update || return 1
  fi
  copy_tree "$source_root/config/includes.chroot/usr/share/themes/WhiteSur-Light" /usr/share/themes/WhiteSur-Light || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/themes/WhiteSur-Dark" /usr/share/themes/WhiteSur-Dark || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/icons/WhiteSur" /usr/share/icons/WhiteSur || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/icons/StradiLab" /usr/share/icons/StradiLab || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/backgrounds/stradilabos" /usr/share/backgrounds/stradilabos || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/grub/themes/stradilabos" /usr/share/grub/themes/stradilabos || return 1
  copy_tree "$source_root/config/includes.chroot/usr/share/plymouth/themes/stradilabos" /usr/share/plymouth/themes/stradilabos || return 1
  copy_tree "$source_root/config/includes.chroot/etc/xdg" /etc/xdg || return 1
  copy_tree "$source_root/config/includes.chroot/etc/skel/.config" /etc/skel/.config || return 1

  for file in usr/lib/os-release etc/lsb-release etc/issue etc/issue.net; do
    source_file="$source_root/config/includes.chroot/$file"
    if [ -f "$source_file" ]; then
      install -D -m 0644 "$source_file" "/$file" || return 1
    fi
  done
  if command -v update-initramfs >/dev/null 2>&1; then
    update-initramfs -u || return 1
  fi

  source_file="$source_root/config/includes.chroot/etc/default/grub.d/60-stradilabos.cfg"
  if [ -f "$source_file" ]; then
    install -d /etc/default/grub.d || return 1
    install -m 0644 "$source_file" /etc/default/grub.d/60-stradilabos.cfg || return 1
    if command -v update-grub >/dev/null 2>&1; then
      update-grub || return 1
    fi
  fi

  install -d /etc/apt/apt.conf.d /usr/share/polkit-1/actions || return 1
  for file in 20auto-upgrades 50unattended-upgrades; do
    source_file="$source_root/config/includes.chroot/etc/apt/apt.conf.d/$file"
    if [ -f "$source_file" ]; then
      install -m 0644 "$source_file" "/etc/apt/apt.conf.d/$file" || return 1
    fi
  done
  source_file="$source_root/config/includes.chroot/usr/share/polkit-1/actions/org.stradilab.stradilabos.policy"
  if [ -f "$source_file" ]; then
    install -m 0644 "$source_file" /usr/share/polkit-1/actions/org.stradilab.stradilabos.policy || return 1
  fi

  for unit in stradilabos-update.service stradilabos-update.timer; do
    source_file="$source_root/config/includes.chroot/etc/systemd/system/$unit"
    if [ -f "$source_file" ]; then
      install -m 0644 "$source_file" "/etc/systemd/system/$unit" || return 1
    fi
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

repair_existing_panel_profiles() {
  # L'autostart di Xfce viene eseguito dopo che il pannello ha già letto la
  # configurazione personale: sui PC installati il dialogo “(null)” può quindi
  # comparire prima della riparazione. Migriamo qui i profili esistenti, usando
  # la sessione D-Bus dell'utente quando è attiva e conservando il backup.
  local user uid home runtime_dir bus_address launcher_source launcher_target
  if ! command -v runuser >/dev/null 2>&1; then
    echo "ERRORE: runuser non disponibile; impossibile migrare il pannello utente." >&2
    return 1
  fi
  if [ ! -x /usr/local/bin/stradilabos-repair-panel ]; then
    echo "ERRORE: riparatore del pannello non installato." >&2
    return 1
  fi

  while IFS=: read -r user _ uid _ _ home _; do
    [ "$uid" -ge 1000 ] 2>/dev/null || continue
    [ "$uid" -lt 60000 ] 2>/dev/null || continue
    case "$home" in
      /home/*) ;;
      *) continue ;;
    esac
    runtime_dir="/run/user/$uid"
    bus_address="unix:path=$runtime_dir/bus"
    if [ -f "$home/.config/xfce4/xfconf/xfce-perchannel-xml/xfce4-panel.xml" ]; then
      launcher_source=/etc/skel/.config/xfce4/panel/launcher-21/chromium.desktop
      launcher_target="$home/.config/xfce4/panel/launcher-21/chromium.desktop"
      if [ -f "$launcher_source" ]; then
        runuser -u "$user" -- install -D -m 0644 \
          "$launcher_source" "$launcher_target" || return 1
      fi

      runuser -u "$user" -- env \
        HOME="$home" USER="$user" LOGNAME="$user" \
        XDG_CONFIG_HOME="$home/.config" \
        XDG_RUNTIME_DIR="$runtime_dir" \
        DBUS_SESSION_BUS_ADDRESS="$bus_address" \
        DISPLAY="${DISPLAY:-:0}" \
        XAUTHORITY="$home/.Xauthority" \
        STRADILABOS_PANEL_DEFAULT=/etc/xdg/xfce4/panel/default.xml \
        STRADILABOS_PANEL_RESTART_DELAY=0 \
        /usr/local/bin/stradilabos-repair-panel --force || return 1
    fi

    if [ -x /usr/local/bin/stradilabos-wallpaper-contrast ]; then
      runuser -u "$user" -- env \
        HOME="$home" USER="$user" LOGNAME="$user" \
        XDG_CONFIG_HOME="$home/.config" \
        XDG_RUNTIME_DIR="$runtime_dir" \
        DBUS_SESSION_BUS_ADDRESS="$bus_address" \
        DISPLAY="${DISPLAY:-:0}" \
        XAUTHORITY="$home/.Xauthority" \
        /usr/local/bin/stradilabos-wallpaper-contrast --once || return 1
    fi
  done < /etc/passwd
}

install_security_updates() {
  # Una 0.2 aggiornata riceve anche unattended-upgrades senza interventi
  # manuali. Se il mirror APT è momentaneamente irraggiungibile, l'aggiornamento
  # dell'interfaccia resta valido e APT ritenterà al prossimo controllo.
  command -v apt-get >/dev/null 2>&1 || return 0
  export DEBIAN_FRONTEND=noninteractive
  if apt-get update -qq && apt-get install -y -qq \
      unattended-upgrades \
      xfce4-power-manager-plugins \
      xfce4-pulseaudio-plugin; then
    echo "Aggiornamenti di sicurezza e plugin dei pannelli attivati."
  else
    echo "ERRORE: unattended-upgrades non installato ora; la serie sarà ritentata." >&2
    return 1
  fi
}

echo "— Serie 7: sfondi per indirizzo e aggiornamenti StradiLabOS 0.3 —"
if [ "$LOCAL_SERIES" -lt 6 ]; then
  install_cookie_policy || exit 1
  sync_0_3_interface || exit 1
  repair_existing_panel_profiles || exit 1
  install_security_updates || exit 1
fi
install_study_wallpapers || exit 1
echo "Installati i cinque sfondi StradiLabOS per indirizzo: nessuna reinstallazione necessaria."

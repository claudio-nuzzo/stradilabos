#!/bin/bash
# install-updater.sh — installazione una tantum dell'aggiornatore StradilabOS
# sui PC gia' installati con la ISO 0.2 (dalla 0.3 e' incluso di serie).
# Uso: sudo bash -c "$(curl -fsSL https://raw.githubusercontent.com/claudio-nuzzo/stradilabos/main/updates/install-updater.sh)"
set -eu

BASE_URL="https://raw.githubusercontent.com/claudio-nuzzo/stradilabos/main/updates"

if [ "$(id -u)" -ne 0 ]; then
  echo "Eseguire come amministratore: sudo bash -c \"\$(curl -fsSL $BASE_URL/install-updater.sh)\"" >&2
  exit 1
fi

fetch() {
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL --connect-timeout 15 -o "$2" "$1"
  else
    wget -q --timeout=15 -O "$2" "$1"
  fi
}

echo "Installo l'aggiornatore StradilabOS..."
fetch "$BASE_URL/stradilabos-update" /usr/local/bin/stradilabos-update
chmod 755 /usr/local/bin/stradilabos-update
fetch "$BASE_URL/stradilabos-update.service" /etc/systemd/system/stradilabos-update.service
fetch "$BASE_URL/stradilabos-update.timer" /etc/systemd/system/stradilabos-update.timer

systemctl daemon-reload
systemctl enable --now stradilabos-update.timer >/dev/null 2>&1 || systemctl enable stradilabos-update.timer

echo "Eseguo subito il primo aggiornamento..."
/usr/local/bin/stradilabos-update --force

echo "Fatto. D'ora in poi il PC controlla gli aggiornamenti da solo a ogni accensione."

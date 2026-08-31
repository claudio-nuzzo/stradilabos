#!/bin/bash
# StradilabOS — aggiornamento cumulativo, serie 1 (2026-08-31)
# Idempotente: puo' essere eseguito piu' volte senza danni.
set -u

echo "— Serie 1: policy Chromium per i cookie dei servizi Google —"

POLICY='{
  "BlockThirdPartyCookies": false,
  "CookiesAllowedForUrls": [
    "https://[*.]google.com",
    "https://[*.]googleusercontent.com",
    "https://[*.]gstatic.com"
  ]
}'

for dir in /etc/chromium/policies/managed /etc/chromium-browser/policies/managed; do
  mkdir -p "$dir"
  printf '%s\n' "$POLICY" > "$dir/stradilabos-cookies.json"
done

echo "Policy cookie installata: le pagine Stradilab con riquadri Google ora funzionano."

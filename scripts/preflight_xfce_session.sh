#!/bin/sh
# Preflight opzionale: avvia una vera sessione Xfce sotto Xvfb e D-Bus e
# verifica che con l'autostart StradilabOS esista un solo xfwm4, stabile, con
# finestre dotate di barra del titolo (frame extents > 0).
#
# Questo script NON è un test bloccante del gate: un container non ha una GPU
# reale né l'ambiente Parallels, quindi un esito verde qui non sostituisce la
# prova Live ARM64. Serve come segnale aggiuntivo in CI (job a parte, segnato
# continue-on-error quando non è strettamente necessario).
#
# Requisiti (Debian): xfwm4 xfce4-session xvfb xfconf dbus-x11 x11-utils
# x11-apps greybird-gtk-theme. Esegue solo in un ambiente con Xvfb disponibile.
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
guard=$root/config/includes.chroot/usr/local/bin/stradilabos-window-manager-guard
display=${STRADILABOS_PREFLIGHT_DISPLAY:-:98}

fail() {
    printf 'ERRORE-PREFLIGHT: %s\n' "$1" >&2
    exit 1
}

for tool in Xvfb xfwm4 xfce4-session xfconf-query dbus-run-session xprop xwininfo; do
    command -v "$tool" >/dev/null 2>&1 || fail "strumento mancante: $tool"
done

# Stato isolato, rimosso dal trap. Include una HOME temporanea con gli
# autostart StradilabOS copiati, per avvicinarsi alla sessione reale.
state_home=$(mktemp -d)
config_home=$(mktemp -d)
export XDG_STATE_HOME="$state_home"
export XDG_CONFIG_HOME="$config_home"
export HOME="$config_home"

mkdir -p "$config_home/.config/autostart"
cp "$root/config/includes.chroot/etc/xdg/autostart/stradilabos-window-manager.desktop" \
   "$config_home/.config/autostart/" 2>/dev/null || true
cp "$root/config/includes.chroot/etc/xdg/autostart/stradilabos-theme.desktop" \
   "$config_home/.config/autostart/" 2>/dev/null || true

Xvfb "$display" -screen 0 1280x800x24 >/dev/null 2>&1 &
xvfb_pid=$!
trap 'kill $xvfb_pid 2>/dev/null || true; pkill -x xfce4-session 2>/dev/null || true; pkill -x xfwm4 2>/dev/null || true; rm -rf "$XDG_STATE_HOME" "$XDG_CONFIG_HOME"' EXIT INT TERM
sleep 2

export DISPLAY=$display
export GUARD=$guard
export STRADILABOS_WM_GRACE=1
export STRADILABOS_WM_INTERVAL=2

# Avvia la sessione Xfce in un bus D-Bus di prova e lancia la guardia come
# farebbe l'autostart. La finestra reale "xlogo" deve ricevere una cornice
# (>0) e, dopo l'assestamento, deve esistere un solo xfwm4 stabile.
dbus-run-session -- sh -eu <<'SCRIPT'
fail() { printf 'ERRORE-PREFLIGHT: %s\n' "$1" >&2; exit 1; }

xfconf-query -c xfwm4 -p /general/theme -n -t string -s Greybird 2>/dev/null || true
xfce4-session >/dev/null 2>&1 &
session_pid=$!

waited=0
while ! pgrep -x xfwm4 >/dev/null; do
    sleep 1
    waited=$((waited + 1))
    [ "$waited" -lt 20 ] || fail "xfwm4 non avviato entro 20 secondi dalla sessione Xfce"
done

# La guardia avvia la sostituzione preventiva subito dopo.
"$GUARD" &
guard_pid=$!

sleep 6
count=$(pgrep -x xfwm4 | wc -l)
[ "$count" -eq 1 ] || fail "atteso un solo xfwm4 nella sessione Xfce, trovati $count"

xwininfo -root -tree >/dev/null 2>&1 || fail "il server X non risponde"
pgrep -x xfwm4 >/dev/null || fail "xfwm4 assente dopo l'avvio della sessione"

# Verifica che il PID resti stabile per due intervalli della guardia.
pid_one=$(pgrep -x xfwm4)
sleep 2
sleep 2
pid_two=$(pgrep -x xfwm4)
[ "$(printf '%s\n' "$pid_two" | wc -l)" -eq 1 ] || fail "piu' di un xfwm4 dopo due intervalli"
[ "$pid_one" = "$pid_two" ] || fail "il PID di xfwm4 è cambiato senza motivo nella sessione Xfce"

# Verifica che una finestra reale abbia davvero una barra del titolo.
xlogo -geometry 400x250 -title 'Preflight StradilabOS' >/dev/null 2>&1 &
sleep 3
window=$(xwininfo -root -tree 2>/dev/null | awk '/"Preflight StradilabOS"/ {print $1; exit}')
[ -n "$window" ] || fail "nessuna finestra reale 'Preflight StradilabOS'"

extents=$(xprop -id "$window" _NET_FRAME_EXTENTS 2>/dev/null | sed -n 's/.*= *//p')
top=$(printf '%s' "$extents" | cut -d, -f3 | tr -d ' ')
printf 'Cornice preflight (sx,dx,alto,basso): %s\n' "$extents"
[ -n "$top" ] && [ "$top" -gt 0 ] || fail "barra del titolo assente nella sessione Xfce"

kill "$guard_pid" 2>/dev/null || true
kill "$session_pid" 2>/dev/null || true
SCRIPT

printf '%s\n' "Preflight sessione Xfce superato (limite: nessuna GPU reale, nessun Parallels)."
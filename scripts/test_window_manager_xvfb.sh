#!/bin/sh
# Prova comportamentale del gestore delle finestre in un X virtuale.
#
# Verifica, senza macchina virtuale, che:
#   1. il tema StradiLab generato dall'hook 012 venga caricato da xfwm4 e
#      produca davvero barra del titolo e bordi (frame extents > 0);
#   2. la guardia stradilabos-window-manager-guard riavvii xfwm4 quando
#      il processo scompare.
#
# Requisiti (Debian/Ubuntu): xfwm4 xvfb xfconf dbus-x11 x11-utils x11-apps
# greybird-gtk-theme. Va eseguito con permessi sufficienti a scrivere in
# /usr/share/themes (l'hook crea /usr/share/themes/StradiLab).
set -eu

root=$(cd "$(dirname "$0")/.." && pwd)
hook=$root/config/hooks/live/012-stradilabos-window-theme.hook.chroot
guard=$root/config/includes.chroot/usr/local/bin/stradilabos-window-manager-guard
display=${STRADILABOS_TEST_DISPLAY:-:97}

fail() {
    printf 'ERRORE: %s\n' "$1" >&2
    exit 1
}

for tool in Xvfb xfwm4 xfconf-query dbus-run-session xprop xlogo; do
    command -v "$tool" >/dev/null 2>&1 || fail "strumento mancante: $tool"
done
[ -d /usr/share/themes/Greybird/xfwm4 ] || fail "tema Greybird non installato"

if [ ! -d /usr/share/themes/StradiLab/xfwm4 ]; then
    if [ "$(id -u)" -eq 0 ]; then
        sh "$hook"
    else
        sudo sh "$hook"
    fi
fi
[ -f /usr/share/themes/StradiLab/xfwm4/themerc ] || fail "tema StradiLab non creato"

Xvfb "$display" -screen 0 1280x800x24 >/dev/null 2>&1 &
xvfb_pid=$!
trap 'kill $xvfb_pid 2>/dev/null || true' EXIT INT TERM
sleep 2

export DISPLAY=$display
dbus-run-session -- sh -eu <<EOF
fail() { printf 'ERRORE: %s\n' "\$1" >&2; exit 1; }

xfconf-query -c xfwm4 -p /general/theme -n -t string -s StradiLab
xfconf-query -c xfwm4 -p /general/button_layout -n -t string -s 'O|HMC'
xfconf-query -c xfwm4 -p /general/borderless_maximize -n -t bool -s false
xfconf-query -c xfwm4 -p /general/titleless_maximize -n -t bool -s false

xfwm4 --compositor=off >/tmp/stradilabos-xfwm4.log 2>&1 &
sleep 3
pgrep -x xfwm4 >/dev/null || fail "xfwm4 non parte con il tema StradiLab"

xlogo -geometry 400x250 -title 'Prova StradilabOS' >/dev/null 2>&1 &
sleep 3
window=\$(xprop -root _NET_CLIENT_LIST | sed -n 's/.*# *//p' | tr ',' '\n' | head -n 1 | tr -d ' ')
[ -n "\$window" ] || fail "nessuna finestra gestita da xfwm4"
extents=\$(xprop -id "\$window" _NET_FRAME_EXTENTS | sed -n 's/.*= *//p')
printf 'Cornice della finestra (sx, dx, alto, basso): %s\n' "\$extents"
top=\$(printf '%s' "\$extents" | cut -d, -f3 | tr -d ' ')
[ -n "\$top" ] && [ "\$top" -gt 0 ] || fail "barra del titolo assente con il tema StradiLab"
[ "\$(xfconf-query -c xfwm4 -p /general/theme)" = StradiLab ] || fail "tema non applicato"

# Simula la scomparsa di xfwm4 e verifica che la guardia lo riavvii.
STRADILABOS_WM_GRACE=1 STRADILABOS_WM_INTERVAL=2 sh "$guard" &
guard_pid=\$!
sleep 2
pkill -x xfwm4
gone=0
while pgrep -x xfwm4 >/dev/null; do
    sleep 1
    gone=\$((gone + 1))
    [ "\$gone" -lt 10 ] || fail "xfwm4 non è stato terminato dalla prova"
done
waited=0
while ! pgrep -x xfwm4 >/dev/null; do
    sleep 1
    waited=\$((waited + 1))
    [ "\$waited" -lt 30 ] || fail "la guardia non ha riavviato xfwm4 entro 30 secondi"
done
printf 'La guardia ha riavviato xfwm4 dopo circa %s secondi.\n' "\$waited"
sleep 6
grep -q 'di nuovo in esecuzione' "\${XDG_STATE_HOME:-\$HOME/.local/state}/stradilabos/window-manager.log" || \
    fail "la guardia non ha registrato il ripristino"
extents=\$(xprop -id "\$window" _NET_FRAME_EXTENTS | sed -n 's/.*= *//p')
top=\$(printf '%s' "\$extents" | cut -d, -f3 | tr -d ' ')
[ -n "\$top" ] && [ "\$top" -gt 0 ] || fail "barra del titolo assente dopo il riavvio"
kill \$guard_pid 2>/dev/null || true
pkill -x xfwm4 || true
EOF

printf '%s\n' "Prova del gestore delle finestre superata."

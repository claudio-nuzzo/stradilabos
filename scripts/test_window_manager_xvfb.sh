#!/bin/sh
# Prova comportamentale del gestore delle finestre in un X virtuale.
#
# Verifica, senza macchina virtuale, che:
#   1. il tema StradiLab generato dall'hook 012 venga caricato da xfwm4 e
#      produca davvero barra del titolo e bordi (frame extents > 0);
#   2. la guardia stradilabos-window-manager-guard esegua una sola
#      sostituzione preventiva per avvio e sostituisca davvero il processo
#      xfwm4 già presente (il caso reale emerso in Parallels);
#   3. dopo la sostituzione esista un solo processo xfwm4 e il suo PID
#      resti stabile per almeno due intervalli della guardia;
#   4. la guardia riavvii xfwm4 quando il processo scompare davvero.
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

for tool in Xvfb xfwm4 xfconf-query dbus-run-session xprop xwininfo xlogo; do
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

# Stato isolato per questo giro di prova: se un'esecuzione precedente avesse
# lasciato nel log la riga di completamento, il test produrrebbe un falso
# positivo. La cartella temporanea viene rimossa dal trap finale.
state_home=$(mktemp -d)
export XDG_STATE_HOME="$state_home"

Xvfb "$display" -screen 0 1280x800x24 >/dev/null 2>&1 &
xvfb_pid=$!
trap 'kill $xvfb_pid 2>/dev/null || true; rm -rf "$XDG_STATE_HOME"' EXIT INT TERM
sleep 2

export DISPLAY=$display
export GUARD=$guard

dbus-run-session -- sh -eu <<'SCRIPT'
fail() { printf 'ERRORE: %s\n' "$1" >&2; exit 1; }
report="$XDG_STATE_HOME/stradilabos/window-manager.log"

# Predispone il tema StradiLab e i controlli delle finestre, come farebbe
# l'autostart StradilabOS. Nessun flag: xfwm4 parte come di consueto.
xfconf-query -c xfwm4 -p /general/theme -n -t string -s StradiLab
xfconf-query -c xfwm4 -p /general/button_layout -n -t string -s 'O|HMC'
xfconf-query -c xfwm4 -p /general/borderless_maximize -n -t bool -s false
xfconf-query -c xfwm4 -p /general/titleless_maximize -n -t bool -s false
xfconf-query -c xfwm4 -p /general/use_compositing -n -t bool -s false

# Il compositore e' spento esplicitamente: sotto Xvfb non c'e' GLX e il caso
# reale Parallels si risolve proprio con --compositor=off.
xfwm4 --compositor=off >/dev/null 2>&1 &
sleep 3

# Conteggio esplicito: all'avvio deve esistere un solo processo xfwm4.
count=$(pgrep -x xfwm4 | wc -l)
[ "$count" -eq 1 ] || fail "atteso un solo xfwm4 all'avvio, trovati $count"
sleep 3

xlogo -geometry 400x250 -title 'Prova StradilabOS' >/dev/null 2>&1 &
sleep 3
window=$(xwininfo -root -tree 2>/dev/null | awk '/"Prova StradilabOS"/ {print $1; exit}')
[ -n "$window" ] || fail "nessuna finestra 'Prova StradilabOS' gestita da xfwm4"

# Il gestore annunciato via EWMH deve essere xfwm4.
supporting=$(xprop -root _NET_SUPPORTING_WM_CHECK 2>/dev/null | sed -n 's/.*window id # *//p')
[ -n "$supporting" ] || fail "_NET_SUPPORTING_WM_CHECK assente"
xprop -id "$supporting" _NET_WM_NAME 2>/dev/null | grep -qi xfwm4 || \
    fail "_NET_WM_NAME non annuncia xfwm4"

extents=$(xprop -id "$window" _NET_FRAME_EXTENTS 2>/dev/null | sed -n 's/.*= *//p')
top=$(printf '%s' "$extents" | cut -d, -f3 | tr -d ' ')
printf 'Cornice (sx,dx,alto,basso): %s\n' "$extents"
[ -n "$top" ] && [ "$top" -gt 0 ] || fail "barra del titolo assente con il tema StradiLab"
[ "$(xfconf-query -c xfwm4 -p /general/theme)" = StradiLab ] || fail "tema non applicato"

# Caso emerso in Parallels: xfwm4 e' presente ma va sostituito preventivamente
# una sola volta. Si registra il PID prima di avviare la guardia.
pid_before=$(pgrep -x xfwm4)
[ "$(printf '%s\n' "$pid_before" | wc -l)" -eq 1 ] || fail "piu' di un xfwm4 prima della sostituzione"

STRADILABOS_WM_GRACE=1 STRADILABOS_WM_INTERVAL=2 "$GUARD" &
guard_pid=$!

waited=0
while [ ! -f "$report" ] || ! grep -q 'inizializzazione preventiva di xfwm4 completata' "$report"; do
    sleep 1
    waited=$((waited + 1))
    [ "$waited" -lt 30 ] || fail "la guardia non ha completato la sostituzione preventiva"
done

# Il PID deve essere cambiato: la guardia ha davvero sostituito il processo.
pid_after=$(pgrep -x xfwm4)
[ -n "$pid_before" ] && [ -n "$pid_after" ] && [ "$pid_before" != "$pid_after" ] || \
    fail "la guardia non ha sostituito il processo xfwm4 iniziale"
[ "$(printf '%s\n' "$pid_after" | wc -l)" -eq 1 ] || \
    fail "piu' di un xfwm4 dopo la sostituzione preventiva"

extents=$(xprop -id "$window" _NET_FRAME_EXTENTS 2>/dev/null | sed -n 's/.*= *//p')
top=$(printf '%s' "$extents" | cut -d, -f3 | tr -d ' ')
[ -n "$top" ] && [ "$top" -gt 0 ] || fail "barra del titolo assente dopo la sostituzione preventiva"

# Stabilita': la guardia resta attiva per almeno due intervalli (2s ciascuno)
# senza una seconda sostituzione. Il PID deve restare identico.
stable_pid=$(pgrep -x xfwm4)
[ "$(printf '%s\n' "$stable_pid" | wc -l)" -eq 1 ] || fail "piu' di un xfwm4 dopo l'assestamento"
sleep 2
sleep 2
second_pid=$(pgrep -x xfwm4)
[ "$(printf '%s\n' "$second_pid" | wc -l)" -eq 1 ] || fail "piu' di un xfwm4 dopo due intervalli"
[ "$stable_pid" = "$second_pid" ] || fail "il PID di xfwm4 è cambiato senza motivo: possibile seconda sostituzione"

# Una sola sostituzione preventiva completata nel log.
preventive=$(grep -c 'inizializzazione preventiva di xfwm4 completata' "$report" || true)
[ "$preventive" -eq 1 ] || fail "attesa una sola sostituzione preventiva, trovate $preventive"

# Simula la scomparsa reale di xfwm4 e verifica separatamente il recupero.
pkill -x xfwm4
gone=0
while pgrep -x xfwm4 >/dev/null; do
    sleep 1
    gone=$((gone + 1))
    [ "$gone" -lt 10 ] || fail "xfwm4 non si è fermato"
done

waited=0
while ! pgrep -x xfwm4 >/dev/null; do
    sleep 1
    waited=$((waited + 1))
    [ "$waited" -lt 30 ] || fail "la guardia non ha riavviato xfwm4 entro 30 secondi"
done

# Il ripristino appartiene al ciclo di monitoraggio, non a una nuova preventiva.
recovery_waited=0
while ! grep -q 'di nuovo in esecuzione' "$report"; do
    sleep 1
    recovery_waited=$((recovery_waited + 1))
    [ "$recovery_waited" -lt 30 ] || fail "la guardia non ha registrato il ripristino"
done

recovered_pid=$(pgrep -x xfwm4)
[ "$(printf '%s\n' "$recovered_pid" | wc -l)" -eq 1 ] || fail "piu' di un xfwm4 dopo il recupero"

preventive=$(grep -c 'inizializzazione preventiva di xfwm4 completata' "$report" || true)
[ "$preventive" -eq 1 ] || fail "la sostituzione preventiva è stata eseguita piu' di una volta"

sleep 2
extents=$(xprop -id "$window" _NET_FRAME_EXTENTS 2>/dev/null | sed -n 's/.*= *//p')
top=$(printf '%s' "$extents" | cut -d, -f3 | tr -d ' ')
[ -n "$top" ] && [ "$top" -gt 0 ] || fail "barra del titolo assente dopo il riavvio"

kill "$guard_pid" 2>/dev/null || true
pkill -x xfwm4 || true
SCRIPT

printf '%s\n' "Prova del gestore delle finestre superata."
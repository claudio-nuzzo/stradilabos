#!/bin/sh
# Avvia davvero il selettore Wi-Fi StradiLabOS in Gtk/Xvfb con nmcli simulato.
# Il test fallisce se la finestra termina o produce un traceback all'avvio.
set -eu

for command_name in Xvfb xdpyinfo dbus-run-session python3; do
    command -v "$command_name" >/dev/null 2>&1 || {
        printf '%s\n' "Comando richiesto assente: $command_name" >&2
        exit 1
    }
done

wifi_tmpdir=$(mktemp -d)
trap 'rm -rf "$wifi_tmpdir"' EXIT HUP INT TERM
fake_bin="$wifi_tmpdir/bin"
wifi_log="$wifi_tmpdir/stradilabos-wifi.log"
mkdir -p "$fake_bin"

cat > "$fake_bin/nmcli" <<'NMCLI'
#!/bin/sh
case " $* " in
    *" radio wifi on "*) exit 0 ;;
    *" device wifi list "*)
        printf '%s\n' '*:Rete StradiLab:88:WPA2' ':Laboratorio:62:--'
        exit 0
        ;;
esac
exit 1
NMCLI
chmod 755 "$fake_bin/nmcli"

export PATH="$fake_bin:$PATH"
export STRADILABOS_WIFI_TEST_LOG="$wifi_log"
export DISPLAY=:98
export GDK_BACKEND=x11

dbus-run-session -- sh -eu <<'INNER'
Xvfb "$DISPLAY" -screen 0 1024x768x24 -nolisten tcp >"$STRADILABOS_WIFI_TEST_LOG.xvfb" 2>&1 &
xvfb_pid=$!
wifi_pid=""
cleanup_inner() {
    [ -z "$wifi_pid" ] || kill "$wifi_pid" >/dev/null 2>&1 || true
    kill "$xvfb_pid" >/dev/null 2>&1 || true
}
trap cleanup_inner EXIT HUP INT TERM

attempt=0
while ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; do
    attempt=$((attempt + 1))
    [ "$attempt" -lt 40 ] || {
        printf '%s\n' "Xvfb non disponibile" >&2
        exit 1
    }
    sleep 0.25
done

python3 config/includes.chroot/usr/local/bin/stradilabos-wifi >"$STRADILABOS_WIFI_TEST_LOG" 2>&1 &
wifi_pid=$!
sleep 4
if ! kill -0 "$wifi_pid" >/dev/null 2>&1; then
    printf '%s\n' "Il selettore Wi-Fi è terminato durante l'avvio" >&2
    cat "$STRADILABOS_WIFI_TEST_LOG" >&2
    exit 1
fi
if grep -Eiq 'Traceback|Gtk-ERROR|segmentation fault' "$STRADILABOS_WIFI_TEST_LOG"; then
    printf '%s\n' "Il selettore Wi-Fi ha prodotto un errore grafico" >&2
    cat "$STRADILABOS_WIFI_TEST_LOG" >&2
    exit 1
fi
kill -KILL "$wifi_pid" >/dev/null 2>&1 || true
wait "$wifi_pid" 2>/dev/null || true
wifi_pid=""
INNER

printf '%s\n' "Selettore Wi-Fi StradiLabOS avviato correttamente."

#!/bin/sh
# Avvia il Benvenuto reale su uno schermo basso e verifica che GTK calcoli una
# finestra contenuta nell'area visibile. Il piè di pagina resta fisso nel codice
# e il contenuto centrale è scorrevole.
set -eu

for command_name in Xvfb xdpyinfo xwininfo dbus-run-session python3; do
    command -v "$command_name" >/dev/null 2>&1 || {
        printf '%s\n' "Comando richiesto assente: $command_name" >&2
        exit 1
    }
done

welcome_tmpdir=$(mktemp -d)
trap 'rm -rf "$welcome_tmpdir"' EXIT HUP INT TERM
fake_bin="$welcome_tmpdir/bin"
welcome_log="$welcome_tmpdir/stradilabos-welcome.log"
mkdir -p "$fake_bin" "$welcome_tmpdir/.config/stradilabos"

cat > "$fake_bin/nmcli" <<'NMCLI'
#!/bin/sh
case " $* " in
    *" -t -f STATE general "*) printf '%s\n' connected; exit 0 ;;
esac
exit 1
NMCLI
chmod 755 "$fake_bin/nmcli"

cat > "$welcome_tmpdir/.config/stradilabos/profiles.json" <<'PROFILE'
{
  "schema_version": 2,
  "role": "base",
  "profiles": [],
  "device_mode": "personal",
  "workspace_onboarding": "first-boot",
  "source": "test"
}
PROFILE

export PATH="$fake_bin:$PATH"
export HOME="$welcome_tmpdir"
export STRADILABOS_WELCOME_TEST_LOG="$welcome_log"
export DISPLAY=:96
export GDK_BACKEND=x11

dbus-run-session -- sh -eu <<'INNER'
Xvfb "$DISPLAY" -screen 0 1024x600x24 -nolisten tcp >"$STRADILABOS_WELCOME_TEST_LOG.xvfb" 2>&1 &
xvfb_pid=$!
welcome_pid=""
cleanup_inner() {
    [ -z "$welcome_pid" ] || kill "$welcome_pid" >/dev/null 2>&1 || true
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

python3 config/includes.chroot/usr/local/lib/stradilabos/welcome.py \
    >"$STRADILABOS_WELCOME_TEST_LOG" 2>&1 &
welcome_pid=$!
sleep 4
if ! kill -0 "$welcome_pid" >/dev/null 2>&1; then
    printf '%s\n' "Il Benvenuto è terminato durante l'avvio" >&2
    cat "$STRADILABOS_WELCOME_TEST_LOG" >&2
    exit 1
fi
if grep -Eiq 'Traceback|Gtk-ERROR|segmentation fault' "$STRADILABOS_WELCOME_TEST_LOG"; then
    printf '%s\n' "Il Benvenuto ha prodotto un errore grafico" >&2
    cat "$STRADILABOS_WELCOME_TEST_LOG" >&2
    exit 1
fi

window_info=$(xwininfo -display "$DISPLAY" -name "Benvenuto in StradiLabOS")
width=$(printf '%s\n' "$window_info" | awk '/Width:/{print $2; exit}')
height=$(printf '%s\n' "$window_info" | awk '/Height:/{print $2; exit}')
case "$width:$height" in
    *[!0-9:]*|:|*:)
        printf '%s\n' "Dimensioni della finestra non rilevabili" >&2
        exit 1
        ;;
esac
if [ "$width" -gt 1024 ] || [ "$height" -gt 600 ]; then
    printf '%s\n' "Il Benvenuto supera lo schermo: ${width}x${height}" >&2
    exit 1
fi

kill -KILL "$welcome_pid" >/dev/null 2>&1 || true
wait "$welcome_pid" 2>/dev/null || true
welcome_pid=""
INNER

printf '%s\n' "Benvenuto avviato e contenuto nello schermo 1024x600."

#!/bin/sh
# Avvia il layout reale dei due pannelli in Xvfb e fallisce se un plugin non
# viene caricato. Deve girare in Debian Trixie con i plugin della ISO installati.
set -eu

for command_name in Xvfb xdpyinfo dbus-run-session xfce4-panel; do
    command -v "$command_name" >/dev/null 2>&1 || {
        printf '%s\n' "Comando richiesto assente: $command_name" >&2
        exit 1
    }
done

panel_tmpdir=$(mktemp -d)
trap 'rm -rf "$panel_tmpdir"' EXIT HUP INT TERM
config_home="$panel_tmpdir/config"
runtime_dir="$panel_tmpdir/runtime"
cache_home="$panel_tmpdir/cache"
data_home="$panel_tmpdir/data"
panel_log="$panel_tmpdir/xfce4-panel.log"

mkdir -p "$config_home" "$runtime_dir" "$cache_home" "$data_home"
chmod 700 "$runtime_dir"
cp -a config/includes.chroot/etc/skel/.config/. "$config_home/"

export XDG_CONFIG_HOME="$config_home"
export XDG_RUNTIME_DIR="$runtime_dir"
export XDG_CACHE_HOME="$cache_home"
export XDG_DATA_HOME="$data_home"
export STRADILABOS_PANEL_TEST_LOG="$panel_log"
export DISPLAY=:97

dbus-run-session -- sh -eu <<'INNER'
Xvfb "$DISPLAY" -screen 0 1280x800x24 -nolisten tcp >"$STRADILABOS_PANEL_TEST_LOG.xvfb" 2>&1 &
xvfb_pid=$!
panel_pid=""
cleanup_inner() {
    [ -z "$panel_pid" ] || kill "$panel_pid" >/dev/null 2>&1 || true
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

# xfce4-panel attiva xfconfd tramite D-Bus dal percorso multiarchitettura di
# Debian; il demone non è necessariamente presente nel PATH.
XFCE_PANEL_DEBUG=all xfce4-panel --disable-wm-check >"$STRADILABOS_PANEL_TEST_LOG" 2>&1 &
panel_pid=$!
sleep 8

if ! kill -0 "$panel_pid" >/dev/null 2>&1; then
    printf '%s\n' "xfce4-panel è terminato durante l'avvio" >&2
    cat "$STRADILABOS_PANEL_TEST_LOG" >&2
    exit 1
fi

if grep -Eiq 'Plugin ".*" could not be loaded|Plugin loading failure|plugin_name.*NULL|wrapper.*exited' "$STRADILABOS_PANEL_TEST_LOG"; then
    printf '%s\n' "Un plugin del pannello non è stato caricato" >&2
    cat "$STRADILABOS_PANEL_TEST_LOG" >&2
    exit 1
fi

# La prova è conclusa: termina direttamente il processo sotto test. In un
# container senza xfce4-session, il comando D-Bus --quit può non chiuderlo.
kill -KILL "$panel_pid" >/dev/null 2>&1 || true
wait "$panel_pid" 2>/dev/null || true
panel_pid=""
INNER

printf '%s\n' "Pannello superiore e barra applicazioni Xfce avviati correttamente."

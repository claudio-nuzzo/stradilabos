#!/bin/sh
set -eu

missing=""
architecture="${BUILD_ARCH:-$(dpkg --print-architecture)}"

for package_list in config/package-lists/*.list.chroot; do
    active=true
    while IFS= read -r package; do
        case "$package" in
            "#if ARCHITECTURES "*)
                active=false
                directive_architectures=${package#"#if ARCHITECTURES "}
                case " $directive_architectures " in
                    *" $architecture "*) active=true ;;
                esac
                continue
                ;;
            "#endif")
                active=true
                continue
                ;;
            ""|\#*) continue ;;
        esac
        [ "$active" = true ] || continue
        if ! apt-cache show "$package" >/dev/null 2>&1; then
            missing="$missing $package"
        fi
    done < "$package_list"
done

# Anche i pacchetti opzionali del Centro App devono esistere nei repository,
# pur non essendo incorporati nell'immagine base.
if ! command -v python3 >/dev/null 2>&1; then
    printf '%s\n' "Impossibile validare il catalogo pacchetti: python3 non disponibile." >&2
    exit 1
fi

catalog_packages="$(python3 - <<'PY'
import json

with open(
    "config/includes.chroot/usr/local/share/stradilabos/packs.json",
    encoding="utf-8",
) as source:
    packs = json.load(source)["packs"]

print(" ".join(sorted({name for pack in packs for name in pack["packages"]})))
PY
)"

for package in $catalog_packages; do
    if ! apt-cache show "$package" >/dev/null 2>&1; then
        missing="$missing $package"
    fi
done

if [ -n "$missing" ]; then
    printf '%s\n' "Pacchetti Debian non trovati:$missing" >&2
    exit 1
fi

printf '%s\n' "Pacchetti base e raccolte del Centro App disponibili per $architecture."

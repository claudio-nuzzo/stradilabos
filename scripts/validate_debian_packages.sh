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
                set -- $package
                shift 2
                for candidate in "$@"; do
                    if [ "$candidate" = "$architecture" ]; then
                        active=true
                        break
                    fi
                done
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

if [ -n "$missing" ]; then
    printf '%s\n' "Pacchetti Debian non trovati:$missing" >&2
    exit 1
fi

printf '%s\n' "Tutti i pacchetti Debian richiesti sono disponibili per $architecture."

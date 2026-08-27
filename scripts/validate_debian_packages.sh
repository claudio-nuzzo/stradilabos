#!/bin/sh
set -eu

missing=""

for package_list in config/package-lists/*.list.chroot; do
    while IFS= read -r package; do
        case "$package" in
            ""|\#*) continue ;;
        esac
        if ! apt-cache show "$package" >/dev/null 2>&1; then
            missing="$missing $package"
        fi
    done < "$package_list"
done

if [ -n "$missing" ]; then
    printf '%s\n' "Pacchetti Debian non trovati:$missing" >&2
    exit 1
fi

printf '%s\n' "Tutti i pacchetti Debian richiesti sono disponibili."

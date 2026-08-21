#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
INSTALL_DIR="${PULSEDECK_BIN_DIR:-$HOME/.local/bin}"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/pulsedeck"
VENV_DIR="$DATA_DIR/venv"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"

mkdir -p "$INSTALL_DIR" "$DATA_DIR"

if ! command -v python3 >/dev/null 2>&1; then
    printf 'Error: python3 is required.\n' >&2
    exit 1
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
    python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install "$PROJECT_DIR"

cat > "$INSTALL_DIR/pulsedeck" <<EOF
#!/usr/bin/env bash
exec "$VENV_DIR/bin/pulsedeck" "\$@"
EOF
chmod 755 "$INSTALL_DIR/pulsedeck"

if command -v konsole >/dev/null 2>&1; then
    mkdir -p "$AUTOSTART_DIR"
    cat > "$AUTOSTART_DIR/pulsedeck.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PulseDeck System Monitor
Exec=konsole -e $INSTALL_DIR/pulsedeck
Icon=utilities-terminal
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
    printf 'Autostart entry created at %s\n' "$AUTOSTART_DIR/pulsedeck.desktop"
else
    printf 'Konsole not detected; skipping desktop autostart.\n'
fi

printf 'PulseDeck installed to %s\n' "$INSTALL_DIR/pulsedeck"

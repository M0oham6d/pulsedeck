#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
INSTALL_DIR="${XDG_DATA_HOME:-$HOME/.local}/bin"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"

mkdir -p "$INSTALL_DIR" "$AUTOSTART_DIR"

python3 -m pip install --user -r "$PROJECT_DIR/requirements.txt"
install -m 755 "$PROJECT_DIR/pulsedeck.py" "$INSTALL_DIR/pulsedeck"
install -m 755 "$PROJECT_DIR/monitor.sh" "$INSTALL_DIR/pulsedeck-monitor.sh"

cat > "$AUTOSTART_DIR/pulsedeck.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=PulseDeck System Monitor
Exec=konsole -e $INSTALL_DIR/pulsedeck-monitor.sh
Icon=utilities-terminal
Terminal=false
X-GNOME-Autostart-enabled=true
EOF

printf 'PulseDeck installed to %s\n' "$INSTALL_DIR/pulsedeck"
printf 'Autostart entry created at %s\n' "$AUTOSTART_DIR/pulsedeck.desktop"

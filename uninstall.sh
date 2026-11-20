#!/usr/bin/env bash
# Removes the obs2pdf uv tool and the bash tab-completion set up by
# install.sh. Leaves uv, pandoc, typst and your config untouched.
set -euo pipefail

BASHRC="$HOME/.bashrc"
MARKER="# obs2pdf tab completion"
COMPLETION_FILE="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions/obs2pdf"

if ! command -v uv >/dev/null 2>&1; then
    echo "ERROR: 'uv' not found on PATH; cannot uninstall a uv tool without it." >&2
    exit 1
fi

if uv tool list 2>/dev/null | grep -q "^obs2pdf\b"; then
    uv tool uninstall obs2pdf
    echo "Uninstalled the obs2pdf uv tool."
else
    echo "obs2pdf is not installed as a uv tool; nothing to remove there."
fi

if [ -f "$COMPLETION_FILE" ]; then
    rm -f "$COMPLETION_FILE"
    echo "Removed $COMPLETION_FILE"
fi

if [ -f "$BASHRC" ] && grep -qF "$MARKER" "$BASHRC"; then
    # Remove the marker line and the obs2pdf line right after it.
    tmp="$(mktemp)"
    awk -v marker="$MARKER" '
        $0 == marker { skip_next = 1; next }
        skip_next && /obs2pdf/ { skip_next = 0; next }
        { skip_next = 0; print }
    ' "$BASHRC" > "$tmp"
    cat "$tmp" > "$BASHRC"
    rm -f "$tmp"
    echo "Removed tab-completion setup from $BASHRC"
else
    echo "No tab-completion setup found in $BASHRC; nothing to remove there."
fi

echo "Open a new terminal for the completion removal to take effect."
echo "Your config ($(dirname "${OBS2PDF_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/obs2pdf/config.toml}")) was left in place; delete it by hand if you no longer need it."

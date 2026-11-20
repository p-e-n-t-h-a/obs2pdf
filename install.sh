#!/usr/bin/env bash
# Installs obs2pdf from this checkout as a uv tool (its own isolated venv,
# `obs2pdf` on PATH via uv's shim) and sets up bash tab-completion.
#
# The install is editable, so `git pull` updates obs2pdf without
# reinstalling. Safe to re-run.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASHRC="$HOME/.bashrc"
MARKER="# obs2pdf tab completion"
COMPLETION_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/bash-completion/completions"
COMPLETION_FILE="$COMPLETION_DIR/obs2pdf"

missing_required=0

check_command() {
    local cmd="$1"
    local hint="$2"
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "ERROR: required dependency '$cmd' not found on PATH. $hint" >&2
        missing_required=1
    fi
}

check_command uv "Install from https://docs.astral.sh/uv/getting-started/installation/"
check_command pandoc "Install from https://pandoc.org/installing.html or your package manager."
check_command typst "Install from https://github.com/typst/typst#installation or your package manager."

if [ "$missing_required" -ne 0 ]; then
    echo "Aborting install: missing required dependencies (see errors above)." >&2
    exit 1
fi

uv tool install --force --editable "$SCRIPT_DIR"
echo "Installed obs2pdf via 'uv tool install'."

# Puts uv's executable directory on PATH in your shell startup files. It
# exits non-zero when those are already set up but the current shell hasn't
# picked them up yet (e.g. on a re-run), which is fine.
uv tool update-shell || true

# Tab-completion. argcomplete's `register-python-argcomplete` lives inside
# the tool's venv (uv only puts `obs2pdf` itself on PATH), so generate the
# completion script once, here, instead of on every shell start.
mkdir -p "$COMPLETION_DIR"
"$(uv tool dir)/obs2pdf/bin/register-python-argcomplete" obs2pdf > "$COMPLETION_FILE"
echo "Wrote bash completion to $COMPLETION_FILE"

# Source it from ~/.bashrc as well, for systems without the bash-completion
# package (which would otherwise load it from that directory on its own).
# Any earlier block is replaced, so re-running the script never duplicates it.
if [ -f "$BASHRC" ] && grep -qF "$MARKER" "$BASHRC"; then
    tmp="$(mktemp)"
    awk -v marker="$MARKER" '
        $0 == marker { skip_next = 1; next }
        skip_next && /obs2pdf/ { skip_next = 0; next }
        { skip_next = 0; print }
    ' "$BASHRC" > "$tmp"
    cat "$tmp" > "$BASHRC"
    rm -f "$tmp"
fi
# Don't glue the block onto a last line that has no trailing newline.
if [ -s "$BASHRC" ] && [ -n "$(tail -c1 "$BASHRC")" ]; then
    echo >> "$BASHRC"
fi
{
    echo "$MARKER"
    echo "[ -f \"$COMPLETION_FILE\" ] && . \"$COMPLETION_FILE\""
} >> "$BASHRC"
echo "Enabled tab-completion in $BASHRC"

CONFIG_PATH="$(obs2pdf config path 2>/dev/null || true)"
if [ -n "$CONFIG_PATH" ] && [ ! -f "$CONFIG_PATH" ]; then
    echo "No config file yet. Create a commented starter with: obs2pdf config init"
fi

echo "Run 'source ~/.bashrc' or open a new terminal, then run: obs2pdf --help"

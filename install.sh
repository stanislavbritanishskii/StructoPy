#!/bin/bash
# Adds a `structopy` alias to ~/.bashrc pointing at this checkout's run.sh.
# Idempotent — re-running updates the alias to the current path.
#
# Usage:   ./install.sh
# Uninstall: ./install.sh --uninstall

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
run_sh="$script_dir/run.sh"
bashrc="$HOME/.bashrc"
marker="# StructoPy alias"

uninstall=0
if [ "${1:-}" = "--uninstall" ]; then
	uninstall=1
fi

if [ ! -f "$run_sh" ]; then
	echo "Error: run.sh not found at $run_sh" >&2
	exit 1
fi
if [ ! -x "$run_sh" ]; then
	chmod +x "$run_sh"
fi

touch "$bashrc"

# Strip any prior install (marker line + alias line) so re-running is safe.
sed -i.structopy.bak \
	-e "/$marker/d" \
	-e "/^alias structopy=/d" \
	"$bashrc"
rm -f "$bashrc.structopy.bak"

if [ "$uninstall" -eq 1 ]; then
	echo "Removed 'structopy' alias from $bashrc"
	echo "Run 'source $bashrc' or open a new shell to take effect."
	exit 0
fi

{
	echo ""
	echo "$marker"
	echo "alias structopy='$run_sh'"
} >> "$bashrc"

echo "Added 'structopy' alias to $bashrc"
echo "  alias structopy -> $run_sh"
echo ""
echo "Run 'source $bashrc' or open a new shell, then:"
echo "  structopy your_header.h"

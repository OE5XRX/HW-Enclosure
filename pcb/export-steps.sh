#!/usr/bin/env bash
# Export module PCB STEP files from a clean origin/main checkout.
# Usage: export-steps.sh [MODULES_DIR]   (default: ..)
# Env (optional): MODULES="BusBoard DeviceTester" subset, OUT_DIR override.
# Exit 2 if a module repo is dirty or HEAD != origin/main.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
mods="$(cd "${1:-..}" && pwd)"
out="${OUT_DIR:-$here}"
modules="${MODULES:-BusBoard PowerBoard CM4Carrier FMTransceiver DeviceTester}"
kv="$(kicad-cli version)"
mkdir -p "$out"

# Guard all repos first, so nothing is exported on refusal.
for m in $modules; do
  repo="$mods/HW-Module-$m"
  [ -d "$repo/.git" ] || { echo "error: HW-Module-$m not found in $mods" >&2; exit 1; }
  git -C "$repo" fetch -q origin
  if [ -n "$(git -C "$repo" status --porcelain --untracked-files=no)" ]; then
    echo "REFUSED: HW-Module-$m has changes to tracked files" >&2; exit 2
  fi
  if [ "$(git -C "$repo" rev-parse HEAD)" != "$(git -C "$repo" rev-parse origin/main)" ]; then
    echo "REFUSED: HW-Module-$m HEAD ($(git -C "$repo" rev-parse --abbrev-ref HEAD)) != origin/main" >&2; exit 2
  fi
done

rows=""
for m in $modules; do
  repo="$mods/HW-Module-$m"
  shopt -s nullglob; pcbs=("$repo"/*.kicad_pcb); shopt -u nullglob
  [ "${#pcbs[@]}" -eq 1 ] || { echo "error: HW-Module-$m: expected exactly one .kicad_pcb at root, found ${#pcbs[@]}" >&2; exit 1; }
  pcb="${pcbs[0]}"
  kicad-cli pcb export step --subst-models --force -o "$out/$m.step" "$pcb" >&2
  if [ "$m" = "DeviceTester" ]; then
    kicad-cli pcb export step --subst-models --force --variant Slot --no-dnp -o "$out/$m-slot.step" "$pcb" >&2
  fi
  sha="$(git -C "$repo" rev-parse HEAD)"
  rows+="| $m | OE5XRX/HW-Module-$m | $sha | $(basename "$pcb") | $kv |"$'\n'
done

{
  echo "# PCB STEP sources"
  echo
  echo "| module | repo | commit | file | kicad-cli version |"
  echo "|---|---|---|---|---|"
  printf '%s' "$rows"
} > "$out/SOURCES.md"

#!/usr/bin/env bash
# Export module PCB STEP files from a clean origin/main checkout.
# Usage: export-steps.sh [MODULES_DIR]   (default: ..)
# Env (optional): MODULES="BusBoard DeviceTester" subset, OUT_DIR override.
# SOURCES.md is merged row by row, so a subset run keeps the other rows.
# Exit 2 if a module repo is dirty or HEAD != origin/main.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
mods="$(cd "${1:-..}" && pwd)"
out="${OUT_DIR:-$here}"
modules="${MODULES:-BusBoard PowerBoard CM4Carrier FMTransceiver DeviceTester}"
kv="$(kicad-cli version)"
# Board detail: pads, silkscreen and solder mask as faces (tracks/zones stay out: they sit
# under the mask and double the file size). DETAIL="" gives a plain board.
DETAIL="${DETAIL---include-pads --include-silkscreen --include-soldermask}"
NOTE="models remapped to KiCad 10${DETAIL:+; $DETAIL}"
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

# SOURCES.md is merged: rows of modules not exported in this run are kept.
declare -A rows
sf="$out/SOURCES.md"
if [ -f "$sf" ]; then
  while IFS= read -r line; do
    case "$line" in
      "| module "*|"|---"*) ;;
      "| "*) key="${line#| }"; key="${key%% |*}"; rows["$key"]="$line" ;;
    esac
  done < "$sf"
fi
for m in $modules; do
  repo="$mods/HW-Module-$m"
  shopt -s nullglob; pcbs=("$repo"/*.kicad_pcb); shopt -u nullglob
  [ "${#pcbs[@]}" -eq 1 ] || { echo "error: HW-Module-$m: expected exactly one .kicad_pcb at root, found ${#pcbs[@]}" >&2; exit 1; }
  pcb="${pcbs[0]}"
  sha="$(git -C "$repo" rev-parse HEAD)"
  # Export from a pristine copy of HEAD with the 3D model paths rewritten for KiCad 10:
  # the boards reference ${KICAD8/9_3DMODEL_DIR}/*.wrl, but the KiCad 10 library ships
  # only .step files, and --subst-models only substitutes when the .wrl exists.
  # Without this rewrite every passive and IC silently drops out of the STEP.
  work="$(mktemp -d)"
  git -C "$repo" archive HEAD | tar -x -C "$work"
  wpcb="$work/$(basename "$pcb")"
  sed -i -E \
    -e 's/\$\{KICAD[0-9]+_3DMODEL_DIR\}/${KICAD10_3DMODEL_DIR}/g' \
    -e 's/(\(model "[^"]*)\.wrl"/\1.step"/g' \
    -e 's#Package_SO\.3dshapes/VSSOP-10_3x3mm_P0\.5mm\.step#Package_SO.3dshapes/MSOP-10_3x3mm_P0.5mm.step#g' \
    "$wpcb"
  export_one() {  # export_one OUTFILE [extra kicad-cli args...]
    local o="$1"; shift
    LC_ALL=C kicad-cli pcb export step --subst-models --force $DETAIL "$@" -o "$o" "$wpcb" 2>&1 \
      | tee "$work/log" >&2
    if grep -qiE "not found|could not" "$work/log"; then
      echo "error: HW-Module-$m: 3D models missing in $(basename "$o") (see above)" >&2
      rm -rf "$work"; exit 1
    fi
  }
  export_one "$out/$m.step"
  rows["$m"]="| $m | OE5XRX/HW-Module-$m | $sha | $(basename "$pcb") | $kv | $NOTE |"
  if [ "$m" = "DeviceTester" ]; then
    export_one "$out/$m-slot.step" --variant Slot --no-dnp
    rows["$m-slot"]="| $m-slot | OE5XRX/HW-Module-$m | $sha | $(basename "$pcb") | $kv | variant Slot, --no-dnp; $NOTE |"
  fi
  rm -rf "$work"
done

{
  echo "# PCB STEP sources"
  echo
  echo "| module | repo | commit | file | kicad-cli version | note |"
  echo "|---|---|---|---|---|---|"
  for k in BusBoard PowerBoard CM4Carrier FMTransceiver DeviceTester DeviceTester-slot; do
    [ -n "${rows[$k]:-}" ] && echo "${rows[$k]}"
  done
  # any other (unknown) keys from an existing file
  for k in "${!rows[@]}"; do
    case "$k" in BusBoard|PowerBoard|CM4Carrier|FMTransceiver|DeviceTester|DeviceTester-slot) ;; *) echo "${rows[$k]}" ;; esac
  done
} > "$sf.tmp" && mv "$sf.tmp" "$sf"

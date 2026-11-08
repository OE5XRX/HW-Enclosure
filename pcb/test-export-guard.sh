#!/usr/bin/env bash
# Guard test for export-steps.sh, runs on a temp clone only.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
src="${1:-$here/../../HW-Module-DeviceTester}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
mods="$tmp/mods"; out="$tmp/out"; mkdir -p "$mods" "$out"
git clone -q "$src" "$mods/HW-Module-DeviceTester"
repo="$mods/HW-Module-DeviceTester"
git -C "$repo" checkout -q -B main origin/main
git -C "$repo" config user.email t@t; git -C "$repo" config user.name t
run() { MODULES="DeviceTester" OUT_DIR="$out" "$here/export-steps.sh" "$mods" 2>"$tmp/err" >"$tmp/outlog"; }
fail() { echo "FAIL: $1"; cat "$tmp/err" >&2; exit 1; }

# (a) other branch with extra commit
git -C "$repo" checkout -q -b scratch
git -C "$repo" commit -q --allow-empty -m extra
rc=0; run || rc=$?
[ "$rc" -eq 2 ] || fail "(a) expected exit 2, got $rc"
grep -q "HW-Module-DeviceTester" "$tmp/err" || fail "(a) repo name not on stderr"
git -C "$repo" checkout -q main

# (b) modified tracked pcb
pcb="$(ls "$repo"/*.kicad_pcb)"
echo " " >> "$pcb"
rc=0; run || rc=$?
[ "$rc" -eq 2 ] || fail "(b) expected exit 2, got $rc"
git -C "$repo" checkout -q -- .

# (c) clean origin/main
run || fail "(c) expected exit 0"
[ -s "$out/DeviceTester.step" ] || fail "(c) empty STEP"
[ -s "$out/DeviceTester-slot.step" ] || fail "(c) empty slot STEP"
echo "PASS"

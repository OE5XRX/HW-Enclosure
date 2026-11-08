# HW-Enclosure

3D-gedrucktes Gehäuse für die OE5XRX-Remote-Station: BusBoard plus bis zu sechs 100×100-mm-Module
stecken in Kartennuten zweier Grundgestelle, seitlich schließen zwei Deckplatten ab. Das
Desktop-Gehäuse ist zum Mitnehmen, Herzeigen und für den Schreibtisch gedacht (erste Station,
DX-Camp 2025). Die ursprüngliche CAD-Quelle (Fusion 360) ist verloren; die Teile wurden aus den
Druck-G-Codes in SolidCraft parametrisch nachgebaut
(siehe [reference/reconstruction.md](reference/reconstruction.md)). Eine 19-Zoll-Variante ist geplant
(`rack-19/`).

![Station, Iso-Ansicht](desktop/station-iso.png)

Die Gesamtbaugruppe `desktop/station.sc` enthält alle Gehäuseteile und die echten Platinen
(KiCad-STEP) und dient der Passungsprüfung.

## Teileliste (pro Station)

| Anzahl | Teil | Datei (SolidCraft / STEP) |
|---|---|---|
| 1 | Grundgestell (normal, unten) | `desktop/parts/grundgestell.sc` / `.step` |
| 1 | Grundgestell gespiegelt (oben; so wurde es 2025 gedruckt) | `desktop/parts/grundgestell-gespiegelt.sc` / `.step` |
| 2 | Deckplatte (mit erhabenem Logo, links und rechts) | `desktop/parts/deckplatte.sc` / `.step` |
| 4 | Leiste (2 pro Gestell) | `desktop/parts/leiste.sc` / `.step` |

Das normale Grundgestell ist ein reines Spiegelbild des gespiegelten. Die beiden Deckplatten sitzen
nach der Auswertung der Bohrbilder an den Seiten (±X), nicht vorne/hinten
([reference/assembly.md](reference/assembly.md)).

![Deckplatte mit Logo](desktop/logo/deckplatte-top.png)

Das Logo stammt aus [OE5XRX/branding](https://github.com/OE5XRX/branding); Herkunft und Aufbereitung
in [desktop/logo/SOURCE.md](desktop/logo/SOURCE.md).

## Druckeinstellungen

Aus den Original-G-Codes (Klipper-Drucker):

| Einstellung | Wert |
|---|---|
| Material | PETG |
| Düse | 0,4 mm |
| Schichthöhe | 0,2 mm (erste Schicht 0,15 mm) |
| Wände | 3 |
| Füllung | 15 %, Crosshatch |
| Deckschichten oben / unten | 4 / 3 |
| Stützen | keine |
| `xy_hole_compensation` | 0,27 mm |

STL, 3MF und G-Code gehören nicht ins Repo
(`.gitignore`). Aus den `.step`-Dateien lassen sich STLs beliebig neu erzeugen.

## Hardware

- 6 × Einschmelzmutter M3 (Ø 5 mm × 5 mm tiefe Taschen) in der Rückseite jedes Gestells. Das ist eine
  **Interpretation** der Ø-5-Taschen, nicht gemessen. Ein Gestell hat 6 Taschen, zusammen 12 für die
  Befestigung des BusBoards. Weitere Ø-5×5-Taschen sitzen an den Seiten und vorne (je Ø 3,2 weiter);
  ob dort ebenfalls Einschmelzmuttern sitzen, ist nicht belegt.
- M3-Schrauben für BusBoard, Leisten und Deckplatten. **Längen unbekannt.** Obergrenzen aus den
  Bohrtiefen: Leisten (3 mm dick) vorne ≤ 12 mm, Deckplatten (3 mm dick) seitlich ≤ 13 mm, jeweils
  ohne Einschmelzmutter-Tasche gerechnet. Bitte am Original nachmessen.

## Status / offene Punkte

Passungsprüfung der Gesamtbaugruppe: [reference/fit-check.md](reference/fit-check.md).
Kurz: Alle 6 Platinen sitzen in den Nuten, alle 12 BusBoard-Löcher fluchten mit den Taschen, die
Stecker stecken (alle 20 Stifte je Slot in ihren Kammern). Offen:

- **Deckplatten-Loch um 1,0 mm daneben:** Das Loch (9 | 105,5) der Deckplatte liegt 1,0 mm neben der
  Gestell-Bohrung. Praktisch: Dort geht so keine M3-Schraube durch (nur ca. 2,2 mm Durchgang, fit-check Befund 2). Entweder ist die nachgebaute Position falsch (8 | 105,5) oder die echte
  Bohrung im oberen Gestell sitzt bei y = 54 (assembly.md, Frage 2).
- **Logo rechts steht auf dem Kopf:** Das Lochbild der Platte ist nicht symmetrisch; auf der +X-Seite
  muss sie um 180° gedreht werden (assembly.md, Frage 3). Eine gespiegelte Platte wäre nötig.
- **Position der hinteren Leisten unbestätigt:** Zwei Leisten sitzen sicher vorne an den Gestellen;
  die zwei anderen sind als Klemmleisten auf der Rückseite des BusBoards angenommen
  (assembly.md, Frage 4).
- **0,1 mm Stecker-Modellkonflikt:** Die Herstellermodelle von Stiftleiste und Buchse überschneiden
  sich um 0,1 mm (4,129 mm³ je Slot). Die Ursache ist offen, vermutlich Modellungenauigkeit; die
  Prüfung meldet deshalb ⚠️.

Die Deckplatten heißen in `station.sc` `Deckplatte-links` (-X) und `Deckplatte-rechts` (+X); die Spec sagte "vorne/hinten" (Seitenzuordnung von Peter zu bestätigen, assembly.md Frage 1).

## Dateien öffnen und neu erzeugen

**Baugruppe öffnen:** `desktop/station.sc` in SolidCraft öffnen. Die Gehäuseteile sind verknüpfte
Komponenten aus `desktop/parts/` (Änderungen an den Teilen wirken in der Baugruppe). Die Platinen sind
**nicht** verknüpft: `station.sc` enthält eingebettete STEP-Schnappschüsse der Dateien aus `pcb/`. Slot 1 PowerBoard,
Slot 2 CM4Carrier, Slot 3-6 FMTransceiver (Platzhalter). Der DeviceTester liegt als STEP bereit
(`pcb/DeviceTester.step`, `pcb/DeviceTester-slot.step`), ist aber nicht bestückt.

**PCB-STEPs neu erzeugen:**

```
pcb/export-steps.sh [MODULES_DIR]   # Standard: .. (dort liegen HW-Module-*)
```

Braucht `kicad-cli` (10.x) und lokale Klone der `HW-Module-*`-Repos. Das Skript bricht ab, wenn ein
Repo uncommittete Änderungen hat oder nicht auf `origin/main` steht. Quelle (Repo + Commit) je STEP
steht in [pcb/SOURCES.md](pcb/SOURCES.md); bei einem Teil-Lauf (`MODULES=...`) bleiben die Zeilen der
anderen Module erhalten.

`export-steps.sh` aktualisiert `station.sc` **nicht**. Neue STEP einsetzen: die alte PCB-Occurrence in
`station.sc` löschen, die neue STEP mit `file.insert_step` einfügen (Transformation aus
[reference/assembly.md](reference/assembly.md)) und danach `python3 tools/check_parts.py` ausführen.

**Prüfungen** (SolidCraft muss laufen, gestartet mit `solidcraft --control 7878`; verwendet wurde SolidCraft 0.27.1,
`solidcraft-cli` muss im `PATH` liegen):

```
python3 tools/check_parts.py [name ...]   # Features und Maße der Teile und Baugruppen (nur lesend)
python3 tools/fit_check.py [--no-images]  # Passungsprüfung, schreibt reference/fit-check.json
```

Exit-Codes: `check_parts.py` 0 = alles PASS, 1 = Prüfung fehlgeschlagen, 2 = SolidCraft nicht erreichbar.
`fit_check.py` (auch `--json PFAD`) liefert 1 (Warnung), solange der Stecker-Modellkonflikt besteht, und 2,
wenn SolidCraft nicht läuft oder ein unerwarteter Fehler auftritt.

![Schnitt durch die Kartennuten](reference/img/section-slot2-grooves.png)

## Lizenz

[CERN-OHL-S-2.0](LICENSE), wie die `HW-Module-*`-Repos.

# HW-Enclosure — Design

Stand: 2026-11-08 · Autor: Peter (OE5XRX) mit Claude

## Worum es geht

Die OE5XRX-Remote-Station besteht aus einem BusBoard und bis zu sechs 100×100-mm-Modulen.
Für die erste Station (DX-Camp, Sommer 2025) wurde ein 3D-gedrucktes Gehäuse gebaut. Die
CAD-Quelle (Fusion 360 auf einem Mac) ist verloren; übrig blieben die G-Codes auf dem Drucker.
Daraus wurden die Teile am 2026-11-08 parametrisch in **SolidCraft** nachgebaut.

Jetzt soll daraus ein ordentliches Repo werden, in dem

1. die Gehäuseteile als bearbeitbare SolidCraft-Designs liegen,
2. eine **Gesamtbaugruppe** aus Gehäuse + echten Platinen (KiCad-STEP) die **Passung prüft**,
3. später eine **19-Zoll-Variante** dazukommt.

Das Desktop-Gehäuse ist zum Mitnehmen/Herzeigen und für den Schreibtisch gedacht.

## Ziele

- **Repo `OE5XRX/HW-Enclosure`** (GitHub, Org OE5XRX), angelegt und gepusht.
- **Teile** (SolidCraft `.sc`, parametrisch, zusätzlich `.step` exportiert):
  - `leiste` — bereits nachgebaut
  - `deckplatte` — bereits nachgebaut, **Logo wird ersetzt** (siehe unten)
  - `grundgestell` — bereits nachgebaut (gespiegelte Version, so wie gedruckt)
  - `grundgestell` **normal** — neu, **reines Spiegelbild** des vorhandenen (vom User bestätigt:
    keine weiteren Unterschiede). Spiegelebene quer zur 136-mm-Länge (YZ durch die Mitte), damit
    die Rückwand hinten bleibt.
- **Stückzahl pro Station (vom User):** 1 × Grundgestell normal, 1 × Grundgestell gespiegelt,
  2 × Deckplatte (vorne und hinten), 4 × Leiste (2 pro Gestell).
- **Neues Logo auf der Deckplatte:** das aktuelle Logo aus dem Repo `OE5XRX/branding`
  (`logo/oe5xrx-full.svg`, Mark + Wordmark) ersetzt das nachgezeichnete 2025er-Logo. Der
  Schriftzug bleibt **so wie im Branding** (Konturen aus dem SVG), **kein** editierbarer
  SolidCraft-Text. Erhaben wie bisher (0,6 mm), im gleichen Rahmen-Bereich der Platte.
- **Gesamtbaugruppe `station.sc`** mit allen Gehäuseteilen (als verknüpfte Komponenten) und den
  Platinen (als STEP-Komponenten), so positioniert, wie die Station real zusammengebaut ist.
  Damit soll man prüfen können:
  1. passen die Module in die Kartennuten des Gestells,
  2. treffen die Steckverbinder der Module die des BusBoards,
  3. passen die Montagelöcher des BusBoards zu den Löchern/Taschen der Halter.
  SolidCraft soll Kollisionen zwischen Körpern melden; Ergebnis der Prüfung wird dokumentiert.
- **Slot-Belegung in `station.sc`:**
  | Slot | Modul | |
  |---|---|---|
  | 1 | PowerBoard | vom BusBoard vorgegeben |
  | 2 | CM4Carrier | vom BusBoard vorgegeben |
  | 3–6 | FMTransceiver (4×) | Slots sind frei belegbar; FM als Platzhalter |
- **PCB-STEPs** werden per Skript aus den lokal geklonten `HW-Module-*`-Repos erzeugt
  (`kicad-cli pcb export step --subst-models`) und **eingecheckt** (≈ 26 MB unkomprimiert,
  ≈ 4,5 MB in Git), damit `station.sc` nach dem Klonen sofort vollständig ist.
  - **Quelle ist immer `origin/main`** jedes Modul-Repos (vom User). Das Skript bricht ab bei
    uncommitteten Änderungen oder wenn der Stand nicht `origin/main` entspricht, und schreibt
    Repo + Commit je STEP in `pcb/SOURCES.md`. (Lokal steht z. B. FMTransceiver auf einem
    Feature-Branch — der wird nicht verwendet.)
  - Module: BusBoard, PowerBoard, CM4Carrier, FMTransceiver, DeviceTester.
  - **DeviceTester zusätzlich in Variante `Slot`** (`--variant Slot --no-dnp`): In dieser
    KiCad-Variante sind die Bauteile, die im Slot-Betrieb stören, als DNP markiert
    (J201, J202, J203, C201, R201–R203, D201). Die Variante liegt im DeviceTester-Repo
    (PR OE5XRX/HW-Module-DeviceTester#6, KiCad-10-Format); die HW-CI wurde dafür auf KiCad 10
    gehoben (OE5XRX/HW-Module-CI#40). Export erst, wenn der PR auf `main` ist.
  - Der DeviceTester ist **nicht** in `station.sc` bestückt, liegt aber als STEP bereit.
- **README** mit: Teileliste, Druckhinweisen (PETG, 0,2 mm Layer — Werte aus den Original-G-Codes),
  Einschmelzmuttern/Schrauben, wie man die PCB-STEPs neu erzeugt, wie man `station.sc` öffnet.
- **Nachbau-Dokumentation** (`reference/`): wie die Maße aus dem G-Code abgeleitet wurden
  (Linienbreite 0,4, `xy_hole_compensation` 0,27, Layer-Raster), welche Werte gemessen und
  welche gerundet/interpretiert sind.

## Nicht-Ziele

- **Keine** Release-Anhänge an die Modul-Repos und **keine** Änderungen an der HW-CI
  (`HW-Module-CI`). Wurde besprochen und bewusst gestrichen.
- **Keine** 19-Zoll-Variante in diesem Schritt — nur Platz dafür im Repo vorsehen.
- **Kein** Herauslösen gemeinsamer Teile für Desktop/19″ jetzt. Erst alles unter `desktop/`;
  was wiederverwendbar ist, entscheidet sich, wenn die 19″-Version entworfen wird.
- **Keine** Änderungen an den Platinen selbst. Fällt bei der Passungsprüfung ein Problem auf,
  wird es dokumentiert und dem User gemeldet, nicht still im Gehäuse „wegkonstruiert“.

## Anti-Ziele (wäre ein Fehlschlag, auch wenn es „funktioniert“)

- Eine Baugruppe, in der Teile nur „ungefähr hingeschoben“ sind und Kollisionsfreiheit
  vortäuschen. Positionen müssen aus echten Maßen kommen (Bohrbilder, Nutlage, Steckerlage
  aus KiCad), nicht aus Augenmaß.
- Ein Repo, das ohne die lokal geklonten Modul-Repos nicht öffnet (deshalb STEPs einchecken).
- Stillschweigend geänderte Gehäusemaße. Die Nachbau-Teile entsprechen dem Gedruckten;
  Änderungen nur bewusst und dokumentiert.

## Randbedingungen

- **Werkzeuge:** SolidCraft 0.27.1 (läuft als `solidcraft --control 7878`, MCP-Server
  `solidcraft` registriert, Zugriff alternativ per JSON-RPC über
  `solidcraft-cli mcp --connect 127.0.0.1:7878`), KiCad 10.0.5 (`kicad-cli`), `gh` mit Zugriff
  auf die Org OE5XRX.
- SolidCraft-Baugruppen: `component.insert_design` (verknüpfte `.sc`-Teile, mit
  `component.update_links` aktualisierbar), `file.insert_step` (STEP als Komponente),
  Joints/`occurrence.move` zum Platzieren, `solid.mirror` zum Spiegeln, `sketch.insert_svg`
  für das Logo.
- Lage der Dateien heute: `~/oe5xrx/station-case/` (`cad/` mit `leiste`, `deckplatte`,
  `grundgestell` je `.sc/.step/.stl`, `logo_2025.dxf`; `gcode/` mit den drei Original-G-Codes).
  Dieser Ordner wird zum Repo bzw. wird ins neue Repo überführt.
- STL und G-Code werden **nicht** eingecheckt (`.gitignore`). G-Codes bleiben lokal als Referenz.
- Commit-Nachrichten enden mit `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Entschieden (vom User)

- Repo-Name `HW-Enclosure`, Desktop- und 19″-Version im selben Repo.
- Struktur: alles Gehäuse-Spezifische vorerst unter `desktop/`.
- Neues Logo = Branding-SVG, Schriftzug als Kontur wie im Branding.
- PCB-STEPs einchecken; STL/G-Code nicht.
- Slot-Belegung wie oben; DeviceTester per KiCad-Variante `Slot` abgespeckt.
- Wie Leiste und Deckplatte am Gestell sitzen, soll **aus den Bohrbildern** ermittelt werden.
- Repo öffentlich, Lizenz **CERN-OHL-S-2.0** wie die `HW-Module-*`-Repos (meine Entscheidung,
  dem User genannt, kein Widerspruch).

## Vorgeschlagene Repo-Struktur (meine Entscheidung, änderbar)

```
HW-Enclosure/
├── README.md
├── .gitignore              (*.stl, *.3mf, *.gcode, .~*.lock, Backups)
├── desktop/
│   ├── parts/              leiste.sc, deckplatte.sc, grundgestell.sc, grundgestell-mirror.sc (+ .step)
│   ├── logo/               oe5xrx-full.svg (Kopie aus branding, mit Quell-Commit vermerkt)
│   └── station.sc          Gesamtbaugruppe
├── pcb/
│   ├── export-steps.sh     erzeugt alle STEPs aus ../HW-Module-* (Pfad konfigurierbar)
│   ├── *.step              eingecheckt, mit Quell-Commit je Modul in pcb/SOURCES.md
├── reference/
│   └── reconstruction.md   Maße aus dem G-Code, Messmethode, Unsicherheiten
├── rack-19/                (leer bzw. README-Platzhalter)
└── docs/superpowers/specs/ dieses Dokument
```

Namen der Gestell-Dateien: Das vorhandene Modell ist die **gespiegelte** Version (Datei hieß
`mirror_…gcode`). Die neue Spiegelung davon ist die **normale** Version.

## Bekannte Teile-Daten (Nachbau, G-Code-Koordinaten sind abgezogen)

- **Leiste:** 136 × 8,5 × 3; 2 × Ø 3,2 im Abstand 100, 4,0 vom Längsrand (0,25 außermittig).
- **Deckplatte:** 117 × 110 × 3; 4 × Ø 3,2 asymmetrisch, bezogen auf Ecke links unten:
  (8 | 4,5), (9 | 105,5), (112 | 10), (112 | 100). Logo bisher 0,6 hoch, Rahmen ≈ 82,4 × 82,9,
  Mitte bei (+1,55 | −0,07) relativ zur Plattenmitte.
- **Grundgestell (gespiegelt):** 136 × 120, Deck 8,5 hoch, Rückwand 11,5 dick / 20 hoch,
  Stufe hinten 6 tief / 5 hoch; 6 Durchbrüche 10 × 92,5 im Raster 20; 6 Nuten 3 breit / 4 tief
  (Mitte = Durchbruch-Kante links + 16), vorne offen; Rückseite 6 × Ø 5 × 5 Taschen (x-Raster 20,
  z = 10); seitlich 4 Bohrungen Ø 5×5 + Ø 3,2 auf 10 Tiefe (hinten y-Mitte Rückwand z = 10,
  vorne 5 vom Rand z = 4,5); vorne 2 Bohrungen Ø 5×5 + Ø 3,2 auf 9 Tiefe (x = ±50, z = 4,5).
- Die Ø-5-Taschen sind vermutlich für Einschmelzmuttern M3 — **Interpretation**, nicht gemessen.

## Dem Builder überlassen

- Wie genau die Teile zueinander liegen (Gestell unten/oben, Leiste, Deckplatte, BusBoard) —
  aus Bohrbildern und Platinenmaßen herleiten; die Herleitung in `reference/` dokumentieren.
  Wenn die Bohrbilder **nicht** eindeutig zusammenpassen: dem User melden statt raten.
- Welches Gestell-Ende Slot 1 ist — aus der Steckerlage auf dem BusBoard (KiCad) ableiten.
- Platzierungsmethode in SolidCraft (Joints vs. feste Positionen), solange die Positionen aus
  Maßen kommen und bei einem neuen PCB-Export erhalten bleiben.
- Größe/Lage des neuen Logos innerhalb der Deckplatte (sinnvoll: vorhandener Logo-Bereich,
  gleiche Höhe 0,6 mm); Behandlung von Strichen im SVG (`stroke`), die erst in Flächen
  umgewandelt werden müssen.
- Ob `export-steps.sh` Bash oder Python ist; Erfassung des Quell-Commits je Modul.
- Format und Inhalt des Prüfberichts der Baugruppe (Kollisionen, Abstände).

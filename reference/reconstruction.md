# Nachbau aus dem G-Code

Die Fusion-360-Quelle des Gehäuses von 2025 ist verloren. Übrig waren die drei G-Codes
(Slicer-Profil: 0,2 mm PETG, Klipper). Die Teile in `desktop/parts/` sind daraus in SolidCraft
nachgebaut. Die G-Codes selbst liegen nicht im Repo.

## Methode

1. Aus den G-Code-Pfaden pro Schicht Außenwand-Konturen und Lochkreise entnommen.
2. **Außenwand-Linienbreite 0,4 mm** (`outer_wall_line_width = 100 %` bei 0,4-mm-Düse): Der Weg der
   Außenwand liegt eine halbe Linienbreite (0,2 mm) innerhalb der Teilkante. Gemessene Pfadmaße
   wurden um diesen Betrag nach außen korrigiert.
3. **`xy_hole_compensation` 0,27 mm:** Der Slicer korrigiert Lochmaße um 0,27 mm; diese Verschiebung
   wurde bei den gemessenen Lochdurchmessern berücksichtigt, damit die Modellmaße (z. B. Ø 3,2) und
   nicht die Druckpfadmaße im Modell stehen.
4. **Schichtraster:** erste Schicht 0,15 mm, danach 0,2 mm, also Schichtoberkanten bei
   0,15 + n·0,2. Höhen im G-Code sind Schichtoberkanten.
5. **Layer-Mitte-Regel für Höhen:** Ein Merkmal (Absatz, Tiefe) beginnt oder endet in einer Schicht,
   nicht dazwischen. Die wahre Höhe liegt in der Schichtmitte, bezogen auf das Raster; gerundet auf
   das nächste plausible Konstruktionsmaß (z. B. 5, 8,5, 11,5, 20).
6. Koordinaten wurden um den Druckbett-Versatz bereinigt (G-Code-Koordinaten sind abgezogen), damit
   die Teile im eigenen Ursprung liegen.

## Gemessen und gewählt

Maße in mm, so wie sie nachgebaut wurden. "Gewählt" bedeutet auf ein plausibles Konstruktionsmaß
gerundet, "gemessen" direkt aus dem G-Code abgeleitet.

| Teil | Maße |
|---|---|
| **Leiste** | 136 × 8,5 × 3; 2 × Ø 3,2 im Abstand 100, 4,0 vom Längsrand (also 0,25 außermittig) |
| **Deckplatte** | 117 × 110 × 3; 4 × Ø 3,2, bezogen auf die linke untere Ecke: (8 \| 4,5), (9 \| 105,5), (112 \| 10), (112 \| 100). Logo 0,6 erhaben |
| **Grundgestell (gespiegelt)** | 136 × 120; Deck 8,5 hoch; Rückwand 11,5 dick / 20 hoch; Stufe hinten 6 tief / 5 hoch |
| | 6 Durchbrüche 10 × 92,5 im Raster 20 |
| | 6 Nuten 3 breit / 4 tief (Mitte = linke Durchbruch-Kante + 16), vorne offen |
| | Rückseite 6 × Ø 5 × 5 Taschen (x-Raster 20, z = 10) |
| | seitlich 4 Bohrungen Ø 5 × 5 + Ø 3,2 auf 10 Tiefe (hinten y-Mitte Rückwand, z = 10; vorne 5 vom Rand, z = 4,5) |
| | vorne 2 Bohrungen Ø 5 × 5 + Ø 3,2 auf 9 Tiefe (x = ±50, z = 4,5) |
| **Grundgestell (normal)** | reines Spiegelbild des gespiegelten (Spiegelebene YZ durch die Mitte der 136-mm-Länge, Rückwand bleibt hinten); vom Benutzer bestätigt: keine weiteren Unterschiede |

Auffällig ist die Asymmetrie der Deckplatte (Loch (9 | 105,5) gegenüber (8 | 100)), die zur offenen
1,0-mm-Frage in [assembly.md](assembly.md) führt. Ob das ein Messfehler, ein Konstruktionsfehler oder
Absicht ist, lässt sich aus dem G-Code allein nicht entscheiden.

## Neu gegenüber 2025

- **Logo:** Das 2025er-Logo (`reference/logo_2025.dxf`, nachgezeichnet) ist durch das aktuelle
  Branding-Logo ersetzt (80 mm breit, 0,6 erhaben, mittig). Siehe
  [../desktop/logo/SOURCE.md](../desktop/logo/SOURCE.md).
- **Normales Grundgestell:** neu als Spiegelung erzeugt, nie gedruckt.

## Interpretation (nicht gemessen)

- Die **Ø-5×5-Taschen** sind als Aufnahmen für **M3-Einschmelzmuttern** gedeutet. Das ist
  plausibel (Ø 5 × 5 mm ist übliche Größe für M3-Einsätze, die Ø-3,2-Bohrung dahinter passt zur
  M3-Schraube), aber nicht belegt.
- Wie Leiste und Deckplatte am Gestell sitzen, ist **aus den Bohrbildern abgeleitet**
  ([assembly.md](assembly.md)); das Lochbild passt für die Deckplatten (seitlich) und die vorderen
  Leisten mit Abweichung 0,000, nur die hinteren Leisten sind eine unbestätigte Hypothese.
- Schraubenlängen sind unbekannt.

# Kalibrier-Set – erster Tag am Creator 5 Pro

Alle Teile liegen flach, brauchen keine Stützen und sind je unter ~30 Min. gedacht. Geprüft am 14.11.2026: jede Datei mit OpenSCAD gerendert,
jede STL wasserdicht; Versatz-Farbkörper paarweise Schnittvolumen 0 mm³, Köpfe 2–4 liegen vollständig auf Kopf 1 auf (keine losen Teile).
Reihenfolge am ersten Tag: 1 → 2 → 3 → 4 → 5. Material PLA, Schicht 0.20 (Versatz/Passung auch 0.12 möglich).

| # | Datei(en) → Kopf | Größe | Was du abliest | Was du Claude zurückmeldest |
|---|---|---|---|---|
| 1 | `haftung.scad` → K1 | 200×200, 1 Schicht | Fünf Felder (4 Ecken + Mitte). Gleichmäßig matt, Bahnen verschmolzen, nichts löst sich = gut. Durchsichtig/Lücken = Düse zu hoch, Rillen/rau/Wellen = zu tief. | Je Feld (VL, VR, HL, HR, Mitte): „gut / zu hoch / zu tief“ + Foto |
| 2 | `winkel.scad` → K1 | 100×100×2 | Außen beide Diagonalen messen: A (Punkt unten links) → gegenüber und die andere. Außerdem Kantenlänge in X (Pfeil) und Y. Soll: Diagonalen 141,42 mm, Kanten 100,0 mm. | Diagonale A–C, Diagonale B–D, Länge X, Länge Y (je 0,05 mm genau) |
| 3 | `versatz_k1.scad` → K1, `versatz_k2.scad` → K2, `versatz_k3.scad` → K3, `versatz_k4.scad` → K4 | 112×80×1,8 | Je Kopf zwei Nonien (Zeile = X, Spalte = Y). Oben/rechts die Striche von Kopf n (Teilung 1,9), darunter/links die Hauptskala von K1 (Teilung 2,0, erhaben – mit Streiflicht ansehen). Den Strich suchen, an dem beide **genau fluchten**: Mitte (langer Strich) = 0, jeder Strich daneben = 0,1 mm, mittellange Striche = ±0,5, Enden = ±1,0. Rechts von der Mitte = Kopf n liegt zu weit in +X; oberhalb der Mitte = zu weit in +Y. | Je Kopf: „K2: X +0,3 / Y −0,1“ usw.; Foto senkrecht von oben |
| 4 | `passung.scad` → K1 | 100×24×5 + Stift | Stift Ø 8 von oben in jedes Loch stecken (Löcher Ø 8 + 0 / 0,1 / 0,15 / 0,2 / 0,3 / 0,4, Zahl eingeprägt). Dazu Stift mit Messschieber messen. | Kleinstes Loch, in das der Stift **ohne Gewalt** geht; Loch für „saugend/drehbar“; gemessener Stift-Ø |
| 5 | `bruecke.scad` → K1 | 160×70×12 | Brücken 10/20/30/40 mm: Unterseite ansehen – glatt, leicht durchhängend, Fäden lose? Überhänge 45/55/65° (ab der Senkrechten): ab welchem Winkel wird die Unterseite rau/lockig? | Längste saubere Brücke, Durchhang in mm; letzter sauberer Überhang-Winkel; Fotos der Unterseiten |

**Hinweise**
- Teil 1 ist 0,25 mm dick = genau eine Erstschicht im Profil „0.20mm Standard @FF C5“ (gewünscht waren 0,2 mm; dünner legt Orca keine eigene Schicht an).
- Teil 3: Die vier Dateien mit `--zusammen` als **ein** Teil slicen (`versatz_k1.scad:PLA:1 … versatz_k4.scad:PLA:4`), Schicht 0.12 oder 0.20.
  Kontrastreiche Farben nehmen (z. B. K1 schwarz, K2 gold, K3 rot, K4 weiß). Bereich ±1,0 mm – liegt ein Kopf weiter daneben, fluchtet nur ein Ende: dann „mehr als 1 mm“ melden.
- Teil 4 sagt, welches `spiel` im Baukasten (`modelle/baukasten`) passt: das Spiel des Lochs, in das der Stift leicht gleitet = `spiel` für Gleitpassung.
- Aus 2 berechnet Claude den Schräglauf: (d1 − d2) / 2 / 100 mm ≈ Winkelfehler in rad. Aus 3 die Kopf-Offsets für die Druckereinstellung.

Druck-Aufrufe (Beispiel):
```
python3 werkzeug/druck.py --drucker c5pro --name kal_haftung --teil modelle/kalibrier/haftung.scad:PLA:1 --schicht 0.20 --brim aus
python3 werkzeug/druck.py --drucker c5pro --name kal_versatz --teil modelle/kalibrier/versatz_k1.scad:PLA:1 \
  --teil modelle/kalibrier/versatz_k2.scad:PLA:2 --teil modelle/kalibrier/versatz_k3.scad:PLA:3 \
  --teil modelle/kalibrier/versatz_k4.scad:PLA:4 --farben "schwarz,gold,rot,weiss" --zusammen --schicht 0.12 --brim aus
```

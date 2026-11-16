# Druckauftrag: gitarre370_hals

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `gitarre370_hals_c5pro.gcode`  
**Druckzeit (geschätzt):** 10h 22m 53s  
**Filament:** 25.77, 10.04, 17.69, 0.73 g (8.64 m, 3.36 m, 5.93 m, 0.25 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | grau | Flashforge PLA Basic @FF C5P |
| 2 | PLA | weinrot | Flashforge PLA Basic @FF C5P |
| 3 | PLA | schwarz | Flashforge PLA Basic @FF C5P |
| 4 | PLA | silber | Flashforge PLA Basic @FF C5P |

## Teil 2 von 2: Hals mit Kopfplatte und Zapfen (liegt schräg auf dem Bett, 251 mm lang)

- Köpfe: 1 Grau, 2 Weinrot, 3 Schwarz, 4 Silber oder Hellgrau (Bünde, Ziffern).
- Stützen unter Halsrücken und Kopfplatte; der Zapfen steht auf dem Bett. Saiten: Kerben im Sattel, sechs Löcher in der Kopfplatte.
- **Decke:** durchgehend Weinrot; das schwarze Muster liegt unter einer 0,16 mm dicken Haut (zwei Schichten) und soll durchscheinen. Wie stark, hängt vom Filament ab –
  ungedruckt. Zu schwach: `--haut 0.08` (eine Schicht); zu hart: `--haut 0.24`.
- **Maximale Details:** 0,25-mm-Düse auf allen Köpfen, Schicht 0,08 mm, Arachne (`min_bead_width=70%`, `min_feature_size=20%`), Auflösung 0,008 mm, nur eine Wand an Deckflächen,
  Außenwand 30 mm/s, kleine Umrisse 20 mm/s, Deckfläche 40 mm/s, 8 Deckschichten, Stützen nur vom Druckbett. Kein Spulenwechsel mehr nötig.
- Alles nur gerechnet, am Gerät nicht erprobt.

## Einstellungen

- Düse: 0.25 mm (alle Köpfe)
- Schichthöhe: 0.08 mm (Standard)
- Füllung: 15 %
- Wände: Profil-Standard
- Stützen: auto
- Brim: auto
- Düsentemperatur: 210,210,210,210 °C, Bett: 60,60,60,60 °C

## Teile

- `gitarre_rundum_hals_grau.stl` → Slot 1 (PLA)
- `gitarre_rundum_hals_rot.stl` → Slot 2 (PLA)
- `gitarre_rundum_hals_schwarz.stl` → Slot 3 (PLA)
- `gitarre_rundum_hals_weiss.stl` → Slot 4 (PLA)

Kopfwechsel in der .gcode: 446, benutzte Köpfe: 1, 2, 3, 4

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

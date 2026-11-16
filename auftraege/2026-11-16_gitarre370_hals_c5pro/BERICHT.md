# Druckauftrag: gitarre370_hals

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `gitarre370_hals_c5pro.gcode`  
**Druckzeit (geschätzt):** 11h 41m 31s  
**Filament:** 25.81, 11.83, 17.68, 5.67 g (8.65 m, 3.97 m, 5.93 m, 1.90 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | grau | Flashforge PLA Basic @FF C5P |
| 2 | PLA | rot | Flashforge PLA Basic @FF C5P |
| 3 | PLA | schwarz | Flashforge PLA Basic @FF C5P |
| 4 | PLA | dunkelrot | Flashforge PLA Basic @FF C5P |

## Teil 2 von 2: Hals mit Kopfplatte und Zapfen (liegt schräg auf dem Bett, weil er 251 mm lang ist)

- Kopf 4 startet mit **Dunkelrot** (Wolken der Kopfplatte). Bei **17,62 mm** hält der Druck an (`M25`): an Kopf 4 **Weiß** einlegen, durchspülen, fortsetzen.
  Weiß wird erst ab 20,18 mm gebraucht (Bünde, Ziffern).
- Stützen unter Halsrücken und Kopfplatte; der Zapfen steht auf dem Bett.
- Saiten: Kerben im Sattel, sechs Löcher in der Kopfplatte vor den Mechaniken.

## Maximale Details (0,25-mm-Düse auf allen Köpfen)

- Schicht 0,08 mm, Arachne-Wände (`min_bead_width=70%`, `min_feature_size=20%`), Auflösung 0,008 mm, nur eine Wand an Deckflächen,
  Außenwand 30 mm/s, kleine Umrisse 20 mm/s, Deckfläche 40 mm/s, 8 Deckschichten, Stützen nur vom Druckbett.
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
- `gitarre_rundum_hals_dunkelrot.stl` → Slot 4 (PLA)
- `gitarre_rundum_hals_weiss.stl` → Slot 4 (PLA)

Kopfwechsel in der .gcode: 563, benutzte Köpfe: 1, 2, 3, 4

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

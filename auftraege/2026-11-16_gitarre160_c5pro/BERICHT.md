# Druckauftrag: gitarre160

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `gitarre160_c5pro.gcode`  
**Druckzeit (geschätzt):** 4h 56m 47s  
**Filament:** 12.87, 3.63, 6.23, 0.30 g (4.32 m, 1.22 m, 2.09 m, 0.10 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | grau | Flashforge PLA Basic @FF C5P |
| 2 | PLA | weinrot | Flashforge PLA Basic @FF C5P |
| 3 | PLA | schwarz | Flashforge PLA Basic @FF C5P |
| 4 | PLA | silber | Flashforge PLA Basic @FF C5P |

## Vergleichsstück 160 mm (einteilig, Maßstab 1:6,05) – gleiche Details wie die 370-mm-Fassung

- Köpfe: 1 Grau, 2 Weinrot, 3 Schwarz, 4 Silber oder Hellgrau (Bünde, Ziffern).
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

- `gitarre_rundum_grau.stl` → Slot 1 (PLA)
- `gitarre_rundum_rot.stl` → Slot 2 (PLA)
- `gitarre_rundum_schwarz.stl` → Slot 3 (PLA)
- `gitarre_rundum_weiss.stl` → Slot 4 (PLA)

Kopfwechsel in der .gcode: 181, benutzte Köpfe: 1, 2, 3, 4

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

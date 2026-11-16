# Druckauftrag: gitarre160

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `gitarre160_c5pro.gcode`  
**Druckzeit (geschätzt):** 5h 38m 13s  
**Filament:** 12.87, 4.81, 5.62, 2.87 g (4.31 m, 1.61 m, 1.88 m, 0.96 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | grau | Flashforge PLA Basic @FF C5P |
| 2 | PLA | rot | Flashforge PLA Basic @FF C5P |
| 3 | PLA | schwarz | Flashforge PLA Basic @FF C5P |
| 4 | PLA | dunkelrot | Flashforge PLA Basic @FF C5P |

## Vergleichsstück 160 mm (einteilig, Maßstab 1:6,05) – gleiche Details wie die 370-mm-Fassung

- Kopf 4 startet mit **Dunkelrot**. Bei **7,7 mm** hält der Druck an (`M25`): an Kopf 4 **Weiß** einlegen, durchspülen, fortsetzen (Weiß ab 8,58 mm).
- Einstellungen wie bei 370 mm: 0,25-mm-Düse auf allen Köpfen, Schicht 0,08, Arachne, nur eine Wand an Deckflächen, Außenwand 30 mm/s, Stützen nur vom Bett.
- Nur gerechnet, am Gerät nicht erprobt.

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
- `gitarre_rundum_dunkelrot.stl` → Slot 4 (PLA)
- `gitarre_rundum_weiss.stl` → Slot 4 (PLA)

Kopfwechsel in der .gcode: 237, benutzte Köpfe: 1, 2, 3, 4

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

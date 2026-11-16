# Druckauftrag: gitarre370_hals

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `gitarre370_hals_c5pro.gcode`  
**Druckzeit (geschätzt):** 10h 24m 14s  
**Filament:** 25.87, 10.04, 17.73, 0.73 g (8.67 m, 3.37 m, 5.95 m, 0.25 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | grau | Flashforge PLA Basic @FF C5P |
| 2 | PLA | weinrot | Flashforge PLA Basic @FF C5P |
| 3 | PLA | schwarz | Flashforge PLA Basic @FF C5P |
| 4 | PLA | silber | Flashforge PLA Basic @FF C5P |

## Teil 2 von 2: Hals mit Kopfplatte und Zapfen – Fassung mit Kegellöchern für drehbare Steckwirbel

- Köpfe: 1 Grau, 2 Weinrot, 3 Schwarz, 4 Silber oder Hellgrau (Bünde, Ziffern). Liegt schräg auf dem Bett (251 mm lang).
- Statt fester Achsen sechs Kegellöcher durch Kopfplatte und Gehäuse; die Wirbel kommen aus dem Auftrag `2026-11-16_gitarre370_wirbel_c5pro`.
- Decke der Kopfplatte: Weinrot als 0,16 mm dünne Haut über dem schwarzen Muster. Stützen unter Halsrücken und Kopfplatte; der Zapfen steht auf dem Bett.
- 0,25-mm-Düse, Schicht 0,08 mm, feinste Einstellungen wie beim Korpus. Nur gerechnet.

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

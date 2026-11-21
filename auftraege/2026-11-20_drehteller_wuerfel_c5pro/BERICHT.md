# Druckauftrag: drehteller_wuerfel

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `Drehteller_Masswuerfel.gcode`  
**Druckzeit (geschätzt):** 1h 2m 32s  
**Filament:** 12.65, 2.16 g (4.24 m, 0.71 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | weiss | Flashforge PLA Basic @FF C5P |
| 2 | PETG | schwarz | Flashforge HS PETG @FF C5P |

## Einstellungen

- Düse: 0.4 mm (alle Köpfe)
- Schichthöhe: 0.12 mm (Standard)
- Füllung: 100 %
- Wände: 3
- Stützen: aus
- Brim: aus
- Düsentemperatur: 210,235 °C, Bett: 65,65 °C

## Teile

- `drehteller_wuerfel_weiss.stl` → Slot 1 (PLA)
- `drehteller_wuerfel_schwarz.stl` → Slot 2 (PETG)

Kopfwechsel in der .gcode: 94, benutzte Köpfe: 1, 2

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

> ⚠ Unterschiedliche Materialien in einem Druck (PETG, PLA) – Haftung zwischen den Materialien und Temperaturen prüfen.

## Schwarz als PETG (21.11.2026)
- Kopf 2 = schwarzes **PETG** (235 °C), Kopf 1 weißes PLA (210 °C), Bett für beide **65 °C** (`--bett 65`, statt 85 °C aus dem PETG-Profil – das wäre für die große PLA-Fläche zu heiß).
- PLA und PETG haften schlecht aneinander → jede schwarze Einlage hat unter der Oberfläche einen **Hinterschnitt** (0,2 mm breiter je Seite, 0,4 mm tief) und sitzt dadurch fest wie ein Schwalbenschwanz.
- Tür beim Druck offen lassen bzw. Kammer nicht heizen (PLA). Nicht gedruckt.

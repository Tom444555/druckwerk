# Druckauftrag: gitarre370_korpus

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `gitarre370_korpus_c5pro.gcode`  
**Druckzeit (geschätzt):** 14h 3m 33s  
**Filament:** 61.04, 7.99, 14.45 g (20.47 m, 2.68 m, 4.85 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | grau | Flashforge PLA Basic @FF C5P |
| 2 | PLA | weinrot | Flashforge PLA Basic @FF C5P |
| 3 | PLA | schwarz | Flashforge PLA Basic @FF C5P |

## Teil 1 von 2: Korpus (Gitarre 370 mm, Maßstab 1:2,62) – Fassung mit Saitenfach auf der Rückseite

- Köpfe: 1 Grau, 2 Weinrot, 3 Schwarz. Kopf 4 bleibt leer.
- Rückseite: Fach 24,5 × 3,6 mm, 3,4 mm tief, über den sechs Saitenlöchern; oben eine Stufe für den Deckel (Auftrag `2026-11-16_gitarre370_klappe_c5pro`).
  Das Fach liegt beim Druck auf dem Bett: Stützen darin nach dem Druck herausnehmen.
- Decke: Weinrot als 0,16 mm dünne Haut über dem schwarzen Muster. Schlitz oben für den Zapfen des Halses (Spiel 0,12 mm je Seite).
- 0,25-mm-Düse, Schicht 0,08 mm, feinste Einstellungen. Nur gerechnet.

## Einstellungen

- Düse: 0.25 mm (alle Köpfe)
- Schichthöhe: 0.08 mm (Standard)
- Füllung: 12 %
- Wände: Profil-Standard
- Stützen: auto
- Brim: auto
- Düsentemperatur: 210,210,210 °C, Bett: 60,60,60 °C

## Teile

- `gitarre_rundum_korpus_grau.stl` → Slot 1 (PLA)
- `gitarre_rundum_korpus_rot.stl` → Slot 2 (PLA)
- `gitarre_rundum_korpus_schwarz.stl` → Slot 3 (PLA)

Kopfwechsel in der .gcode: 266, benutzte Köpfe: 1, 2, 3

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

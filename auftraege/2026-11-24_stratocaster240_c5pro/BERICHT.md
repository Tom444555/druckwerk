# Druckauftrag: stratocaster240

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `Stratocaster_240_komplett.gcode`  
**Druckzeit (geschätzt):** 9h 54m 23s  
**Filament:** 27.74, 9.17, 10.92, 8.30 g (9.30 m, 3.08 m, 3.66 m, 2.78 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | creme | Flashforge PLA Basic @FF C5P |
| 2 | PLA | weiß | Flashforge PLA Basic @FF C5P |
| 3 | PLA | holz | Flashforge PLA Basic @FF C5P |
| 4 | PLA | silber | Flashforge PLA Basic @FF C5P |

## Einstellungen

- Düse: 0.25 mm (alle Köpfe)
- Schichthöhe: 0.08 mm (Standard)
- Füllung: 15 %
- Wände: Profil-Standard
- Kopf 1: Hersteller-Filamentprofil für 0,25-mm-Düse (220 °C, höchstens 2.8 mm³/s).
- Kopf 2: Hersteller-Filamentprofil für 0,25-mm-Düse (220 °C, höchstens 2.8 mm³/s).
- Kopf 3: Hersteller-Filamentprofil für 0,25-mm-Düse (220 °C, höchstens 2.8 mm³/s).
- Kopf 4: Hersteller-Filamentprofil für 0,25-mm-Düse (220 °C, höchstens 2.8 mm³/s).
- Stützen: aus
- Brim: auto
- Düsentemperatur: 220,220,220,220 °C, Bett: 55,55,55,55 °C

## Teile

- `strat_korpus.stl` → Slot 1 (PLA)
- `strat_weiss.stl` → Slot 2 (PLA)
- `strat_hals.stl` → Slot 3 (PLA)
- `strat_metall.stl` → Slot 4 (PLA)
- `strat_schwarz.stl` → Slot 1 (PLA)
- `strat_wirbel_platte.stl` → Slot 4 (PLA)
- `strat_regler_platte.stl` → Slot 2 (PLA)

Kopfwechsel in der .gcode: 427, benutzte Köpfe: 1, 2, 3, 4

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

## Spulenwechsel an Kopf 1 (fünfte Farbe)

- Die Datei hält bei **10,34 mm** von selbst an (`M25`). Dann an **Kopf 1 Creme gegen Schwarz** tauschen, nachschieben, bis rein Schwarz kommt, und fortsetzen.
- Bis 10,26 mm druckt Kopf 1 den Korpus (creme), ab 10,50 mm nur noch Schwarz: schwarze Mittellage an der Schlagbrett-Kante, 18 Tonabnehmer-Pole, 10 Griffbrett-Punkte.
- Ohne Wechsel werden diese Teile creme statt schwarz – der Druck gelingt trotzdem.
- Am Gerät noch nicht erprobt.

## Drehbare Steckregler (neu bei 240 mm)

- Vier Regler (drei gebraucht, einer Ersatz) liegen kopfüber neben der Gitarre, Kopf 2 (weiß): Kappe Ø 4,4 mit 20 Rippen, Rock Ø 6,3, Höhe 3,3 mm, Zapfen Ø 2,0 × 3,6 mm.
- Loch im Schlagbrett Ø 2,3 × 4,0 mm (Spiel 0,15 je Seite). Der Zapfen ist an der Wurzel 0,02 mm dicker als das Loch: Regler eindrücken, bis er leicht klemmt – er bleibt drehbar.
- Wirbel bei dieser Größe mit Rädern Ø 6,4 auf einer Ebene (Kegel Ø 2,85 → 2,15). Alles nur gerechnet, nicht gedruckt.

- Bau: `python3 werkzeug/gitarre_farben.py modelle/quelle/stratocaster_original.stl <ziel> 240 --schnur 1 --details 1 --regler 1`, slicen mit `--wie` vom 190er-Auftrag, danach `spulenwechsel.py <gcode> --kopf 1 --min-luecke 0.1 --bei 10.4`; Teil `strat_schwarz.stl` bekommt in auftrag.json `"farbe": "schwarz"`.

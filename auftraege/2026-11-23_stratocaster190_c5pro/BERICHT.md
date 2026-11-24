# Druckauftrag: stratocaster190

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `Stratocaster_190_komplett.gcode`  
**Druckzeit (geschätzt):** 6h 12m 2s  
**Filament:** 17.51, 2.98, 7.09, 6.28 g (5.87 m, 1.00 m, 2.38 m, 2.11 m)  


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
- Detail-Paket: Arachne (70 %/20 %), Auflösung 0,008, eine Wand oben, Außenwand 30 / Kleinumfang 20 / Oberfläche 40 mm/s, Außenwand-Beschleunigung 3000, 8 Deckschichten, Stützen nur ab Platte.
- Kopf 1: Hersteller-Filamentprofil für 0,25-mm-Düse (220 °C, höchstens 2.8 mm³/s).
- Kopf 2: Hersteller-Filamentprofil für 0,25-mm-Düse (220 °C, höchstens 2.8 mm³/s).
- Kopf 3: Hersteller-Filamentprofil für 0,25-mm-Düse (220 °C, höchstens 2.8 mm³/s).
- Kopf 4: Hersteller-Filamentprofil für 0,25-mm-Düse (220 °C, höchstens 2.8 mm³/s).
- Stützen: auto
- Brim: auto
- Düsentemperatur: 220,220,220,220 °C, Bett: 55,55,55,55 °C

## Teile

- `strat_korpus.stl` → Slot 1 (PLA)
- `strat_weiss.stl` → Slot 2 (PLA)
- `strat_hals.stl` → Slot 3 (PLA)
- `strat_metall.stl` → Slot 4 (PLA)
- `strat_schwarz.stl` → Slot 1 (PLA)
- `strat_wirbel_platte.stl` → Slot 4 (PLA)

Kopfwechsel in der .gcode: 273, benutzte Köpfe: 1, 2, 3, 4

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

## Spulenwechsel an Kopf 1 (fünfte Farbe)

- Die Datei hält bei **8,26 mm** von selbst an (`M25`). Dann an **Kopf 1 Creme gegen Schwarz** tauschen, nachschieben, bis rein Schwarz kommt, und fortsetzen.
- Bis 8,18 mm druckt Kopf 1 den Korpus (creme), ab 8,34 mm nur noch Schwarz: schwarze Mittellage an der Schlagbrett-Kante (eine Schicht zwischen Weiß), 18 Tonabnehmer-Pole, 10 Griffbrett-Punkte.
- Ohne Wechsel werden diese Teile creme statt schwarz – der Druck gelingt trotzdem.
- Am Gerät noch nicht erprobt.

- Bau: `python3 werkzeug/gitarre_farben.py modelle/quelle/stratocaster_original.stl <ziel> 190 --schnur 1 --details 1`, danach `spulenwechsel.py <gcode> --kopf 1 --min-luecke 0.1 --bei 8.25`; Teil `strat_schwarz.stl` bekommt in auftrag.json `"farbe": "schwarz"`.

## Änderung 24.11.2026 (Toms Bildschirmfotos)
- Schlagbrett dreilagig an der senkrechten Kante: unten Weiß, Mitte Schwarz, oben Weiß – oben auf der Fläche keine schwarze Linie mehr.
- Buchsenplatte: Umriss rundum gleich (alte Platte des Original-Netzes stand rechts als zweite Kante über), Schrauben bleiben drauf.
- 06:45 Nachbesserung: Buchsenplatte als spiegelgleiches Oval (15,5 × 6,2 mm), Achse durch beide Schrauben; Reste der schiefen alten Platte unten bündig mit Korpus gefüllt, oben weg (keine Beule rechts unten mehr).

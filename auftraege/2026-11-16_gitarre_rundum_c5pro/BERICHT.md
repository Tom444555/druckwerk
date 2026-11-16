# Druckauftrag: gitarre_rundum

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `gitarre_rundum_c5pro.gcode`  
**Druckzeit (geschätzt):** 6h 25m 44s  
**Filament:** 20.24, 5.06, 7.88, 1.73 g (6.78 m, 1.70 m, 2.64 m, 0.58 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | grau | Flashforge PLA Basic @FF C5P |
| 2 | PLA | rot | Flashforge PLA Basic @FF C5P |
| 3 | PLA | schwarz | Flashforge PLA Basic @FF C5P |
| 4 | PLA | dunkelrot | Flashforge PLA Basic @FF C5P |

## Fünfte Farbe: Spulenwechsel an Kopf 4

- Kopf 4 startet mit **Dunkelrot** (Wolken der Decke, etwa 1,7 g mit Reinigungsturm).
- Bei **9,3 mm Höhe** hält der Druck an (Befehl `M25` aus dem Hersteller-Profil): an Kopf 4 **Weiß** einlegen, durchspülen, fortsetzen.
- Weiß wird erst ab 10,8 mm gebraucht (Bünde, Ziffern). Am Gerät noch nicht erprobt.

## Saiten

- Vorbereitet für Draht bis 0,3 mm: sechs Löcher durch den Korpus (hinter den Reitern), Kerben in Reitern und Sattel, sechs Löcher in der Kopfplatte vor den Mechaniken.

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

Kopfwechsel in der .gcode: 231, benutzte Köpfe: 1, 2, 3, 4

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

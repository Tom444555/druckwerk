# Druckauftrag: gitarre370_korpus

**Drucker:** Flashforge Creator 5 Pro  
**Datei für USB:** `gitarre370_korpus_c5pro.gcode`  
**Druckzeit (geschätzt):** 14h 19m 11s  
**Filament:** 60.87, 7.30, 9.79, 5.14 g (20.41 m, 2.45 m, 3.28 m, 1.72 m)  


## Spulen / Köpfe einlegen

| Slot | Material | Farbe | Profil |
|---|---|---|---|
| 1 | PLA | grau | Flashforge PLA Basic @FF C5P |
| 2 | PLA | rot | Flashforge PLA Basic @FF C5P |
| 3 | PLA | schwarz | Flashforge PLA Basic @FF C5P |
| 4 | PLA | dunkelrot | Flashforge PLA Basic @FF C5P |

## Teil 1 von 2: Korpus (Gitarre 370 mm, Maßstab 1:2,62)

- Kopf 4 = **Dunkelrot** für den ganzen Druck, kein Spulenwechsel. Weiß wird am Korpus nicht gebraucht.
- Der Schlitz oben nimmt den Zapfen des Halses auf (Spiel 0,12 mm je Seite). Sitzt er zu stramm: Zapfenflanken leicht schleifen; sitzt er lose: ein Tropfen Kleber.
- Saiten: sechs Löcher hinter den Reitern durch den Korpus, Kerben in den Reitern.
- Decke fällt unter dem Unterarm zum Rand hin ab (Armschräge).

## Maximale Details (0,25-mm-Düse auf allen Köpfen)

- Schicht 0,08 mm, Arachne-Wände (`min_bead_width=70%`, `min_feature_size=20%`), Auflösung 0,008 mm, nur eine Wand an Deckflächen,
  Außenwand 30 mm/s, kleine Umrisse 20 mm/s, Deckfläche 40 mm/s, 8 Deckschichten, Stützen nur vom Druckbett.
- Alles nur gerechnet, am Gerät nicht erprobt.

## Einstellungen

- Düse: 0.25 mm (alle Köpfe)
- Schichthöhe: 0.08 mm (Standard)
- Füllung: 12 %
- Wände: Profil-Standard
- Stützen: auto
- Brim: auto
- Düsentemperatur: 210,210,210,210 °C, Bett: 60,60,60,60 °C

## Teile

- `gitarre_rundum_korpus_grau.stl` → Slot 1 (PLA)
- `gitarre_rundum_korpus_rot.stl` → Slot 2 (PLA)
- `gitarre_rundum_korpus_schwarz.stl` → Slot 3 (PLA)
- `gitarre_rundum_korpus_dunkelrot.stl` → Slot 4 (PLA)

Kopfwechsel in der .gcode: 258, benutzte Köpfe: 1, 2, 3, 4

## Am Drucker

- Geschlossen + Kammerheizung bis 65 °C: erste Wahl für ABS, ASA, Nylon/CF.
- 4 echte Druckköpfe: Farbwechsel ohne Spülabfall, Kopf 1–4 = Farbe 1–4.
- PLA/PETG/TPU: Kammerheizung aus (unter 45 °C), sonst kann die Düse verstopfen.
- USB: .gcode auf FAT32-Stick, am Drucker unter Dateien/USB auswählen.
- Vor dem Start: Druckplatte sauber und leer, richtige Spulen in den Slots.

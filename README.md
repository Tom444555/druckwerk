# druckwerk

**App:** https://tom444555.github.io/druckwerk/ (Start mit nächstem Schritt, Aufträge mit 3D-Vorschau + Download, neuen Auftrag zusammenklicken, Bibliothek/Werkstatt, Material, Drucker; offline-fähig, Sicherung als Datei)

Prompt rein → fertige USB-Druckdatei raus. Für den **Flashforge Creator 5 Pro** (alte Aufträge: Anycubic Kobra X).

**So benutzt du es:** Schreib Claude z. B.
> „druckwerk: Wandhalter für 3 Schraubendreher, schwarz mit rotem Logo“

Du bekommst:
- `<name>_c5pro.gcode` → auf FAT32-USB-Stick → am Drucker starten
- `BERICHT.md` → welcher Kopf welche Farbe, Druckzeit, Filament in Gramm, Einstellungen

Alle Aufträge liegen unter `auftraege/` (Datum_Name), Modelle unter `modelle/`.
Technik und Ablauf für Claude: siehe `CLAUDE.md`.

# druckwerk

**App:** https://tom444555.github.io/druckwerk/ (Aufträge mit 3D-Vorschau + Download, neuen Auftrag zusammenklicken, Drucker, USB-Anleitung)

Prompt rein → fertige USB-Druckdatei raus. Für **Anycubic Kobra X** und **Flashforge Creator 5 Pro**.

**So benutzt du es:** Schreib Claude z. B.
> „druckwerk: Wandhalter für 3 Schraubendreher, schwarz mit rotem Logo, auf der Kobra“

Du bekommst:
- `<name>_kobrax.gcode` bzw. `<name>_c5pro.gcode` → auf FAT32-USB-Stick → am Drucker starten
- `BERICHT.md` → welche Spule/welcher Kopf welche Farbe, Druckzeit, Filament in Gramm, Einstellungen

Alle Aufträge liegen unter `auftraege/` (Datum_Name), Modelle unter `modelle/`.
Technik und Ablauf für Claude: siehe `CLAUDE.md`.

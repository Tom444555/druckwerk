# Nachrecherche Creator 5 Pro – 28.11.2026

Anlass: Tom fragt, ob wirklich alle aktuellen Hersteller-Infos in Druckwerk stecken, und warum das Rot/Bordeaux am
Strat-Schlüsselanhänger geschmiert hat. Der Buddha 150 (0,25 mm / 0,08 mm, Grau + Schwarz, unsere .gcode per USB) läuft
dabei gerade „sehr gut“. **Nichts aus dieser Datei ist am Gerät bestätigt, außer wo es ausdrücklich dasteht.**

## 1. Unsere Werte gegen den neuesten Hersteller-Stand

Verglichen: Flash Studio, öffentlicher Quelltext `FlashForge/Orca-Flashforge`, Zweig `release_0817` (Version 1.7.15,
25.08.2026 – neuer gibt es öffentlich nicht) gegen den Kopf einer Druckwerk-.gcode (0,25-mm-Düse, 0,08 mm, PLA).

**Gleich:** Start-, Kopfwechsel-, Pause- und End-Befehle · Filamentprofil „Flashforge PLA Basic @FF C5P 0.25 nozzle“
(220 °C, Fluss 0,98, Druckvorschub 0,1, höchstens 2,8 mm³/s, Lüfter 70 %) · Rückzug beim Kopfwechsel 2 mm ·
wartende Köpfe −100 °C · Wischturm (seit 28.11. Herstellerwerte).

**Verschieden – Maschine (unsere Basis ist das ältere Orca-2.5-Profil):**

| Wert | Hersteller 1.7.15 | Druckwerk | Einschätzung |
|---|---|---|---|
| Rückzug (`retraction_length`) | 1,0 mm | 0,8 mm | erster Hebel, falls feine Fäden zwischen Teilen bleiben |
| Rückzug ab Fahrweg (`retraction_minimum_travel`) | 1 mm | 2 mm | wie oben |
| Nachschub nach Kopfwechsel (`retract_restart_extra_toolchange`) | 0 | −0,8 mm | unseres fördert nach dem Wechsel etwas weniger; Turm fängt es ab |
| Z-Hub | 0,3 | 0,4 mm | unerheblich |
| Turm-Bauart (`wipe_tower_type`) | type1 | type2 | offen, nicht umgestellt |

**Verschieden – Prozess (gewollt, unser `--detail`):** Arachne statt klassisch · Außenwand 30 statt 60 mm/s ·
Kleinumfang 20 statt 30 · Oberfläche 40 statt 150 · 8 statt 7 Deckschichten · Stützen nur ab Platte ·
Auflösung 0,008 statt 0,012.

**Übernommen am 28.11.:** `--detail` rechnet jetzt mit Auflösung **0,012** (Herstellerwert). Gründe: der Buddha wurde
schon so gerechnet und druckt sauber; eine zu feine Auflösung kann laut Fehlerliste E0017 („Befehls-Warteschlange
voll“) auslösen; die Dateien werden kleiner.

**Bewusst nicht umgestellt:** Rückzug 1,0 / Fahrweg 1 mm. Der eine Druck mit Hersteller-Maschinenprofil (Anhänger über
Flash Studio) hatte Fäden nur beim Rot; der Druck mit unseren 0,8 mm (Buddha) ist sauber. Erst nach dem Buddha-Foto
entscheiden.

## 2. Firmware

- **2.0.0 (Kernel 2.0.7, 22.10.2026):** exFAT/NTFS-Sticks, Objekt überspringen in der App, Düsen-Angaben aus 3MF in der
  Dateiliste, fünf neue Materialarten, verstecktes WLAN, stabileres WLAN, überarbeiteter Reste-Abwurf und Heizregelung,
  **bessere Druckqualität bei 0,08 / 0,10 / 0,12 mm Schicht und bessere Haftung der ersten Schicht**, Schutz gegen
  unbeabsichtigtes Aufheizen nach dem Einschalten. **Kein Zurück auf 1.9.8 oder älter.**
- Welche Fassung auf Toms Gerät läuft, ist offen. Nie während eines Drucks einspielen; danach Kopf-Versatz neu
  kalibrieren. Die Druckwerk-Brücke ist mit 2.0.0 ungeprüft.

## 3. Fluss-Kalibrierung vor dem Druck

- Am Gerät beim Start anwählbar. Je Kopf: aufheizen, kalibrieren, auf Wartetemperatur, nächster Kopf; erst danach
  Nivellieren und Druck. Bei vier Köpfen rund 15 Minuten.
- Sie stimmt auch den Druckvorschub (Pressure Advance) ab. **Ein Wert in der Druckdatei überschreibt das Ergebnis** –
  unsere Dateien setzen 0,1 (Hersteller-Profil). Für Flashforge-Filament richtig; für Fremd-Filament wäre der Versuch
  „Druckvorschub in der Datei aus + Kalibrierung am Gerät an“ sinnvoll. Nicht eingebaut.

## 4. Rot/Bordeaux am Schlüsselanhänger

Befund vom Foto (27.11.): Grau, Schwarz, Weiß sauber; nur Rot aus Kopf 2 rau, verschmiert, Fäden und Klumpen im Turm.
Gedruckt über die 3MF in Flash Studio. Kopf 2 war beim ersten Druck (24./25.11.) schon einmal verstopft.

Wahrscheinliche Gründe, nach Aufwand der Prüfung geordnet:
1. **Düse von Kopf 2 teilweise zu** (Vorgeschichte). Prüfen: von Hand fördern – Faden gerade und glatt?
2. **Zu heiß für diese Spule:** Professional Lab PLA nennt 190–220 °C; das 0,25-mm-Profil fährt 220 °C bei sehr wenig
   Durchsatz (≤ 2,8 mm³/s) → das Material steht lange in der heißen Düse. Der Hersteller nennt bei Fäden: trocknen,
   Rückzug erhöhen, Temperatur anpassen.
3. **Feuchte Spule** (Knistern, Bläschen).
4. **Farbstoff:** Farben derselben Marke fließen unterschiedlich; jede Farbe wie ein eigenes Filament behandeln.

**Neu dafür: `druck.py --temp <kopf>=<°C>`** (mehrfach). Geprüft am Strat-Anhänger mit `--wie … --temp 2=205`:
in der .gcode `nozzle_temperature = 220,205,220,220`, Kopf 2 heizt auf 205 und wartet bei 105 °C; Zeit und Gramm
unverändert (29 min; 1,10 / 0,11 / 0,63 / 0,21 g). Wirkt beim Neu-Rechnen über `--wie` und beim normalen Slicen.

Test nach dem Buddha: Kopf 2 von Hand fördern → Anhänger mit 205 °C drucken → Foto. Bleibt es schlecht: Bordeaux in
einen anderen Kopf legen (wandert der Fehler mit = Filament, bleibt er = Kopf 2).

## 5. Sonst aus Tests und Berichten (nichts davon bei Tom geprüft)

- Geparkte Köpfe tropfen leicht nach; Tropfschutz unter den Köpfen muss beim Aufstellen montiert sein.
- Filament vor mehrfarbigen Drucken trocknen – feuchtes Material gibt Fäden in fremder Farbe.
- Nach Firmware-Update und Düsentausch Kopf-Versatz neu (feine Schrift leidet sonst).
- PETG zieht an diesem Drucker in Tests deutlich mehr Fäden als PLA.
- Ein Test maß die Bettfläche bei Soll 60 °C nach 15 Minuten knapp 8 °C darunter und ungleichmäßig; bei PLA auf der
  PEI-Platte ohne Folgen.

## Quellen

- Flash-Studio-Profile: https://github.com/FlashForge/Orca-Flashforge (Zweig `release_0817`, `resources/profiles/Flashforge`)
- Firmware 2.0.0: https://github.com/Parallel-7/FlashForge-Firmware-Updates/releases/tag/creator-5-pro/2.0.0-1.3.0
- Fluss-Kalibrierung und Druckvorschub: https://github.com/OrcaSlicer/OrcaSlicer/pull/14933
- Bekannte Probleme (E0017 u. a.): https://printer-hub.ru/en/posts/flashforge-creator-5-known-issues
- Flashforge-Wiki, Fäden/Nachtropfen: https://wiki.flashforge.com/en/ad5x/troubleshooting_print_quality_problems
- Flashforge-Wiki, Fragen und Antworten: https://wiki.flashforge.com/en/creator-series/creator-5-series/faq_c5p
- China-Gadgets, Test Creator 5: https://www.china-gadgets.de/flashforge-creator-5-pro-multicolor-multitoolhead-3d-drucker-test-snapmaker-u1-konkurrent/
- Dazu Testberichte (Fauxhammer, Anton Mansson, mizumakes) aus der Suche vom 28.11. – Adressen nicht festgehalten.

# druckwerk – Arbeitsanleitung für Claude

Ziel: Tom gibt einen Prompt („Halter für …, rot/schwarz, auf der Kobra“) → Claude liefert eine
**fertige USB-Druckdatei (.gcode)** plus **BERICHT.md** (Spulen, Einstellungen, Zeit, Gramm).
Tom muss nur noch die Datei auf den USB-Stick ziehen und am Drucker starten.

## Drucker (Standard seit 13.11.2026: `c5pro`)
| Kürzel | Drucker | Stärken |
|---|---|---|
| `kobrax` | Anycubic Kobra X (offen, 4 Farben im Kopf, ACE Gen 2) | PLA/PETG/TPU bunt, günstig |
| `c5pro` | Flashforge Creator 5 Pro (geschlossen, 4 Köpfe, Kammer 65 °C) | ABS/ASA/CF, Mischmaterial, kein Spülabfall |

Tom arbeitet nur noch mit dem Creator 5 Pro: ohne Angabe **immer `c5pro`**, nicht nachfragen. `kobrax` nur, wenn Tom ihn ausdrücklich nennt.
Alte `_kobrax`-Aufträge laufen nicht auf dem Creator 5 Pro – bei Bedarf aus dem Modell neu slicen.

## Ablauf
1. `bash werkzeug/setup.sh` (einmal pro Sitzung, ~2 Min.)
2. Modell beschaffen:
   - Technische Teile: OpenSCAD in `modelle/<name>.scad` (Maße als Variablen oben, Kommentare deutsch).
     Mehrfarbig = **eine .scad-Datei pro Farbe**, gleiche Koordinaten (siehe `test_wuerfel`/`test_buchstabe`).
   - Fertige Modelle (Figuren usw.): Tom schickt STL/3MF oder Link (Printables/Thingiverse) → in `modelle/`.
3. Druckbarkeit prüfen: liegt flach auf, Überhänge < 45° oder Stützen, Wandstärke ≥ 1,2 mm, passt in 256 mm.
4. Slicen:
   ```
   python3 werkzeug/druck.py --drucker c5pro --name <name> \
     --teil modelle/a.scad:PLA:1 --teil modelle/b.scad:PLA:2 --farben "schwarz,rot" \
     --zusammen --schicht 0.20 --infill 15 [--waende 3] [--stuetzen auto|baum] [--brim an|aus] [--duese 0.25|0.6|0.8] [--duesen 0.4,0.25,0.4,0.4] [--rau fein|mittel|grob]
   ```
   - `Datei:Material:Slot` – Slot 1–4 = Spule (Kobra) bzw. Kopf (Creator). Materialien: siehe `drucker/*.json`.
   - `--zusammen` = mehrere Dateien bilden EIN mehrfarbiges Teil. Ohne = getrennte Teile, werden verteilt.
   - Schichten: Creator 0.12/0.20/0.24 (0,4-mm-Düse), Kobra 0.08–0.28.
   - `--duese` (nur c5pro, gilt für ALLE Köpfe): 0.25 → Schicht 0.08/0.10/0.12/0.14 · 0.6 → 0.18/0.30/0.42 · 0.8 → 0.32/0.4/0.48
     (Profile in `drucker/c5pro.json → duesen`).
   - `--duesen 0.4,0.25` (seit 15.11.2026) = Düse **je Kopf** gemischt: Schichthöhen und Prozessprofil der kleinsten Düse, Linienbreiten als Prozent der
     jeweiligen Düse, Brückenlinie = kleinste Düse. Bericht nennt die Düse je Kopf. Nur mit Orca-CLI geprüft (Breiten je Kopf in der .gcode), **nicht gedruckt**.
   - `--rau fein|mittel|grob` (seit 15.11.2026) = raue Oberfläche (Fuzzy Skin) an den Seitenwänden: fein 0,1/0,4 mm (Schichtlinien kaschieren), mittel 0,3/0,8
     (Stein, Griff), grob 0,4/1,0 (Stärke/Punktabstand, Tabelle `RAU` in druck.py). Setzt mindestens 3 Wände, Außenwand zuletzt, erste Schicht glatt.
     `--rau-wo kontur|loecher|alle`. **Trägt je Seite bis zur Stärke auf** (gemessen: 0,30 mm bei „mittel“) → nie bei Passteilen, Bohrungen, Gewinden. Nicht gedruckt.
   - Gold = `PLA-SILK` (230 °C, langsamer); mit normalem PLA zusammen meldet der Bericht „gemischt“ – das ist in Ordnung.
5. Ergebnis (auch `auftrag.json`; `auftraege/index.json` wird automatisch neu gebaut → erscheint in der App) liegt in `auftraege/<datum>_<name>_<drucker>/`: `.gcode`, `BERICHT.md`, STL, `slicer.log`.
6. Committen + pushen. An Tom: `.gcode` per SendUserFile + Kurzfassung aus BERICHT.md (Spulen, Zeit, Gramm)
   + **App-Link** `https://tom444555.github.io/druckwerk/#hinzu=<ordner>` (speichert den Auftrag in seiner App; Pages braucht ~1 Min.).

## App (index.html, GitHub Pages)
- Live: https://tom444555.github.io/druckwerk/ – liest `drucker/*.json` und `auftraege/index.json`.
- **Seit 18.11.2026 vier Reiter** (Tom fand sieben nicht intuitiv): **Projekte** (`projekte.js`: Startseite, eine Karte je Projekt, „Als Nächstes drucken“, Suche über alles) ·
  **Neu** (eine Frage „Was willst du drucken?“, Wege als Auswahl, Feinheiten eingeklappt) · **Drucker** (Überblick mit „Meine Spulen“, Einrichten, Wartung, Hilfe, Tagebuch) ·
  **Wissen** (`mehr.js`: Material, Von der Idee zum Modell, Bibliothek & Werkstatt, KI-Weg, Videos, Gerät & Daten). Interne Seiten-Kennungen (`material`, `workflow`, `bibliothek`,
  `kiweg`) gibt es weiter; sie gehören zum Reiter Wissen und bekommen den Knopf „‹ Wissen“. `start.js` gibt es nicht mehr. Prompts aus der App beginnen mit `druckwerk:`.
- **Projekt = mehrere Aufträge mit gleicher `gruppe`** in `auftrag.json` (Felder `gruppe`, `gruppe_titel`, `nr` = Druck-Reihenfolge, `titel` = Name des Teils, `datei` = Dateiname
  ohne Endung). Beim Slicen angeben: `--gruppe schecter370 --gruppe-titel "Schecter 370 mm" --nr 4 --titel Korpus --datei Schecter_370_Korpus`. Fehlen die Angaben, übernimmt
  `druck.py` sie vom Vorgänger (gleicher Ordner oder gleicher `--name` im Lager) – beim Neu-Slicen eines Teils bleiben Projekt und Dateiname also erhalten. Aufträge ohne Gruppe
  sind ein Projekt für sich. **Jedes neue mehrteilige Vorhaben bekommt eine Gruppe und sprechende Dateinamen** (Tom will „Schecter Korpus“ statt „gitarre370_korpus_c5pro“).
- Projektseite: Köpfe und Düse einmal oben, Teile in Reihenfolge mit Haken, **„Alles für den USB-Stick laden“** = ZIP ohne Kompression, im Browser gebaut (`projekte.js → zip`):
  Ordner `<Projekt>/` mit `1_<datei>.gcode`, `2_…` und `LIESMICH.txt` (Köpfe, Reihenfolge, Zeiten). Zweiter Knopf: dieselben Teile als 3MF für Flash Studio am Mac.
  Ob der Creator 5 Pro am Bildschirm Unterordner des Sticks anzeigt, ist **am Gerät unbestätigt** – die Nummern vorn sortieren auch ohne Ordner.
- **Seit 24.11.2026:** alte Einträge vom Gerät (`druckwerk_meine`), die es im Lager nicht mehr gibt, zeigt die App nicht mehr (waren Karten ohne Bild); nur ohne Netz gilt die gemerkte Liste. Das Kalibrier-Set gehört jetzt zum Projekt `drehteller` (Nr. 14–18, Titel „Kalibrieren: …“).
- Alles aus dem Lager erscheint von selbst (kein „Speichern“ per Link mehr nötig); „ausblenden“ merkt sich das Gerät in `druckwerk_weg`, zurückholen unter Projekte ganz unten.
  Der Link `#hinzu=<ordner>[,…]` geht weiter und öffnet das Projekt; neu: `#projekt:<gruppe>`. Alte Adressen `#start`/`#auftraege` führen zu `#projekte`.
- Direkte Verbindung App ↔ Drucker: geprüft 18.11.2026, **nicht zuverlässig möglich** (Webseite darf nicht ins Heimnetz, keine offizielle Schnittstelle; Tom will nichts Wackeliges).
  Kabellos nur über Flash Studio Desktop am Mac (3MF), sonst USB.
- **Druckwerk-Brücke (seit 25.11.2026, `werkzeug/bruecke.py`, Versuch – am echten Drucker UNGETESTET):** kleines Programm auf Toms Mac (nur Python-Standardbibliothek, `python3 bruecke.py` → http://localhost:8787),
  spricht die HTTP-Schnittstelle des Creator 5 Pro auf Port 8898 (Doku Parallel-7/flashforge-api-docs: `/detail`, `/gcodeList`, `/uploadGcode` multipart `gcodeFile` mit `printNow "false"`, `/printGcode`, `/control`).
  Im Auftrag am Rechner Knopf „Direkt an den Drucker senden“ = Link zur Brücke mit `?datei=<Pages-Adresse>&name=&titel=` (Adresse änderbar über localStorage `druckwerk_bruecke`; `--netz` macht die Brücke im Heimnetz erreichbar, dann ginge auch das iPad).
  Brücke holt die .gcode nur von Toms Pages/GitHub, lädt hoch OHNE zu starten; Start ist ein eigener Knopf mit Haken „Platte leer, Köpfe bestückt“. Bei reiner .gcode druckt Filament n fest aus Kopf n (keine Farb-Zuordnung wie beim Senden aus Flash Studio).
  POST nur von der eigenen Seite (Origin = Host). **Seriennummer und Check Code liegen nur in `~/.druckwerk/drucker.json` auf dem Mac – nie ins Lager.** Geprüft nur gegen nachgestellten Drucker (Playwright). Offen: Firmware 2.0.0 (laut Doku API auch ohne „Nur LAN“, unbestätigt),
  ob der Upload ohne `Expect: 100-continue` angenommen wird, Dateien ~100 MB, ob Python 3 auf Toms Mac da ist (sonst fragt macOS nach den Command Line Tools).
  **Für alle Geräte (25.11. nachmittags):** `python3 bruecke.py --netz` → die Brücke nennt im Terminal und auf der Seite ihre Adressen (`http://<mac>.local:8787`, IP); iPad/iPhone öffnen sie in Safari (http-Seite, daher kein Mixed-Content-Problem).
  Die Brücken-Seite hat jetzt selbst „Aus dem Lager“ (liest `auftraege/index.json` von Pages, Suche, Antippen → hochladen → starten; `/api/hochladen {ordner}`), Köpfe des Auftrags, Kamera (MJPEG `http://<drucker>:8080/?action=stream` bzw. `cameraStreamUrl`, Pfad UNBESTÄTIGT)
  und den Link „Diese Brücke in der Druckwerk-App merken“ (`#bruecke=<Adresse>` → localStorage `druckwerk_bruecke`; in der App auch von Hand über `#brSetz`). Ist die Adresse gemerkt, zeigt die App den Sende-Knopf auf jedem Gerät. Private Aufträge kennt die Brücke nicht.
  **Auf GitHub gefunden (25.11., nicht eingebaut, nicht ausprobiert):** `Parallel-7/FlashForgeWebUI` (fertige Web-Oberfläche für Mac/Raspberry Pi/Docker, Creator 5 „neu“, vom Autor der API-Doku; jetzt auf GitLab) – Alternative fürs reine Überwachen/Steuern, falls ein Dauer-Rechner da ist;
  `varavut/FlashforgeCreator5WebUI` (kleines Python-Dashboard, gleiche Bauart wie unsere Brücke); `GhsVilela/FF-3MF-Converter` (wandelt Orca/Bambu-3MF in Flash-Studio-Projekte für den Creator 5 – **bei Gelegenheit mit `fs_3mf.py` vergleichen**); `ben0551/orca-flashforge-c5` (Senden aus OrcaSlicer);
  `ghzserg/zmod`, OpenCreator (fremde Firmware – nicht ohne Toms ausdrücklichen Wunsch). Immer-an-Lösung: dieselbe `bruecke.py` läuft auch auf einem Raspberry Pi. Von unterwegs geht nichts (bewusst: Platte muss ohnehin leer sein).
- **Mac ↔ Flash Studio (seit 18.11.2026):** Am Rechner (nicht iPhone/iPad) zeigt die Projektseite „Direkt in Flash Studio öffnen“ und das Teil den Knopf „In Flash Studio öffnen“:
  Link `orcaslicer://open?file=<Adresse der .3mf auf Pages, URL-kodiert>` (`projekte.js → studioLink`). Das Schema steht in der Info.plist des öffentlichen Flash-Studio-Quelltexts
  (FlashForge/Orca-Flashforge: `orcaslicer`, `orcasliceropen`, `bambustudioopen`); Flash Studio braucht einen Download-Ordner in den Einstellungen. **Auf Toms Mac ungetestet**
  (auch ob die aktuelle Fassung das Schema noch so registriert); Rückweg ZIP/3MF bleibt. Nur Richtung druckwerk → Flash Studio, kein Status zurück.
- **Rückweg Mac → Druckwerk (seit 18.11.2026, `zurueck.js`):** Tom ändert ein Teil selbst in Flash Studio und legt es zurück. (1) Im Teil „Geänderte Fassung hochladen“
  (.gcode und/oder .3mf + Notiz, jeder Browser). (2) In Chrome/Edge am Rechner „Flash-Studio-Ordner verbinden“ (Projektseite): beim Zurückkommen in die App sucht Druckwerk dort
  nach .gcode/.3mf, deren Name mit dem `datei`-Namen eines Teils beginnt, und fragt, ob es sie hochladen soll (Safari kann das nicht). Ablage wie beim Slicen:
  `eingang/<id>/neu.gcode|neu.3mf` + `auftrag.json {art:"zurueck", ordner, notiz}` → Action → `eingang.py → zurueck()` ersetzt die Dateien im Auftrag (Namen bleiben), liest Zeit/Gramm
  aus der .gcode, schreibt `geaendert {datum, notiz, von, gcode, projekt, id, hinweis}` in `auftrag.json` und einen Abschnitt in BERICHT.md. STL/Vorschau bleiben der alte Stand.
  **Vor jedem Neu-Slicen eines Teils `geaendert` in `auftrag.json` ansehen** – `druck.py` warnt dann laut; Toms Änderung (Notiz) in die neuen Einstellungen übernehmen und ihm
  sagen, dass seine Fassung ersetzt wird. Mit echtem Flash Studio, echtem GitHub und am Mac **ungetestet** (nur mit nachgestellter Schnittstelle geprüft).
- Anleitung für Tom zum ganzen Mac-Weg steht in der App: Wissen → Hilfe → „Anleitung: Mac und Flash Studio“ (`zurueck.js → anleitung`); bei Änderungen am Ablauf dort mitziehen. Wissen → Modelle verlinkt Printables.com („STL-Modelle“).
- Jede Ansicht hat eine Adresse (`#projekte`, `#projekt:<gruppe>`, `#auftrag:<ordner>`, `#werkstatt:…`, `#kiweg:<schritt>`); Zurück/Vor funktionieren.
- **Sicherung** (`sicherung.js`): alle `druckwerk_*`-Schlüssel + IndexedDB (eigene Modelle, Tagebuch-Fotos) als eine Datei; `druckwerk_gesichert` = Datum.
- **Offline/PWA**: `manifest.webmanifest`, `symbol-*.png`, `sw.js` (immer zuerst Netz, Zwischenspeicher nur ohne Netz; .gcode/STL nie).
  **Bei jeder Änderung an App-Dateien `CACHE` in `sw.js` hochzählen** (Stand `druckwerk-v33`) und neue Dateien dort eintragen.
- „Aus dem Lager hinzufügen“ heißt in der App jetzt „Weitere Aufträge von Claude“. Überall „Kopf 1–4“, nie „Spule“; Werkstatt-Slicen sendet `c5pro`.
- Aufträge sind wie die Ideen im Looper **pro Gerät gespeichert** (localStorage `druckwerk_meine`): neue Besucher
  sehen eine leere Liste. Tom speichert einen Auftrag über den Link `https://tom444555.github.io/druckwerk/#hinzu=<ordner>`
  (mehrere mit Komma) oder über „Aus dem Lager hinzufügen“. „Auftrag löschen“ entfernt ihn nur aus seiner Liste.
  Dateien endgültig aus dem Repo löschen (nur auf Wunsch): `git rm -r auftraege/<ordner>` + `druck.index_neu(Path('auftraege'))`.
- **Modell-Quellen (geprüft 15.11.2026, Liste in `wissen/workflow.json` → „Modelle finden …“):** Von der Cloud-Sitzung aus NICHT abrufbar (weder Shell noch WebFetch):
  Printables, Thingiverse, MakerWorld, Cults3D, MyMiniFactory, GrabCAD, Yeggi, TraceParts → Tom lädt am iPad und hängt STL/3MF/STEP an (Link nur für `--quelle`).
  Direkt nutzbar: GitHub per `git clone` (BOSL2, NopSCADlib, gridfinity-rebuilt-openscad), Hugging Face (Objaverse), Poly-Haven-API (CC0), Thangs-Suche
  (`/api/search/v5/search-by-text?searchTerm=…`, nur suchen), Sketchfab-Suche (`api.sketchfab.com/v3/search?downloadable=true`, Download braucht Toms Token), NIH 3D.
- **Privates Modell-Lager `Tom444555/druckwerk-modelle` (seit 18.11.2026):** fremde Modelle mit unbekannter/unfreier Lizenz (gekauft, GrabCAD, Shops) kommen dorthin
  (Ordner je Projekt, `projekt.json`, `katalog.py` → `index.json` + Vorschau; Regeln in dessen CLAUDE.md). Slicen mit den Werkzeugen hier, Auftragsordner aber **dort**
  unter `<projekt>/auftraege/` ablegen, nie hier. Die App zeigt es in der Bibliothek unter „Private Modelle“ (`privat.js`: GitHub-API mit Toms Schlüssel `druckwerk_token`,
  der Zugriff auf beide Lager braucht; Knopf „Werkstatt“ lädt ein Teil bis 30 MB in „Meine Modelle“, „Mit Claude drucken“ öffnet Claude). Mit nachgestellter API geprüft, am iPad offen.
- **Lizenz fremder Modelle:** Das Repo ist öffentlich. Modelle mit „Standard Digital File License“, ND-Lizenz oder Kaufmodelle NICHT einchecken (weder STL noch .gcode/3MF):
  slicen, .gcode nur per SendUserFile schicken, Auftragsordner nicht committen. CC0/CC-BY/CC-BY-SA dürfen ins Repo, Urheber + Lizenz in BERICHT.md nennen.
- **Links aus der App zu Claude** (seit 15.11.2026): `https://claude.ai/code/new?repo=Tom444555%2Fdruckwerk&q=<Text>` – die Claude-App am iPhone/iPad reagiert laut
  Hilfeseite nur auf `claude.ai/code…` (neue Sitzung mit Lager, Text vorausgefüllt); `claude.ai/new?q=` tat dort nichts. Beim Antippen wird der Text zusätzlich kopiert
  (Sammel-Handler in index.html). Neue Claude-Links immer in dieser Form bauen; Preissuche ohne `repo`. Am echten Gerät von Tom noch zu bestätigen.
- Original-Modell verlinken: `--quelle <URL>` (MakerWorld, Printables …) → Knopf „Original auf … öffnen“ im Auftrag.
- Nach Änderung an index.html: lokal mit Playwright (390×844) prüfen, dann pushen.

## Meine Köpfe und Lager-Ordnung (seit 23.11.2026)
- **Toms Köpfe, Stand 28.11.2026 (von ihm genannt): Kopf 1 grau · Kopf 2 bordeaux · Kopf 3 schwarz · Kopf 4 weiß – überall PLA, alle mit 0,25-mm-Düse.** Neue Aufträge ohne andere Ansage so belegen
  (Schwarz ist PLA, nicht mehr PETG). Die Belegung ändert sich mit jedem Spulenwechsel – bei mehrfarbigen Aufträgen kurz fragen, wenn der Stand älter als ein paar Tage ist, und hier nachtragen.
  In die App kommt sie über einen Link, den Tom antippt: `https://tom444555.github.io/druckwerk/#koepfe=1:PLA:grau,2:PLA:bordeaux,3:PLA:schwarz,4:PLA:weiss` (fragt nach, schreibt „Mein Lager“ auf dem Gerät; `index.html → kpMerk`).
- **Meine Köpfe = eine Wahrheit:** Spulen mit Kopf-Zuordnung aus Wissen → Material → Mein Lager (`druckwerk_spulen`; Kopf-Zeile antippen → Spule wählen, `wissen.js → kopfBlatt`).
  `koepfe.js`: Ampel im Teil (`#kAmpel`) und im Projekt (`#pAmpel`) – passt / anderes Material / andere Farbe / Kopf leer; Blatt „Köpfe für diesen Druck“ (je Druckfarbe Kopf + Material wählbar,
  Vorschlag: Farbe dorthin, wo sie bei Tom sitzt; zwei Farben auf einem Kopf gesperrt; Misch-Hinweise PLA+PETG, TPU, ABS/ASA). Werkstatt → Slicen belegt „Material je Kopf“ daraus vor.
- **„An meine Köpfe anpassen“ ohne Chat:** App legt `eingang/<id>/auftrag.json {art:"anpassen", ordner, koepfe:[{von, kopf, material, farbe}]}` bzw. `{liste:[…]}` fürs ganze Projekt ab
  (`werkstatt.js → auftragSenden`) → `eingang.py → anpassen()` → **`druck.py --wie <ordner>`**: übernimmt ALLE Prozess-Einstellungen aus `Metadata/project_settings.config` der Projekt-3MF
  (Zusätze, `--schoen`, Detailwerte), nur Material/Kopf/Farbe neu; Ordner und Dateinamen bleiben, `angepasst {datum, id, koepfe, vorher}` in auftrag.json, Abschnitt im BERICHT.md.
  Gegenprobe 23.11.: sechs Aufträge unverändert neu gerechnet → Zeit und Gramm identisch; Schecter 160 mit Kopftausch + PETG läuft. Nicht anpassbar: bemalte Modelle, gemischte Düsen, private Aufträge (→ Chat).
  Farbe ändert das Anpassen nicht (nur Hinweis „Spule wechseln“). Neu gerechnete Dateien lädt die App mit `?v=<id>` (kein alter Stand aus dem Zwischenspeicher). **Mit echtem GitHub/Action ungetestet** (nachgestellt geprüft).
- **`druck.py`: PLA + PETG gemischt → Bett automatisch 65 °C** (ohne `--bett`); `"zusammen"` steht jetzt in auftrag.json. Auch hier im Chat gilt: Material tauschen = `--wie <ordner>` nehmen statt den Aufruf zu rekonstruieren. Seit 23.11.: `--wie` übernimmt auch Düse (`duese_mm`) und Schicht aus `auftrag.json`; `--extra` überschreibt danach (Reihenfolge: Profil → `--wie` → `--extra`).
- **Lager-Ordnung:** Karteikarte je Projekt in **`lager/karten.json`** (Schlüssel = `gruppe`, sonst `name`): `bereich` (musik | foto | werkstatt | deko | drucker | sonstiges), `stand` (idee | gerechnet | gedruckt | bewaehrt),
  `herkunft`, `schlagworte`, `archiv`, `modell` (Pfade der Quell-Skripte). **Bei jedem neuen Projekt `--bereich … --schlagworte "a,b"` beim Slicen angeben** (legt die Karte an) und `modell` von Hand ergänzen.
  `python3 werkzeug/katalog.py [--privat ../druckwerk-modelle]` → **`lager/KATALOG.md`** (Übersicht Bereich → Projekt → Teile → Modell-Quellen; meldet Projekte ohne Karte) – zuerst dort nachsehen, statt Ordner zu durchsuchen.
- App (`ordnung.js`): Projekte und Bibliothek haben Bereichs-Knöpfe (ein Filter für beide), Suche findet Schlagworte, Archiv ist ausgeblendet („Archiv zeigen“), Projekt → „Einordnen“ ändert die Karte
  (sofort auf dem Gerät `druckwerk_karten`, mit GitHub-Zugang auch zurück in `lager/karten.json`; neuere Änderung gewinnt über `t`). Private Modelle: `bereich`/`schlagworte` in `projekt.json`,
  `katalog.py` dort listet jetzt auch `auftraege` → in der App „Fertige Druckdateien“ mit Laden-Knopf (über die GitHub-API, bleibt privat). Dateien wurden nicht verschoben.

## Bibliothek & Werkstatt (werkstatt.js, seit 11.11.2026)
- Tab **Bibliothek**: alle Modelle aus `auftraege/index.json` (je Name einmal) + „Meine Modelle“ (IndexedDB `druckwerk/modelle`
  auf dem Gerät; Import STL/3MF/OBJ). Tippen öffnet die **Werkstatt** (`werkstatt:l:<ordner>` bzw. `werkstatt:e:<id>`).
- Werkstatt: skalieren (% oder mm, proportional/frei), drehen (X/Y/Z ±15/±90°), auf angetippte Fläche legen, spiegeln,
  4 Spulenfarben, Teil → Spule, Teile aus-/entfernen, Rückgängig. Alle Änderungen werden direkt in die Geometrie gerechnet
  und das Modell danach mittig auf die Platte gesetzt.
- Export: 3MF (Teile als eine Baugruppe, Spule je Teil in `Metadata/model_settings.config` – in OrcaSlicer 2.5 getestet,
  slict mehrfarbig), STL gesamt, STL einzeln (ZIP), OBJ+MTL (ZIP), GLB.
- **Auftrag aus der Werkstatt** („An Claude zum Slicen schicken“): Prompt nennt Lager-Ordner, Änderungsliste und eine
  3×4-Matrix (Zeilen mit ` | ` getrennt). Diese Matrix mit trimesh auf **alle** Original-STL des Ordners anwenden
  (`mesh.apply_transform`, 4. Zeile 0 0 0 1; bei negativer Determinante dreht trimesh die Flächen selbst), dann normal slicen.
  Bei eigenen Modellen hängt Tom die exportierte 3MF an.
- **Slicen aus der App (Stufe 2, seit 11.11.2026):** Werkstatt → „Slicen“ → Einstellungen (Voreinstellung, Schicht, Wände,
  Füllung/Muster, Deck-/Bodenschichten, Stützen, Brim, Oberfläche glatt/rau (`rau`), Naht, Bügeln, Material je Spule) → App legt per GitHub-API
  `eingang/<id>/auftrag.json` ab (Lager-Modelle: nur Pfade + Matrix; eigene: STL-Teile dazu). Workflow
  `.github/workflows/slicen.yml` startet `werkzeug/eingang.py` → `druck.py` → Ergebnis in `auftraege/`, Rückmeldung in
  `status/<id>.json`, App übernimmt den Auftrag automatisch (~1–3 Min.). Token (Fine-grained, Contents RW) liegt nur
  im Gerät (localStorage `druckwerk_token`). Erlaubte Extra-Schlüssel stehen in `EXTRA_OK` (eingang.py) – dort erweitern.
- **Seit 24.11.2026 im Slicen-Blatt der Werkstatt:** „Düse“ (0,4 Serie / 0,25 fein → Schichten 0,08–0,14, schaltet „Maximale Details“ ein), Haken „Maximale Details“ (`detail` → `druck.py --detail`,
  ersetzt „Schön“) und unter Stützen „Kontaktschicht aus anderem Material“ (Kopf 1–4; liegt dort kein Teil, erscheint der Kopf als „nur Stützen“ bei „Material je Kopf“).
  Auftrag: `duese`, `detail`, `stuetz_kopf`, `stuetz_material` → `eingang.py` → `--duese`, `--detail`, `--stuetz-kopf`, neu **`--stuetz-material <MAT>`** (belegt einen sonst leeren Kopf; PVA/BVOH/HIPS → auch `--stuetz-koerper`).
  Probe über `eingang.py` (Brücken-Teil, 0,25/0,08, PETG-Kontakt Kopf 2): in der .gcode Düse 0,25, Arachne, `support_interface_filament = 2`, PLA 225 / PETG 235, Bett 65. Mit echter Action und am Gerät ungetestet.
- Schichtvorschau: `schichten.js` (Knopf „Schichten ansehen“ im Auftrag) liest die .gcode und zeichnet jede Schicht.
- **Bemalte 3MF in der Werkstatt (seit 15.11.2026):** Beim Import erkennt die App `paint_color` und hebt das Original auf (`bemalt: {daten, matrix}` am eigenen Modell,
  höchstens 25 MB). Slicen schickt `eingang/<id>/bemalt.3mf` + `bemalt`/`matrix`/`materialien` in `auftrag.json`; `eingang.py` ruft `druck.py --bemalt … --matrix …`.
  Die 3D-Ansicht zeigt die Bemalung nicht; Teile entfernen wirkt bei bemalten Modellen nicht.
- Noch offen: 1b schneiden/zusammensetzen/Text · Senden per WLAN · Abgleich iPhone↔iPad über das Repo · Auftrag ohne Chat. Erledigt: Filamentlager mit Check und Kosten, Druck-Tagebuch, geführter Auftrag (14.11.), Start/Sicherung/Offline/KI-Weg (15.11.).

## Wissen: Material, Drucker, Workflow (wissen.js + wissen/*.json, seit 14.11.2026)
- **Inhalte stehen in `wissen/*.json`, nicht im Code.** Neue Erkenntnisse (Toms Druckergebnisse, neue Preise, Firmware) dort eintragen und
  `stand` + `quellen` mitziehen. `herkunft` je Wert: „Profil“ (Hersteller-Profil Orca 2.5), „Wiki“ (Flashforge), „Richtwert“. Nichts erfinden –
  was am echten Gerät bestätigt ist, im Text auch so nennen.
  - `filamente.json` – Materialkarten (Düse/Bett/Kammer/Lüfter/Trocknen/Durchfluss, Wofür, Achtung), Finder-Schlagworte `eignung`,
    Mischregeln, Grundausstattung. Feld `druckwerk` = Schlüssel aus `drucker/c5pro.json` (leer = Profil fehlt noch).
    Dazu `vergleich` (Segment „Vergleich“: 15 Materialien, Hitze in °C und Punkte 1–5 für Festigkeit, Steifigkeit, Zähigkeit, Weichheit, Wetter, Einfachheit –
    alles Richtwerte, nach Toms Drucken nachschärfen), `stabil` (Kurzantwort „Was ist am stabilsten?“) und `shops` (Filamentor, Flashforge).
  - `zubehoer.json` – Gruppen mit Teilen (`prio` Muss/Sinnvoll/Später, Preis, Shop-Link).
  - `c5pro.json` – Steckbrief, Stärken/Grenzen, Programme, Einrichtungs-Liste, Vor-dem-Druck, Wartung (`tage` = Erinnerungs-Abstand),
    Probleme+Lösungen (durchsuchbar), Firmware-Verlauf, USB-Schritte.
  - `workflow.json` – fünf Wege Idee → Modell (mit `vorlage` für den Tab Neu), Werkzeugliste, Ausbau-Vorschläge (`status` pflegen!).
- Tab **Material**: Filamente (Finder + Karten), Vergleich (sortierbare Rangliste), **Mein Lager** (Spulen im Gerät, `druckwerk_spulen`; Kopf-Zuordnung), Zubehör (Haken `druckwerk_habe`).
  Im Auftrag: „Verbrauch vom Filamentlager abbuchen“ (`wissen.abbuchen`, merkt sich `druckwerk_gebucht`).
  Im Filament-Blatt öffnet „Günstigsten Preis suchen“ Claude mit `filament-preise: <Material> …` (Skill `filament-preise`, sucht Preise nur auf Abruf; keine Preise im Lager speichern).
- Tab **Drucker**: Überblick, Einrichten (`druckwerk_c5_ein`), Wartung (`druckwerk_c5_wartung`), Hilfe, Tagebuch (`druckwerk_tagebuch`, Fotos in IndexedDB `druckwerk_fotos`). Die frühere USB-Seite steht jetzt hier.
- **„Von der Idee zum Modell“** (Reiter Workflow; auch über Neu und Start erreichbar): Weg (Knopf „Auftrag so beginnen“ öffnet den geführten Auftrag), Werkzeuge, Vorschläge (Auswahl `druckwerk_wunsch` → Prompt).
  Kommt ein Prompt „Bitte diese Vorschläge aus der App umsetzen“, sind die Titel aus `workflow.json → vorschlaege` gemeint.
- Prüfskript-Muster: Playwright 390×844, alle vier Reiter und Unterseiten durchklicken, ZIP eines Projekts laden und prüfen, `scrollWidth` muss 390 bleiben.

## Qualität: technische Teile wie konstruiert (seit 15.11.2026) – Regeln in `werkzeug/QUALITAET.md`
- **Pflicht-Schleife vor jedem Slicen eines neuen Teils:** bauen → `python3 werkzeug/pruefen.py <stl…>` (0 Fehler) → `python3 werkzeug/ansichten.py <stl…> --aus bild.png`
  und das Bild SELBST ansehen → korrigieren (höchstens 3 Runden) → Bild an Tom → erst dann slicen. Kurz: `cad.py <skript> --name n --pruefen --bild /tmp/n.png`.
- `werkzeug/profi.py` (build123d): Tabellen (Wand = Vielfache 0,45 mm, Spiel-Klassen, Lochaufmaß) und Helfer – sichere Rundung/Fase, Fase unten gegen Elefantenfuß,
  Senk-/Schraubloch (waagrecht automatisch Tropfenform), Einschmelzmutter, Rippe, Rändelung, Waben, Schrift mit Mindeststrich, Schnapphaken, Schwalbenschwanz,
  Scharnier, Gewinde/Normteile (`bd_warehouse`), Zahnräder (`py_gearworks`), 45°-Druckgewinde, Teilung mit Passstiften. Selbsttest: `python3 werkzeug/profi.py`.
- Vorzeige-Teile als Muster: `modelle/profi/gitarrenhalter.py` (PETG + TPU-Auflage), `zahnradpaar.py`, `dose.py` (Gewindedeckel, Waben, Gold-Einlage).
- `cad.py` neu: `--arg k=v`, `--pruefen`, `--bild`, `--ohne-step`; vernetzt vor dem Export frisch (vorher teils offene STL).
- Wann was: einfache Klötze/Halter → OpenSCAD + Baukasten; alles mit Rundungen, Gewinden, Zahnrädern, STEP → build123d + profi.py.
- Alle Spiele/Passungen sind gerechnet, nicht gedruckt – nach Toms Kalibrier-Teil 4 in `profi.py` und `baukasten.scad` nachstellen.

## Qualität: Figuren und freie Formen über KI (seit 15.11.2026) – Recherche in `wissen/recherche_modellqualitaet.md`
- Kein KI-Generator ist maßhaltig; technische Teile immer per CAD. Für Figuren/Deko liefern Rodin, Tripo, Meshy, Hunyuan, TRELLIS.2 das heutige Maximum.
- **Weg in der App** (`kiweg.js`, Adresse `#kiweg:1…6`, Speicher `druckwerk_kiweg`): 1 Bild-Idee (erzeugt den Text für eine Bild-KI – Claude erzeugt keine Bilder) →
  2 Bild extern → 3 Prüfliste Bild → 4 Umwandeln: `ki.js` „Aus Foto erzeugen (KI)“ über GitHub Action `generieren.yml` + `werkzeug/generieren.py`
  (fal.ai mit Repo-Secret `FAL_KEY`: TRELLIS.2 0,25–0,35 $, Rodin 0,40 $, Hunyuan 0,375 $; gratis-experimentell Hugging Face mit `HF_TOKEN`) ODER extern
  (MakerWorld MakerLab) + STL-Import → 5 Prüfliste Modell in Grau → 6 Werkstatt/Auftrag. Ergebnis der Action: `ki/<id>/` (GLB, STL, info.json), Status `status/<id>.json`.
  **Der echte Dienst-Aufruf ist ungetestet (kein Schlüssel)** – beim ersten Lauf von Tom Status/Log ansehen. Fotos liegen im (öffentlichen) Repo.
- **Gratis hier im Chat (seit 15.11.2026):** `python3 werkzeug/ki_lokal.py bild.png --name n --ziel-mm 120 --aus /tmp/n` – freies Modell TripoSR ohne Grafikkarte
  (Einrichten ~2 Min., dann ~2 Min. je Bild inkl. `ki_rohling.py`), kein Schlüssel, keine Kosten. Qualität grob (Entwurf, einfache kompakte Figuren; dünne Teile fehlen) –
  Tom vorher sagen, Vorschau zeigen. Schickt Tom ein Foto mit „hier umwandeln“/„ki_lokal“, diesen Weg nehmen. TRELLIS.2/Hunyuan/Rodin gehen hier nicht (brauchen GPU).
- **Text zu Bild hier im Chat (seit 15.11.2026):** `python3 werkzeug/bild_ki.py "<Motiv auf Englisch>" --name n --aus /tmp/n [--anzahl 4] [--ansicht einzel|vorne|ansichten] [--farbe grau|vier|frei]`
  – holt Entwürfe von Pollinations (ohne Schlüssel gratis: 768 px, ein Bild alle 45 s, bei Überlast 503 → wartet selbst), hängt die 3D-Regeln an den Text, stellt jedes Bild frei
  (rembg), setzt es mittig auf Weiß (1024 px) und rechnet eine Ampel (ein Objekt? angeschnitten? klein? sperrig?). `uebersicht.png` SELBST ansehen, Tom zeigen, er wählt die Nummer;
  dann `ki_lokal.py bild_<n>_fertig.png …` (gratis, grob) oder fal.ai/MakerLab. Mit `FAL_KEY` bzw. `POLLINATIONS_KEY` in der Umgebung nimmt das Skript bessere Modelle (ungetestet).
  Qualität ohne Schlüssel = Entwurf; das Gratis-Modell hält sich nur teilweise an Farbe und Sockel. **Nur für freie Figuren:** bei technischen oder realen
  Gegenständen (Test 15.11.: Pistole, Karabiner) kommt Unbrauchbares heraus, und die Ampel merkt das nicht → Foto als Vorlage, fertiges Modell oder CAD nehmen. Tom sagt z. B. „druckwerk: Bild-Idee Eule …“. Hintergrund: `wissen/recherche_text_zu_bild.md`.
- Schickt Tom ein KI-Modell (GLB/STL): `werkzeug/ki_rohling.py` (aufrichten, skalieren, schließen, Boden plan, Info) → Bild zeigen → bei Farbe
  `werkzeug/textur_farben.py` (Textur → 4 Köpfe) → slicen. Abschlussbild: `werkzeug/foto.py` (Blender). Details und Grenzen: `werkzeug/KI_MODELLE.md`.
- **Lehren aus Toms Videos** (Auswertungen unter `videos/`, Bastlwastl): Eingabebild = ein Objekt, neutraler Hintergrund, einfarbig grau und matt, leicht schräg von
  oben, kompakt, nichts Schwebendes, wenig Hinterschneidungen, Aufstellung klären; **Zielgröße immer nennen** (15–20 cm statt 5–6 cm bringt Details);
  abstehende Teile getrennt erzeugen und kleben; 3D-Ergebnis in Grau auf Fehler prüfen (Finger, krumme Klingen, erfundene Rückseite); Boden plan schneiden;
  Fehler lieber im Bild als im Netz beheben; jede Umwandlung kostet. Hohle Objekte (Vase, Helm, Maske) gelingen der KI kaum → CAD.
- Foto/Farbverlauf auf Modell (Primed3D + Farbmischung im Slicer, 5 Filamente, 0,08 mm, Tage Druckzeit): für den Creator 5 Pro nur mit 4 Farben denkbar,
  **nicht erprobt und nicht eingebaut**; druckwerk nutzt feste 4-Farben-Zerlegung (`textur_farben.py`, `bild_relief.py`).

## Lehren aus Videos zum Creator 5 Pro (Auswertungen unter `videos/`)
**Ablauf „Video auswerten und aneignen“** (Tom schickt eine Transkript-.txt aus a-Shell, oft nur mit „genau wie beim letzten“; bei einem bloßen Link zuerst den a-Shell-Befehl nennen):
1. Transkript ganz lesen, dann nach Skill `transkript-auswertung` auswerten (A–I, Fundstellen, 📚/❓, neutral, höchstens ein kurzes Zitat, zwei Zeichnungen).
2. Als Seite `videos/<thema>-<kanal>.html` bauen: Kopf/CSS aus einer vorhandenen Seite übernehmen (z. B. `videos/z-naht-bastlwastl.html`), Karte oben in `videos/index.html`,
   Stichwort in `mehr.js` (Zeile „Videos ausgewertet“), `CACHE` in `sw.js` hochzählen, mit Playwright 390×844 prüfen (`scrollWidth` 390, Zeichnungen ansehen).
3. Abgleich: jede prüfbare Aussage gegen Handbuch/Hersteller (OrcaSlicer-Wiki, Bambu-/Flashforge-Wiki) **mit geprüftem Link** und gegen Toms Creator-Profil
   (Werte aus `project_settings` einer vorhandenen .3mf oder dem Kopf einer .gcode lesen). Das Video zeigt meist Bambu Studio auf einem anderen Drucker – Unterschiede nennen.
4. Aneignen, wenn es Sinn hat: als Schalter in `werkzeug/druck.py` (und `eingang.py`/Werkstatt, wenn Tom es selbst wählen soll), an einem kleinen Testteil ohne/mit rechnen,
   in der .gcode nachweisen, Zeit und Gramm vergleichen. Was schon im Profil steckt, nicht doppelt bauen. Unklare Werte (Hörfehler) und Ungeprüftes nicht übernehmen.
5. Festhalten: Abschnitt hier darunter (was eingebaut, was bewusst nicht, Messwerte), Zeile in `UEBERGABE.md`, Abschnitt H der Seite („was das für Druckwerk heißt“).
6. An Tom: Link zur Seite, was das Video sagt, was übernommen, was nicht und warum, und dass nichts gedruckt ist; Vergleichsdruck anbieten.

- **My Engines DE, „Technische Filamente“** (ein Tester, Leihgerät, nichts an Toms Gerät bestätigt): PA12-CF, PC-PBT-CF, ASA-CF mit wenig Verzug bei Bett 120 / Kammer 65 / Düse 320 °C;
  PETG außen + TPU innen hielt von Hand untrennbar (andere Quellen: haften kaum → große Kontaktfläche + Beam Interlocking); Stützen bei Faser-Material kaum lösbar →
  **stützfrei konstruieren** oder Stützmaterial in eigenen Kopf; TPU zieht Fäden; druckdicht erst nach Versiegelung. Steht auch in `wissen/filamente.json` und `wissen/c5pro.json`.

- **Bastlwastl, „PLA PERFEKT drucken … Bambu Studio Einstellungen“** (`videos/pla-einstellungen-bastlwastl.html`, 18.11.2026; X1 Carbon, eigenes Filament des Sprechers): langsame
  Außenwand, drei Wände in Reihenfolge innen-außen-innen (laut OrcaSlicer-Handbuch beste Außenfläche/Maßhaltigkeit; für Überhänge ist innen-außen besser), langsame Überhänge/Brücken.
  Eingebaut als **`druck.py --schoen`** (und Haken „Schön (langsam)“ beim Slicen in der Werkstatt, `schoen` in `eingang.py`): 3 Wände innen-außen-innen, Arachne, ≥ 5 Deck-/Bodenschichten,
  Außenwand ≤ 45, Innenwand ≤ 100, erste Schicht ≤ 30, Überhänge/Brücken ≤ 30 mm/s, `reduce_crossing_wall`, Naht hinten, Schrägnaht. **Für Sichtteile und Deko aus PLA mit 0,4-mm-Düse von selbst
  nehmen** (im Bericht steht es); nicht für Funktionsteile mit Eile, nicht zusammen mit den 0,25-mm-Detailwerten (die sind schon langsamer). Winkel-Testteil: 16:28 statt 12:27 min,
  5,9 statt 5,4 g. Creator-Profil hat schon 210/205 °C und Lüfter aus in Schicht 1 (Außen 200 / Innen 300 / erste Schicht 50 mm/s). **Nicht übernommen:** ohne Füllung als Standard
  (Blitz-Füllung `sparse_infill_pattern=lightning` nur auf Wunsch für hohle Deko), Baumstützen, „nach Objekt“ (Kopfabstand ungeprüft), Lüfter 100 %. Nichts davon gedruckt.

- **Bastlwastl, „Z-Naht komplett unsichtbar … Quick-Tip #27“** (`videos/z-naht-bastlwastl.html`, 18.11.2026): Schrägnaht (Scarf Joint) – Anfang und Ende jeder Runde laufen als Rampe
  ineinander. In Bambu Studio beim Filament, in OrcaSlicer unter Qualität → Naht. Eingebaut als **`druck.py --schraegnaht`** und **Teil von `--schoen`**: `seam_slope_type=external`,
  `seam_slope_start_height=10%`, `seam_slope_min_length=8` (Werte aus dem Video; Orca-Standard 0 / 20 mm), `seam_slope_conditional=1` (nur runde Konturen, Ecken behalten die normale Naht).
  In der .gcode geprüft (`has_scarf_joint_seam = 1`, Z steigt am Nahtanfang); Zylinder Ø 30: +11 s. Nicht übernommen: „Lücke 2“ (in Orca 2.5 kein eigener Wert), Schrägnaht an Löchern
  (Maßhaltigkeit). Bleibt eine Wulst: Rampe Richtung 20 mm verlängern oder `scarf_joint_speed` senken. Nicht gedruckt.

- **Bastlwastl, „Fuzzy Skin im Bambu Studio“** (`videos/fuzzy-skin-bastlwastl.html`): raue Außenwand überdeckt Schichtlinien/Streifen, gibt Stein-Optik und Griff; wirkt nur an
  Seitenwänden (Sichtflächen so legen oder Teil teilen), unten prägt die Plattenstruktur; trägt um die Stärke auf; ≥ 3 Wände, innen vor außen. Eingebaut als `--rau` und
  in der Werkstatt („Oberfläche“). Nicht eingebaut: Flächen gezielt bemalen (`paint_fuzzy_skin`), neuere Muster (Perlin, Voronoi), Muster/Logo als SVG-Relief, Testraster.

- **Bastlwastl, „Diese neue 3D-KI ist unglaublich! AIMIA von MakerWorld im Test“** (`videos/aimia-makerlab-bastlwastl.html`, 18.11.2026): Aimia = KI-Arbeitsplatz im MakerLab
  (Beta mit Warteliste, 2 Versuche gratis, dann Credits; Generatoren laut Berichten Tripo, Meshy, Hi3D, Rodin, Hunyuan). Text → 4–5 Bilder → 3D (~4 Min.) mit 4–18 Farben → Browser-Slicer
  (Boden plan, „Geometric Split“ = Teile entlang der Form trennen mit Steckverbindern, Spiel 0,20) → STL/3MF. Für Tom: Farbanzahl 4, als 3MF schicken (Farbzuordnung in Druckwerk **ungetestet**).
  **Angeeignet als `werkzeug/teilen.py`** (gerade Schnitte, keine KI-Erkennung): `python3 werkzeug/teilen.py modell.stl --aus /tmp/t` teilt, bis jedes Stück ≤ `--bett 250` mm ist;
  oder `--achse x|y|z --bei <mm>|mitte`. Passstifte `--stift druck` (Ø `--stift-d 4`, Spiel `--spiel 0.2` je Seite, Stift-STL dazu) | `filament` (Loch Ø 1,95 für 1,75-mm-Stückchen) | `keine`;
  Tiefe ≤ `--tiefe 6`, höchstens 40 % der dünneren Hälfte; Stiftorte automatisch im eingezogenen Schnitt (Wand `--wand 1.6`), längliche Inseln zwei Stifte. `--lage auto`: Z-Schnitt → Schnittfläche
  nach unten. Test: Les-Paul-Korpus 437 × 331 mm → 4 Stücke, 6 Stifte, alle dicht, Lochvolumen nachgerechnet. Nicht übernommen: organisches Teilen (bräuchte KI-Segmentierung), Scharniere. Nichts gedruckt.

- **Der Druckt Schon Wieder, „Meshy AI … 3D Agent“** (Werbe-Video, Snapmaker U1): Agent fragt erst nach (Form, Farben), zeigt ein Konzeptbild, baut dann 3D – so auch selbst vorgehen.
  Meshy „Multi-Color Print“ liefert eine **bemalte 3MF** (Farbanzahl dort auf ≤ 4 stellen) → `druck.py --bemalt`; mit echter Meshy-Datei **ungetestet**: beim ersten Mal prüfen, ob
  `lese_3mf` die Farbcodierung liest (sonst alles auf Kopf 1) und die Größe stimmt (Meshy-Standard 50 mm → `--groesse <mm>` oder `--skala <Faktor>`; der Bericht nennt die Maße vorher/nachher). Baumstützen sind im Video umgerissen
  → bei `--stuetzen auto` bleiben; Stringing kam von fehlender Kalibrierung → erst Kalibrier-Set. KI bleibt Deko, kein CAD-Ersatz.

## Weitere Werkzeuge (seit 14.11.2026)
- **Technik-Baukasten** `modelle/baukasten/baukasten.scad` (`use <baukasten/baukasten.scad>`): Durchgangs-/Senklöcher M3–M8, Einschmelzmuttern M3–M5,
  Mutterntaschen, Langloch, Schnapphaken, Schwalbenschwanz, Gewinde M6–M12, Kantenrundung/Fase, Wandlasche, Schlüsselloch, Kabel-Clip.
  Globales `spiel=0.2` – nach Toms Passungs-Test (Kalibrier-Teil 4) anpassen. Tabelle: `modelle/baukasten/LIESMICH.md`. Für Funktionsteile zuerst hier nachsehen.
- **CAD-Stufe build123d** `werkzeug/cad.py <modell.py> --name <n>` → `modelle/<n>.stl` (je Farbe) + `.step`; Beispiel `modelle/beispiel_winkel.py`.
  Nehmen, wenn Rundungen/Fasen/STEP gefragt sind; einfache Teile weiter in OpenSCAD.
- **Bild-zu-Farbrelief** `werkzeug/bild_relief.py bild.png --name <n> --breite 180 --rahmen 6 [--nur-bild /tmp/v.png]` → bis zu vier überlappungsfreie STL
  (schwarz/gold/rot/weiß oder `--farben auto`); gibt den passenden druck.py-Aufruf aus. Erst `--nur-bild` zeigen, dann Netze.
- **Kalibrier-Set** `modelle/kalibrier/` (haftung, winkel, versatz_k1–k4, passung, bruecke) – als Aufträge `…_kalibrier_1…5_c5pro` gesliced.
  Was Tom je Teil meldet und wie daraus Werte werden: `modelle/kalibrier/LIESMICH.md`. Bestätigte Werte in `wissen/c5pro.json`, `wissen/filamente.json`
  (Herkunft dann „Gerät“) und hier unter Technik-Notizen eintragen.
- **Druck-Tagebuch** (`tagebuch.js`): Tom schickt „druckwerk: Druckergebnis …“ aus der App (Auftrag, Einstellungen, Note, Mängel, Notiz, Foto im Chat).
  Daraus Einstellungen ableiten, neu slicen und die Erkenntnis in `wissen/*.json` festhalten.
- **Geführter Auftrag**: Fragen je Weg stehen in `wissen/workflow.json → wege[].fragen` (Tab Neu, Umschalter „Geführt“).
- `setup.sh` installiert zusätzlich trimesh/manifold3d/scikit-image, build123d und pymeshlab (ohne pymeshlab entstehen keine `*.app.stl`).

## Organische/feine Modelle (Erfahrung Gitarren-Reihe, 11.–12.11.2026)
- **Erst Bild, dann Druckdatei:** bei Deko/Entwürfen zuerst eine schnelle Vorschau schicken (Sekunden), Tom entscheidet, dann slicen (bis 10 Min.).
  Bei Geschmacksfragen 3–4 Varianten nebeneinander rechnen und die beste nehmen. Toms Fotos = Stilvorlage, kein 1:1-Nachbau fremder Motive.
- **Relief statt OpenSCAD** für Bäume, Blätter, Borke, Leder usw.: Höhenfeld in numpy → wasserdichtes Netz (manifold3d, bei y=0 abschneiden),
  eine Höhenkarte je Farbe, Farben überlappen nie. Vorlage: `werkzeug/baum_relief.py` (`--saat N`, `--nur-bild x.png`). Liegt flach auf dem Bett → keine Überhänge.
- **Fremde Ein-Körper-STL mehrfarbig machen:** `werkzeug/gitarre_farben.py` (Schnitte per Boolean, Splitter mit decompose filtern); lose Teile: `werkzeug/lose_teile.py`.
- **Passung zweier Teile** (z. B. Gitarre im Ständer) immer per Schnittvolumen prüfen (manifold `a ^ b`, soll 0 mm³ sein) – Maße der Gabel stehen in `baum_relief.py` oben.
- **Feine Stege < 0,45 mm:** `--extra wall_generator=arachne --extra min_bead_width=70% --extra min_feature_size=20%`, sonst lässt der Slicer sie weg.
  Stützen: `auto` (Baumstützen gaben Slicer-Fehler). Schicht 0.12 für feine Reliefs.
- **Dateigröße:** GitHub lehnt Dateien > 100 MB ab. Sehr feine Modelle: `--extra resolution=0.06` (G-Code wird ~20 % kleiner), Netze ≤ ~500.000 Dreiecke je Farbe.
  Große erzeugte STL in `modelle/` nicht einchecken (.gitignore), wenn ein Skript sie neu bauen kann. Alte Stände eines Auftrags ersetzen, nicht sammeln.
- **Farben:** Tom mag die Verstärker-Farben schwarz / gold / rot / weiß; Farben nur tauschen = gleiche STL, andere Slots, neu slicen (kein Neubau).
- **Git:** ein zweiter Chat schreibt ins selbe Repo. Reihenfolge: `git add -A && git commit` → `git fetch` → `git rebase origin/main` → **Status prüfen** (Konfliktmarker in
  UEBERGABE.md entfernen, beide Teile behalten) → `druck.index_neu(Path('auftraege'))` → commit → `git push origin HEAD:main`. Nie mitten im Rebase `git add -A`.

## Ideengebung bei freien Entwürfen (seit 20.11.2026) – ausführlich in `wissen/ideengebung.md`
Sagt Tom „mach dir Gedanken“, „hau was raus“ oder nennt nur Rahmen (Düse, Farbe, Menge): **vor dem Bauen `wissen/ideengebung.md` lesen**, danach arbeiten und am Ende nachtragen.
- Vom Rahmen zur Idee: Was kann genau dieses Material / diese Farbe / diese Düse am besten? Toms Geschmack + ein bewährter Baustein aus dem Lager als Kern.
- **Bedeutung über die Form, nicht über das Symbol** (Tom: „kreativ, nicht kitschig“): das Thema wird Teil des Motivs (Wurzeln als gedrehtes Endlos-Tau statt Herz), ein Gedanke kehrt an mehreren Stellen wieder, die Technik erzählt mit (dünn = hell).
- Erst ein starker, begründeter Vorschlag mit Bild, dann Runden mit je einem Satz von Tom; kommt der nächste Wunsch mitten in der Arbeit, abbrechen und zusammen umsetzen.
- Grenzen ehrlich nennen (z. B. Strich 0,6 mm ist das Feinste mit 0,4 mm). Liegen gebliebene Einfälle in den Ideen-Speicher der Datei schreiben und Tom gelegentlich einen davon vorschlagen.

## Stehendes Relief / Lichtbild für die 0,4-mm-Düse (Erfahrung `modelle/lebensbaum_licht.py`, 19.11.2026 – nur gerechnet)
- **Feinste Details mit der Serien-Düse: Relief STEHEND drucken** (Prinzip Lithophanie): jede 0,12-mm-Schicht zeichnet die Tiefe als Kontur, statt Stufen auf der Deckfläche.
  Platte im Grundriss biegen (Radius 130 mm) → dünne Wand wird steif und steht von selbst; Bild beim Bauen spiegeln und 180° drehen, damit es seitenrichtig nach vorn (−Y) zeigt.
- **Stützfrei rechnen:** Dickenfeld von oben nach unten durchgehen, `t[j] = max(t[j], t[j+1] − tan(55°)·RES)` → unter jedem Vorsprung entsteht eine Fase.
- Weiß: Himmel 1,5 mm, dünnste Stellen (Mond, Sterne) 0,85 mm = zwei Bahnen → leuchten mit Licht dahinter; Füllung 100 %, damit dicke Stellen gleichmäßig dunkel bleiben.
- Slicen: `--schicht 0.12 --schoen --infill 100 --stuetzen aus --brim an --extra resolution=0.05` (hält die .gcode unter 100 MB; Netz ~800.000 Dreiecke, STL nicht ins Lager).
- `pruefen.py` meldet bei Reliefs „Details < 0,45“ / „Wand < 0,8“ wegen der Oberflächen-Riefen – bei Reliefs kein Fehler.
- **Flash Studio am Mac (Befund 19.11.):** unsere .3mf bringt die Prozess-Einstellungen dort nicht mit (Stützen waren aus) → Tom die **.gcode** geben, bis das behoben ist.
  **Ursache (20.11., Quelltext FlashForge/Orca-Flashforge `Plater.cpp`):** Liegt schon etwas auf der Platte, fragt Flash Studio „Als Projekt öffnen / Nur Geometrie importieren“ und hat **Geometrie vorausgewählt**; „Importieren“ (⌘I) und jede weitere 3MF beim Öffnen mehrerer Dateien laden ebenfalls nur die Form. Unsere 3MF selbst wird als Bambu/Orca-Projekt erkannt (Application `BambuStudio-…`), Version 02.08 > 01.10 gibt höchstens einen Hinweis, Einstellungen werden trotzdem geladen. Lösung: „Als Projekt öffnen“ bzw. ⌘O auf leerer Platte, einmalig Einstellungen → Ladeverhalten → „Alles laden“. Hinweis steht in der App (Projektseite, Anleitungen). **Bestätigt an Toms Mac 24.11.2026 (Schecter 190):** als Geometrie geladen → Warnung „floating regions“, keine Stützen, 5 h 43 / 26,0 g; als Projekt geladen → Stützen da, 33,69 g (aufs Hundertstel wie unsere .gcode), 236 Kopfwechsel (wir 238), 7 h 25 (wir 7 h 17). Erkennungszeichen für Tom: Spalte „Support“ in der Filament-Tabelle und gleiche Gramm wie im Bericht. **„Print plate“ bleibt mit unserem Projekt grau** (Drucker verbunden, idle): das Druckerprofil aus unserer 3MF nimmt Flash Studio nicht zum Senden. Mit Flash-Studio-eigenem Profil (Geometrie + Stützen von Hand an) wurde der Knopf blau: 28,18 g, 6 h 10, 233 Wechsel – Modell-Gramm fast gleich (17,93 statt 18,04), aber kleinerer Wischturm (8,1 statt 13,6 g) und Hersteller-Geschwindigkeiten statt `--detail`. Offen: 3MF so schreiben, dass Flash Studio sie direkt senden lässt (Drucker-/Prozessnamen wie in Flash Studio). Namen in Toms Flash Studio (Foto 24.11.): Drucker „Flashforge Creator 5 Pro“ + Düse 0.25 (Hardened), Prozess „0.08mm Standard @FF C5 0.25 nozzle“ (Schicht 0,08 / erste 0,10, Naht Aligned, Precise wall an, eine Wand oben an), Filamente „Flashforge PLA …“; „Wall generator“ sieht man dort nur mit eingeschaltetem Experten-Schalter neben Global/Objects.
  **Eigentliche Ursache gefunden und behoben (24.11.2026 abends, `werkzeug/fs_3mf.py`, von `druck.py` nach jedem Slicen aufgerufen):** Heißt ein Profil in der 3MF wie ein System-Profil
  („0.08mm Standard @FF C5 0.25 nozzle“), setzt Flash Studio beim Öffnen ALLE Werte auf das System-Profil zurück, außer denen in `different_settings_to_system`
  (`PresetCollection::load_external_preset` → `update_non_diff_values_to_base_config`). Die Orca-CLI schreibt das Feld leer → Stützen und Detailwerte gingen verloren, auch bei „Als Projekt öffnen“.
  `fs_3mf.herrichten()` trägt dort alle Prozess- und Filament-Schlüssel ein (Listen in `drucker/fs_schluessel.json`, aus Flash Studios `Preset.cpp`), lässt das Druckerprofil bei Flash Studio
  und nimmt die eingebettete .gcode samt Verweisen heraus (öffnet als normales Projekt in „Prepare“, 3MF wird kleiner). Geprüft: hergerichtete Halter-3MF schneidet in der Orca-CLI wieder auf
  16,85 / 7,55 g; `--wie` liest sie weiter. **In Flash Studio selbst noch unbestätigt** (Toms Test offen). Umgestellt: Schecter 190, Strat 190/240, Halter 190, beide Anhänger; übrige Aufträge mit
  `python3 werkzeug/fs_3mf.py auftraege/<ordner>` nachziehen, sobald Tom es bestätigt hat. **Achtung Strat:** die Pause für den Spulenwechsel (Creme → Schwarz) steckt nur in unserer .gcode –
  beim Neu-Schneiden in Flash Studio fehlt sie → Strat per .gcode drucken oder die Pause dort am Schichtregler bei 8,26 mm (240er: 10,34 mm) von Hand setzen.

## Mehrfarbige Teile aus 2D-Umrissen (Erfahrung `modelle/gitarre_rotschwarz.py`, 15.11.2026)
- Eigener Entwurf statt Nachbau: Umrisse als Splines → manifold3d `CrossSection` → Prismen je Farbe; `python3 modelle/gitarre_rotschwarz.py --ziel /tmp/x --bild /tmp/x/v.png`.
- **Farben in 2D aufteilen, nie 3D-Körper voneinander abziehen** (gab tausende Splitter). Zwischen Farben 0,02 mm Fuge; Polygone mit `FillRule.NonZero`.
- Vor dem Extrudieren `simplify(0.004)` (fast gerade Spline-Punkte machen das Netz undicht); Inseln entfernen; spitze Keile an Ring-Enden abschneiden.
- Gleiche Farbe übereinander: obere Lage 0,012 mm einziehen und 0,03 mm überlappen, sonst deckungsgleiche Wände. Ringe 0,04 mm einziehen.
- Markennamen/Logos weglassen. Feine Stege < 0,45 mm → Arachne-Zusätze (siehe unten). Nur gerechnet, nicht gedruckt.

## Fünfte Farbe und zweiteilige Modelle (Erfahrung `modelle/gitarre_rundum.py`, 16.11.2026 – nur gerechnet)
- **Fünfte Farbe:** zwei Farben, die in getrennten Höhen liegen, beim Slicen auf denselben Kopf legen (`--teil a.stl:PLA:4 --teil b.stl:PLA:4`), danach
  `python3 werkzeug/spulenwechsel.py <gcode> --kopf 4` → setzt `M25` in die Höhen-Lücke; im BERICHT.md Höhe und Farben nennen. Am Gerät unerprobt.
- **Maximale Details mit 0,25-mm-Düse:** `--duese 0.25 --schicht 0.08` + `--extra` `wall_generator=arachne`, `min_bead_width=70%`, `min_feature_size=20%`,
  `resolution=0.008`, `only_one_wall_top=1`, `outer_wall_speed=30`, `small_perimeter_speed=20`, `top_surface_speed=40`, `top_shell_layers=8`,
  `support_on_build_plate_only=1` (sonst Stützen an feinen Teilen auf der Oberseite). Dünnster Strich im Modell 0,28 mm.
- **Teilen über 250 mm:** nicht quer durchsägen, sondern eine Fuge nehmen, die es am Original gibt (hier Hals mit durchgehendem Zapfen); Zapfen so legen, dass er auf dem Bett steht,
  Spiel 0,12 mm je Seite, Schnittfläche nie deckungsgleich mit vorhandenen Flächen (0,06 mm versetzen). Mit dem Maßstab wachsen die Details nur, wenn Feinheiten als
  Druckmaß `p(mm)` und echte Maße als `max(echt, p(...))` angegeben sind.
- **Gewölbte/abgeschrägte Flächen bei mehrfarbigen Einlagen:** alle Farbkörper gemeinsam verformen (`refine_to_length` + `warp_batch`), nicht einzeln schneiden.

## Detailgetreue Miniatur eines realen Gegenstands (Erfahrung Gitarren-Miniatur 16.–17.11.2026 – nur gerechnet)
So kam `modelle/gitarre_rundum.py` zustande; für ähnliche Vorhaben (Instrument, Gerät, Fahrzeug als Modell) genauso vorgehen:
1. **Vorlagen sammeln:** gerade Vorderansicht, Rückseite, Seite, Nahaufnahmen aller Anbauteile, dazu ein Maßblatt. Fremde CAD-Dateien nur zum Abgleich, nicht ins Lager.
2. **Aus dem Foto vermessen:** Maßstab und Perspektive über bekannte Abstände herausrechnen (hier 24 Bundabstände, Mensur 648), Umriss und Lage aller Teile als Daten in eine
   JSON neben dem Skript. Muster (Wolkung) per Bandpass + Schwelle aus der Nahaufnahme.
3. **Ein parametrisches Skript in echten mm**, am Ende auf `--laenge` skaliert. Feinheiten als Druckmaß `p(mm)`, echte Maße als `max(echt, p(...))` → dasselbe Modell geht in 160 und 370 mm.
   Je Farbe eine Liste von Körpern; Farben nur an Flächen berühren lassen (2D aufteilen, Fuge 0,03), Schnittvolumen aller Farbpaare ausgeben (soll 0 sein).
4. **Runde um Runde mit Tom:** nach jeder Änderung ein gerendertes Bild der betroffenen Stelle selbst ansehen und schicken (pyvista unter `xvfb-run -a`), Toms Foto daneben denken.
   Toms Aussage zur Lage/Form geht vor der eigenen Foto-Deutung (Armschräge: eigene Deutung war falsch; Buchsenplatte: „Kante“ war nur Schatten). Geschätzte Werte (Tiefen, Winkel)
   als ein Parameter anlegen und Tom nennen.
5. **Anbauteile an gekrümmten Flächen** (Buchsenplatte an der Zarge): Platte aus dem versetzten Umriss schneiden (`K.offset(+t) − K.offset(−e)` ∩ Form entlang der Normalen),
   nicht als ebene Scheibe aufsetzen. **Kantige Ausfräsungen:** Quader mit `trim_by_plane` je Fläche beschneiden (Ebene durch Kante am Rücken und Tiefpunkt).
6. **Funktion nur, wo der Maßstab es trägt:** Steckzapfen, Steckwirbel mit Kegel, Saitenfach erst ab 370 mm; im kleinen Stück dieselben Stellen als Farbdetail.
7. **Farbe über Schichtung:** dünne Haut (0,16 mm) der hellen Farbe über dunklem Muster wirkt echter als zwei Farben nebeneinander – Durchscheinen am Gerät unbestätigt.
8. **Slicen** mit den Werten aus „Maximale Details mit 0,25-mm-Düse“; nur das betroffene Teil neu slicen, Ordnernamen behalten, Zeiten/Gramm melden. Markennamen und Schriftzüge weglassen.

## Foto-Scans (Photogrammetrie, Plan vom 16.11.2026 – **ungetestet**)
- Tom fotografiert selbst (Canon 5D Mark IV, Softboxen) und rechnet am Windows-Laptop (RTX 3060 6 GB) mit Meshroom; er schickt OBJ + Textur (+ MTL) als ZIP.
- Ablauf: ZIP in eigenen leeren Ordner entpacken → `werkzeug/ki_rohling.py` (aufrichten, Maßstab – **Zielgröße erfragen, Scans haben keinen Maßstab** –, schließen, Boden plan)
  → Bild an Tom → bei Farbe `werkzeug/textur_farben.py` → slicen. Große Netze vorher auf ≤ ~500.000 Dreiecke verkleinern.
- Scans glänzender/dunkler/dünner Teile (Saiten, Chrom, Lack) haben Löcher und Beulen. Für Maßhaltiges den Scan nur als Vorlage nehmen und das Teil konstruieren.

## Drehteller für Foto-Scans (`modelle/drehteller.py`, 20.11.2026 – nur gerechnet)
- Alles gedruckt (Toms Wunsch): Sockel Ø212 mit flachem Laufring (Ø160–200), Führungslippen innen/außen und Zapfen · Käfig mit 24 Taschen + 48 Walzen Ø8 × 6,8 mm
  (je zwei pro Tasche gegen Schlupf, stehend gedruckt, Fasen 0,5) in einem Druck · Teller Ø226 (größter Ø mit Spülturm; `--teller <Ø>`), Oberseite nach unten gedruckt ·
  Visier „Kimme und Korn“ (Kopf 2 schwarz) steckt mit 8×8-Zapfen in einem Block vorn am Sockel; Visierlinie 0,5 mm über Tellerunterkante, Korn zeigt auf die Zahlenmitte am Rand, flache Kimme (1 mm), damit die Zahl darüber sichtbar bleibt.
- Markierungen als schwarze Einlage 0,6 mm: oben 25 Linien, Zahlen 1–25 (6./9. mit Punkt), Kreise R50/75/100, Mittelkreuz; **auch auf dem Außenrand** Zahlen 1–25 und senkrechte Linien
  an denselben Stellen (Toms Wunsch, für Kameras von der Seite). Schnittvolumen aller Paare 0. Projekt `drehteller` (1 Sockel, 2 Käfig und Walzen, 3 Teller, 4 Kimme und Korn,
  5 Podest und Stifte, 6 Maßwürfel 20 mm).
- Meshroom-Hilfen: Zufallsmuster (Punkte Ø1,2–2,2, Abstand ≥ 4,2, feste Saat 25) zwischen den Linien, vier **CCTag3-Marker** (IDs 0–3, Ø24, Ringe aus `modelle/drehteller_daten/cctag3.txt`
  = AliceVision/CCTag) auf R75 in Feld 1/7/14/20 mit weißem Rand; drei Löcher Ø4,4 × 3 auf R30 für das Podest (Ø70 × 40, oben 19 Löcher Ø3,3 für Stifte Ø3 × 18).
  Spickzettel für Tom mit Marker-Koordinaten für SfMTransform `from_markers`: `modelle/drehteller_daten/MESHROOM.md`. Mit echten Fotos ungetestet.
- **Schwarz als PETG (21.11.):** Tom hat nur schwarzes PETG → Teller und Maßwürfel: Kopf 2 PETG; alle Einlagen mit **Hinterschnitt-Anker** (`ANKER`/`ANKER_T` in drehteller.py: 0,2 je Seite breiter, 0,4 tief unter der 0,6-Einlage), weil PLA und PETG kaum aneinander haften. Neuer Schalter **`druck.py --bett <°C>`** setzt alle Platten-Temperaturen aller Filamente (sonst nimmt Orca das Höchste: 85 °C vom PETG) – hier 65. Teller 7 h 20, Würfel 1 h 03. Nicht gedruckt.
- **Rastung (20.11.):** 25 V-Kerben (2,4 × 1,0) unter dem Tellerrand in den Feldmitten, am Sockel eine beidseitig eingespannte Brücke (46 × 4 × 1,2 mm, gerechnet ~2 N) mit Nocken r 1
  (0,6 mm Eingriff) bei `RAST_WINKEL` = −90 + 5·14,4° → rastet genau, wenn das Visier auf eine Zahlenmitte zeigt. Geprüft: Schnitt 0 in Rast, 2,4 mm³ bei halbem Feld (= Federweg).
- **Zubehör** `modelle/scan_zubehoer.py`: Halter-Baukasten (3 Spitzen, 2 Säulen stapelbar, 2 Klemmen, V-Auflage; Zapfen Ø3,1 in Podest-Löcher Ø3,3) und **Prüfkörper**
  (Stufenklotz 60 × 52, Stufen 2–10, Löcher Ø2–6, Stifte Ø1,5–4, Pyramide, Halbkugel, Eck-Loch für die Lage); Bezugsmodell `modelle/drehteller_daten/pruefkoerper_bezug.stl`.
  Projekt-Nr. 7 Halter, 8 Prüfkörper.
- **`werkzeug/scan_aufbereiten.py <zip|obj> --aus d [--podest] [--vergleich bezug.stl] [--ziel-mm n]`:** Meshroom (Y oben, Einheit 100 mm aus den Markern) → Z oben, mm →
  Schnitt über Teller (+0,3) bzw. Podest (40,3) → größte Teile → Löcher schließen, sonst Poisson (Tiefe 10, Normalen aus dem Netz, nicht aus der Punktwolke – sonst Blasen)
  → Boden plan (unterste 0,5 mm fehlen) → STL + `_bericht.json`; `--vergleich` legt per ICP (vier Startlagen) auf das Bezugsmodell und misst mittel/95 %/max.
  Mit nachgestelltem Scan geprüft (Rauschen 0,08 mm): mittel 0,20, 95 % 0,30, max 0,47 mm. Braucht `shapely` (steht jetzt in setup.sh).
- **Lehren:** Mit `--zusammen` (Orca `--assemble`) werden die Teile nicht verschoben → STL in Bett-Koordinaten legen (Mitte 128/128), sonst „No object is fully inside“.
  Spülturm (Standardlage x165/y250) passt bis Teller Ø226; Ø230 und größer nur ohne Turm (`enable_prime_tower=0`, Verschieben in die Ecke gab Code -101). Rand-Zahlen = ~49 Kopfwechsel.
  `ironing_type=top` bügelt auch die ganze Sockelplatte (3 h 20 → 9 h 40) – weggelassen. Einlage-Körper „roh“ abziehen, nicht den mit dem Körper geschnittenen (sonst undichte Netze).

## Messmatte und Makroschlitten (`modelle/foto_helfer.py`, 20.11.2026 – nur gerechnet)
- **Messmatte** 250 × 180 × 3, weiß, schwarze Einlage: 4 ArUco-Marker (DICT_4X4_50, IDs 0–3, 30 mm, 0 oben links im Uhrzeigersinn) + Messstriche 1/5/10 mm; Lage der
  Markerecken in `modelle/messmatte.json` (bei Maßänderung neu schreiben: `foto_helfer.py --ziel …` legt sie mit ab). Projekt `messmatte`.
- **`werkzeug/messmatte.py foto.jpg --aus d [--hell] [--dicke 3] [--hoehe <mm> --kamera-abstand 600]`:** Marker finden → Homographie → 10 px/mm Draufsicht → Otsu im Messfeld →
  Außenumriss + Löcher in mm → `_umriss.json`, `.svg`, `_entzerrt.jpg`, optional STL. Nachgestelltes Foto (schräg, Rauschen): Maße auf ±0,2 mm, Löcher Ø10/6 → 9,88/5,92,
  Lochabstand 40 → 39,84. Dicke Teile: Oberkante wirkt größer → `--hoehe`. Für Passteile: Umriss als Vorlage, Bohrungen/Passungen in CAD sauber setzen.
- **Makroschlitten** (Focus Stacking): Schiene 190 × 70 mit Schwalbenschwanz 30/38 × 6 (45°), Schlitten 70 × 70 (Spiel 0,3), Spindel M6 bei y −27/z 22 mit Mutter im Schlitten,
  Knopf Ø40 mit 10 Strichen (= 0,1 mm), Stativmutter 1/4" unten, Kameraschraube 1/4" von unten (Senkung im Schwalbenschwanz-Kanal). Kaufteile: M6-Gewindestange 220 mm,
  4 Muttern M6, Mutter 1/4"-20, Stativschraube 1/4" mit Ring. Projekt `makroschlitten`. Ungetestet, ob der Schlitten unter 1,5 kg Kamera kippelt.

## Erster echter Scan: Amp-Plektrumhalter (21.11.2026, privat in druckwerk-modelle/amp-plektrumhalter)
- **FlashBuild (Apple Object Capture) am Mac:** OBJ + 8k-Textur + MTL, Einheit **Meter ohne echten Maßstab** (Amp kam ~2,7× zu groß), Y oben, Vorderseite +Z.
  8k-PNG nicht mit trimesh-Material laden (Speicher, Prozess abgeschossen) → `skip_materials=True` + Textur vorher auf 4096 verkleinern.
- Ablauf: Höhenprofil je Schicht → Standfläche/Hocker abtrennen (Flächenmitte über Schnitthöhe) → je Achse auf Toms echte Maße skalieren → GLB mit UV →
  `ki_rohling.py --voxel 0.1 --boden schnitt:1.5 --aufrichten aus --oben z` (ragged Unterkante weg).
- **Farben aus dunklen Scan-Texturen taugen nicht** (`textur_farben.py` gab 99,8 % schwarz bzw. fleckige Auto-Farben) → Farbbereiche **geometrisch** festlegen
  (Bespannung als Rechteck-Einlage vorn, Knöpfe über Höhenkarte, Keder als 0,4-mm-Rahmen), Muster `amp-plektrumhalter/modell/halter.py`. Bespannungsrelief kam aus dem Scan mit.
- Keder über die ganze Höhe = viele Kopfwechsel (544 bei 0,08 mm, 8 h 12 min); ohne Keder deutlich weniger.
- **Detailfotos (21.11.):** Farben danach statt nach Gefühl – Bespannung = schwarzer Grund + creme Noppen (versetztes Raster, als Druckmaß 1,0 × 0,8 mm bei 0,25er, 1,4 × 1,1 bei 0,4er; echt 0,65 × 0,53), Keder gold, Knöpfe schwarz mit goldener Kappe, rotes Schild ohne Schrift, LED rot. Flächen auf schräger Scan-Front über eine Scherungs-Matrix aus der gefitteten Ebene bauen (`front()` in halter.py). Manifold-Ausgabe vor dem Export entarten-frei machen (`nondegenerate_faces`), sonst meldet pruefen.py hunderte Null-Splitter. 0,25er: 7 h 33, 496 Wechsel.
- **Ledernarbung, die druckbar ist (21.11.):** keine Fuzzy Skin (wirkt auf alle Köpfe, Noppen würden rau), sondern Worley-Zellen direkt in die Scan-Punkte gerechnet (Rille = Zellgrenze, F2−F1 klein; nur nach innen entlang der Normalen; Bespannung, Bedienfeld und Standfläche per Abstand ausgeblendet) – Scan-Netz ist mit Voxel 0,1 fein genug. Zelle 0,6/Tiefe 0,12 (0,25er), 0,8/0,15 (0,4er). **0,4er feinste Stufe:** Profil 0.12 + `--extra layer_height=0.08` + Detail-Zusätze + `--schoen` (in der .gcode geprüft: 0.08, Arachne, innen-außen-innen); Bericht-Schichthöhe danach von Hand korrigieren. Nicht gedruckt.

- **Fassung 3 (23.11.): konstruiert statt Scan** – Tom wollte den Tragegurt weg und alles detaillierter: der Scan war dafür zu weich. `halter.py <ordner> 0.25|0.4` baut jetzt alles aus Maßen
  (Kasten mit runden Kanten per `batch_hull` aus Scheiben, Mulden, Knöpfe mit Riffelung/Kappe/Zeiger, Buchsen, Kippschalter, Zierstreifen über die Oberseite), Ledernarbung über `refine_to_length(0.14)` + Worley.
  Schlitze von vorn nach hinten nebeneinander: außen 2,0 mm (Toms Wunsch, erst 3,2), innen 1,5 mm, nach unten schmaler, oben Fase. **Lehren:** (1) Bündige Einlage 0,02 über die Fläche
  ziehen – float32 legt sonst eine hauchdünne Haut darüber und die Einlage wird ein eingeschlossener Hohlraum. (2) `decompose()` liefert Hohlräume als Stücke mit **negativem Volumen**; beim Splitter-Filtern
  nur kleine positive Stücke abziehen, nie „Summe der großen“ bilden (füllt die Hohlräume → Farben überlappen). (3) `decompose()` auf Netzen mit ~1000 Stücken zweimal = Speicher weg (Prozess abgeschossen).
  Für reale Geräte künftig gleich so: Scan/Fotos nur zum Vermessen, Modell konstruieren.

- **Fassung 4 (23.11.):** Bedienfeld nach Toms Foto der Oberseite neu vermessen (Foto-Breite = 50 mm → Lage aller Regler/Tasten in mm); Linien, Ringe, Balken jetzt gold (wie am Gerät), Schrift als Balken, Zeiger als Kerbe in der Kappe. Neues Teil mit alten Einstellungen slicen: `--wie <alter ordner>` + neue `--teil` + `--ausgabe <neuer ordner>` klappt. Nur noch 0,25er-Fassung im Lager.

## Fremde Figur nachbearbeiten: Buddha auf Lotus (23.11.2026, privat in druckwerk-modelle/buddha-lotus – nur gerechnet)
- Toms 3MF (Bambu-Projekt, KI-Modell „tripo_node“, 2 Mio. Dreiecke, nicht mannigfaltig + flacher „Generic-Cylinder“ als Sockel): Netze direkt aus `3D/Objects/object_1.model` lesen (Regex auf vertex/triangle),
  Sockel-Objekt weglassen. Kein Boolean nötig: Figur und neue Teile als zwei STL auf **denselben Kopf mit `--zusammen`** – Orca vereinigt überlappende Teile beim Slicen.
- **Mehr Struktur nur in einem Bereich:** weiche Maske über z/r (hier Blüte unten/außen), dann (1) vorhandene Feinstruktur verstärken = Abstand zur Taubin-geglätteten Fläche entlang der Normalen × 1,6,
  (2) feine Längsadern als Rippen über den Winkel um die Hochachse (104 Stück, 0,24 mm, leicht verwackelt). Figur bleibt unangetastet.
- **Neue Blütenblätter prozedural** (`buddha.py → kranz`): je Blatt lokales Raster (Länge u, Breite q), Umriss `sqrt(u)·(1−u)^0,46`, Mulde, Adern als Linien q = konstant (laufen an Ansatz und Spitze zusammen), Mittelrippe;
  **Unterseite = max(Bett, Oberseite − 0,7 − 1,1·Randabstand)** → dünner Rand, 48°-Schräge bis zum Bett: druckt ohne Stützen und sieht von der Seite wie ein Blatt aus (senkrecht bis zum Bett gezogen wirkte es wie Treppenstufen).
  Blätter einzeln als Manifold, dann `batch_boolean`. 0,12 mm `--schoen`, Stützen auto: 7 h 41, 85 g.

## Fertige Figur schärfer machen: `werkzeug/verfeinern.py` (23.11.2026 – nur gerechnet)
- Für „maximal feine Details“ an fremden Figuren/Deko (Drachen-Räucherset, privat in druckwerk-modelle/drachen): `xvfb-run -a python3 -I -u werkzeug/verfeinern.py figur.stl|npz --aus x.stl --bild v.png [--skala f] [--bett]`.
  Verdichtet das Netz (Kante ≤ 0,22 mm bzw. so grob, dass ≤ ~4,5 Mio. Dreiecke bleiben), verstärkt vorhandene Struktur entlang der Normalen (Band bis 0,4 mm × `--fein 1.2`, Band 0,4–1,5 mm × `--mittel 0.6`,
  höchstens `--grenze 0.45` mm) und legt ein Zellkorn (`--korn 0.06`, Zelle ≥ 2,5 Netzkanten) als Haut darüber; Standfläche bleibt. **Es entsteht keine neue Form** – nur schärfere Schuppen/Fugen und Haut. Bild selbst ansehen.
- Lehren: nicht-mannigfaltige Netze vor dem Unterteilen reparieren; Taubin-Glättung glättet zu wenig für die Bandtrennung → einfache Laplace-Glättung (Schritte = 2·(Reichweite/Kante)²); Vorher/Nachher nacheinander rendern,
  sonst reicht der Speicher (7 GB) nicht; über ~5 Mio. Dreiecke wird der Prozess abgeschossen. Slicen mit den 0,25-Detailwerten dauert je Teil 10–40 Min., .gcode 90–300 MB → im privaten Lager `gross.py`.
- Zeiten 0,25/0,08: Schale 100 mm 14 h 25 / 49 g · Halter 247 mm 29 h 10 / 146 g. Große Figuren mit 0,25 dauern Tage – Tom vorher sagen und 0,4er-Fassung anbieten.

## Gridfinity (`modelle/gridfinity/`, 21.11.2026)
- Bibliothek gridfinity-rebuilt-openscad (kennetek, **MIT**, `LICENSE` liegt dabei) als Kopie in `modelle/gridfinity/src` + `gridfinity-rebuilt-baseplate.scad`.
- **OpenSCAD hier ist 2021.01:** `cgs()`/`bin_subdivide` scheitern („No grid element available“, $-Variablen) → Fachgröße selbst rechnen (`bin_get_infill_size_mm` / Zellen,
  `- d_div/2`), Lage weiter mit `bin_translate`, dann `compartment_cutter(…, center_top=false)`; Muster `drehteller_kiste.scad`. Grundplatte: Datei per `include` und Werte danach überschreiben.
- OpenSCAD-STL hat Splitter/Nan-Volumen → vor dem Slicen mit pymeshlab säubern (Duplikate, Komponenten < 2 % Diagonale weg, Nicht-Mannigfaltiges, kleine Löcher). `pruefen.py` meldet an der
  Stapellippe „Wand < 0,8“ – bei Gridfinity normal.
- Drehteller-Kiste 4 × 2 × 5 (Fächer: Walzen | Stifte | Spitzen+Säulen / Klemmen+V-Auflage | Visier+Würfel, mit Beschriftungslaschen) + Grundplatte 4 × 2 dünn ohne Magnete; Projekt `drehteller` Nr. 9/10.

## Gitarren 190 mm und ein Druck je Gitarre (23.11.2026 – nur gerechnet)
- **Schecter:** `modelle/gitarre_rundum.py --laenge 190 --wolken 4 --wirbel 1 --armschraege 0.25` (Rundungen jetzt `SEG` 72 / `KANTE` 14 / Kreise 96); Wirbel neben den Korpus verschieben und mit `--zusammen` in denselben Druck.
- **Stratocaster:** `werkzeug/gitarre_farben.py modelle/quelle/stratocaster_original.stl <ziel> 190 --schnur 1` → keine festen Saiten, Kerben in Sattel/Reitern, Kegellöcher (Klein-Modus wie Schecter) + `strat_wirbel.stl` (6 Wirbel + 8 Lochkugeln Ø 1,8 × 1,5, Loch 0,5), `strat_wirbel_platte.stl` neben dem Korpus, Saitenlöcher Ø 0,72 durch den Korpus, hinten Rinne 2,0 × 1,6 für die Kugeln (Lochabstand nur 1,94 mm). Rippenbogen/Armauflage unverändert.
- **Strat mit Details nach Toms Fotos (23.11. abends, seine eigene Strat: cremeweiß, Ahornhals, 22 Bünde, Zwei-Punkt-Tremolo):** zusätzlich `--details 1` → fünftes Teil `strat_schwarz.stl`
  (Linie der schwarzen Schlagbrett-Mittellage 0,30 breit/0,28 vom Rand, 18 Pole, 10 Griffbrett-Punkte). **Trick fünfte Farbe ohne fünften Kopf:** alles Schwarze liegt über der Korpusdecke (8,15 mm),
  der Korpus-Kopf ist dort frei → `strat_schwarz.stl` auch auf Kopf 1, danach `spulenwechsel.py <gcode> --kopf 1 --min-luecke 0.1 --bei 8.25` (Pause bei 8,26 mm; **`--bei` angeben**, sonst nimmt das Skript
  die größere Lücke innerhalb der schwarzen Teile). Dazu: 22. Bund auf Überstand, Sattel weiß, Schrauben/Gurtknöpfe/Halsplatte silber (Zonen-Umfärben `farbe(zone, ziel, von)`), zwei Bolzen statt sechs
  Brückenschrauben, Saitenniederhalter als Keil (45°, stützfrei), Halsstab-Tropfen 0,25 vertieft. **Rückseite plan:** Deckel/Halsplatte standen im Netz 1,6 mm vor (Korpus schwebte 0,5 mm über dem Bett)
  → abgeschnitten und als bündige Einlagen 0,32 dick neu gesetzt. Nicht machbar bei 190 mm: Zahlen auf den Reglern, Schriftzug (bewusst weg), dunkler Halsstreifen hinten (liegt unter der Decke, bräuchte zweiten Wechsel).
  **Farbnamen je Kopf nur aus der App-Palette** (creme, silber, holz …) – „creme (dann schwarz)“ zeigte die App grau. Zweite Farbe am selben Kopf: nach dem Slicen in `auftrag.json` beim Teil `"farbe": "schwarz"` eintragen (teile + teile_app), dann `index_neu`; die Werkstatt zeigt das Teil so.
  Lage aller Teile per Höhenkarte aus dem Netz gemessen (Punktwolke → max z je 0,5-mm-Zelle → `scipy.ndimage.label` je Höhenband) – so auch bei anderen fremden Netzen vorgehen.
- **Strat 240 mm mit drehbaren Steckreglern (24.11.2026):** `gitarre_farben.py <orig> <ziel> 240 --schnur 1 --details 1 --regler 1` → Regler aus dem Netz entfernt (Lage gemessen, `REG`), Loch Ø 2,3 × 4,0 im Schlagbrett
  (darunter volles Material), `strat_regler_platte.stl` (3 + 1 Ersatz, kopfüber, stützfrei, Kopf 2 weiß): Kappe Ø 4,4 mit Rippen, Rock Ø 6,3, Zapfen Ø 2,0 leicht kegelig (Wurzel 0,02 über Lochmaß → klemmt leicht, dreht).
  Ab ~215 mm (Assert im Skript). Bei 240 sind die Wirbel im Groß-Modus (Rad Ø 6,4, eine Ebene). Slicen `--wie` vom 190er-Auftrag + Regler-Teil auf Kopf 2; Pause mit `--bei 10.4` (Decke 10,29). Auftrag `2026-11-24_stratocaster240_c5pro`: 9 h 54, 56 g, 427 Kopfwechsel.
- **Schecter: Decken-Kante gerundet (24.11.2026, Toms Wunsch „wie bei der Strat, etwas minimaler“):** `gitarre_rundum.py --kante 3` (echte mm; 0 = alte Kante 0,30 Druckmaß; erst 5, Tom wollte sie kleiner). **Toms Korrektur 10:14: „die Rundung muss vom Rot zum Schwarz, nicht vom Schwarz zum Grau“** → Schwarz sitzt als Band an der SEITE
  (Stärke 0,32 Druckmaß, reicht 0,6 mm unter den Bogen), Rot läuft oben bis in die Rundung (`rot_ring`), Grau beginnt erst darunter; kein schwarzer Streifen mehr auf der Decke.
  Der Kern ist dafür oben um die Bandstärke eingezogen; das Band weicht am Hals dem Grau (`schwarz_k − (rand_k ^ grau)`). Bei 190 mm ist nur die oberste Schicht des Bogens rot, die Schulter druckt schwarz.
  Lehre: Tom benennt eine Rundung nach den Farben der beiden Flächen, die sie verbindet (Decke → Zarge). Für alle Schecter-Größen jetzt Standard.
  **10:52 „gleiche Rundung an der Unterseite“:** statt der 45°-Fase unten derselbe Radius (grau); der Bogen setzt mit 23° an (`T0 = 0.4`), damit die ersten Schichten tragen. Im Slicer geprüft: keine zusätzlichen Stützen am Rand (916 statt 917 Abschnitte), Zeit gleich.
- **Strat: Kantenrundung umlaufend, auch an der Armauflage (24.11.2026, Toms rot markiertes App-Bild):** der Keil der Armauflage hatte dort die Original-Rundung (r ≈ 7 mm, aus dem Netz gemessen:
  Einzug des Umrisses je Höhe) weggeschnitten. Neu in `gitarre_farben.py` direkt nach dem Keil: Abtrag mit demselben Radius **relativ zur abgesenkten Fläche** (`_zt`), als EIN Netz je Lauf (Querschnitt × Stationen alle 1,5 mm).
  Erst als ~2300 Einzel-Hüllen gebaut → bei 190 mm wurde der Prozess beim späteren `decompose()` abgeschossen (Speicher). Außerhalb der Abflachung trifft der Abtrag nur Luft. Strat 190 (6 h 12) und 240 (9 h 54) neu gerechnet.
- **Schecter-Zarge „noch runder“ (24.11.2026):** `fein()` tastet den Umriss alle 0,5 mm neu ab und glättet ihn (Gauß 3 mm; 6 mm machte `schwarz` undicht), `band()` jetzt mit Schritt 0,6 statt 1,2 – Abweichung zur alten Form höchstens 0,14 mm im Druck.
  **Die senkrechten Streifen in Toms Bildschirmfoto waren keine Kanten, sondern Helligkeitsstufen des Bildes** (Grauwert springt je Streifen um genau 1 von 255) – bei solchen Rückfragen erst die Pixelwerte prüfen, dann erklären.
- **Schlüsselanhänger 50 mm aus beiden Gitarren (24.11.2026, Projekt `anhaenger`, je EIN Teil):** erst klein bauen – Schecter `gitarre_rundum.py --laenge 50 --wolken 4 --armschraege 0.25 --kante 3` (ohne `--wirbel`),
  Strat `gitarre_farben.py <orig> <ziel> 50 --saiten 0` (neu: ohne Saiten, die Stege verschmelzen bei 50 mm zu einem Band; ohne `--schnur/--details`) – dann **`werkzeug/anhaenger.py --aus <ordner> --teil name=datei.stl … --korpus <farbe> --hals <farbe>`**:
  füllt Hals und Kopfplatte von unten bis aufs Bett (Strahlen-Raster 0,12 mm → Säulen; aus 1,2 mm Hals wird ein Balken), holt eine schwebende ebene Korpus-Rückseite aufs Bett (Strat: 0,14 mm) und setzt eine Öse (außen Ø 6, Loch Ø 3,2, 2 mm dick)
  ans Korpus-Ende; Gesamtlänge ~55 mm. Slicen 0,25/0,08 `--detail --infill 100`: Strat 45 min / 3,8 g / 47 Wechsel, Schecter 1 h 14 / 5,8 g / 79 Wechsel. Schecter-Farben überlappen bei 50 mm um ~1 mm³ und `schwarz` ist nicht dicht – der Slicer nahm es an.
  Rückseite des Halses ist dadurch kantig (kein C-Profil), Bauch-Ausfräsung der Schecter bleibt. Nichts gedruckt.
  **12:27 Toms Korrektur:** Öse weg (`--oese 0` ist Standard), stattdessen **Loch vorn oben durch die Kopfplatte** (`--kopfloch 2.0`, breiteste Stelle, Rand ≥ `--rand 0.7`; Strat Ø 2,0, Schecter nur Ø 1,64 mit `--rand 0.5` – Kopfplatte ist 4 mm schmal),
  **Hals hinten schlanker** als Kiel (`--kiel 0.3`: unten 40 % der Halsbreite, steile Flanken, läuft an der Kopfplatte aus; bleibt auf dem Bett und durchgehend bis in den Korpus – wirklich dünner ginge nur mit Stützen),
  Schecter-Buchse nur angedeutet: `gitarre_rundum.py --buchse klein` (flache Linse an der Zarge + silberner Punkt). Neu: Strat 44 min / 3,8 g, Schecter 1 h 06 / 5,1 g.
- **Ständer für die 190-mm-Gitarren (24.11.2026, `modelle/gitarrenhalter190.py`; Verlauf der Entwürfe, Endstand am Schluss):** zwei Wangen (5 mm, Abstand 30) auf Grundplatte 52 × 73, Kanal 9,4 mm für die Korpus-Unterkante,
  Lehne 12° / 66 mm, Gurtknopf hängt frei zwischen den Wangen (Zwei-Punkt-Auflage), Querwand hinten; druckt aufrecht ohne Stützen, ~30 g. Passung per Schnittvolumen: Schecter 0,000, Strat 0,2 mm³ (steht 1,7° schief, weil ihr Korpus unten unsymmetrisch ist).
  **12:20 Toms Korrektur am Bild:** Grundplatte komplett weg (stattdessen drei Querkufen 54 mm breit + Querwand) und in den Flossen ein Lochblech-Muster, 1 mm je Seite eingelassen (23 Löcher Ø 2,4, Sechseck-Raster 3,6); jetzt ~19 g, 54 × 69 × 72 mm.
  **12:25 „unten die Querstreben weg, nur hinten eine, alles eleganter“:** jede Wange ist jetzt EINE geschwungene Linie (Zehe vorn, Rücken in einem Bogen bis zur Ferse, Kanten gebrochen), Lochfeld mit nach oben kleiner werdenden Löchern (Ø 2,6 → 1,1), einzige Verbindung = Querstrebe hinten (9,7 mm hoch, Spitzbogen); 40 × 67 × 72 mm, ~14 g, Schnitt mit beiden Gitarren 0. Höhe der Wange an einer Stelle per Schnitt mit einem senkrechten Streifen bestimmen (Bezier ist in der Tiefe nicht monoton – `np.interp` gab 70 statt 10 mm).
  **13:10 „zweifarbig, denk dir was aus“:** Halter als kleiner Verstärker – schwarzes Gehäuse, Lochfeld = goldene Lautsprecher-Blende (`--zwei 1`, `gitarrenhalter190_gold.stl`): 3 mm starke Scheibe mitten in der Wange, greift ringsum 0,6 mm unter den schwarzen Rahmen (Formschluss, hält auch bei PETG + PLA). Schnitt Gold/Schwarz 0. Bild bei Tom, noch nicht gesliced. **13:15 „Löcher nicht schön angeordnet“:** kein Sechseck-Raster mehr (der geschwungene Rand zerhackt es), sondern Lochreihen parallel zur Lehne, alle unten auf gleicher Höhe begonnen, entlang der Reihe kleiner (Ø 2,3 → 1,1; 12/9/7/5/3/2 Löcher). Lehre: Muster in freien Feldern an einer Kante des Feldes ausrichten; Prüfbild gerade von der Seite in Parallelprojektion. **Gesliced 13:40:** `2026-11-24_gitarrenhalter190_c5pro` – Kopf 1 PETG schwarz, Kopf 2 PLA-Silk gold, 0,20 / 30 % / 4 Wände / ohne Stützen / Brim, Bett 65: 1 h 52, 24 g, 188 Kopfwechsel. Nicht gedruckt.
- **Prüfbilder ohne `smooth_shading`** rendern: geglättete Normalen auf groben Original-Netzen zeigen Streifen/Kanten, die es nicht gibt (Tom hielt die Strat-Rückseite deshalb für „komisch“).
- Gemeinsamer Druck = gemeinsame Einstellungen (Wirbel dann mit 15 % und Stützen auto statt 100 % / ohne Stützen) – Tom sagen.

## Erster echter Druck: Schecter 190 aus Flash Studio (24./25.11.2026) – Befund von Toms Fotos, Ursachen teils Vermutung
- Gedruckt wurde Toms eigener Flash-Studio-Schnitt (Geometrie importiert, Stützen/Arachne/Fein-Werte von Hand, 28,32 g, 6 h 45), kabellos gesendet; nach ~6 h abgebrochen.
- **Farben falsch: Korpus komplett rot, alles Übrige weiß; Grau (Kopf 1) und Schwarz (Kopf 3) haben nie gedruckt** (im Gerätebild standen T1/T3 auf Soll 0 °C, nur T2 220 und T4 120).
  Wahrscheinliche Ursache: beim Geometrie-Import gingen die Filamentfarben verloren (Flash Studio zeigte 1 = orange, 2–4 = weiß); beim Senden ordnet Flash Studio die Schnitt-Filamente den Köpfen
  nach Farbe/Material zu → orange → roter Kopf 2, alle weißen → weißer Kopf 4. **Vor jedem Senden die Zuordnung Filament → Kopf im Sende-Dialog prüfen (1→1 … 4→4)**; unsere .gcode per USB hat die Köpfe fest.
- **Fäden von Anfang an**, Stützen an der Kopfplatte mit dem Teil verklebt und verfilzt; **Steckwirbel nur ein weißes Knäuel** (winzige stehende Teile, lösten sich/kippten); Düse T2 anfangs einmal verstopft.
  Noch ohne jede Kalibrierung gedruckt (Kalibrier-Set, Kopfversatz, trockenes Filament offen) – erst das klären, dann wieder lange Drucke.
- **Buchse an der Zarge (190 mm): weißer Klumpen in der Aussparung** – die seitliche Buchsenplatte hängt in der Luft und ist für diese Größe zu fein → wie beim Anhänger vereinfachen (`--buchse klein`) oder als Farbfläche bündig.
- Unterseite (strukturierte Platte), Bodenrundung, Deckel-Einlage und Saitenlöcher hinten kamen sauber. Decke fehlt wegen Abbruch (Füllmuster sichtbar).
- Lehren fürs Vorgehen: erster Druck eines neuen Aufbaus = kleines Teil (Anhänger 45 min, Kalibrier-Teile), nicht 7 h vierfarbig; Wirbel als eigenen kleinen Druck anbieten; Tom nach dem Sende-Dialog fragen.

## Herstellerwerte Creator 5 Pro (Recherche 23.11.2026) – in `druck.py` eingebaut, nichts davon gedruckt
- **Quelle:** Flash-Studio-Profile im Zweig `release_0817` von FlashForge/Orca-Flashforge (neuer als unsere Orca-2.5-Profile), Flashforge-Wiki (FAQ, Filament-Leitfaden, Stützmaterial-PDF), Handbuch, Tests (Notebookcheck, Anton Mansson).
- **0,25-mm-Filamentprofile** (`drucker/fs_025/*.json`, 1:1 vom Hersteller): `druck.py` legt sie automatisch über das Filament, sobald der Kopf eine 0,25er-Düse hat. PLA 220 °C, PLA-Silk 230, HS-PETG 235 / Bett 70, PA 0,1, Fluss 0,98, **höchstens 2,8 mm³/s (PETG 2)** – vorher galten die 0,4er-Werte (210 °C, 18 mm³/s → Innenwände/Füllung konnten zu wenig Material bekommen). Neue Profile nachziehen: Datei aus `resources/profiles/Flashforge/filament/<Name> @FF C5P 0.25 nozzle.json` kopieren.
- **Kopfwechsel immer** (c5pro): wartende Köpfe −100 °C (`standby_temperature_delta`), `retract_length_toolchange` 2 mm (Orca 2.5: 3), Ooze-Schutz und Wischturm an. **Wischturm nie abschalten** (Flashforge-FAQ: Köpfe tropfen leicht nach).
- **`--detail`** = Paket „Maximale Details“ (ersetzt die von Hand angehängten `--extra`): Arachne 70 %/20 %, resolution 0.008, eine Wand oben, Außenwand 30 / Kleinumfang 20 / Oberfläche 40 mm/s, Außenwand-Beschleunigung 3000 (wie Flash-Studio-Feinstufe), 8 Deckschichten, Stützen nur ab Platte. Für jede 0,25er-Arbeit nehmen. Hersteller selbst fährt die Außenwand mit 60 und klassischem Wandgenerator; ein Tester fand Standard insgesamt am besten – unsere langsamere Fassung ist am Gerät noch zu bestätigen.
- **`--stuetz-kopf <n>`** = Kontaktschicht der Stützen aus anderem Material (Flashforge-Wiki Creator 5): Abstand oben/unten 0, 3 Kontaktlagen oben, 0 unten, Muster `rectilinear_interlaced`, Kontakt-Abstand 0, Stützkörper bleibt im Hauptmaterial; PLA-Köpfe werden bei PETG-Kontakt auf ≥ 225 °C gesetzt, Bett 65 (PLA+PETG automatisch). `--stuetz-koerper` = auch der Körper (PVA/BVOH/HIPS); bei PVA/BVOH normale statt Baumstützen. Bericht nennt: Deckel ab, Tür auf, Kammerheizung aus.
- **Was zu was:** PVA → PLA/TPU · BVOH → PLA/TPU/PETG · HIPS → ABS/ASA · PLA → PETG/TPU · PETG → Kontakt unter PLA (Toms schwarzes PETG passt; dunkel unter weiß kann Spuren lassen). Steht in `wissen/filamente.json → mischen`.
- **Am Gerät:** Kopfversatz nach jedem Firmware-Update/Düsentausch neu (sonst leidet feine Schrift), Düsen vorher säubern; einmal Vibration- und VFA-Kompensation; jede Düse möglichst bei einem Material. In `wissen/c5pro.json → probleme`.
- **Wischturm wie der Hersteller (seit 28.11.2026, Toms Wunsch „so klein, dass er noch sauber druckt“):** `druck.py` setzt für c5pro Breite 35 mm (vorher 45), Menge je Kopfwechsel
  `prime_volume` 20 mm³ bei 0,25-mm-Düse bzw. 30 mm³ sonst (vorher 45), Abstand 165 %, `rib`-Wand, Rand automatisch – Werte aus Flash Studio `release_0817`
  („0.10mm Standard @FF AD5X 0.25 nozzle“ bzw. „0.20mm Standard @FF C5“). Wirkt auch bei `--wie`/`neu_rechnen.py`; `--extra prime_volume=<mm³>` überschreibt (kleiner = Versuch, am Gerät unbestätigt).
  Gemessen: Strat-Anhänger 43 → 29 min, 3,6 → 2,1 g · Halter 160 4 h 13 → 3 h 14 · Schecter 190 7 h 17 → 6 h 12 · Verstärker 1 d 6 h 36 → 1 d 0 h 56. Alle Mehrkopf-Aufträge neu gerechnet
  **außer Strat 190/240** (brauchen danach `spulenwechsel.py` und die Farbe „schwarz“ in auftrag.json – beim nächsten Anfassen mitziehen) und den privaten Aufträgen.
- **Nicht übernommen:** 0,08-Stufe für 0,4-Düse aus Flash Studio (fehlt in Orca 2.5; weiter Profil 0.12 + `--extra layer_height=0.08`), gemischte Düsen in Flash Studio laut einem Tester nicht unterstützt → `--duesen` bleibt Versuch.
- **Neu rechnen:** `python3 werkzeug/neu_rechnen.py <ordner…> [--detail-025]` rechnet Aufträge mit allen alten Einstellungen (über `--wie`) und den neuen Herstellerwerten neu; Ordner/Dateinamen/Projekt bleiben. Aufträge ohne Projekt-3MF (zu groß, `gross.py`) gehen so nicht.

## Faustregeln Einstellungen
- Deko/Figur: 0.16–0.20, Infill 10–15 %, Baumstützen bei Überhängen.
- Funktionsteil/Halter: 0.20, Infill 25–40 %, `--waende 4`.
- Hitze/Draußen/Auto: ASA auf `c5pro`. ABS/ASA auf `kobrax` nur kleine Teile (offen → Verzug).
- TPU: langsam, nur ein Material pro Druck empfohlen.

## Technik-Notizen
- OrcaSlicer v2.5.0 CLI unter `xvfb-run`. Profile werden aus den Hersteller-JSON (inherits-Kette)
  aufgelöst; Werte außerhalb des erlaubten Bereichs korrigiert das Skript selbst (steht in slicer.log).
- Flashforge-Filamente: `filament_is_support` fehlt im Profil → Skript ergänzt es.
- **Druckplatte** (`platte` in drucker/*.json, Standard „Textured PEI Plate“) setzt `curr_bed_type` – sonst nimmt Orca
  „Cool Plate“ und heizt PLA nur auf 35 °C (Fehler vom 10.11.2026, Druck misslungen). Nach dem Slicen prüfen:
  Kobra `G9111 bedTemp=60`, Creator `M140 S55/60`.
- Jeder Auftrag bekommt zusätzlich `<name>_<drucker>.3mf` (Projekt mit Einstellungen, Feld `projekt`) – App-Knopf „3MF-Projekt laden“.
- `druck.py` rendert automatisch `vorschau.png` (OpenSCAD, Farben je Spule) → App zeigt es sofort, 3D lädt dahinter nach.
- Große Netze bekommen eine leichte Kopie `*.app.stl` (~60.000 Dreiecke, Feld `teile_app`) nur für die 3D-Ansicht am Handy.
- Vorschaubild für die Drucker-Anzeige (seit 15.11.2026): `druck.py` schreibt `vorschau.png` als Thumbnail-Block (Größe aus dem Maschinenprofil, 140×110 PNG)
  hinter den Kopfblock der .gcode (`bild_in_gcode`, Feld `bild_im_gcode`). Format wie OrcaSlicer; **am Gerät bestätigt 28.11.2026** (Buddha 150 per USB: Bild zu sehen, Druck läuft – erster USB-Druck einer Druckwerk-.gcode).
  Ältere Aufträge haben es erst nach neuem Slicen.
- `druck.py --bemalt` mit `--groesse`/`--skala`/`--matrix` (`bemalt_umformen`): schreibt nur die Eckpunkte neu, die Bemalung bleibt unverändert; von der Matrix zählt
  nur der 3×3-Teil (Lage bestimmt der Slicer). Spiegeln geht nur bei einfacher Bemalung (ein Farbcode je Dreieck).
- Später (Stufe 2): Senden per LAN über Heim-Brücke (Kobra X: MQTT, grunna/ha-anycubic-kobra-x-lan;
  Flashforge: HTTP 8898, Parallel-7/flashforge-api-docs). Erst nach Kauf am echten Gerät testen.

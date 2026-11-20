# Übergabe druckwerk

## STAND 20.11.2026, 06:40 Uhr – hier einsteigen (neuer Chat: „druckwerk: Weiterarbeiten“)
**Wo wir stehen**
- Drucker steht, WLAN läuft, **Flash Studio Desktop 1.7.22** ist am Mac installiert und mit dem Creator 5 Pro verbunden (Kopf 1 = PLA weiß, vier 0,4-mm-Düsen, Firmware 2.0.0-1.3.1).
- **Toms Weg zur Druckdatei, der funktioniert (bestätigt 20.11.):** App → Auftrag → **„Druckdatei laden“** → USB-Stick oder am Mac ins Flash-Studio-Fenster ziehen und senden.
  Ein direkter Link auf eine .gcode zeigt im Browser nur Text – immer den App-Link `…/#auftrag:<ordner>` oder `…/#projekt:<gruppe>` geben, nie die nackte Datei-Adresse.
- **Immer die .gcode geben, nicht die 3MF:** in Flash Studio kommen unsere Prozess-Einstellungen aus der .3mf nicht an (Probedruck: Stützen aus). Ursache offen – nächster technischer Punkt.
- Aktuelles Stück: **Lebensbaum-Lichtbild „Thomas & Sandra“** (`modelle/lebensbaum_licht.py`, Auftrag `2026-11-19_lebensbaum_licht_c5pro`, Projekt `lebensbaum`):
  stehendes, gebogenes Relief 181 × 41 × 182 mm in Weiß, Kopf 1, 0,12 mm, `--schoen`, Füllung 100 %, ohne Stützen, Brim an → **12 h 6 min, 112 g**. Tom hat die Datei geladen. **Noch nicht gedruckt.**

**Ideengebung (neu, Tom will, dass wir uns da weiterentwickeln):** `wissen/ideengebung.md` – der Weg zum Lebensbaum (vom Rahmen zur Idee, Bedeutung über die Form statt Symbol,
ein Gedanke zieht sich durch, Technik erzählt mit, Runden mit je einem Satz), Fragen zur Ideenfindung, **Ideen-Speicher** und was nach jedem Druck nachzutragen ist.
Bei jedem freien Entwurf zuerst lesen, am Ende ergänzen. Kurzfassung in CLAUDE.md („Ideengebung bei freien Entwürfen“).

**Als Nächstes**
1. Toms Fotos vom Lebensbaum (Tageslicht + Licht dahinter) auswerten: kommen Schrift (Strich 0,6 mm), Mond und Tau sauber? Stärken (Himmel 1,5 / dünn 0,85 mm) nachstellen, Ergebnis in
   `wissen/ideengebung.md` und `wissen/c5pro.json` (Herkunft „Gerät“) eintragen.
2. ~~3MF → Flash Studio~~ **Ursache gefunden (20.11. früh):** nicht die Version, sondern der Lade-Dialog – bei nicht leerer Platte ist „Nur Geometrie importieren“ vorausgewählt (auch ⌘I und Mehrfach-Öffnen laden nur Form). Hinweis in der App (sw.js v20), CLAUDE.md, `wissen/c5pro.json`. **Tom bestätigen lassen:** 3MF mit „Als Projekt öffnen“ laden → sind Stützen an? Dann Ladeverhalten auf „Alles laden“.
3. Offen von vorher: Probedruck `Schecter_160_Probe_einfarbig` und Kalibrier-Teile (keine Rückmeldung), ob der Drucker Unterordner auf dem Stick zeigt, 0,25-mm-Düsen für die Gitarre, Zahnrad-Maße.
4. Einen Einfall aus dem Ideen-Speicher vorschlagen, wenn Tom wieder „hau was raus“ sagt (z. B. Sternenhimmel eines Datums, Sockel mit LED-Teelicht).

## STAND 19.11.2026, 20:20 Uhr
**Erste Befunde am echten Gerät (Tom, 19.11.):**
- Mac: Slicer heißt **Flash Studio Desktop** (1.7.22, .pkg von flashforge.com/pages/flash-studio-desktop). Im Mac App Store gibt es nur die iPad-App „Flash Studio“ (= Mobile, kein Slicer);
  beide heißen im Ordner Programme „Flash Studio“ → Mobile-App erst löschen, dann .pkg installieren.
- Drucker ist im WLAN und in Flash Studio unter „Device“ verbunden (Firmware 2.0.0-1.3.1, vier 0,4-mm-Düsen, Kopf 1 PLA). Senden: Pfeil neben „Print plate“ → Print plate / Send / Export G-code.
- **Unsere .3mf öffnet sich in Flash Studio, aber die Prozess-Einstellungen kommen NICHT mit** (Probedruck: Stützen aus, 42 min / 13,1 g statt 51 min / 15,4 g, Warnung „floating regions“).
  Ursache offen (Vermutung: Projekt aus OrcaSlicer 2.5 ist „neuer“ als Flash Studio → nur Geometrie). **Bis das gelöst ist: Tom die fertige .gcode geben** (USB oder in Flash Studio ziehen
  und senden), nicht die 3MF neu slicen lassen. Offen: prüfen und beheben; ob der Knopf „In Flash Studio öffnen“ (orcaslicer://) ging oder Tom die 3MF von Hand lud, hat er nicht gesagt.
- Ob der Probedruck `Schecter_160_Probe_einfarbig` gedruckt wurde: keine Rückmeldung.

**Neu am 19.11.: Projekt `lebensbaum` – „Lebensbaum Lichtbild“** (Toms Auftrag: extrem detailliert, 0,4-mm-Düse, weiß, druckfertig)
- `modelle/lebensbaum_licht.py` (Saat 4): stehendes, gebogenes Relief 181 × 41 × 182 mm, Wand 0,85–6,9 mm, stützfrei (Überhänge rechnerisch ≤ 55°), Baum aus `baum_relief.py`,
  Mond/Sterne als dünne Stellen (leuchten mit LED-Teelicht dahinter). STL wird nicht eingecheckt (`python3 modelle/lebensbaum_licht.py --ziel modelle`, 15 s).
- Auftrag `2026-11-19_lebensbaum_licht_c5pro`: Kopf 1 PLA weiß, 0,12 mm, `--schoen`, Füllung 100 %, Stützen aus, Brim an, `resolution=0.05` → 11 h 25 min, 111 g, .gcode 87 MB.
- Stand 20:40 Uhr nach Toms Wünschen: Wurzeln laufen spitz bis zum Rahmen aus; zwei Wurzelstränge bilden unter dem Stamm eine **Endlos-Schleife (liegende Acht) als gedrehtes Tau aus zwei Strängen**, in den Schlaufen
  die Namen **Thomas** und **Sandra** als ultrafeine Ein-Strich-Kursive (TeX Gyre Chorus → Mittellinie, Strich 0,6 mm, dünn = leuchtet), Haarstriche verbinden Namen und Strang;
  Mond als Scheibe mit Kratern, Meeren und Erdschein. Tom wollte „endlose Liebe, kreativ, nicht kitschig“. Namen ändern: `NAMEN` im Skript.
  `pruefen.py` meldet bei Reliefs „Details < 0,45 mm“ und „Wand < 0,8 mm“ (Riefen der Oberfläche, kein Bruchrisiko) – so gelassen. **Nicht gedruckt.**

## STAND 18.11.2026, 19:15 Uhr
**Am echten Gerät ist weiterhin nichts bestätigt** – Drucker kam am 17.11., bisher keine Rückmeldung zu einem Druck. Alles unten ist gerechnet oder im Browser nachgestellt.

**App (seit 18.11., sw.js `druckwerk-v17`; Details CLAUDE.md → „App“)**
- Vier Reiter: Projekte · Neu · Drucker · Wissen. Projekt = Aufträge mit gleicher `gruppe`; Teile in Druck-Reihenfolge mit Haken; „Alles für den USB-Stick laden“ (ZIP mit
  Ordner, `1_…gcode`, LIESMICH.txt). Alles aus dem Lager erscheint von selbst; ausblenden statt löschen.
- Projekte im Lager: `schecter370` (1 Wirbel, 2 Saitenfach-Deckel, 3 Hals, 4 Korpus), `schecter160` (Probedruck einfarbig mit 0,4-mm-Düse, Wirbel, Gitarre, Wirbel aus der App),
  `schecter200` (erster Stand), `kalibrier` (1–5). Dateien heißen `Schecter_370_Korpus.gcode` usw. Neue Teile immer mit `--gruppe … --gruppe-titel … --nr … --titel … --datei …`.
- Mac: „Direkt in Flash Studio öffnen“ (`orcaslicer://open?file=…`) und Rückweg „Geänderte Fassung hochladen“ / „Flash-Studio-Ordner verbinden“ (Chrome), Anleitung unter
  Wissen → Hilfe. **Beides am Mac ungetestet** – beim ersten echten Lauf Action-Log und `status/<id>.json` ansehen. Vor dem Neu-Slicen `geaendert` in `auftrag.json` beachten.
- Wissen → Modelle verlinkt Printables.com („STL-Modelle“).

**Slicen (neu am 18.11.)**
- `druck.py --schoen` = Sichtteil-Paket für PLA mit 0,4-mm-Düse (3 Wände innen-außen-innen, Arachne, ≥ 5 Deck-/Bodenschichten, Außenwand ≤ 45, Innenwand ≤ 100, erste Schicht ≤ 30,
  Überhänge/Brücken ≤ 30 mm/s, Fahrwege meiden Wände, Naht hinten, Schrägnaht). Bei Deko/Sichtteilen aus PLA von selbst nehmen. `--schraegnaht` einzeln. In der Werkstatt: Haken
  „Schön (langsam)“, Füllmuster „Blitz“. Messwerte: Winkel-Teil 16:28 statt 12:27 min; Zylinder mit Schrägnaht +11 s.
- Videos ausgewertet am 18.11.: `videos/pla-einstellungen-bastlwastl.html`, `videos/z-naht-bastlwastl.html`, `videos/aimia-makerlab-bastlwastl.html` (Aimia → neues Werkzeug
  `werkzeug/teilen.py`: zu große/fremde STL gerade teilen mit Passstift-Löchern, siehe CLAUDE.md). sw.js jetzt `druckwerk-v18`. Ablauf für weitere Videos: CLAUDE.md → „Video auswerten und aneignen“.

**Neu am 18.11. abends**
- Vogel-Ring-Schlüsselanhänger, eigener Entwurf nach Toms Stilbild (das Albatros-Shopmodell wird nicht nachgebaut): `modelle/vogelring.py` (Höhenfeld → marching cubes, 45 mm, 8 mm,
  beidseitig gleich, halbrund, Öse). Vorschau an Tom geschickt, Rückmeldung offen; Plan: zwei Hälften mit flacher Rückseite + Filament-Passstiften, Hälften-Teil im Skript noch nicht fertig.
- Tom hat fremde Gitarren-Modelle geschickt (Strat-Bausatz 1:1, Les-Paul-Bausatz 1:1, Les Paul komplett, Telecaster-STEP von GrabCAD, Plektrumhalter, Kork-Diorama, Albatros-Hueforge).
  Statt druckwerk privat zu machen: **neues privates Lager `Tom444555/druckwerk-modelle`** (Tom hat es angelegt und für Claude freigegeben). Alle Dateien dort einsortiert
  (7 Projekte, `index.json`, Vorschaubilder). App: Bibliothek → „Private Modelle“ (`privat.js`, sw.js `druckwerk-v19`) – braucht Toms Schlüssel mit Zugriff auf druckwerk-modelle;
  am iPad ungetestet. Nichts davon geslict; Bausätze 1:1 bei Bedarf mit `teilen.py` teilen.

**Offen / wartet auf Tom**
- Erste Drucke: Kalibrier-Teil 1 (Haftung) und 2, dann `Schecter_160_Probe_einfarbig`; Rückmeldung per Tagebuch. Zeigt der Drucker Unterordner auf dem Stick?
- Vergleichsdrucke: kleines Teil normal/„schön“, Zylinder ohne/mit Schrägnaht (Testdateien noch nicht als Auftrag angelegt – auf Wunsch rechnen).
- Gitarre: alle Detail-Aufträge brauchen die **0,25-mm-Düse auf allen vier Köpfen** (Tom hat sie evtl. noch nicht). Filament bestellt bei filamentor.io: PLA matt grau/schwarz,
  PLA Silber (kein Silk), für Kopf 2 „Bordeaux“, PETG als Stütz-Material unter PLA (Stütz-Kopf in druck.py noch nicht eingebaut).
- Zahnrad: ca. Ø 10 mm, 20 Zähne, Dauereinsatz in einer Maschine – Tom misst noch (Außen-Ø, Bohrung, Breite, Gegenrad, Achsabstand, Wärme); Empfehlung PA12 mit 0,25-mm-Düse oder Kaufteil.
- Mac-Wege testen (Flash Studio öffnen, Zurücklegen). GitHub-Token am iPad ist eingerichtet (ein Slice aus der App lief: `gitarre160_wirbel_2`), am Mac noch nicht.
- Verworfen: Albatros-Anhänger (Tom wollte ihn nicht; ein Kaufmodell aus einem Shop wird nicht nachgebaut – eigener Entwurf oder gekaufte Datei von Tom).
- Nicht gebaut, weil unzuverlässig: direkte Verbindung App ↔ Drucker im WLAN (Tom: „zu wackelig“).

## STAND 17.11.2026, 12:45 Uhr – Gitarren-Miniatur (Einzelheiten zu Modell, Baubefehlen, Aufträgen)
- **Drucker:** nur Flashforge Creator 5 Pro (`c5pro`). Am echten Gerät ist weiterhin **nichts bestätigt**, auch von der Gitarre ist nichts gedruckt.
- **Laufendes Hauptvorhaben: Miniatur von Toms E-Gitarre** (T-Form, 24 Bünde, weinrot gewolkte Decke, graue Zarge). Tom: „Details sind absolute Priorität“, Druckzeit egal,
  alles mit 0,25-mm-Düse, alles Machbare auch grenzwertig. Modell: `modelle/gitarre_rundum.py` + `modelle/gitarre_rundum_daten.json` (Arbeitsweise: CLAUDE.md → „Detailgetreue Miniatur …“).
- **Gültige Aufträge** (Köpfe 1 grau · 2 weinrot · 3 schwarz · 4 silber; für Kopf 2 bestellt Tom „Bordeaux“ bei Filamentor, 17.11.; dazu PLA matt grau/schwarz, PLA Silber (kein Silk), PETG als Stütze für PLA):
  - `2026-11-17_gitarre370_korpus_c5pro` – 15 h 19 min; grau 62,9 / weinrot 8,0 / schwarz 16,0 / silber 1,3 g (braucht seit 17.11. auch Kopf 4 für die Buchsenhülse)
  - `2026-11-16_gitarre370_hals_c5pro` – 10 h 24 min, mit Kegellöchern für die Wirbel
  - `2026-11-16_gitarre370_wirbel_c5pro` (47 min, nur Kopf 3) · `2026-11-16_gitarre370_klappe_c5pro` (6 min, nur Kopf 3: Deckel + Lochkugeln)
  - `2026-11-17_gitarre160_c5pro` – Vergleichsstück 160 mm einteilig, 5 h 17 min, **seit 17.11. 07 Uhr mit Steckwirbeln** (Tom will Schnur als Saite spannen)
  - `2026-11-17_gitarre160_einfarbig_c5pro` – Probedruck für den ersten Tag: alle Farben vereint, Kopf 1 PLA grau, **0,4-mm-Serien-Düse**, 0.12, 51 min, 15 g (Drucker kommt 17.11.)
  - `2026-11-17_gitarre160_wirbel_c5pro` – acht kleine Steckwirbel, 25 min, 0,6 g, nur Kopf 3. Klein-Modus im Skript (`KLEIN`, greift, wenn das Gehäuse zu dünn ist):
    Kegelloch 2,08 → 1,45 mm (Wand im Gehäuse 0,45), Rändelrad Ø 4,1, Wirbel 2/4/6 mit 2,8 mm längerem Schaft (Räder auf zwei Ebenen, Mechaniken nur 3,3 mm auseinander),
    Saitenstift Ø 1,27 / 2,6 mm hoch, Querloch 0,5. Gedacht für Schnur bis ~0,3 mm (z. B. Angelschnur), Knoten hinten am Korpusloch Ø 0,72. Passung und Festigkeit ungedruckt.
  - App-Link: `https://tom444555.github.io/druckwerk/#hinzu=2026-11-17_gitarre370_korpus_c5pro,2026-11-16_gitarre370_hals_c5pro,2026-11-16_gitarre370_wirbel_c5pro,2026-11-16_gitarre370_klappe_c5pro,2026-11-17_gitarre160_c5pro,2026-11-17_gitarre160_wirbel_c5pro`
  - Veraltet (auf Toms Wort löschen): `2026-11-16_gitarre_rundum_c5pro` (200 mm, alter Fünf-Farben-Stand).
- **Neu bauen** (je ~20 s, STL liegen nicht im Lager):
  370: `python3 modelle/gitarre_rundum.py --laenge 370 --teilen 1 --wolken 4 --wirbel 1 --klappe 1 --ziel /tmp/gp` · 160: `… --laenge 160 --wolken 4 --wirbel 1 --ziel /tmp/gq` (Wirbel slicen: Kopf 3, infill 100, `--waende 4 --stuetzen aus --brim an`)
  Slicen: `druck.py --drucker c5pro --duese 0.25 --schicht 0.08 --infill 12 (160: 15) --stuetzen auto --zusammen --farben "grau,weinrot,schwarz,silber"` + Extras aus CLAUDE.md
  („Maximale Details mit 0,25-mm-Düse“, dazu `inner_wall_speed=60`). Prüfung: `M140 S55` (erste Schicht) und `S60`.
- **Stand der Details (alles nach Toms Fotos von schecter-guitars.de):** Decke = 0,16 mm Weinrot-Haut über schwarzem Muster (`--haut`), schwarzer Deckenrand; Armschräge Bassseite
  unterer Bogen (`--armschraege`; Toms Ansage, nicht anders deuten); Kopfplatte 10° geneigt (geschätzt); Ziffern in gebrochener Schrift, Bünde silber; Tonabnehmer versenkt in schwarz
  ausgekleideter Fräsung; Schalterhebel mittig; Brücke, Regler; Gurtknopf am Korpusende mittig; Deckel hinten mit zwei Schrauben; **Rippen-Ausfräsung kantig aus vier Ebenen**
  (Bassseite, Raute an der Taille, Tiefe `dR` = 0,5 × Korpusdicke – geschätzt); **Klinkenbuchse**: Linsenplatte, folgt der Zargenrundung und liegt rundum auf (Toms Korrektur 17.11.),
  Schale, Sechskantmutter, silberne Hülse. 370 mm: Hals steckbar (Zapfen, Spiel 0,12), drehbare Steckwirbel, Saitenfach hinten mit Klappe für echte Saiten. Kein Schriftzug/Markenname.
- **Offen bei Tom:** Druckergebnisse (Passung Zapfen/Wirbel/Klappe, scheint Schwarz durch die Weinrot-Haut?, Stützfläche der Ausfräsung); Ausfräsung tiefer/flacher?; Kopfplatte flacher (6°)?;
  Polschrauben als Innensechskant bei 370 mm (angeboten); später kleinere Maßstäbe. Außerdem weiter offen: Foto-Scan-ZIP aus Meshroom (Zielgröße erfragen), Auswahl Text-zu-Bild-Vorschläge.
- App: `sw.js` steht auf `druckwerk-v11`. Alles Übrige (App, Werkzeuge, Regeln) unverändert wie im Block darunter.

## Stand 16.11.2026 (Verlauf, nur bei Bedarf lesen)
- **Drucker:** nur Flashforge Creator 5 Pro (`c5pro`). **Am echten Gerät ist weiterhin nichts bestätigt** (Werte aus Profilen, Wiki, Tests, Videos; Spiele nur gerechnet).
- **Lager:** `2026-11-14_stratocaster_c5pro`, `2026-11-14_loopsmiths_amp_c5pro`, `2026-11-15_vox_plektrumhalter_c5pro` (3 h 38 min, 73 g, schwarz/rot/weiß),
  Kalibrier-Set `2026-11-14_kalibrier_1…5_c5pro`. Keine `_kobrax`-Aufträge mehr.
- **App:** sieben Reiter Start · Aufträge · Neu · Bibliothek · Material · Drucker · **Workflow** („Von der Idee zum Modell“; Tom fand die Seite unter „So geht's“ nicht →
  wieder eigener Reiter). `sw.js` steht auf `druckwerk-v9` (bei jeder App-Änderung hochzählen). Startseite mit „Nächster Schritt“ und Suche, gedruckt-Haken, Sicherung,
  Offline/PWA, KI-Ablauf in 6 Schritten (`kiweg.js`, Schritt 4 jetzt mit A fal.ai · B MakerLab · C „Bei Claude im Chat“), „Videos ausgewertet“ (`videos/`, vier Auswertungen).
- **Links zu Claude:** `https://claude.ai/code/new?repo=Tom444555%2Fdruckwerk&q=<Text>` (die alte Form `claude.ai/new?q=` tat am iPhone/iPad nichts; laut Anthropic-Hilfe
  reagiert die App nur auf `claude.ai/code…`). Beim Antippen wird der Text zusätzlich kopiert (Sammel-Handler in `index.html`). **Tom hat noch nicht bestätigt, ob es jetzt geht** –
  er soll auch sagen, ob er Druckwerk in Safari, als Home-Symbol oder in der Claude-App öffnet.
- **Modell-Quellen:** Liste in der App (Workflow → Werkzeuge → vier Gruppen „Modelle finden …“). Von hier NICHT abrufbar: Printables, Thingiverse, MakerWorld, Cults3D,
  MyMiniFactory, GrabCAD → Tom lädt und hängt die Datei an. Direkt nutzbar: GitHub (BOSL2, NopSCADlib, Gridfinity Rebuilt), Objaverse, Poly Haven; Thangs/Sketchfab nur Suche.
- **Lizenz-Regel (neu):** Repo ist öffentlich → Modelle mit „Standard Digital File License“, ND-Lizenz oder Kaufmodelle nicht einchecken (nur .gcode per Chat schicken).
  **Offen, Tom entscheidet:** Lizenz des Vox-Plektrumhalters (MakerWorld 1485935) ansehen; steht dort diese Lizenz, Ordner auf sein Wort aus dem Repo nehmen.
- **Gratis-KI im Chat (neu):** `python3 werkzeug/ki_lokal.py bild.png --name n --ziel-mm 120 --aus /tmp/n` – TripoSR ohne Grafikkarte, Einrichten ~2 Min., dann ~2 Min. je Bild
  inkl. `ki_rohling.py`. Grob (Entwurf, kompakte Figuren; dünne Teile fehlen). Getestet mit zwei Beispielbildern des Modells, **nichts gedruckt, noch kein Foto von Tom**.
  TRELLIS.2/Hunyuan/Rodin/Meshy laufen hier nicht (GPU nötig) → dafür weiter fal.ai (Schlüssel fehlt), MakerLab oder Meshy.
- **fal.ai-Code gegengeprüft (15.11. nachmittags):** `werkzeug/generieren.py` stimmt mit der aktuellen fal-Doku überein (Endpunkte, Feldnamen, Rodin-Stufen, Ausgabefelder,
  fal-client 1.0.3 ist aktuell). Einzige Unklarheit: TRELLIS.2 `resolution` als Zahl oder Text → bei 422 jetzt automatisch zweiter Versuch als Text. Echter Lauf weiter ungetestet.
- **Videos (neu):** My Engines DE „Technische Filamente“ (PA12-CF, PC-PBT-CF, ASA-CF mit wenig Verzug; PETG außen + TPU innen hält; Stützen bei Faser-Material kaum lösbar →
  stützfrei konstruieren) und Der Druckt Schon Wieder „Meshy 3D Agent“ (bemalte 3MF mit ≤ 4 Farben → `druck.py --bemalt`, ungetestet). Lehren stehen in CLAUDE.md
  („Lehren aus Videos zum Creator 5 Pro“), `wissen/filamente.json`, `wissen/c5pro.json`, `wissen/workflow.json`, `werkzeug/KI_MODELLE.md`.
- **Qualität:** `werkzeug/QUALITAET.md` (Pflicht-Schleife bauen → pruefen.py → ansichten.py ansehen → korrigieren), `profi.py`, Muster `modelle/profi/`. KI-Modelle: `ki_rohling.py`,
  `textur_farben.py` (Weg A bemalte 3MF, Weg B Farbkörper), `foto.py`, `werkzeug/KI_MODELLE.md`. Recherche: `wissen/recherche_modellqualitaet.md`.
- **Getestet:** App mit Playwright (320/390/820 px), alle neuen Seiten `scrollWidth` = Fensterbreite; Profi-Teile 0 Fehler; Farbwege A und B mit Orca-CLI; `ki_lokal.py` Ende zu Ende.
  **Nicht getestet:** alles am Drucker, Claude-Links und Offline-Speicher am echten iPhone/iPad, echter fal-Aufruf, bemalte Meshy-3MF, MakerLab.
- **Slicer-Lücken geschlossen (15.11. 15:30 Uhr, alles nur mit Orca-CLI/Playwright geprüft, nichts gedruckt):** gemischte Düsen `druck.py --duesen 0.4,0.25`;
  Vorschaubild 140×110 in der .gcode (Anzeige am Creator 5 Pro unbestätigt; alte Aufträge erst nach neuem Slicen); bemalte 3MF skalieren/drehen
  (`--groesse`, `--skala`, `--matrix`); bemalte 3MF aus der Werkstatt slicen (App hebt Original auf, `eingang.py` → `--bemalt`). In der App gibt es für gemischte Düsen noch keinen Schalter.
- **Raue Oberfläche / Fuzzy Skin (15.11. 18:45 Uhr):** Video von Bastlwastl ausgewertet (`videos/fuzzy-skin-bastlwastl.html`); `druck.py --rau fein|mittel|grob`
  (+ `--rau-wo`), `eingang.py` nimmt `rau`, Werkstatt-Slicen hat die Zeile „Oberfläche“. Gemessen: „mittel“ trägt je Seite 0,30 mm auf. Nichts gedruckt.
  Mögliche nächste Schritte: Testraster als Kalibrier-Teil 6, gezieltes Bemalen, Muster als Relief.
- **Text zu Bild (15.11. 20:45 Uhr):** Vorschlag 1/5/6 als Chat-Werkzeug gebaut: `werkzeug/bild_ki.py` (Entwürfe gratis, freistellen, Ampel, Übersicht; Test „Eule“ gut).
  In der App noch nichts; Schlüssel-Wege (fal, Pollinations-Schlüssel) im Skript vorbereitet, aber ungetestet. Rest der Recherche: `wissen/recherche_text_zu_bild.md` mit acht Vorschlägen; Test: Pollinations liefert von der
  Sitzung aus gratis Entwurfsbilder (768 px, Wasserzeichen). Tom wählt noch aus; empfohlen 1 (Entwurf gratis im Chat), 4 (Bild-Text schärfen), dann 2 + 3 mit `FAL_KEY`.
- **Gitarre rot-schwarz (15.11. 22:15 Uhr, wartet auf Tom):** eigener Entwurf in der Optik von Toms Gitarre, `modelle/gitarre_rotschwarz.py` → vier STL (schwarz/rot/gold/weiß), 200 mm,
  liegt flach, keine Stützen. `pruefen.py`: alle dicht; bleibende Meldungen sind gewollt (Einlagen 0,6–1 mm dick, einzelne rote Stege < 0,45 mm → beim Slicen Arachne-Zusätze nehmen).
  Vorschau an Tom geschickt, **noch nicht gesliced** – wartet auf sein Ja bzw. Wünsche (`--saat`, `--schwarz`, `--laenge`). Text-zu-Bild taugt für so ein Motiv nicht (getestet).
  Die STL liegen nicht im Lager: neu bauen mit `python3 modelle/gitarre_rotschwarz.py --ziel /tmp/git --bild /tmp/git/v.png` (Sekunden). Bauweise und Netz-Lehren: CLAUDE.md
  → „Mehrfarbige Teile aus 2D-Umrissen“.
- **Gitarre rundum (16.11. mittags, wartet auf Toms Ja zum Slicen):** Tom schickte 14 Bildschirmfotos eines 3D-Modells seiner Gitarre (T-Form, 24 Bünde, rot gewolkte Decke,
  graue Zarge) und ein Maßblatt (Mensur 648, Sattel 42, Halsdicke 20/22, Korpus ca. 400 × 320 × 45, Saitenabstand 10,5) mit „so präzise wie möglich“. Neu: `modelle/gitarre_rundum.py`
  + `modelle/gitarre_rundum_daten.json` (Umriss, Wolkung, Lage der Teile aus der geraden Vorderansicht vermessen; Perspektive über die 24 Bundabstände herausgerechnet, 1 px Restfehler).
  Rundum-Modell 200 mm: echte Korpusdicke, Halsprofil mit Fuß, um 10° geneigte Kopfplatte, Mechaniken, Brücke, Tonabnehmer mit roten Streifen, Regler, Schalter, Buchse, Gurtknöpfe,
  Rückseite mit Deckel, Saitenhülsen, Bauch-Ausfräsung, rote Halsstreifen; römische Ziffern bis XXI. Farben grau/rot/schwarz/weiß (Grau statt Gold, wie am Original). Kein Schriftzug, keine Saiten.
  Bauen: `python3 modelle/gitarre_rundum.py --ziel /tmp/g1 [--wolken 0|1|2] [--bauch 0] [--laenge 200]` (2 s). Vier STL dicht, Schnittvolumen 0. `pruefen.py` meldet gewollte
  Kleinteile (Einlagen < 1 mm³, Stege um 0,45 mm) → Arachne-Zusätze; Hals und Kopf schweben → Stützen `auto`. **Nur gerechnet, nichts gesliced/gedruckt.** Die flache Fassung
  (`gitarre_rotschwarz.py`) ist damit vermutlich überholt – Tom fragen.
  Nachtrag 13:15 Uhr: Tom schickte drei Vergleichsdateien (CAD einer T-Form mit Fender-Hals als STEP, eine S-Form als STL, ein Fender-Griffbrett als STL – alles andere
  Gitarren, Lizenz unbekannt → **nicht im Lager**, nur zum Abgleich benutzt). Ergebnis: der aus dem Foto vermessene Umriss deckt sich mit der CAD-T-Form auf wenige mm; echte
  Unterschiede nur am Cutaway/Horn (bei Toms Gitarre tiefer und kürzer). Übernommen: Korpusbreite 320 mm (`--breite`), Umriss stärker geglättet, Foto-Nase am Gurtknopf weg.
  Nachtrag 13:25 Uhr: nach Toms Nahaufnahme der Decke Muster wolkiger und zerklüfteter (`--wolken 1` = 38 % dunkel, wie Nahaufnahme; `2` = ruhiger; `0` = ohne),
  Klingenschalter mit zwei Schrauben und schrägem Hebel, Regler unten glatt mit vier Rillen oben. Vorschau 3 an Tom.
  **Gesliced 13:30 Uhr auf Toms Ja:** Auftrag `2026-11-16_gitarre_rundum_c5pro` – 2 h 09 min, 31 g (grau 19,3 · rot 4,1 · schwarz 7,6 · weiß 0,2), Schicht 0.12, Füllung 15 %,
  Stützen auto (nur unter Hals, Kopfplatte, Bauch-Ausfräsung, Gurtknopf; über der Decke keine – Regler-Rillen dafür unten 45° angeschrägt, Hebel steiler), Arachne-Zusätze,
  143 Kopfwechsel, Köpfe 1 grau · 2 rot · 3 schwarz · 4 weiß. In den Schichten geprüft: Ziffern III–XVII lesbar, XIX/XXI nur als Punkte. **Nicht gedruckt.**
  Nachtrag 13:40 Uhr: Ziffern auf Toms Wunsch „genauso“ wie am Griffbrett – gebrochene Schrift (dicker/dünner Strich, Rauten an den Enden), jetzt alle zehn inkl. XIX, XXI, XXIV;
  neu gesliced (gleicher Ordner, 2 h 09 min). Mit 0,4-mm-Düse zeigt die Schrift ihren Charakter nur bis etwa XII, XIX–XXIV werden kleine Kleckse (Feld nur 2 mm hoch).
  Feiner geht es mit `--strich 0.28` + `druck.py --duesen 0.4,0.4,0.4,0.25` (0,25-mm-Düse am weißen Kopf) oder größer (`--laenge 240`) – Tom angeboten, Antwort offen.
  **Stand 14:00 Uhr – gilt:** Tom druckt mit **0,25-mm-Düse** („stimm alles darauf ab, so detailreich wie möglich“; angenommen: alle vier Köpfe – er sprach von „einer“ Düse,
  Rückfrage gestellt). `gitarre_rundum.py --duese 0.25` ist jetzt Standard (`--duese 0.4` = alte Fassung): Ziffern als fette gebrochene Schrift nach Toms Nahaufnahme der „III“
  (schräg geschnittene Balken mit Zacken, Tabelle `GLYPH`), dünnster Strich 0,28 mm, feinere Wolkung, schmaler schwarzer Rand um die Decke, schmalerer Kopfplatten-Rand.
  Auftrag `2026-11-16_gitarre_rundum_c5pro` neu: `druck.py --duese 0.25 --schicht 0.08` + Arachne-Zusätze → **5 h 49 min, 34 g** (grau 19,7 · rot 5,0 · schwarz 8,7 · weiß 0,35),
  165 Schichten, 213 Kopfwechsel, keine Stützen über der Decke; in den Bahnen sind alle zehn Ziffern einzeln angelegt (XIX–XXIV nur etwa 1 mm hoch). **Nicht gedruckt.**
  **Stand 14:20 Uhr – gilt:** Details nach vier weiteren Nahaufnahmen: Regler (glatter Fuß, drei Ringe, Kappe mit Fase, Madenschraube), Klingenschalter (zwei Schrauben,
  grauer Schaft, schwarze Kegelkappe, 66° geneigt), Brücke (Grundplatte, Rückwand, sechs U-Reiter mit Langloch, Federn, Madenschrauben, sechs Schraubenköpfe hinten).
  Neu gesliced mit `--extra support_on_build_plate_only=1` (sonst setzt der Slicer Stützen an den Schalterhebel): **5 h 56 min, 34 g**, 223 Kopfwechsel. Nicht gedruckt.
  **Stand 14:45 Uhr – gilt:** Tom fand das schwarze Muster unpassend und will „probieren, was maximal möglich ist“ → **fünf Farben**: Wolken als eigener Körper
  `…_dunkelrot.stl` (feine Wolkung `--wolken 3`, Standard), beim Slicen zusammen mit Weiß auf Kopf 4; nach dem Slicen `M25` bei Z 9,3 eingefügt (Kopf 4 druckt bis 9,22 Dunkelrot,
  Weiß erst ab 10,82) – das Einfügen ist Handarbeit per Python nach `druck.py`, noch kein Schalter. Deckenrand wieder rot. **Saiten zum Einfädeln** (Tom: passt): Löcher Ø 0,72 mm
  durch Korpus und Kopfplatte, Kerben in Reitern und Sattel. Auftrag neu: **6 h 26 min, 35 g**, 231 Kopfwechsel. `dunkelrot` als Farbname in `druck.py` und App (sw.js v10).
  Offen: ob `M25` am Creator 5 Pro den Spulenwechsel erlaubt, ob Tom Dunkelrot hat, Düsen-Frage (alle Köpfe 0,25?). Nicht gedruckt.
  **Stand 15:30 Uhr – gilt (Toms Ansage: alles 0,25 mm, 370 mm, zweiteilig, „alles Machbare, auch grenzwertig“, Druckzeit egal; später auch kleiner):**
  `python3 modelle/gitarre_rundum.py --laenge 370 --teilen 1 --wolken 4 --ziel /tmp/g6` → `…_korpus_<farbe>.stl` und `…_hals_<farbe>.stl` (Hals 45° gedreht, 251 mm lang).
  Teilung: Hals mit **durchgehendem Zapfen** (Griffbrettbreite, bis hinter den 24. Bund, volle Korpusdicke – steht auf dem Bett), Korpus mit Schlitz, `--spiel 0.12` je Seite
  (ungedruckt). Neu im Modell: Armschräge (`--armschraege 0.33`, weiche Verformung aller Farben per `warp_batch`; Linie A1/A2 geschätzt, nicht aus den Fotos vermessen),
  Wolken auf der Kopfplatte (Rauschen, keine Foto-Vorlage), feinste Foto-Wolkung `--wolken 4`, Bünde in echter Breite mit Krone, höherer Sattel, Sechskant-Muttern,
  Tonabnehmer-Schrauben, Kreuzschlitze, mehr Feder-Windungen, vier Deckel-Schrauben, rote Streifen über Halsfuß und Zapfen.
  Aufträge: `2026-11-16_gitarre370_korpus_c5pro` (14 h 19 min, 83 g, Kopf 4 nur Dunkelrot) und `2026-11-16_gitarre370_hals_c5pro` (11 h 42 min, 61 g, Pause bei 17,62 mm:
  Kopf 4 Dunkelrot → Weiß). Einstellungen für maximale Details stehen in beiden BERICHT.md. Pause setzt jetzt `werkzeug/spulenwechsel.py <gcode> --kopf 4`.
  Bekannt: `korpus_rot.stl` hat 12 offene Kanten, `hals_grau.stl` zwei doppelt belegte Kanten (Slicer kam damit klar). Der 200-mm-Auftrag `…_gitarre_rundum_c5pro` bleibt
  auf dem Stand von 14:45 Uhr (ohne die neuen Details) – für „kleiner“ neu bauen mit `--laenge 200` bzw. `--laenge 250` (einteilig bis ~250 mm). **Nichts gedruckt.**
  Dazu als Vergleichsstück `2026-11-16_gitarre160_c5pro` (einteilig 160 mm, gleiche Details und Einstellungen, 5 h 38 min, 26 g, Pause bei 7,7 mm). Tom will später
  den Unterschied zwischen 160 und 370 mm sehen → nach den Drucken fragen, welche Details bei 160 mm noch herauskommen.
  **Stand 16:15 Uhr – gilt und ersetzt die Farbangaben darüber:** Tom will die Decke in **dunklem Weinrot** (besorgt das Filament) mit dem **schwarzen Muster darunter**
  und Bünde/Ziffern in **Silber/Hellgrau**. `--decke unter` (Standard; `einlage` = alte Fünf-Farben-Fassung mit Dunkelrot), `--haut 0.16` = Dicke der Weinrot-Haut über dem
  Muster im Druck. Wieder schmaler schwarzer Deckenrand; ovale Buchsenplatte mit zwei Schrauben (nach Toms Fotos). Nur noch vier Köpfe, **kein Spulenwechsel**:
  1 Grau · 2 Weinrot · 3 Schwarz · 4 Silber. Alle drei Aufträge neu: `…gitarre370_korpus` 14 h 01 min, 83 g (Köpfe 1–3) · `…gitarre370_hals` 10 h 23 min, 54 g ·
  `…gitarre160` 4 h 57 min, 23 g. Ob das Schwarz durch 0,16 mm Weinrot sichtbar durchscheint, ist ungedruckt – nach dem ersten Druck `--haut` nachstellen.
  `weinrot` als Farbname in `druck.py` und App (sw.js v11). Der 200-mm-Auftrag `…_gitarre_rundum_c5pro` ist veraltet (Fünf-Farben-Stand 14:45 Uhr).
  **Abflachung geklärt (17:10 Uhr):** Tom: „oben hinten, quasi über den Knöpfen“ = Bassseite, unterer Bogen, hinten (Spielhaltung). Das ist die erste Lage
  (`--armschraege 0.33`, A1/A2 im Skript) und steckt in allen drei Aufträgen im Lager. Ein Zwischenversuch am oberen Bogen war falsch und ist zurückgenommen.
  Offen: ob Breite/Tiefe passen; Kopfplatten-Winkel 10° (geschätzt), evtl. flacher gewünscht.
  **Steckwirbel (17:40 Uhr):** Tom will die Saiten wirklich spannen → `--wirbel 1`: Kegellöcher (Druck 2,70 → 2,10 mm) durch Kopfplatte und Gehäuse statt fester Achsen,
  dazu `…_wirbel.stl` (acht Wirbel: Rändelrad hinten, Kegel 2,84 → 2,16, Stift 1,96 mit Querloch 0,76). Reibschluss wie Geigenwirbel, kein Getriebe; Flügel bleiben Attrappe.
  Aufträge: `…gitarre370_hals` neu (10 h 24 min, mit Kegellöchern) und `…gitarre370_wirbel` (47 min, 1,6 g, nur Kopf 3). Passung ungedruckt – nach dem Druck Sitz erfragen
  (zu tief/zu lose → `WR_H`/`WR_V` bzw. Übermaß 0,05 im Skript). Für 160 mm nicht machbar (Stift unter 1 mm). `druck.py` kann jetzt Aufträge, die Kopf 1 nicht benutzen.
  **Saitenfach (18:30 Uhr):** Tom will die Saiten im Korpus festmachen → `--klappe 1`: Mulde auf der Rückseite über den sechs Löchern (Druck 24,5 × 3,6 × 3,4 mm) mit Stufe
  für einen steckbaren Deckel (26,6 × 5,7 × 1,0, Spiel 0,08, Griffmulde) und `…_klappe.stl` (Deckel + zehn Lochkugeln 2,4 × 2,0, Loch 0,9). Ersetzt die schwarzen Hülsen.
  Aufträge: `…gitarre370_korpus` neu (14 h 04 min) und `…gitarre370_klappe` (6 min, 0,3 g, nur Kopf 3). Vollständiger Satz 370 mm: korpus, hals, wirbel, klappe.
  Baubefehl: `gitarre_rundum.py --laenge 370 --teilen 1 --wolken 4 --wirbel 1 --klappe 1`. 160 mm hat weder Wirbel noch Fach. Alles ungedruckt.
  **Stand 17.11. nachts:** nach Toms Fotos Tonabnehmer in Fräsungen versenkt (`PU_G` Spalt, `PU_T` Tiefe 12 mm echt) und niedriger (Oberkante T_B + 5,5 / 6,5 statt 9 / 10,5,
  Saiten bei etwa T_B + 11), Schalterhebel senkrecht in der Schlitzmitte. Neu gesliced, **neue Ordnernamen wegen Datum**: `2026-11-17_gitarre370_korpus_c5pro` (14 h 24 min)
  und `2026-11-17_gitarre160_c5pro` (4 h 58 min); Hals, Wirbel, Klappe bleiben `2026-11-16_…`. Offen/nicht umgesetzt aus den Fotos: Polschrauben als Innensechskant,
  Stoffband am Tonabnehmer. Alles ungedruckt.
  Nachtrag 17.11., 03:10 Uhr: Fräsungen der Tonabnehmer schwarz ausgekleidet (`futter`, Stärke `PU_W` = 0,5 mm im Druck), weil Tom das Grau der Wände störte; Korpus 370 (14 h 36 min) und 160 mm (5 h 00 min) neu, gleiche Ordner.
  Nachtrag 17.11., 03:30 Uhr: Gurtknopf am Korpusende genau auf der Mittellinie (vorher am nächstgelegenen Randpunkt, leicht versetzt), Deckel hinten mit zwei statt vier Schrauben (Foto der Rückseite); Korpus 370 (14 h 35 min) und 160 mm (5 h 01 min) neu, gleiche Ordner.
  Toms Angabe: die drei Vergleichsdateien stammen von GrabCAD und seien frei – sie liegen trotzdem nicht im Lager (nur verglichen). Mögliche nächste Wünsche: größer (bis ~240 mm),
  Saiten, schwarzer Rand um die Decke, Ständer dazu.
- **Grenze Text zu Bild (15.11. nachts):** `bild_ki.py` ohne Schlüssel taugt nur für freie Figuren (Eule gut). Technische/reale Gegenstände (Test: Pistole, Karabiner, Toms
  Gitarre) werden unbrauchbar, die Ampel merkt das nicht → Foto, fertiges Modell, Foto-Scan oder eigene Konstruktion.
- **Foto-Scan (16.11., Plan, noch nichts geliefert):** Tom probiert Photogrammetrie selbst: Canon 5D Mark IV + Softboxen, Windows-Laptop Gigabyte G5 KD (RTX 3060 6 GB, 16 GB RAM)
  mit **Meshroom** (gratis). Tipps an ihn: 60–80 Fotos in 2–3 Höhenringen, Blende 8–11, Belichtung/Weißabgleich fest, Objekt unbewegt, Glanz mit Polfilter oder Scan-Spray.
  Er schickt OBJ + Textur als ZIP → `ki_rohling.py` → Bild zeigen → `textur_farben.py` → slicen. **Mit echtem Foto-Scan ungetestet** (Netze sind groß und löchrig: erst
  verkleinern/schließen). Empfohlen: Scan als Maß- und Formvorlage, das Druckteil sauber konstruieren. Ablauf: CLAUDE.md → „Foto-Scans“.
- **Bekannte Lücken:** Stützen kommen vom aktiven Kopf;
  WLAN-Senden, Abgleich iPhone↔iPad, Auftrag ohne Chat offen (Vorschläge in `wissen/workflow.json`).
- **Toms Geschmack:** detailreich, geschwungen, naturnah, breit statt hoch; Farben schwarz/gold/rot/weiß; erst schnelle Vorschau, kurze Antworten. Will Modellqualität „wie Hyper3D“.
- **Nächste Schritte:** 1) Toms Rückmeldung zum Druck der Gitarre rundum (`2026-11-16_gitarre_rundum_c5pro`); die flache `gitarre_rotschwarz.py` ist nicht gesliced und wohl überholt. 2) Erstes Meshroom-ZIP von Tom verarbeiten. 3) Toms Auswahl aus
  den acht Text-zu-Bild-Vorschlägen. 4) Rückmeldung zu den Claude-Links am iPhone/iPad. 5) Vox-Lizenz klären. 6) `FAL_KEY` → erster echter KI-Lauf; erste Meshy-3MF durch `--bemalt`.
  7) Kalibrier-Set drucken → Spiele in `profi.py`/`baukasten.scad`, Herkunft „Gerät“; evtl. Fuzzy-Skin-Testraster als Teil 6. 8) Gitarrenhalter aus `modelle/profi/` slicen, wenn gewünscht.
- **Nachtrag 17.11., 05:40 Uhr:** Nach Toms Fotos (Rückseite, Buchse): Rippen-Ausfräsung jetzt kantig aus vier Ebenen (Bassseite, Schulter bis unterer Bogen, Raute an der Taille; Tiefe an der Taille 0,5 × Korpusdicke, `dR` in `gitarre_rundum.py`), statt der runden Mulde. Klinkenbuchse: Linsenplatte mit spitzen Enden, Schale, Sechskantmutter, **silberne Hülse → Korpus braucht jetzt auch Kopf 4 (silber)**. Korpus 370 neu: 15 h 19 min (grau 62,9 / weinrot 8,0 / schwarz 16,1 / silber 1,3 g); 160 mm neu: 5 h 18 min. Ordnernamen unverändert. Ausfräsung liegt auf Stützen (Unterseite) – Oberfläche dort am Gerät prüfen. Nichts gedruckt.
- **Nachtrag 17.11., 06:40 Uhr:** Buchsenplatte folgt jetzt der Rundung der Zarge und liegt rundum auf (Tom: die Kante im Foto war nur Schatten, Platte minimal erhöht); Korpus 370 und 160 mm neu gesliced (Zeiten praktisch gleich).

---
## Verlauf (älter)

**Stand 10.11.2026 – Stufe 1 (USB) fertig und getestet (Slicen, ohne echten Drucker)**
- OrcaSlicer v2.5.0 CLI + Herstellerprofile Kobra X / Creator 5 Pro laufen headless.
- `werkzeug/druck.py`: mehrere Teile/Farben, Material je Slot, Schicht/Infill/Wände/Stützen/Brim, Bericht.
- Testauftrag `auftraege/2026-11-10_testwuerfel_kobrax` und `_c5pro` für beide Drucker (2 Farben).

- App `index.html` (v1): Aufträge/3D-Vorschau/Download, Neu (Prompt-Baukasten), Drucker, USB.
  Live unter https://tom444555.github.io/druckwerk/ sobald Pages aktiviert ist (Settings → Pages → main / root).

**Offen**
1. Erster echter Druck nach Kauf: Testwürfel von USB drucken, Ergebnis notieren (Startcode/Spülen ok?).
2. Vorschaubild (Thumbnail) fürs Druckerdisplay fehlt headless.
3. Stufe 2: Senden per LAN über Heim-Brücke (Raspberry Pi/PC), siehe CLAUDE.md.
4. Eigene Filamente (Fremdmarken) als Profile ergänzen, sobald bekannt.

## 2026-11-10 – Realistische Hände (werkzeug/hand/)
- `hand_pose.py`: rechte Hand + Unterarm aus dem MakeHuman-Basismodell (CC0, raw.githubusercontent.com/makehumancommunity/makehuman: base.obj, rigs/default.mhskel, default_weights.mhw) per Skelett biegen (mcp/pip/dip, Daumen th1/th1s, Handgelenk gerade), Ausgabe STL + Gelenkpunkte (.json).
- `baue_hand.py`: Hand an „FTZ“ ausrichten (Griff-Spalt messen), Loop-Unterteilung ×3 + Taubin-Glättung, Adern/Sehnen als Verschiebung auf dem Handrücken, Unterarm im Sockel kappen, mit manifold3d von Schrift/Brett/Leiste/Sockel freischneiden.
- Pakete: trimesh manifold3d shapely networkx mapbox_earcut rtree (pip --break-system-packages). Fürs Beispiel siehe Auftrag ftz_hand_real.

## 2026-11-10 – Aufträge löschbar
- App: Knopf „Auftrag löschen“ (Detailansicht) mit Abfrage; GitHub-Zugang (Fine-grained-Token) einmalig, Verwaltung im Tab USB.
- Getestet mit Playwright + gemockter GitHub-API (390×844).
- Gelöscht: ftz_fritz, ftz_fritz_3d, ftz_hand, ftz_hand_real (Modelle in modelle/ bleiben erhalten).

## 2026-11-10 – App wie Looper: Aufträge pro Gerät
- Eigene Liste im Gerät (localStorage), neue Besucher starten leer; Speichern per Link `#hinzu=<ordner>` oder „Aus dem Lager hinzufügen“.
- Löschen nur lokal (kein Token mehr nötig, Token-Code entfernt).
- `druck.py --quelle URL` → Knopf „Original auf MakerWorld/Printables … öffnen“; Tab Neu: Liste „Modelle finden“.
- Getestet mit Playwright (390×844).

## 2026-11-10 – Vorschaubild
- druck.py erzeugt vorschau.png, auftrag.json Feld "vorschau"; App zeigt Bild sofort + Ladeanzeige in %, 3D ersetzt es danach. Bestehende Aufträge nachgerüstet.

## 2026-11-10 – Loopsmiths v2
- Lederhaut: werkzeug/loopsmiths_farben.py baut die Rundbox als 0,3-mm-Netz und prägt Narbung (Worley) ein; Ausschnitte über teil="korpus_aus", Anbauten "korpus_dazu".
- Korbgeflecht-Bespannung (schwarz Fäden + weiße Kissen), Band versenkt, Biese + Nähte auf Spule 4 (gold). Nur Kobra X, c5pro-Auftrag entfernt.
- v3: 8,8 cm breit (B84 T55 H48), 8 Fächer à 28 mm, 5 Regler; Maße für die Lederhaut liest loopsmiths_farben.py per echo aus der .scad.
- App-3D: teile_app (reduzierte STLs) + Bild bleibt, bis das 3D-Bild gezeichnet ist; bei WebGL-Absturz zurück zum Bild.

## 2026-11-11 – Betttemperatur-Fehler behoben + 3MF
- Ursache misslungener Druck: Orca-CLI nahm „Cool Plate“ → PLA-Bett 35 °C statt 60 °C. druck.py setzt jetzt default_bed_type/curr_bed_type aus drucker/*.json („platte“).
- Alle Aufträge neu gesliced (60 °C), zusätzlich 3MF-Projekt (--export-3mf) + App-Knopf.

## 2026-11-11 – Stratocaster (Toms STL)
- werkzeug/gitarre_farben.py: Ein-Körper-STL per Höhen-/Zonen-Schnitt in 4 Farbteile (korpus, weiss, hals, metall), Saiten als 0,5-mm-Stege neu, Maßstab über Ziel-Länge. Original in modelle/quelle/.
- Strat v2: Saiten abgestuft 0,6–0,3 mm (braucht --extra wall_generator=arachne, min_bead_width=70%, min_feature_size=20%, sonst fallen Stege < 0,45 mm weg), Rippenbogen hinten. druck.py: neue Option --extra schluessel=wert.
- Strat v3: Rippenbogen flacher (11,5 mm), Armauflage vorne als Schrägschnitt (Keil).
- Strat v4: Armauflage als tangentialer Kreisbogen (95 mm breit, 19 mm am Rand), Halsrücken als Halbellipse (C-Profil) mit Übergängen.

## 2026-11-11 – Gitarrenständer
- modelle/gitarrenstaender.scad: Hänge-Ständer für die 20-cm-Strat (Gabel 11,2 mm, Gabelhöhe aus sattel_h), einteilig, liegend gedruckt. Passung per Boolean geprüft (Gitarre liegt bei ca. +0,7 mm auf, sonst kollisionsfrei).
- staender_schleife.scad: Zopf-Ständer zweifarbig (schwarz/gold), Farbteile über Wrapper-Dateien *_schwarz/_gold.scad (include + teil=…). abstand=11, damit Halsplatte/Tremolo-Deckel frei bleiben.
- Weitere Ständer-Entwürfe: staender_baum.scad (Lebensbaum, Wurzel-Relief) und staender_note.scad (Sechzehntelnote, Wulst-Module für plastische Formen). Tom fand staender_schleife hässlich.

## 2026-11-11 – Umbau zur Werkstatt, Stufe 1 (Bibliothek, Werkstatt, Export)
- Neu: `werkstatt.js` (wird von index.html bei Bedarf geladen), Tab „Bibliothek“ (5 Tabs), Knopf „In der Werkstatt umbauen“ im Auftrag.
- Getestet mit Playwright 390×844 (Skalieren, Drehen, Spiegeln, Farbe, Export, Sichern, Import STL); exportierte 3MF mit
  OrcaSlicer-CLI gesliced → beide Spulen (T0/T1) genutzt, Netze wasserdicht.
- Fahrplan: 1b Schneiden/Zusammensetzen/Text · 2 Slice-Knopf (GitHub Actions) + Detail-Einstellungen + Schichtvorschau ·
  3 Filamentlager + Druckprotokoll · 4 „Mit Claude bauen“.
- staender_baum v2 (fein, 3 Farben): Äste rekursiv mit Blättern/Locken, Dicke je Generation; Ablauf: OpenSCAD -> STL je Farbe -> werkzeug/lose_teile.py (lose Splitter raus; Blätter nur, wenn sie Gold berühren) -> modelle/staender_baum_*.stl -> druck.py mit arachne-Extras, 0.12. Rendern dauert ca. 4 Min. Vorlagenbilder von Tom nur als Stil genutzt, nicht nachgezeichnet.

## 2026-11-11 – Stufe 2: Slicen aus der App
- `.github/workflows/slicen.yml` + `werkzeug/eingang.py`; auf GitHub echt getestet (Probe-Auftrag, ~1 Min., Push + Pages laufen).
- App: Slice-Blatt in der Werkstatt, Token-Einrichtung, Fortschritt/Warten, automatische Übernahme; `schichten.js` Schichtvorschau.
- Playwright-Test mit gemockter GitHub-API (390×844) ok. Offen: echter Durchlauf mit Toms Token am Handy.
## Lebensbaum-Ständer v3 (11.11.2026, naturnah)
- Toms Rückmeldung zu v2: „zu unrealistisch, Struktur passt nicht, Halter auch als Ast“. v3 = `werkzeug/baum_relief.py` (ersetzt staender_baum.scad):
  Baum wächst nach Regeln (da-Vinci-Regel für Astdicken, unregelmäßige Winkel, Zug nach oben/ins Freie), Äste als halbrunde Wülste
  mit Borkenfurchen, 192 Blätter mit Mittelrippe/Adern, Wurzeln hinten + auf der Fußplatte, Halter = Astgabel (runde Zinken, Maße wie bisher).
- `--saat N` ändert den Wuchs (Standard 5), `--nur-bild x.png` zeigt schnell ein Schattenbild ohne Netze.
- Die STL `modelle/staender_baum_*.stl` sind groß und werden nicht eingecheckt (Skript erzeugt sie in ~10 s); im Auftrag liegen sie.
- Slots: schwarz (Fuß), holz (Baum+Gabel), grün (Blätter), gold (Blume des Lebens). 6 h 09 min, 29/20/7/3 g. Passung per Schnittvolumen geprüft (0 mm³),
  Gitarre hängt ca. 1,5 mm tiefer als bei v2 (runde Zinken). Tom fand den Weg „richtig“ (Vorschau), Druck noch offen.
- **v4 (11.11., 11 Uhr):** Tom: „Verzweigung gut, mehr Richtung Lebensbaum, noch realistischere Strukturen, Farben zum Verstärker (müssen nicht echt sein)“.
  Stamm = 6 Stränge, die sich umeinander winden, unten zu Wurzeln und oben zu Ästen werden; Leitast = 2 gedrehte Stränge bis zur Gabel;
  Borke mehrstufig (Furchen + Platten), knorrige Äste, 460 kleinere V-förmig gefaltete Blätter, Raster 0,125 mm, Saat 17.
  Slots jetzt wie beim Verstärker: schwarz (Fuß), gold (Baum, Datei *_holz.stl), rot (Blätter), weiß (Blume des Lebens, Datei *_gold.stl). 7 h 40 min, 29/21/8/3 g.
  Achtung: Auftragsordner ist 138 MB groß (feine Netze) – bei weiteren Varianten alte Stände nicht zusätzlich aufheben.
- **v4 Farbtausch (11.11., 13:20):** auf Toms Wunsch Baum schwarz (Slot 1, zusammen mit Fuß), Blätter gold (Slot 2), Blume des Lebens rot (Slot 3). 6 h 53 min, 42/8/3 g. Geometrie unverändert.
- **v5 (12.11.2026):** Tom schickte ein Bild (breiter Lebensbaum, leuchtende Adern, Wurzelgeflecht): „baut zu weit nach oben, mehr diese Optik, extrem viele Details“.
  `baum_relief.py` neu: kurzer gedrehter, geschwungener Stamm (z 14–58), Krone als breite Kuppel mit flacher Unterkante (155 mm breit),
  Kurztriebe → 2045 kleine Blätter, feine Zweige (r 0,6–1,1) als goldene „Adern“ über dem Laub (3,4 mm hoch), breite Fußplatte (132 mm)
  mit goldenem Wurzelgeflecht, Blume des Lebens weiß. Dateien: staender_baum_{schwarz,gold,blatt,weiss}.stl, Saat 6.
  Slots: 1 schwarz, 2 gold, 3 rot, 4 weiß. 11 h 55 min, 60/11/14/3 g (resolution=0.06, sonst wird die .gcode > 100 MB und GitHub lehnt sie ab). Passung geprüft (0 mm³). Auftrag jetzt `2026-11-12_staender_baum_kobrax`
  (der Ordner vom 11.11. wurde ersetzt). Eigenentwurf in der Optik des Bildes, kein Nachbau des Motivs.

## 2026-11-14 – Material, Drucker, Workflow in der App
- Neu: `wissen.js` + `wissen/filamente.json`, `zubehoer.json`, `c5pro.json`, `workflow.json`; index.html: Navigation mit 6 Tabs, alte Funktionen `drucker()`/`hilfe()` entfernt,
  Standarddrucker im Tab Neu = c5pro, Knopf „Verbrauch vom Filamentlager abbuchen“ im Auftrag, 3MF-Knopf nennt Flash Studio.
- Quellen der Recherche stehen je Datei unter `quellen` (Flashforge-Seite/Wiki/PDFs, Notebookcheck, drucktipps3d, China-Gadgets, printer-hub, EU-Shop).
- Filament-Sollwerte kommen aus den Profilen `resources/profiles/Flashforge/filament/* @FF C5P.json` (Orca v2.5.0, inherits-Kette aufgelöst).
- Früherer Einstiegsblock (Stand 12.11.) ist im neuen Block oben aufgegangen.

## 2026-11-14 (Nachmittag) – Aufräumen und Ausbau
- Gelöscht: 8 Aufträge (Ständer ×4, Vox-Amp, Stratocaster 2, beide Testwürfel), danach die Kobra-Fassungen von Strat und Verstärker durch c5pro-Fassungen ersetzt.
- `druck.py`: `--duese`, mehr Vorschaufarben (creme, holz …). `drucker/c5pro.json`: `duesen`, Hinweis Kammer aus bei PLA.
- Zwei Helfer (opus) parallel: App (tagebuch.js, geführter Auftrag, Filament-Check) und Werkzeug (Baukasten, Kalibrier, cad.py, bild_relief.py).
- Wissen als Markdown ins Offline-Paket (`offline-paket/werkzeuge/druckwissen_bauen.py`).

## 2026-11-15 – Programm-Durchsicht, Qualitäts-Werkzeuge, KI-Weg
- Fünf Helfer (opus): Recherche Modellqualität · App-Prüfung mit Umsetzung · Profi-CAD · KI-Rohling/Textur/Foto · KI-Erzeugung über Action + App · zwei Video-Auswertungen mit KI-Ablauf.
- Vox-Plektrumhalter für c5pro neu gesliced (Einstellungen aus der Historie von b2f109f^).
- CLAUDE.md um die Abschnitte „Qualität: technische Teile“ und „Qualität: Figuren und freie Formen über KI“ ergänzt.

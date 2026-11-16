# Übergabe druckwerk

## STAND 16.11.2026 – hier einsteigen (neuer Chat: „druckwerk: …“)
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
- **Grenze Text zu Bild (15.11. nachts):** `bild_ki.py` ohne Schlüssel taugt nur für freie Figuren (Eule gut). Technische/reale Gegenstände (Test: Pistole, Karabiner, Toms
  Gitarre) werden unbrauchbar, die Ampel merkt das nicht → Foto, fertiges Modell, Foto-Scan oder eigene Konstruktion.
- **Foto-Scan (16.11., Plan, noch nichts geliefert):** Tom probiert Photogrammetrie selbst: Canon 5D Mark IV + Softboxen, Windows-Laptop Gigabyte G5 KD (RTX 3060 6 GB, 16 GB RAM)
  mit **Meshroom** (gratis). Tipps an ihn: 60–80 Fotos in 2–3 Höhenringen, Blende 8–11, Belichtung/Weißabgleich fest, Objekt unbewegt, Glanz mit Polfilter oder Scan-Spray.
  Er schickt OBJ + Textur als ZIP → `ki_rohling.py` → Bild zeigen → `textur_farben.py` → slicen. **Mit echtem Foto-Scan ungetestet** (Netze sind groß und löchrig: erst
  verkleinern/schließen). Empfohlen: Scan als Maß- und Formvorlage, das Druckteil sauber konstruieren. Ablauf: CLAUDE.md → „Foto-Scans“.
- **Bekannte Lücken:** Stützen kommen vom aktiven Kopf;
  WLAN-Senden, Abgleich iPhone↔iPad, Auftrag ohne Chat offen (Vorschläge in `wissen/workflow.json`).
- **Toms Geschmack:** detailreich, geschwungen, naturnah, breit statt hoch; Farben schwarz/gold/rot/weiß; erst schnelle Vorschau, kurze Antworten. Will Modellqualität „wie Hyper3D“.
- **Nächste Schritte:** 1) Toms Ja/Wünsche zur Gitarre rot-schwarz → slicen (Schicht 0.12, Arachne-Zusätze). 2) Erstes Meshroom-ZIP von Tom verarbeiten. 3) Toms Auswahl aus
  den acht Text-zu-Bild-Vorschlägen. 4) Rückmeldung zu den Claude-Links am iPhone/iPad. 5) Vox-Lizenz klären. 6) `FAL_KEY` → erster echter KI-Lauf; erste Meshy-3MF durch `--bemalt`.
  7) Kalibrier-Set drucken → Spiele in `profi.py`/`baukasten.scad`, Herkunft „Gerät“; evtl. Fuzzy-Skin-Testraster als Teil 6. 8) Gitarrenhalter aus `modelle/profi/` slicen, wenn gewünscht.

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

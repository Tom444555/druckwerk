# Übergabe druckwerk

## STAND 12.11.2026 – hier einsteigen (neuer Chat: „druckwerk: …“)
- **Läuft:** Slicen für Kobra X (Tom druckt selbst, PLA, strukturierte PEI-Platte, Bett 60 °C wird geprüft), App mit Bibliothek/Werkstatt/Slice-Knopf (zweiter Chat), Aufträge pro Gerät.
- **Gitarren-Reihe (zusammengehörig, Farben schwarz/gold/rot/weiß):**
  - `2026-11-10_loopsmiths_amp_kobrax` – Verstärker-Plektrumhalter, 8,8 cm.
  - `2026-11-11_stratocaster_kobrax` – Strat 20 cm, 4 Farben (`werkzeug/gitarre_farben.py`).
  - `2026-11-12_staender_baum_kobrax` – Hänge-Ständer „Lebensbaum“ v5 (`werkzeug/baum_relief.py`), 11 h 55 min. **Noch nicht gedruckt, Tom hat v5 noch nicht bewertet.**
  - Ältere Ständer im Lager: `…_gitarrenstaender` (schlicht), `…_staender_note`, `…_staender_schleife` (von Tom abgelehnt – kann gelöscht werden, nur auf Wunsch).
- **Toms Geschmack (aus den Rückmeldungen):** detailreich, geschwungen, naturnah/realistisch, nichts Schlichtes oder Symmetrisch-Künstliches; breite statt hohe Formen;
  schickt gern Fotos als Vorlage; will schnelle Vorschau und kurze Antworten.
- **Nächste Schritte:** 1) Rückmeldung zu v5 abwarten (mögliche Wünsche: anderer Wuchs = `--saat`, Farbtausch = nur neu slicen, weniger Druckzeit = Laub/Schicht gröber).
  2) Erster echter Druck des Ständers: prüfen, ob Blattadern/Borke bei 0,4-mm-Düse sichtbar sind und ob die Gitarre in der Astgabel sitzt. 3) Repo ist durch große Aufträge gewachsen –
  bei Gelegenheit alte Ständer-Aufträge löschen (nur auf Toms Wunsch).
- **Arbeitsregeln/Erfahrungen:** stehen in CLAUDE.md, Abschnitt „Organische/feine Modelle“. Abschnitte unten nur bei Bedarf lesen.

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

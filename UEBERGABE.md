# Übergabe druckwerk

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

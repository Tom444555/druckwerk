# Technik-Baukasten (`baukasten.scad`)

Einbinden aus `modelle/`: `use <baukasten/baukasten.scad>` · Vorschau aller Teile: `beispiel.scad` (ca. 230 × 95 mm, flach, ohne Stützen).

**Regeln:** Loch-Module sind Körper zum *Abziehen* (`difference(){ teil(); translate(...) loch_…(); }`); Bauteil-Oberfläche bei z = 0, Loch geht nach −z
(Ausnahme Schlüsselloch: Rückseite bei z = 0). Spiel global 0,2 mm; mit `use` pro Aufruf `spiel=…` übergeben, mit `include` einfach `spiel = 0.3;` setzen.
Runde Löcher sind umschriebene Vielecke (drucken nicht zu eng). Alle Module am 14.11.2026 mit OpenSCAD 2021.01 gerendert, jede STL wasserdicht (trimesh).

| Baustein | Aufruf | Maße / Annahmen | Druckhinweis |
|---|---|---|---|
| Durchgangsloch | `loch_durchgang(m=3, tiefe=10)` | ISO 273 mittel (M3 3,4 · M4 4,5 · M5 5,5 · M6 6,6 · M8 9,0) + Spiel | senkrecht drucken = rund; liegend leicht oval |
| Senkkopf | `loch_senkkopf(m=4, tiefe=10, versenkt=0.2)` | DIN 7991 / ISO 10642, 90°, Kopf-Ø + 2·Spiel | Senkung oben → keine Stützen |
| Zylinderkopf | `loch_zylinderkopf(m=4, tiefe=10)` | DIN 912, Senkung Kopf-Ø + 0,8 + Spiel, Tiefe M + 0,4 | Senkung oben drucken |
| Einschmelzmutter | `loch_einschmelz(m=3)` | Ruthex-Kurzform: M3 Ø4,0×5,7 · M4 Ø5,6×8,1 · M5 Ø6,4×9,5, +1 mm Luft, Fase 0,6 | kein Spiel (Presssitz); ≥ 1,6 mm Wand drumherum |
| Mutterntasche | `mutterntasche(m=4, tasche_tief=3, seitlich=10)` | ISO 4032 Schlüsselweite + 2·Spiel; `seitlich` = Einschubkanal in +X | Tasche im Teil = Brücke über der Mutter, druckt ohne Stütze |
| Langloch | `langloch(d=4.5, laenge=10, tiefe=5)` | `laenge` = Mittenabstand in X | – |
| Schnapphaken | `schnapphaken(laenge=15, dicke=1.8, hoehe=6, nase=1)` | Balken in X, Feder in Y, Nase +Y; Dehnung 1,5·d·n/L² < 3 % | flach liegend (Schichten längs) – sonst bricht er; PETG federt besser |
| Rastfenster | `schnapphaken_ausschnitt(…gleiche Werte…)` | in gleicher Lage abziehen; Wand-Innenfläche bei y = dicke + Spiel | geprüft: Nase überschneidet das Fenster nicht |
| Schwalbenschwanz | `schwalbe_stecker(breite=8, hoehe=4, laenge=20, winkel=15)` / `schwalbe_nut(…)` | Profil in XZ, Länge +Y, Nut rundum + Spiel | geprüft: Stecker liegt ganz in der Nut; 15° Flanke = stützenfrei |
| Gewinde M6–M12 | `gewinde_bolzen(m=8, laenge=20)` / `gewinde_ausschnitt(m=8, tiefe=10)` / `gewinde_mutter(m=8)` | ISO 60°, Regelsteigung 1/1,25/1,5/1,75, rechtsgängig; Bolzen −0,1, Mutter +0,1 im Radius; Enden angefast | Bolzen stehend, Schicht 0,12–0,16; geprüft: M8/M12-Bolzen passt vollständig in den Ausschnitt |
| Rundung | `rund_quader([30,20,10], r=3, kanten="senkrecht"/"alle")` | Ecke bei 0,0,0 wie `cube()` | „alle“ hat unten eine kleine Überhangrundung |
| Fase | `fase_quader([30,20,10], f=1.5)` | alle Kanten 45° | stützenfrei |
| Wandlasche | `wandlasche(breite=20, laenge=18, dicke=4, m=4, anzahl=2)` | Anbaukante x = 0, Senklöcher | flach drucken, Wände 4 |
| Schlüsselloch | `schluesselloch(kopf_d=8, schaft_d=4, kopf_h=3, laenge=10, steg=2)` | Rückseite (Bett) bei z = 0; Kopf rein, nach +X schieben | Kopftasche wird gebrückt (≈ 8,4 mm) |
| Kabel-Clip | `kabelclip(d=6, breite=8)` | Kabel-Ø ohne Spiel (klemmt), Öffnung 0,75·d, 2 × M3-Lasche | liegend drucken (Profil in XY); PETG/TPU besser als PLA |

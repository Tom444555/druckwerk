# Drehteller + Meshroom – Spickzettel (Stand 20.11.2026, ungetestet)

## Aufbau
1. Sockel hinstellen, Käfig zwischen die Lippen, in jede Tasche zwei Walzen, Teller aufsetzen.
2. Visier vorn in den Block stecken. Durch die Kimme über das Korn auf die Zahl am Rand schauen.
3. Podest mit den drei Zapfen in die drei Löcher im Teller stecken (Tellermitte). Modell darauf, bei Bedarf mit den Stiften (Ø3) in den Löchern abstützen.
4. Maßwürfel (20 mm, Ziffern 1–6) neben das Modell auf den Teller legen – er dreht mit und dient als Höhen- und Maßprüfung.

## Fotografieren
- Hintergrund einfarbig, ohne Muster, gleichmäßig ausgeleuchtet (Softboxen). Raum und Tisch dürfen keine Merkmale liefern – sie drehen nicht mit.
- Stativ, manuell: Blende f/8–f/11, ISO 100, feste Zeit, fester Weißabgleich, Fokus fest.
- 25 Bilder je Runde (ein Feld = 14,4°), drei Runden: flach (h1), schräg (h2), steil von oben (h3); danach Modell umlegen, eine Runde (h4).
- Dateinamen: `h1_f01.jpg` … `h3_f25.jpg` (Feld = Zahl im Visier).
- Glänzendes vorher mattieren (Scan-Spray).

## Meshroom: Maßstab und Lage aus den Markern (CCTag3)
- FeatureExtraction, FeatureMatching, StructureFromMotion: Describer Types zusätzlich **cctag3** einschalten (SIFT bleibt an).
- Nach StructureFromMotion einen **SfMTransform**-Knoten: Methode **from_markers**, Describer nur **cctag3**, Scale/Rotation/Translation an.
- Marker (Mitte des Tellers = Ursprung, Tellerebene = X/Z, Y nach oben; Einheit 1 = 100 mm):

| ID | liegt in | x mm | y mm (Draufsicht) | Eingabe X, Y, Z |
|---|---|---|---|---|
| 0 | Feld 1 | +9.4 | +74.4 | +0.0940, 0, -0.7441 |
| 1 | Feld 7 | +74.9 | -4.7 | +0.7485, 0, +0.0471 |
| 2 | Feld 14 | -18.7 | -72.6 | -0.1865, 0, +0.7264 |
| 3 | Feld 20 | -73.7 | +14.1 | -0.7367, 0, -0.1405 |

- Danach ist das Modell in echten Maßen (Einheit 100 mm → in Druckwerk Faktor 100) und steht gerade auf dem Teller. Der Würfel muss 20 mm messen.
- Marker sind Ø24 mm; im Foto sollte der äußere Ring mindestens ~30 Pixel Radius haben (bei der 5D Mark IV unproblematisch).
- Falls die Marker nicht erkannt werden: Meshroom-Wiki „CCTAG scaling“; notfalls Maßstab über die Kreise R50/75/100 oder den Würfel – mache ich dann beim Aufbereiten.

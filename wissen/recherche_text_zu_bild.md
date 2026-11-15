# Recherche: Text zu Bild für Druckwerk (Stand 15.11.2026)

Ziel: aus einer Beschreibung ein Bild, das sich gut in ein 3D-Modell wandeln lässt – möglichst ohne Umweg über ChatGPT.
Heute: `kiweg.js` Schritt 1 baut den Text, Schritt 2 schickt Tom zu einer externen Bild-KI. Claude selbst erzeugt keine Bilder.
**Alles hier ist Recherche + ein kurzer Test; eingebaut ist noch nichts.** Tom wählt aus den Vorschlägen.

## Was getestet ist (15.11.2026, Cloud-Sitzung)
- `image.pollinations.ai/prompt/<Text>` ist von der Sitzung aus erreichbar, ohne Schlüssel: Bild in 1–5 s, 768 × 768, JPEG, Wasserzeichen unten rechts,
  Modell laut Datei „sana“ (die Angabe `model=flux` wird ohne Schlüssel ignoriert). Test-Text (sitzender Fuchs, grau matt, ein Objekt, Sockel) wurde brauchbar umgesetzt:
  ein Objekt, ganz im Bild, matte helle Figur; Hintergrund grau statt weiß, Details weich. → taugt als **Entwurf**, nicht als Endqualität.
- Laut Pollinations-Doku: ohne Schlüssel ein Bild zur Zeit, mindestens 45 s Abstand, sonst HTTP 402. Kein Betriebsversprechen.
- Hugging Face ist erreichbar (für Modelle zum Herunterladen); die Sitzung hat 2 Kerne / 7 GB – ein gutes Bildmodell lokal rechnen lohnt hier nicht.

## Dienste und Preise (Abruf 15.11.2026, Preise ändern sich)
| Weg | Kosten je Bild | Qualität | Braucht |
|---|---|---|---|
| Pollinations ohne Schlüssel | 0 | Entwurf, 768 px, Wasserzeichen | nichts |
| Pollinations mit Schlüssel (enter.pollinations.ai, GitHub-Anmeldung) | Gratis-Guthaben, Höhe unklar | bessere Modelle (z. B. Z-Image Turbo) | Schlüssel |
| fal.ai FLUX.2 klein / dev / flash | ca. 0,005–0,012 $ | gut | `FAL_KEY` (derselbe wie für 3D) |
| fal.ai FLUX.2 pro | ca. 0,03 $ | sehr gut | `FAL_KEY` |
| fal.ai Nano Banana 2.1 | ca. 0,04 $ | sehr gut, stark beim Bearbeiten (weitere Ansichten) | `FAL_KEY` |
| fal.ai GPT Image 2.5 | ca. 0,006 $ (niedrig) bis 0,053 $ (hoch) | Spitze der Ranglisten | `FAL_KEY` |
| Gemini-App / ChatGPT von Hand | 0 (mit Tageslimit) | sehr gut | Handarbeit wie bisher |
| Gemini-API | ab 0,0336 $, kein Gratis-Kontingent | – | eigener Schlüssel → kein Vorteil gegenüber fal |
| Hugging Face Inference | Gratis-Guthaben für freie Konten im Okt. 2026 gestrichen | – | → nicht weiterverfolgen |
| Mac offline: Draw Things oder mflux mit FLUX.2 klein 4B | 0 | gut | MacBook Air 16 GB: läuft, je nach Quelle 16–90 s je Bild |

Ranglisten (Arena, 12.11.2026): GPT Image 2.5/2.6 vorn, danach u. a. Nano Banana 2.1, Grok Imagine 2.0, Reve 2.1. Für unsere Zwecke (ein Objekt, neutraler Hintergrund)
reicht ein günstiges Modell meist; die teuren lohnen bei Schrift und beim Bearbeiten.

## Was ein 3D-taugliches Bild ausmacht (Anleitungen der 3D-Dienste)
- Ein Objekt, einfarbiger Hintergrund (weiß, grau oder freigestellt), gleichmäßiges weiches Licht, keine harten Schatten.
- Objekt ganz im Bild und groß (60–80 % der Fläche), scharf, mindestens ca. 1024 px.
- **Mehrere Ansichten schlagen ein Einzelbild deutlich:** Vorne, Seite, Hinten (gleiches Licht, gleiche Größe, gleicher Hintergrund). Sonst rät das 3D-Modell die Rückseite.
- Ansichten lassen sich aus EINEM Bild erzeugen: Bild-Bearbeitungsmodell (Nano Banana, GPT Image, FLUX Kontext) mit der Anweisung „gleiche Figur von der Seite / von hinten,
  nichts sonst ändern“. Jede Ansicht als eigenes Bild. Verdeckte Details werden dabei erfunden, aber über alle Ansichten gleich.
- Dazu passt: grau-matte „Matcap“-Fassung für die Form. Deckt sich mit den Bastlwastl-Regeln (grau, matt, kompakt).
- Abweichung: Bastlwastl empfiehlt „leicht schräg von oben“ (gut für EIN Bild); für mehrere Ansichten gerade von vorn / Seite / hinten.
- `werkzeug/generieren.py` kann schon mehrere Bilder: Hunyuan bis 4, Rodin bis 5. Es fehlt nur der Weg, sie zu erzeugen.

## Vorschläge (Reihenfolge = Empfehlung)
1. **Entwurf gratis im Chat:** `werkzeug/bild_ki.py` – Text → 3–4 Entwürfe über Pollinations (45 s Abstand), Wasserzeichen wegschneiden, Claude sieht die Bilder an
   und prüft sie gegen die Prüfliste, zeigt Tom die besten; auf Wunsch gleich grober 3D-Entwurf mit `ki_lokal.py`. Kosten 0, Qualität Entwurf.
2. **„Bild erzeugen“ in der App** (Schritt 2 des KI-Ablaufs) über die vorhandene GitHub Action und denselben `FAL_KEY`: Stufe Günstig (FLUX.2) / Beste (Nano Banana 2.1 oder
   GPT Image 2.5), 4 Varianten, antippen, weiter. Ersetzt den Umweg über ChatGPT.
3. **Weitere Ansichten automatisch:** aus dem gewählten Bild Seite und Rückseite erzeugen, dann Hunyuan/Rodin mit 3–4 Bildern. Größter Hebel für die 3D-Qualität.
4. **Bild-Text schärfen** (`kiweg.js bildText`): zwei Vorlagen (Einzelbild schräg / Ansichten gerade), feste Bausteine „ein Objekt, weißer Hintergrund, weiches Licht ohne Schatten,
   füllt das Bild, grau matt“, dazu eine **Farb-Fassung für Mehrfarbdruck: höchstens vier flächige Farben ohne Verläufe** (Toms Filamente schwarz/gold/rot/weiß),
   damit `textur_farben.py` sauber auf vier Köpfe trennt.
5. **Bild vorbereiten** (`werkzeug/bild_vorbereiten.py`): Hintergrund entfernen, Objekt mittig und groß zuschneiden, auf 1024 px bringen. Vor jeder Umwandlung, auch bei eigenen Fotos.
6. **Bild automatisch prüfen:** Ampel statt Handliste – angeschnitten? mehr als ein Objekt? Hintergrund unruhig? zu klein? (im Chat sieht Claude das Bild selbst an;
   in der App einfache Regeln).
7. **Schilder, Logos, Wandbilder:** kein KI-Bild nötig – Claude zeichnet die Vorlage als Vektor (maßgenau, gratis) → `bild_relief.py`.
8. **Offline am Mac:** Draw Things mit FLUX.2 klein 4B ins Offline-Paket aufnehmen.

Kosten-Beispiel bester Weg (2 + 3): 4 Varianten ≈ 0,05–0,20 $, zwei bis drei Zusatz-Ansichten ≈ 0,08–0,12 $, 3D-Umwandlung 0,25–0,53 $ → unter 1 $ je Figur.

## Was Tom dafür braucht
- Für 1, 4–7: nichts.
- Für 2 und 3: fal.ai-Konto mit etwas Guthaben, Schlüssel als Repo-Secret `FAL_KEY` (ohnehin offen).
- Für 8: Draw Things aus dem App Store am Mac.

## Quellen
- Pollinations: https://github.com/pollinations/pollinations/blob/master/APIDOCS.md · https://agentdeals.dev/vendor/pollinations-ai
- fal-Preise: https://www.teamday.ai/blog/fal-ai-pricing-2026 · https://www.teamday.ai/blog/ai-image-video-api-providers-comparison-2026 · https://blog.picassoia.com/fal-ai-pricing-api-costs-free-credits-and-mcp
- Ranglisten: https://arena.ai/leaderboard/image/text-to-image
- Gemini: https://felloai.com/nano-banana-pricing/ · Hugging Face: https://www.usagepricing.com/blueprint/activity/hugging-face-2026-10-15-free-inference-credits-removed
- 3D-taugliche Bilder: https://docs.3daistudio.com/how/ImgTo3D · https://printpal.io/wiki/image-to-3d-best-practices · https://docs.meshy.ai/en/webapp/image-to-3d · https://www.meshy.ai/blog/meshy-5-image-to-3d
- Mehrere Ansichten: https://www.tripo3d.ai/blog/nano-banana-for-3d-animation · https://www.meshy.ai/blog/nano-banana-3d · https://help.scenario.com/articles/1419523552-generate-character-turnarounds
- Mac: https://www.teamday.ai/blog/best-local-image-generation-models-2026 · https://vidregen.com/blog/how-to-use-flux-on-mac-local-and-cloud-options

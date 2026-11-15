# Recherche: Modellqualität „wie Hyper3D Rodin“ – was geht heute maximal? (Stand 15.11.2026)

Zweck: Grundlage für die Entscheidung, welche Bausteine druckwerk bekommt. Alle Preise und Versionen stammen von den
verlinkten Primärquellen, abgerufen am 15.11.2026. **[1 Quelle]** = nur eine Quelle gefunden. **[nicht verifiziert]** = nicht prüfbar.
**[selbst getestet]** = in der Recherche-Sandbox ausprobiert (2 CPU-Kerne, Python 3.13.18).

> **Wichtige Beobachtung zur Sandbox:** In dieser Recherche-Sitzung haben `queue.fal.run`, `huggingface.co`
> (auch `*.hf.space`), `openapi.tripo3d.com`, `api.replicate.com`, `api.meshy.ai` und `api.hyper3d.com` per `curl` aus der
> Sandbox geantwortet (HTTP 401/404 = Server erreicht). Die Annahme „nur PyPI/npm/GitHub“ gilt hier also nicht.
> Ob das in Toms normalen Sitzungen genauso ist, ist **[nicht verifiziert]**. Vor dem Einbau einmal testen. Der sichere Weg
> bleibt die GitHub Action (Schlüssel als Secret, nicht in der Sandbox).

---

## Kurzfazit

1. **Das Maximum bei „organisch/Deko/Figur“** liefern heute Rodin Gen‑2.5 (bis 2 Mio. Dreiecke, Quad-Netze, Teile-Zerlegung „Bang“),
   Tripo (H3.1 / P2 mit Quads, Segmentierung, 3MF-Export), Meshy 7.1 (Geometrie „4k“, eigene **Mehrfarb-3MF-API mit Flashforge-Profil**),
   Hunyuan3D 3.1 (Tencent, nur als Dienst) und offen TRELLIS.2 (MIT-Lizenz, 4B, bis 1536³). Unterschiede sind klein; Ranglisten
   (Arena-ELO) liegen eng beieinander und stammen meist von Anbietern selbst.
2. **Keiner dieser Generatoren ist maßhaltig.** Ausgabe ist ein Netz in Einheitsgröße ohne Maße, ohne Toleranzen, ohne echte Bohrungen.
   Für technische Teile bleibt **Code-CAD (build123d/OpenSCAD) + LLM + Render-Prüfschleife** der beste Weg; spezialisierte
   Text‑to‑CAD-Modelle schlagen allgemeine LLMs im aktuellen Benchmark *nicht*.
3. **Ohne GPU** geht KI-3D nur über Dienste: **fal.ai** bündelt TRELLIS.2, Hunyuan 3.1, Rodin 2.5, Meshy und Hi3D-Mehrfarbe
   unter einem Schlüssel (0,25–0,80 $ je Modell). Hugging-Face-Spaces sind gratis, aber kontingentiert.
4. **Mehrfarbig aus Textur** ist lösbar: Das 3MF-Format `paint_color` ist im OrcaSlicer-Quellcode eindeutig (Tabelle unten).
   Alternativ machen Meshy (10 Credits) oder Hi3D über fal (0,40 $) die Farbreduktion als Dienst.
5. **Fotorealistische Vorschau ohne GPU** geht: `pip install bpy` (Blender 5.3) läuft in der Sandbox; Cycles auf der CPU braucht
   ~84 s für 800×800 px bei 64 Samples mit Entrauschen **[selbst getestet]**.

---

## 1. KI-Generatoren Bild/Text → 3D

| Werkzeug (aktuell) | Besonderheit Qualität | Export | API / Preis je Modell | MCP / Blender |
|---|---|---|---|---|
| **Hyper3D Rodin Gen‑2.5** (seit 26.05.2026) | bis 2 Mio. Polygone, Quad- oder Raw-Topologie, 1–5 Bilder, Texturen bis 12K (HighPack); „Bang“ zerlegt in Teile (1–12 Stufen, per Text steuerbar); `bbox_condition` (Größen-Steuerung), `TAPose` (T/A-Pose); Tier bis „Extreme-High“ + `is_micro` (Mikrodetail) | GLB, FBX, OBJ, USDZ, STL | Offiziell: ab 0,5 Credit/Generierung, HighPack +1 Credit; **Basic-API im Creator-Abo (30 $/Monat) nur Gen‑2.5-Low/Extreme-Low**, volle API ab Business (120 $/Monat); Gratis-Plan „generieren vor Bestätigung“, Einzel-Credit 1,5 $. Über fal: **0,40 $**, HighPack +0,80 $ | Hyper3D-MCP (laut Herstellerseite für Claude Code u. a.), Blender-Add-on, ComfyUI |
| **Tripo** H3.1 (03/2026), P1, **P2** (08/2026) | P2: echte Quad-Ausgabe (48–25.000 Quads), saubere Topologie; Segmentierung + „Mesh Complete“ (Teile ergänzen), Retopologie, Smart UV | Konvertierung nach GLTF, FBX, USDZ, OBJ, **STL, 3MF** | Credits; 1 Credit = 0,07 ¥ (ab 01.12.2026 Anzeige in ¥). P2: 100 Credits ohne Textur, 110/120/130 mit Textur. Kosten H-Serie in der Doku **[nicht gefunden]**. Python-SDK `tripo3d` 1.0.0 | Tripo-CLI, Codex-Plugin, Blender-, ComfyUI-Plugins |
| **Meshy 7.1** (API seit 18.09.2026), Meshy 6, T2/T2.5 | `geometry_resolution` „2k/4k“ (+5 Credits), Multi-Image; **3D-Druck-APIs**: Printability-Analyse (gratis), Reparatur (10), **Multi-Color-Print → 3MF bis 16 Farben, Slicer-Profil `flashforge`** (10), Relief aus Foto (20). Meshy‑7-Geometrie wird am 31.12.2026 abgeschaltet [1 Quelle] | GLB, FBX, OBJ, STL, USDZ, BLEND, 3MF (Convert 1 Credit) | Image→3D 7.1: 20 Credits (nur Netz) / 30 (Textur); Preis je Credit in der Doku **[nicht angegeben]**; über fal Meshy v6: **0,80 $**. Test-Schlüssel ohne Kosten vorhanden | Offizieller MCP-Server `@meshy-ai/meshy-mcp-server` (npm 0.6.11), Meshy-CLI |
| **Hunyuan3D 3.1** (Tencent, Dienst) | Pro: 40.000–1,5 Mio. Flächen, Mehransicht, PBR; „Rapid“; „Part“ (Teile) | GLB, OBJ | fal: Pro **0,375 $**, +0,15 $ je PBR/Mehransicht/Flächenzahl; Rapid/Part eigene Endpunkte | über blender-mcp |
| **Hunyuan3D 2.1** (offen, 06/2025), Omni, Part | 10 GB VRAM Form, 29 GB mit Textur | GLB | HF-Space gratis (ZeroGPU) | – |
| **TRELLIS.2** (Microsoft, 12/2025) | 4B Parameter, O-Voxel, bis **1536³**, scharfe Kanten, PBR inkl. Alpha; **MIT-Lizenz**; braucht ≥24 GB GPU | GLB | fal: **0,25 / 0,30 / 0,35 $** (512/1024/1536); HF-Space `microsoft/TRELLIS.2` gratis | ComfyUI |
| **Hi3D v1.0 = offenes Sparc3D** (23.10.2026) | verfeinert ein *grobes* Netz zu bis 1536³, nur Geometrie, keine CPU-Variante; eigene Lizenz (kein OSI) | – | Hitem3D-Dienst; über fal: „Hi3D Multicolor“ (Textur → 1–8 Farben) **0,40 $** | – |
| **Direct3D‑S2** (MIT, 05/2025), **Hi3DGen** (Normalen-Brücke, auf TRELLIS-Basis), **TripoSG** (MIT) | Forschung/offen, gute Geometrie, ältere Generation | GLB | HF-Spaces laufen (Stand heute) | – |
| **Stability Stable Fast 3D / SPAR3D** | schnell, niedrige Auflösung | GLB | Fast 3D: 10 Credits (Preis je Credit **[nicht verifiziert]**); SPAR3D-Space: BUILD_ERROR | – |
| **CSM, Luma Genie** | nur Sekundärquellen gefunden | – | **[nicht verifiziert]** | – |

**Eignung für FDM-Druck (alle):** Ausgabe ist ein Dreiecksnetz in Einheitsgröße → skalieren; oft nicht wasserdicht oder mit
Innenflächen → reparieren (manifold3d/pymeshlab, Meshy-Repair); dünne Teile (Finger, Antennen, Haare) unter 1,2 mm → verstärken
oder weglassen; Textur ist nur Farbe, keine Geometrie. Hi3D-Bericht: Wasserdichtheit, Wandstärke und Überhänge werden nicht geprüft.

**Was ist „das Maximum“?** Für Deko/Figuren: Rodin Gen‑2.5 Extreme-High / Tripo P2/H3.1 / Meshy 7.1 4k / TRELLIS.2 1536³ – alle
in einer Liga. Eine öffentliche Arena-Rangliste (03.08.2026, Anbieter Sloyd, 186.939 Stimmen) sah Tripo v3.1 vorn (ELO 1042),
Rodin 2.5 bei 1009, Meshy 6 bei 1004 – **[1 Quelle, Anbieter-Blog]**.
**Grenzen:** keine Maße, keine Passungen, keine planen Flächen mit exakter Lage, keine Gewinde; Rückseiten bei Einzelbild
werden erfunden; Lizenz-Fallen (siehe Hunyuan unten).

> **Lizenz-Falle Hunyuan (offen):** Die Tencent-Hunyuan-3D-2.1-Lizenz *„DOES NOT APPLY IN THE EUROPEAN UNION, UNITED KINGDOM AND
> SOUTH KOREA“*. Für Tom in Deutschland sind die offenen Hunyuan-Gewichte damit rechtlich nicht freigegeben. Der kostenpflichtige
> Tencent-Dienst (z. B. über fal) läuft über die Nutzungsbedingungen des Anbieters, nicht über diese Lizenz (Details **[nicht geprüft]**).
> TRELLIS.2 (MIT) ist hier unproblematisch.

Quellen: [Hyper3D API](https://hyper3d.ai/features/api) · [Hyper3D Preise](https://hyper3d.ai/pricing) · [Rodin Quick Start](https://docs.hyper3d.ai/en/get-started/quick-start) ·
[fal Rodin 2.5](https://fal.ai/models/fal-ai/hyper3d/rodin/v2.5/llms.txt) · [Tripo Doku-Index](https://developers.tripo3d.com/llms.txt) ·
[Tripo Billing](https://developers.tripo3d.com/en/docs/billing.md) · [Meshy API-Preise](https://docs.meshy.ai/api/pricing.md) ·
[Meshy Multi-Color-Print](https://docs.meshy.ai/api/multi-color-print.md) · [Meshy llms.txt](https://docs.meshy.ai/llms.txt) ·
[TRELLIS.2 Projektseite](https://microsoft.github.io/TRELLIS.2) · [TRELLIS.2 README](https://github.com/microsoft/TRELLIS.2) ·
[Hunyuan3D-2.1 README/LICENSE](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1) · [fal Hunyuan 3.1 Pro](https://fal.ai/models/fal-ai/hunyuan-3d/v3.1/pro/image-to-3d/llms.txt) ·
[Zeitleiste 2026 (Cinevva)](https://app.cinevva.com/guides/ai-3d-model-generation-timeline-2026) · [Hi3D Druck-Check](https://www.orcarouter.ai/blog/hi3d-v1-0-3d-printing-reality-check) ·
[Direct3D-S2](https://github.com/DreamTechAI/Direct3D-S2) · [Hi3DGen](https://github.com/Stable-X/Hi3DGen) · [TripoSG](https://github.com/VAST-AI-Research/TripoSG) ·
[Stability Preise](https://stability.ai/api-pricing-update-25) · [Arena-Rangliste (Sloyd)](https://www.sloyd.ai/blog/ai-3d-model-generator-rankings)

---

## 2. Automatisiert nutzen ohne eigene GPU (Ziel: GitHub Action + Secret)

### 2a. fal.ai – ein Schlüssel für viele Modelle (Empfehlung)
`pip install fal-client` (1.0.3), Secret `FAL_KEY`. Beispiel aus der fal-Doku:
```python
import fal_client
result = fal_client.subscribe("fal-ai/trellis-2",
    arguments={"image_url": "https://…/bild.png"}, with_logs=True)
print(result)          # enthält URL der GLB
```
Gleicher Aufruf mit `fal-ai/hyper3d/rodin/v2.5` (Feld `image_urls`, `tier`, `quality_mesh_option`, `geometry_file_format: "stl"`),
`fal-ai/hunyuan-3d/v3.1/pro/image-to-3d`, `fal-ai/meshy/v6/image-to-3d`, `hitem3d/hi3d/multicolor` (Feld `mesh_url`, `number_of_colors` 1–8).
Lokale Bilder: vorher `fal_client.upload_file()` **[aus Client-Doku bekannt, Signatur nicht erneut geprüft]**.

| Endpunkt | Preis je Lauf |
|---|---|
| `fal-ai/trellis-2` | 0,25 $ (512) / 0,30 $ (1024) / 0,35 $ (1536) |
| `fal-ai/trellis` (alt) | 0,02 $ |
| `fal-ai/hunyuan3d/v2` | 0,16 $ (mit Textur ×3) |
| `fal-ai/hunyuan-3d/v3.1/pro/image-to-3d` | 0,375 $ (+0,15 $ PBR / Mehransicht / Flächenzahl) |
| `fal-ai/hunyuan3d-v3/image-to-3d` | 0,225 $ Geometrie / 0,375 $ Normal / 0,45 $ LowPoly |
| `fal-ai/hyper3d/rodin/v2.5` | 0,40 $ (+0,80 $ HighPack) |
| `fal-ai/meshy/v6/image-to-3d` | 0,80 $ |
| `hitem3d/hi3d/multicolor` | 0,40 $ |

### 2b. Offizielle Hersteller-APIs
- **Rodin:** `POST https://api.hyper3d.com/api/v2/rodin` (multipart: `images`, `tier`, `mesh_mode`, `quality`) → `jobs.subscription_key` an
  `/api/v2/status`, danach `uuid` an `/api/v2/download`. Header `Authorization: Bearer $RODIN_API_KEY`. Antwort `"consumed": 0.5`.
  Basic-Zugang (Creator) muss Tier `Gen-2.5-Low` oder `Gen-2.5-Extreme-Low` setzen.
- **Meshy:** `POST https://api.meshy.ai/openapi/v1/image-to-3d` mit `{"image_url":…, "should_texture":true, "enable_pbr":true}` → `result` = Task-ID,
  dann `GET …/image-to-3d/{id}` bis fertig, `model_urls["glb"]`. Danach optional `POST /openapi/v1/print/multi-color`
  (`input_task_id`, `max_colors: 4`, `printer_brand: "flashforge"`) → fertige 3MF.
- **Tripo:** `POST https://openapi.tripo3d.com/v3/generation/image-to-model` mit `{"input": "<bild-url>", "model": "P2-20260801", "quad": true, "texture": true}`,
  Status `GET /v3/tasks/{task_id}`; fehlgeschlagene Aufgaben kosten nichts.
- **Replicate:** `tencent/hunyuan-3d-3.1` vorhanden (Preis auf der Seite **[nicht angegeben]**). Client `replicate` 1.0.7.
- **Stability:** Stable Fast 3D 10 Credits.

### 2c. Hugging-Face-Spaces per `gradio_client` (gratis, kontingentiert)
Laufend (Abfrage 15.11.2026): `microsoft/TRELLIS.2`, `tencent/Hunyuan3D-2.1`, `tencent/Hunyuan3D-2`, `tencent/Hunyuan3D-Part`,
`VAST-AI/TripoSG`, `Stable-X/Hi3DGen`, `wushuang98/Direct3D-S2-v1.0-demo` (jetzt nur CPU-Hardware → praktisch tot).
`microsoft/TRELLIS` (v1): CONFIG_ERROR; `stabilityai/stable-point-aware-3d`: BUILD_ERROR.

ZeroGPU-Kontingent: PRO-Konten bekommen 8× mehr Tageskontingent und können mit Guthaben darüber hinaus; für Gratis-Konten
nennt ein Forenbeitrag **5 GPU-Minuten/Tag** und zusätzlich „3 Läufe/Tag“ (Staff, April 2026) **[1 Quelle, nicht in der offiziellen Doku]**.
Mit HF-Token im Secret wird das Kontingent des Kontos genutzt. API-Endpunkte TRELLIS.2 (selbst aus `/gradio_api/info` gelesen):
```python
from gradio_client import Client, handle_file   # gradio_client 2.7.2
c = Client("microsoft/TRELLIS.2", token=os.environ["HF_TOKEN"])
c.predict(api_name="/start_session")
img = c.predict(handle_file("bild.png"), api_name="/preprocess_image")
c.predict(img, 0, "1024", api_name="/image_to_3d")          # weitere Regler haben Standardwerte
glb = c.predict(300000, 2048, api_name="/extract_glb")      # decimation_target, texture_size
```
**[Ablauf aus der Endpunktliste abgeleitet, nicht end-to-end getestet – Sitzungs-Zustand des Space kann abweichen.]**
Hunyuan3D-2.1-Space (Gradio 4.44): Endpunkte `shape_generation`, `generation_all`. Achtung EU-Lizenz (oben).

Quellen: [fal 3D-Übersicht](https://fal.ai/docs/model-api-reference/3d-api/overview.md) · [fal TRELLIS.2](https://fal.ai/models/fal-ai/trellis-2/llms.txt) ·
[fal Hi3D Multicolor](https://fal.ai/models/hitem3d/hi3d/multicolor/llms.txt) · [Rodin Quick Start](https://docs.hyper3d.ai/en/get-started/quick-start) ·
[Meshy llms-full](https://docs.meshy.ai/llms-full.txt) · [Tripo llms-full](https://developers.tripo3d.com/llms-full.txt) ·
[Replicate Hunyuan 3.1](https://replicate.com/tencent/hunyuan-3d-3.1) · [HF ZeroGPU-Doku](https://github.com/huggingface/hub-docs/blob/main/docs/hub/spaces-zerogpu.md) ·
[HF-Forum ZeroGPU-Kontingent](https://discuss.huggingface.co/t/what-is-the-free-zerogpu-quota-for-1-space/178610) · PyPI (Versionen)

---

## 3. Text-zu-CAD für technische Teile

- **Zoo (ehem. KittyCAD):** Text-to-CAD ist jetzt im Agenten **Zookeeper** (Zoo Design Studio, Sprache KCL) aufgegangen. API-Abrechnung
  0,50 $/Minute sekundengenau; Gratis-Plan 10 $ Guthaben/Monat, Plus 20 $/Monat mit 50 $ Guthaben (Stand Blog 30.09.2025 – **möglicherweise veraltet**).
  Zoo-MCP vorhanden. Ausgabeformate auf der aktuellen Seite **[nicht genannt]**.
- **Adam / CADAM:** Open Source (GPL‑3.0), Web-App: Claude erzeugt **parametrisches OpenSCAD** (mit BOSL/BOSL2/MCAD), Schieberegler für Maße,
  Export STL/SCAD/DXF. Selbst-Hosting braucht Node + Supabase. → Bestätigt druckwerks Ansatz (LLM + OpenSCAD); **BOSL2** fehlt druckwerk noch.
- **Forschung:** *CAD-Recode* (ICCV 2025): Punktwolke → CadQuery-Code, Qwen2‑1.5B, Gewichte `filapro/cad-recode-v1.5` (Rückwärts-Konstruktion
  eines Scans/Netzes zu CAD). *CAD-Coder* (NeurIPS 2025): Text → CadQuery mit Chain-of-Thought + geometrischer Belohnung.
  **Text2CAD-Bench (05/2026, 600 Aufgaben):** allgemeine LLMs (GPT‑5.2 vorn bei einfachen, Claude‑4.5‑Sonnet am robustesten bei komplexen Teilen)
  schlagen Spezialmodelle (Text2CAD, Text2CADQuery, CADFusion) deutlich; **Ungültig-Rate steigt von ~15 % (einfach) auf 70–90 % (komplex)**;
  geometrische Beschreibungen funktionieren besser als Schrittfolgen. Benchmark nutzt nur Fehlermeldungs-Retry (3×), keine Bildschleife.
- **Bewährte Praxis (abgeleitet):** Maße als Parameter → Code ausführen → Fehler zurückgeben → **Mehransicht-Render + Schnittbild + Maßprüfung
  (Bounding Box, Volumen, Wandstärke, Kollision `a ^ b`)** → korrigieren. B-Rep (build123d/CadQuery/Zoo-KCL/Onshape) ist maßhaltig und
  liefert STEP; OpenSCAD ist CSG-Netz (maßhaltig, aber kein STEP).
- **MCP-Server:** Onshape **offiziell** (FeatureScript-MCP, Onshape Labs, Early Access); Fusion 360 **offiziell** (Fusion MCP + Fusion Data MCP);
  FreeCAD nur Community-Projekte; SolidWorks/Creo nur Community. Für druckwerk (Linux, headless) sind sie wenig nützlich – sie brauchen die
  jeweilige Desktop-/Cloud-App.

Quellen: [Zoo Sekundenabrechnung](https://zoo.dev/blog/per-second-billing) · [Zoo API-Preise](https://zoo.dev/api-pricing) · [Zookeeper](https://zoo.dev/zookeeper) ·
[CADAM](https://github.com/Adam-CAD/CADAM) · [CAD-Recode](https://cad-recode.github.io) · [CAD-Coder](https://arxiv.org/html/2505.19713v3) ·
[Text2CAD-Bench](https://arxiv.org/html/2605.18430v1) · [CAD-MCP-Vergleich 2026](https://www.getleo.ai/blog/cad-mcp-server-comparison-2026) ·
[Onshape FeatureScript MCP](https://embeddedcomputing.com/technology/software-and-os/ptcs-onshape-featurescript-mcp-server-delivers-ai-text-to-code-to-cad)

---

## 4. Open-Source-Bibliotheken (pip, ohne GPU) – Versionen laut PyPI am 15.11.2026

Sandbox-Python ist **3.13.18** → passt zu allem unten (auch `bpy`, das *nur* 3.13 unterstützt).

| Paket (pip-Name) | Version (Datum) | Wofür | Reife / Stolpersteine |
|---|---|---|---|
| `build123d` | 0.13.0 (21.09.2026) | B-Rep-CAD, Fillet/Chamfer, Text, STEP | reif; Python <3.15 |
| `bd_warehouse` | 0.4.0 (07.10.2026) | Gewinde, Schrauben/Muttern (Fastener), Lager, Buchsen, Flansche, Zahnräder, Kettenräder, O-Ringe, Sicherungsringe, Passfedern, Rohre, OpenBuilds | reif, Apache‑2.0; echte Gewinde machen STEP/STL groß und langsam |
| `py_gearworks` | 0.0.24 (24.09.2026) | Zahnräder (genaue Evolventen, Paare) auf build123d | jung (0.0.x); Algebra-Stil, im Builder per `add()` |
| `cq_gears` | nicht auf PyPI | Stirn-, Schräg-, Hohl-, Kegelräder, Zahnstange (CadQuery) | Installation aus GitHub; braucht CadQuery |
| `gggears`, `bd_beams`, `cq-warehouse` | nicht auf PyPI | – | gggears ist vermutlich der Vorgänger von py_gearworks **[nicht verifiziert]** |
| `cadquery` | 2.8.0 (21.06.2026) | Alternative zu build123d | reif; gleicher Kern |
| `cadquery-ocp` / `-novtk` | 8.0.1.1.0 (05.10.2026) | OpenCascade-Bindings (OCP) | `-novtk` ist kleiner, reicht headless |
| `manifold3d` | 3.5.5 (13.11.2026) | robuste Booleans, SDF→Netz (`Manifold.level_set`), glatte Netze | sehr reif; schon im Einsatz |
| `trimesh` | 5.2.1 (12.11.2026) | Netz-Prüfung, Reparatur, Strahltests (Wandstärke), 3MF/GLB | reif |
| `pymeshlab` | 2025.7.post1 | Remeshing (isotrop), Glätten, Löcher schließen, Dezimieren | reif; großes Wheel |
| `meshlib` | 3.2.0.3 (12.11.2026) | schnelle Netz-Booleans, Offset (Wandstärke aufdicken!), Reparatur, Voxel | reif; teils kommerzielle Lizenz **[Lizenz nicht geprüft]** |
| `open3d` | 0.20.0 (16.09.2026) | Punktwolken, Poisson-Rekonstruktion | reif; groß |
| `libigl` | 2.6.3 | Geometrie-Algorithmen (Winding Number = Innen/Außen, Glätten) | reif, API knapp dokumentiert |
| `pygalmesh` | 0.10.7 (2022) | CGAL-Vernetzung | **veraltet**, braucht CGAL-Systembibliothek |
| `gmsh` | 4.15.2 | FE-Vernetzung, STEP→Netz | reif, für druckwerk Nebensache |
| `pyvista` 0.49.2 / `vedo` 2026.6.3 | Visualisierung, Offscreen-Bilder (VTK) | reif |
| `sdfcad` | 0.5.2 (2024) | SDF-Modellierung (Fork von fogleman/sdf) | wenig gepflegt |
| fogleman `sdf` | **nur GitHub** (`pip install git+https://github.com/fogleman/sdf`) | glatte organische Übergänge (`union(a, b, k=…)`) | **Achtung: PyPI-Paket `sdf` ist etwas anderes (Scientific Data Format)!** |
| `libfive` | 0.1.0a3 (2020) | SDF-Kernel | auf PyPI veraltet |
| `bpy` | **5.3.0 (10.11.2026)** | Blender als Modul: Cycles-Render, Remesh (Voxel, QuadriFlow), Displacement, Subdivision | **nur Python 3.13**, Linux-Wheel **428 MB**, entpackt ~1,1 GB **[selbst getestet]** |
| `pyinstantmeshes` | 1.0.0 (16.12.2025) | Instant Meshes (Quad-Retopologie) | jung [1 Quelle]; Alternative `pynanoinstantmeshes` 0.0.3 |
| `fast-simplification` 0.2.0 / `pyfqmr` 0.5.0 | Dezimieren | reif |
| `xatlas` 0.0.11 | UV-Abwicklung | reif |
| `lib3mf` 2.5.0 | 3MF lesen/schreiben (offizielle Referenz) | reif |
| `pygltflib` 1.16.5 | GLB lesen (Texturen, Vertexfarben) | reif |
| `geomdl` 5.5.1 (15.11.2026) / `splinepy` 0.2.1 | NURBS/B-Splines | Nische |
| `pymadcad` 1.0.3 | eigenes CAD mit Fillets auf Netzen | Nische |
| `pyrender` | 0.1.45 (**2021**) | OSMesa/EGL-Offscreen-Render | **nicht mehr gepflegt** |
| `fal-client` 1.0.3, `gradio_client` 2.7.2, `replicate` 1.0.7, `tripo3d` 1.0.0 | API-Clients | – |

QuadriFlow ist in Blender eingebaut (`bpy.ops.object.quadriflow_remesh`); als eigenes pip-Paket **[nicht gefunden]**.

Quellen: PyPI-JSON je Paket (`https://pypi.org/pypi/<name>/json`) · [bd_warehouse](https://github.com/gumyr/bd_warehouse) ·
[py_gearworks](https://github.com/GarryBGoode/py_gearworks) · [cq_gears](https://github.com/meadiode/cq_gears) · [fogleman/sdf](https://github.com/fogleman/sdf) ·
[build123d](https://github.com/gumyr/build123d) · [pyrender](https://github.com/mmatl/pyrender)

---

## 5. Profi-Modell statt Bastelmodell – FDM-Gestaltungsregeln

| Thema | Regel (Zahl) | Quelle |
|---|---|---|
| Wandstärke (0,4-mm-Düse) | Linienbreite 0,45 mm: 2 Wände ≈ 0,9 mm, 3 ≈ 1,35 mm, 4 ≈ 1,8 mm. Wände zwischen 1 und 2 Linienbreiten drucken schlecht → Maße als Vielfache von 0,45 wählen | Prusa |
| Faustregel Industrie | Mindestwand ≈ 4× Schichthöhe (0,25 mm → 1,0 mm) | Stratasys Direct |
| Überhang | bis 45° stützfrei (50 % Auflage); je nach Kühlung 45–60°, Prusa Nextruder bis 75° | Hubs, Prusa |
| Brücken | unter 5 mm sauber; länger → teilen oder Nacharbeit | Hubs |
| Unterkante | **Fase statt Rundung** an Kanten auf dem Bett (Rundung = steiler Überhang); 45°-Fase gegen Elefantenfuß und Verzug | Prusa, Hubs |
| Ecken | Innenradius ≥ Düsenradius; Rundungen (Fillets) senken Spannungsspitzen | Hubs, Stratasys |
| Löcher | drucken zu klein → untermaßig konstruieren und aufbohren oder Testlehre; liegende Löcher oben als Tropfen/Spitze | Hubs, CNC Kitchen |
| Stifte | unter 5 mm Ø schwach (nur Wände) → Metallstift einsetzen; Fuß mit kleiner Rundung | Hubs |
| Spiel/Passung | eng 0,2 mm · Schnappverbindung 0,3 mm · Gleit-/Drehpassung 0,4 mm; bewegliche Teile ab 0,3 mm; Prusa-Genauigkeit ≥ 0,2 mm | Core77, Prusa |
| Schnapphaken | Biegebalken in X-Y-Ebene drucken, nicht in Z; in Z zulässige Dehnung um 50 % senken; Wurzel verrunden; Rückwinkel 90° = nicht lösbar | Core77 |
| Filmscharnier | FDM 0,4–0,8 mm dick (≥ 2 Schichten), in PLA nur ~25–30 Zyklen; besser Nylon/PP oder TPU-Scharnier im Mehrmaterial-Druck | FacFox |
| Gewindeeinsätze | Sackloch ~1 mm tiefer als Einsatz, gerade (nicht konisch), Lochmaß per Testlehre; Lötkolben 10–20 °C über Drucktemp. (PLA ≈225, PETG ≈245, ABS ≈265 °C); Wand um Einsatz ≥ 2 mm (0,080 in) | CNC Kitchen, Stratasys |
| Gedruckte Gewinde | Anlaufkegel/Zapfen ~1 mm; Innengewinde kleiner als ~4 mm vermeiden | Stratasys |
| Schrift | fett, ≥ 24 pt laut Stratasys; erhaben besser als vertieft auf Seitenwänden **[Teil 2 nicht belegt]** | Stratasys |
| Teilung | große/ungünstige Teile teilen, Klebeflächen glatt, Zentrierstifte | Prusa |
| Orientierung | Schichten quer zur Hauptlast vermeiden (Z ist schwächste Richtung) | Hubs, Prusa |
| Feindetail | ASA/PETG/PC bilden kleine Details schlechter ab als PLA | Prusa |

**Was „professionell“ ausmacht (Zusammenfassung):** durchgehend Fasen/Radien statt scharfer Kanten (unten Fase, oben/außen Radius 1–3 mm),
Wände als Vielfache der Linienbreite, Rippen statt massiver Blöcke, definierte Spiele aus der Kalibrierung, Funktionsdetails aus einer
Normteil-Bibliothek (Gewinde, Einsätze, Lager), geplante Druckorientierung, Oberflächenstruktur (Fuzzy Skin, Textur-Verschiebung) und
saubere Mehrfarb-Trennung. Konkrete Radien für „Optik“ fanden sich in keiner Primärquelle → als Hausregel festlegen **[keine Quelle]**.

**Oberflächen:** OrcaSlicer 2.5.0/2.5.1 kann **Fuzzy Skin** (malbar, `paint_fuzzy_skin`) und neu **Textur-Verschiebung** (Displacement,
bis 8 malbare Ebenen `paint_texture_0…7`, Daten unter `Metadata/texture_displacement/`) – laut Quellcode in beiden Versionen vorhanden;
ob die CLI das ohne GUI nutzt, **[nicht getestet]**.

Quellen: [Prusa – Modellieren für 3D-Druck](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135) ·
[Hubs FDM-Design](https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/) · [Stratasys Direct FDM-Leitfaden (PDF)](https://www.stratasys.com/siteassets/sdm/content---website-storage/design-guides/dg_sdm_fdm_0725a.pdf) ·
[Core77 Schnapphaken](https://www.core77.com/posts/65318/How-to-Design-Snap-Fit-Components) · [CNC Kitchen Gewindeeinsätze](https://www.cnckitchen.com/blog/tipps-amp-tricks-fr-gewindeeinstze-im-3d-druck-3awey) ·
[FacFox Filmscharniere](https://facfox.com/docs/?p=101827) · [OrcaSlicer bbs_3mf.cpp](https://github.com/SoftFever/OrcaSlicer/blob/main/src/libslic3r/Format/bbs_3mf.cpp)

---

## 6. Mehrfarbig aus Textur (4 Köpfe)

### 6a. Format `paint_color` (OrcaSlicer/Bambu Studio) – aus dem Quellcode verifiziert
- In `3D/3dmodel.model` bekommt jedes `<triangle v1 v2 v3 …>` optional das Attribut **`paint_color="…"`** (PrusaSlicer nutzt dafür historisch
  `slic3rpe:mmu_segmentation` mit gleicher Kodierung **[PrusaSlicer-Quelle nicht abrufbar, nicht verifiziert]**).
- Wert = Hex-String eines Bitstroms (Teilungsbaum je Dreieck). Für ein **ungeteiltes Dreieck in einer Farbe** gilt die Tabelle
  `CONST_FILAMENTS` aus `Model.cpp`:

| Extruder/Kopf | 1 | 2 | 3 | 4 | 5 | … | 16 |
|---|---|---|---|---|---|---|---|
| `paint_color` | `4` | `8` | `0C` | `1C` | `2C` | … | `DC` |

  Leer/fehlend = Grundfarbe des Teils/Objekts (Teil-Extruder, sonst Objekt-Extruder, sonst 1). **„4“ heißt Extruder 1, nicht 4.**
- Kodierung (`TriangleSelector::serialize`): je Knoten 2 Bit Anzahl geteilter Seiten; bei Teilung 2 Bit „spezielle Seite“ und rekursiv die Kinder
  (umgekehrte Reihenfolge); Blatt: Zustand 0–2 in 2 Bit, ab 3 Präfix `11` + 4 Bit (Zustand−3). Nibbles werden von hinten nach vorne als Hex geschrieben.
- **Praktischer Weg ohne Teilungsbaum:** Netz fein genug unterteilen (z. B. trimesh `subdivide_to_size`), je Dreieck Farbe aus Textur am
  Schwerpunkt (UV → Pixel) bzw. Mittel der Vertexfarben holen, auf 4 Filamentfarben quantisieren (k-Means im Lab-Raum oder feste Palette),
  dann nur die Ein-Farb-Codes aus der Tabelle schreiben. Ungeteilte Dreiecke reichen, wenn das Netz fein ist (Kanten folgen den Dreiecken).
- OrcaSlicer 2.5.0 enthält außerdem einen **Import texturierter OBJ (map_Kd) mit Farb-Stichprobe** (`obj_to_textured_mesh`) – vermutlich
  GUI-Dialog; per CLI **[nicht getestet]**.

### 6b. Fertige Werkzeuge
- **Meshy Multi-Color-Print-API:** GLB/FBX (auch fremde Modelle per URL) → 3MF mit bis zu 16 Farben, Stil `realistic`/`cartoon`,
  Unterteilungstiefe 3–6, **`printer_brand: "flashforge"`**; 10 Credits.
- **Hi3D Multicolor (fal):** GLB → 1–8 Farben, Ausgabe GLB/OBJ/FBX (kein 3MF) – 0,40 $.
- Open-Source-Konverter GLB→`paint_color`: **keinen gepflegten gefunden** (nur Blender-Add-ons kommerziell, z. B. „AMS Splitter“) → selbst bauen (klein).

### 6c. Alternativen
- **Farbkörper per Boolean** (wie druckwerk heute): Netz in 4 Teilkörper schneiden (Voxel-/Labelfeld → manifold3d) → robust, jede Farbe
  eigenes STL mit Slot; gut bei großen Farbflächen, schlecht bei feinen Mustern.
- **HueForge-Prinzip:** flaches Relief, Farbe entsteht durch Schichthöhe und Lichtdurchlässigkeit (Filament-Wechsel je Höhe). druckwerk
  hat mit `bild_relief.py` schon das Gegenstück für 4 echte Köpfe.

Quellen: [OrcaSlicer TriangleSelector.cpp](https://github.com/SoftFever/OrcaSlicer/blob/main/src/libslic3r/TriangleSelector.cpp) ·
[OrcaSlicer Model.cpp (CONST_FILAMENTS)](https://github.com/SoftFever/OrcaSlicer/blob/main/src/libslic3r/Model.cpp) ·
[OrcaSlicer bbs_3mf.cpp](https://github.com/SoftFever/OrcaSlicer/blob/main/src/libslic3r/Format/bbs_3mf.cpp) ·
[Was steckt in einer Bambu/Orca-3MF (dev.to)](https://dev.to/joyfunc/whats-actually-inside-a-bambuorca-3mf-24p0) ·
[Meshy Multi-Color-Print](https://docs.meshy.ai/api/multi-color-print.md) · [fal Hi3D Multicolor](https://fal.ai/models/hitem3d/hi3d/multicolor/llms.txt)

---

## 7. Vorschau-Qualität ohne GPU

- **Blender `bpy` 5.3.0, Cycles CPU [selbst getestet]:** Szene mit unterteiltem Testkopf, Flächenlicht, Boden, Principled-BSDF „PLA rot“,
  800×800 px, 64 Samples + Entrauschen → **83,5 s** auf 2 Kernen; Ergebnis fotorealistisch (weiche Schatten). EEVEE lief auch
  (Software-OpenGL, EGL-Warnungen), aber **115 s** – also langsamer als Cycles. Hochrechnung: 4 Ansichten ≈ 5–6 Min.; 32 Samples ≈ halbe Zeit.
  Installation ~1,5 Min., 1,1 GB. Für die Bildschleife „rendern → ansehen → korrigieren“ zu langsam; für das Abschluss-Foto gut.
- **Schnell (Sekunden):** OpenSCAD-PNG (heute), PyVista/vedo Offscreen (VTK) oder trimesh+Pillow; `pyrender` (OSMesa) ist seit 2021 ungepflegt.
- **Im Browser:** three.js (npm 0.187.0) mit `RoomEnvironment` (Studio-Umgebungslicht, in `examples/jsm/environments/`) +
  `MeshPhysicalMaterial` + ACES-Tonemapping + Kontaktschatten – kostet nichts in der Sandbox und wirkt am iPad sofort „Studio“. Nur Konfiguration in `index.html`.

Quellen: [bpy auf PyPI](https://pypi.org/project/bpy/) · [three.js RoomEnvironment](https://github.com/mrdoob/three.js/blob/dev/examples/jsm/environments/RoomEnvironment.js) ·
[pyrender](https://github.com/mmatl/pyrender) · Eigentest in der Sandbox

---

## Empfehlung für druckwerk

Geordnet nach Wirkung/Aufwand (höchste zuerst). Kosten = Kosten für Tom.

### (a) Geht sofort in der Sandbox
1. **Normteile-Bibliothek:** `bd_warehouse` + `py_gearworks` in `setup.sh` (Gewinde, Schrauben, Lager, Zahnräder als echte B-Rep).
   Kosten 0 €. Risiko gering (STEP/STL bei Gewinden groß, Rechenzeit).
2. **Profi-Regeln als Code:** Baukasten-Standards (Fase unten 45°, Wände als Vielfache 0,45 mm, Spiel 0,2/0,3/0,4 mm, Einsatz-Loch +1 mm tief)
   plus Prüfskript (trimesh: Wandstärke per Strahl, Überhänge > 45°, Brücken > 5 mm, wasserdicht). Kosten 0 €. Risiko gering.
3. **Render-Prüfschleife für technische Teile:** nach jedem CAD-Lauf 4 Ansichten + Schnitt + Maßliste als Bild, Claude sieht und korrigiert
   (bis 3 Runden). Schnelle Bilder per OpenSCAD/PyVista. Kosten 0 €. Risiko: mehr Sitzungsvolumen.
4. **Textur → 4 Farben (`paint_color`-3MF):** eigenes Skript `werkzeug/textur_farben.py` (GLB lesen, unterteilen, Farbe je Dreieck, 4er-Palette,
   Codes `4/8/0C/1C`). Macht jedes KI-Modell mehrfarbig druckbar. Kosten 0 €. Risiko mittel (Kantenqualität, CLI-Verhalten erst testen).
5. **Blender (`bpy`) für Foto-Vorschau + Reparatur:** Cycles-Abschlussbild (~1,5 Min./Ansicht) und Voxel-/QuadriFlow-Remesh zum Schließen
   und Glätten von KI-Netzen. Kosten 0 €. Risiko: 428-MB-Download je Sitzung, nur Python 3.13.
6. **Glatte organische Formen:** fogleman `sdf` (von GitHub, *nicht* PyPI `sdf`) bzw. `manifold3d` `level_set` für weiche Übergänge (Griffe, Figuren-Sockel).
   Kosten 0 €. Risiko gering, Rechenzeit.

### (b) Über GitHub Action mit API-Schlüssel des Nutzers
7. **Workflow `generieren.yml` über fal.ai** (ein Secret `FAL_KEY`): TRELLIS.2 (0,25–0,35 $), Hunyuan 3.1 Pro (0,375 $), Rodin 2.5 (0,40 $),
   Hi3D-Multicolor (0,40 $) – Ergebnis-GLB ins Repo, dann normale Pipeline (reparieren, skalieren, färben, slicen). Kosten je Modell 0,25–0,80 $.
   Risiko: Kosten bei Fehlversuchen, Modell-Endpunkte ändern sich.
8. **Meshy direkt** (Secret `MESHY_API_KEY`) für „Foto → fertige Mehrfarb-3MF mit Flashforge-Profil“ + kostenlose Printability-Analyse.
   Kosten: 20–35 Credits Modell + 10 Credits Mehrfarbe; Preis je Credit **[nicht verifiziert]**. Risiko: Meshy‑7-Geometrie endet 31.12.2026.
9. **Gratis-Weg über Hugging Face** (Secret `HF_TOKEN`): `gradio_client` an `microsoft/TRELLIS.2`. Kosten 0 € (oder HF PRO für 8× Kontingent).
   Risiko hoch: Kontingent (Gratis wenige Läufe/Tag), Spaces fallen aus/ändern Endpunkte. **Hunyuan-Spaces wegen EU-Lizenzausschluss meiden.**

### (c) Macht Tom selbst am iPad/Mac
10. **Rodin/Tripo/Meshy-Web-App** zum Ausprobieren (Rodin: gratis generieren, zahlen erst bei Download; Creator 30 $/Monat mit Basic-API),
    GLB/STL in der druckwerk-Werkstatt importieren → Claude repariert, färbt, slict. Kosten 0–30 $/Monat. Risiko gering.
11. **Gute Eingabebilder** liefern (freigestellt, Objekt > 50 % des Bildes, ggf. 2–4 Ansichten) – größter Hebel für KI-Qualität; Toms
    Druckergebnisse der Kalibrier-Teile melden, damit Spiele/Toleranzen echte Werte bekommen. Kosten 0 €.
12. **Optional Zoo Design Studio / Onshape** für maßkritische Teile mit STEP (Zoo: 10 $ Gratis-Guthaben/Monat laut Stand 09/2025). Risiko: weiteres Werkzeug.

### Nicht verifizierbar / offen
- Preis je Credit bei Meshy und Stability; Tripo-H-Serien-Kosten; Zoo-Preise aktuell (Quelle 09/2025).
- Ob die KI-API-Hosts in Toms normalen Sandbox-Sitzungen erreichbar sind (hier ja).
- Ob OrcaSlicer-CLI `paint_color`, Textur-OBJ-Import und Textur-Verschiebung ohne GUI anwendet (nur Quellcode gelesen).
- Gratis-ZeroGPU-Kontingent (nur Forenbeitrag), Arena-Rangliste (nur Anbieter-Blog), CSM/Luma (nur Sekundärquellen).
- Rechtslage Hunyuan-Dienst (nicht offene Gewichte) für Nutzer in der EU.

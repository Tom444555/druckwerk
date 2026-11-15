#!/usr/bin/env python3
"""bild_ki.py – Text zu Bild direkt in der Chat-Sitzung (für Claude), als Vorlage für Bild-zu-3D.

  python3 werkzeug/bild_ki.py "sitting owl figurine with big round eyes" --name eule --aus /tmp/eule
  python3 werkzeug/bild_ki.py "…" --name eule --aus /tmp/eule --anzahl 4 --ansicht einzel --farbe grau
  python3 werkzeug/bild_ki.py "…" --ansicht ansichten      → Vorne, Seite, Hinten (je ein Bild, für Hunyuan/Rodin mit mehreren Bildern)
  python3 werkzeug/bild_ki.py "…" --farbe vier             → höchstens vier flächige Farben (für textur_farben.py / vier Köpfe)

Dienst (automatisch der beste, für den ein Schlüssel da ist):
  FAL_KEY in der Umgebung           → fal.ai (Standard fal-ai/flux-2-pro, ca. 0,03 $ je Bild; --fal-modell ändert das)
  POLLINATIONS_KEY                  → gen.pollinations.ai (Modell --modell, Standard zimage)
  sonst                             → image.pollinations.ai ohne Schlüssel: gratis, 768 px, Logo unten rechts, ein Bild alle 45 s.
                                      Qualität = ENTWURF. Tom das vorher sagen.

Der Text gehört auf Englisch (die Modelle folgen dem besser) – Claude übersetzt Toms Beschreibung selbst.
Die 3D-Regeln hängt das Skript an (ein Objekt, weißer Hintergrund, weiches Licht, ganz im Bild …); --roh lässt den Text unverändert.

Ergebnis in --aus: bild_<n>.png (roh), bild_<n>_fertig.png (freigestellt auf Weiß, mittig, groß, 1024 px), uebersicht.png (alle freigestellt nebeneinander,
nummeriert – DIESE Datei ansehen und Tom zeigen), info.json (Text, Saat, Prüfwerte je Bild).
Danach: bestes Bild → werkzeug/ki_lokal.py (gratis, grob) oder generieren.py/App (fal.ai) oder MakerLab.
Regeln und Hintergrund: wissen/recherche_text_zu_bild.md
"""
import argparse, io, json, os, sys, time, urllib.parse, urllib.request, urllib.error
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

REGELN = ("single object only, entire object visible and centered, fills most of the frame, plain pure white background, "
          "soft even studio lighting, no cast shadow, no text, no logo, no extra objects, sharp focus, "
          "compact solid shape with a flat base, thick sturdy parts, no thin fragile parts, nothing floating")
FARBE = {"grau": "made of uniform matte light grey clay, single color, no texture pattern",
         "vier": "flat cel-shaded colors, at most four solid colors (black, gold yellow, red, white), no gradients, no shading, clear color boundaries",
         "frei": ""}
ANSICHT = {"einzel": ["three-quarter front view from slightly above"],
           "vorne": ["straight front view, orthographic, eye level"],
           "ansichten": ["straight front view, orthographic, eye level", "exact left side profile view, orthographic, eye level",
                         "straight back view from behind, orthographic, eye level"]}
ANSICHT_NAME = {"three-quarter": "schräg", "front": "vorne", "side": "seite", "back": "hinten"}


def log(*a):
    print(*a, flush=True)


def holen(url, kopf=None, versuche=4):
    """GET mit Geduld: 402/429 = Tempolimit (Pollinations ohne Schlüssel: ein Bild alle 45 s)."""
    for i in range(versuche):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "druckwerk-bild_ki", **(kopf or {})}), timeout=180) as r:
                d = r.read()
                if not r.headers.get("Content-Type", "").startswith("image"):
                    raise RuntimeError("Antwort ist kein Bild: " + d[:200].decode("utf-8", "ignore"))
                return d
        except urllib.error.HTTPError as e:
            if e.code in (402, 429, 503) and i < versuche - 1:
                w = min(120, int(float(e.headers.get("Retry-After", 15 if e.code == 503 else 45) or 45)) + 2)
                log(f"  Tempolimit – warte {w} s"); time.sleep(w); continue
            raise RuntimeError(f"Bilddienst antwortet mit {e.code}: {e.read()[:200].decode('utf-8', 'ignore')}")
    raise RuntimeError("Bilddienst nicht erreichbar")


def erzeugen(text, saat, a):
    """→ (Bild-Bytes, Dienst-Name)"""
    if os.environ.get("FAL_KEY") and not a.gratis:
        import fal_client                                     # pip install fal-client (macht setup der Action; hier bei Bedarf)
        r = fal_client.subscribe(a.fal_modell, arguments={"prompt": text, "image_size": "square_hd", "seed": saat, "num_images": 1},
                                 with_logs=False, client_timeout=300)
        return holen(r["images"][0]["url"]), "fal.ai " + a.fal_modell
    q = urllib.parse.quote(text, safe="")
    if os.environ.get("POLLINATIONS_KEY") and not a.gratis:
        url = f"https://gen.pollinations.ai/image/{q}?model={a.modell}&width=1024&height=1024&seed={saat}&nologo=true"
        return holen(url, {"Authorization": "Bearer " + os.environ["POLLINATIONS_KEY"]}), "Pollinations " + a.modell
    return holen(f"https://image.pollinations.ai/prompt/{q}?width=1024&height=1024&seed={saat}"), "Pollinations ohne Schlüssel (Entwurf)"


_SITZUNG = None


def maske(im):
    """Objekt-Maske über rembg (u2net; lädt beim ersten Mal 176 MB). → (Maske, Zahl getrennter Teile)"""
    global _SITZUNG
    try:
        import rembg
    except ImportError:
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "rembg[cpu]"], check=True)
        import rembg
    if _SITZUNG is None:
        _SITZUNG = rembg.new_session("u2net")
    alpha = np.asarray(rembg.remove(im.convert("RGB"), session=_SITZUNG, only_mask=True), dtype=np.float32) / 255.0
    from scipy import ndimage as ndi
    m = ndi.binary_opening(alpha > 0.5, iterations=2)
    lab, n = ndi.label(m)
    if n == 0:
        return alpha, m, 0
    gr = ndi.sum(m, lab, range(1, n + 1))
    return alpha * (lab == int(np.argmax(gr)) + 1), lab == int(np.argmax(gr)) + 1, int((gr > 0.04 * gr.max()).sum())


def pruefen_und_zuschneiden(im, ziel=1024, rand=0.10):
    """Objekt freistellen, auf reines Weiß setzen, mittig und groß auf ziel × ziel. Dazu Rechenprüfung (Ampel)."""
    alpha, m, teile = maske(im)
    h, w = m.shape
    info = {"objekte": teile}
    if not m.any():
        return im.resize((ziel, ziel), Image.LANCZOS), {**info, "ampel": "rot", "hinweise": ["kein Objekt erkannt"]}
    ys, xs = np.where(m); y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    info["fuellt_prozent"] = round(100 * max(y1 - y0, x1 - x0) / max(h, w))
    seiten = [n for n, t in (("oben", y0 <= 2), ("unten", y1 >= h - 3), ("links", x0 <= 2), ("rechts", x1 >= w - 3)) if t]
    info["angeschnitten"] = seiten
    duenn = float(m.sum()) / max(1, (y1 - y0) * (x1 - x0))        # Anteil der Hüllfläche: klein = sperrig/dünne Teile
    info["kompakt_prozent"] = round(100 * duenn)
    hin = []
    if teile > 1: hin.append(f"{teile} getrennte Teile")
    if seiten: hin.append("angeschnitten (" + ", ".join(seiten) + ")")
    if info["fuellt_prozent"] < 35: hin.append("Objekt sehr klein im Bild")
    if duenn < 0.35: hin.append("sperrig – dünne/abstehende Teile?")
    if min(im.size) < 700: hin.append("Bild klein")
    info["hinweise"] = hin
    info["ampel"] = "rot" if (teile > 1 or seiten) else ("gelb" if hin else "grün")
    x = np.asarray(im.convert("RGB"), dtype=np.float32)
    frei = (x * alpha[..., None] + 255.0 * (1 - alpha[..., None])).astype(np.uint8)[y0:y1 + 1, x0:x1 + 1]
    s = int(max(y1 - y0, x1 - x0) * (1 + 2 * rand)) + 2
    feld = Image.new("RGB", (s, s), (255, 255, 255))
    feld.paste(Image.fromarray(frei), ((s - frei.shape[1]) // 2, (s - frei.shape[0]) // 2))
    return feld.resize((ziel, ziel), Image.LANCZOS), info


def uebersicht(bilder, texte, ziel):
    n = len(bilder); k = 384
    blatt = Image.new("RGB", (k * n, k + 46), (255, 255, 255)); z = ImageDraw.Draw(blatt)
    try:
        from PIL import ImageFont
        schrift = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
    except Exception:
        schrift = None
    farbe = {"grün": (40, 160, 70), "gelb": (220, 150, 0), "rot": (210, 50, 40)}
    for i, (b, (titel, ampel)) in enumerate(zip(bilder, texte)):
        blatt.paste(b.resize((k, k), Image.LANCZOS), (i * k, 0))
        z.rectangle([i * k, k, (i + 1) * k - 1, k + 45], fill=(245, 245, 247))
        z.ellipse([i * k + 10, k + 14, i * k + 28, k + 32], fill=farbe.get(ampel, (150, 150, 150)))
        z.rectangle([i * k, 0, (i + 1) * k - 1, k - 1], outline=(225, 225, 230))
        z.text((i * k + 36, k + 13), titel, fill=(0, 0, 0), font=schrift)
    blatt.save(ziel)


def main():
    p = argparse.ArgumentParser(description="Text zu Bild für Bild-zu-3D (Entwurf gratis, mit Schlüssel besser)")
    p.add_argument("text", help="Motiv auf Englisch, z. B. 'sitting owl figurine with big round eyes'")
    p.add_argument("--name", default="bild"); p.add_argument("--aus", required=True)
    p.add_argument("--anzahl", type=int, default=4, help="Varianten (bei --ansicht ansichten: Sätze)")
    p.add_argument("--ansicht", choices=sorted(ANSICHT), default="einzel")
    p.add_argument("--farbe", choices=sorted(FARBE), default="grau")
    p.add_argument("--saat", type=int, default=1)
    p.add_argument("--roh", action="store_true", help="Text unverändert senden (keine 3D-Regeln anhängen)")
    p.add_argument("--gratis", action="store_true", help="Schlüssel ignorieren, Pollinations ohne Schlüssel nehmen")
    p.add_argument("--modell", default="zimage", help="Pollinations-Modell (nur mit POLLINATIONS_KEY)")
    p.add_argument("--fal-modell", default="fal-ai/flux-2-pro")
    a = p.parse_args()
    aus = Path(a.aus); aus.mkdir(parents=True, exist_ok=True)
    plan = []                                               # (Nr, Saat, Ansichtstext)
    if a.ansicht == "ansichten":
        for s in range(a.anzahl if a.anzahl < 4 else 1):
            plan += [(len(plan) + 1 + i, a.saat + s, v) for i, v in enumerate(ANSICHT["ansichten"])]
    else:
        plan = [(i + 1, a.saat + i, ANSICHT[a.ansicht][0]) for i in range(a.anzahl)]
    fertig, titel, infos = [], [], []
    for nr, saat, sicht in plan:
        text = a.text if a.roh else ", ".join(x for x in (a.text, FARBE[a.farbe], sicht, REGELN) if x)
        log(f"Bild {nr}/{len(plan)} (Saat {saat}, {sicht.split(',')[0]}) …")
        try:
            daten, dienst = erzeugen(text, saat, a)
        except Exception as e:
            log("  FEHLER:", e); continue
        im = Image.open(io.BytesIO(daten)).convert("RGB"); im.save(aus / f"bild_{nr}.png")
        f, info = pruefen_und_zuschneiden(im); f.save(aus / f"bild_{nr}_fertig.png")
        kurz = "eigener Text" if a.roh else next((v for k, v in ANSICHT_NAME.items() if k in sicht), "")
        info.update({"nr": nr, "saat": saat, "ansicht": kurz, "dienst": dienst, "text": text, "groesse_roh": im.size})
        infos.append(info); fertig.append(f); titel.append((f"{nr} · {kurz} · {info['ampel']}" + (" – " + info["hinweise"][0][:26] if info["hinweise"] else ""), info["ampel"]))
        log(f"  {dienst} · {im.size[0]} px · Ampel {info['ampel']}" + (" · " + "; ".join(info["hinweise"]) if info["hinweise"] else ""))
        if "ohne Schlüssel" in dienst and nr != plan[-1][0]:
            time.sleep(46)                                  # Tempolimit des Gratis-Dienstes
    if not fertig:
        sys.exit("Kein Bild erzeugt.")
    uebersicht(fertig, titel, aus / "uebersicht.png")
    (aus / "info.json").write_text(json.dumps({"name": a.name, "motiv": a.text, "bilder": infos}, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"\nFertig: {aus}/uebersicht.png ansehen (Ampel je Bild = Rechenprüfung; das Auge entscheidet).")
    log("Weiter: python3 werkzeug/ki_lokal.py " + str(aus / "bild_<n>_fertig.png") + f" --name {a.name} --ziel-mm 120 --aus /tmp/{a.name}_3d")


if __name__ == "__main__":
    main()

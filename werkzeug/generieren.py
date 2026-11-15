#!/usr/bin/env python3
"""KI-Modell aus Foto (läuft in der GitHub Action generieren.yml).

eingang/<id>/ki.json (+ Bilder) -> Dienst (fal.ai oder Hugging Face) -> ki/<id>/ (GLB, STL, vorschau.png, info.json)
Rückmeldung an die App in status/<id>.json (wie beim Slicen).

ki.json: {"name": "Hund", "dienst": "trellis2|rodin|hunyuan|hf-trellis2", "bild": "1.jpg" oder ["1.jpg", "2.jpg"],
          "text": "optional (nur Rodin)", "ziel_mm": 100, "qualitaet": "schnell|standard|hoch"}
Schlüssel kommen nur aus der Umgebung (Secrets FAL_KEY, HF_TOKEN) und werden nie ausgegeben.
Aufruf: python3 werkzeug/generieren.py            # alle offenen eingang/*/ki.json
        python3 werkzeug/generieren.py --notfall  # nur Fehler-Status schreiben (z. B. wenn die Installation scheiterte)
"""
import datetime, json, os, re, shutil, subprocess, sys, time, traceback, urllib.request
from pathlib import Path

W = Path(os.environ.get("DRUCKWERK_WURZEL") or Path(__file__).resolve().parent.parent)
MAX_MB = 95                    # GitHub lehnt Dateien > 100 MB ab
MAX_DREIECKE = 400_000         # reicht für FDM (0,4-mm-Düse) und bleibt am Handy bedienbar
BILD_MAX_MB = 8                # Grenze von Hunyuan; Fotos kommen aus der App auf 1536 px verkleinert

# Endpunkte und Felder nach fal-Doku (llms.txt, abgerufen 15.11.2026; am 15.11. nachmittags erneut gegen die Doku geprüft:
# Endpunkte, Feldnamen, Rodin-Stufen, Ausgabefelder stimmen); Preise in US-Dollar je Lauf
DIENSTE = {
    "trellis2": {"name": "TRELLIS.2", "ep": "fal-ai/trellis-2", "bilder": 1,
                 "preis": {"schnell": 0.25, "standard": 0.30, "hoch": 0.35}},
    "rodin": {"name": "Hyper3D Rodin Gen-2.5", "ep": "fal-ai/hyper3d/rodin/v2.5", "bilder": 5,
              "preis": {"schnell": 0.40, "standard": 0.40, "hoch": 0.40}},
    "hunyuan": {"name": "Hunyuan3D 3.1 Pro", "ep": "fal-ai/hunyuan-3d/v3.1/pro/image-to-3d", "bilder": 4,
                "preis": {"schnell": 0.375, "standard": 0.375, "hoch": 0.375}, "mehransicht": 0.15},
    "hf-trellis2": {"name": "TRELLIS.2 (Hugging Face, gratis)", "space": "microsoft/TRELLIS.2", "bilder": 1,
                    "preis": {"schnell": 0.0, "standard": 0.0, "hoch": 0.0}},
}
AUFLOESUNG = {"schnell": 512, "standard": 1024, "hoch": 1536}
RODIN_TIER = {"schnell": "Gen-2.5-Medium", "standard": "Gen-2.5-High", "hoch": "Gen-2.5-Extreme-High"}
HUNYUAN_ANSICHT = ["input_image_url", "back_image_url", "left_image_url", "right_image_url"]   # Reihenfolge der Fotos


class Fehler(Exception):
    """Fehler mit fertiger deutscher Meldung für die App."""


def geheim_weg(text):
    """Schlüssel aus jedem Text entfernen, der ins Log oder in den Status geht."""
    s = str(text)
    for k in ("FAL_KEY", "HF_TOKEN", "FAL_KEY_ID", "FAL_KEY_SECRET"):
        v = os.environ.get(k)
        if v and len(v) >= 6: s = s.replace(v, "***")
    return re.sub(r"(Key|Bearer)\s+[\w:\-.]{12,}", r"\1 ***", s)


def kosten(dienst, qualitaet, n_bilder):
    d = DIENSTE[dienst]; p = d["preis"].get(qualitaet, d["preis"]["standard"])
    if dienst == "hunyuan" and n_bilder > 1: p += d["mehransicht"]
    return round(p, 3)


def preis_text(p):
    if not p: return "gratis"
    z = f"{p:.3f}".rstrip("0"); z = z + "0" * (2 - len(z.split(".")[1]))
    return f"ca. {z.replace('.', ',')} $"


def name_sauber(n):
    t = str(n or "modell").lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")): t = t.replace(a, b)
    return re.sub(r"[^a-z0-9_]+", "_", t).strip("_")[:40] or "modell"


def auftrag_lesen(ordner: Path):
    try: j = json.loads((ordner / "ki.json").read_text(encoding="utf-8"))
    except Exception: raise Fehler("ki.json ist kaputt oder leer.")
    dienst = str(j.get("dienst") or "trellis2")
    if dienst not in DIENSTE: raise Fehler(f"Dienst „{dienst}“ ist unbekannt.")
    q = str(j.get("qualitaet") or "standard")
    if q not in AUFLOESUNG: q = "standard"
    bilder = j.get("bild") or []
    if isinstance(bilder, str): bilder = [bilder]
    pfade = []
    for b in bilder[:8]:
        p = ordner / re.sub(r"[^\w\-.]+", "_", str(b))
        if ".." in str(b) or p.suffix.lower() not in (".jpg", ".jpeg", ".png", ".webp") or not p.exists():
            raise Fehler(f"Bild „{b}“ fehlt im Eingang.")
        if p.stat().st_size > BILD_MAX_MB * 1024 * 1024: raise Fehler(f"Bild „{b}“ ist größer als {BILD_MAX_MB} MB.")
        pfade.append(p)
    if not pfade: raise Fehler("Kein Foto im Auftrag.")
    pfade = pfade[:DIENSTE[dienst]["bilder"]]
    try: ziel = float(j.get("ziel_mm") or 100)
    except Exception: ziel = 100.0
    ziel = max(10.0, min(256.0, ziel))
    text = re.sub(r"\s+", " ", str(j.get("text") or ""))[:400]
    return {"name": str(j.get("name") or "KI-Modell")[:60], "datei": name_sauber(j.get("name")), "dienst": dienst,
            "qualitaet": q, "bilder": pfade, "ziel_mm": ziel, "text": text}


# ---------- Dienste ----------
def fal_fehlertext(e):
    code = getattr(e, "status_code", None)
    roh = getattr(e, "message", None) or str(e)
    if not isinstance(roh, str): roh = json.dumps(roh, ensure_ascii=False)
    t = geheim_weg(roh)[:300]
    klein = t.lower()
    if code == 401 or "unauthorized" in klein or "invalid key" in klein or "no credentials" in klein:
        return "fal.ai lehnt den Schlüssel ab: FAL_KEY ist ungültig oder gelöscht. Neuen Schlüssel erzeugen und das Secret ersetzen."
    if code in (402, 403) or any(w in klein for w in ("balance", "exhausted", "locked", "credit", "billing", "payment")):
        return "fal.ai-Guthaben ist leer (oder das Konto ist gesperrt). Unter fal.ai → Billing Guthaben aufladen, dann erneut versuchen."
    if code == 422: return f"fal.ai lehnt die Eingabe ab (z. B. Foto ungeeignet): {t}"
    if code == 429: return "fal.ai meldet zu viele Anfragen – in ein paar Minuten erneut versuchen."
    return f"Dienst-Fehler bei fal.ai{f' ({code})' if code else ''}: {t}"


def glb_url(res):
    """URL der GLB aus der Antwort holen (model_glb bei TRELLIS.2/Hunyuan, model_mesh bei Rodin)."""
    if isinstance(res, dict):
        for k in ("model_glb", "model_mesh"):
            v = res.get(k)
            if isinstance(v, dict) and str(v.get("url", "")): return v["url"]
    gefunden = []
    def such(x):
        if isinstance(x, dict):
            u = x.get("url")
            if isinstance(u, str) and re.search(r"\.glb(\?|$)", u): gefunden.append(u)
            for v in x.values(): such(v)
        elif isinstance(x, list):
            for v in x: such(v)
    such(res)
    if gefunden: return gefunden[0]
    raise Fehler("Der Dienst hat kein 3D-Modell (GLB) zurückgegeben.")


def fal_erzeugen(A, aus: Path, log):
    if not os.environ.get("FAL_KEY", "").strip():
        raise Fehler("Schlüssel fehlt: Im GitHub-Repo unter Settings → Secrets and variables → Actions das Secret FAL_KEY anlegen "
                     "(App → Bibliothek → „Aus Foto erzeugen (KI)“ → Einrichtung).")
    try: import fal_client
    except ImportError: raise Fehler("fal-client ist in der Action nicht installiert.")
    d = DIENSTE[A["dienst"]]
    try:
        urls = [fal_client.upload_file(p) for p in A["bilder"]]
        log(f"{len(urls)} Foto(s) an fal.ai übertragen, Dienst {d['ep']} läuft …")
        if A["dienst"] == "trellis2":
            arg = {"image_url": urls[0], "resolution": AUFLOESUNG[A["qualitaet"]]}
        elif A["dienst"] == "rodin":
            arg = {"image_urls": urls, "tier": RODIN_TIER[A["qualitaet"]], "geometry_file_format": "glb"}
            if A["text"]: arg["prompt"] = A["text"]
        else:
            arg = {k: u for k, u in zip(HUNYUAN_ANSICHT, urls)}
        try:
            res = fal_client.subscribe(d["ep"], arguments=arg, with_logs=False, client_timeout=1800)
        except Exception as e:
            # fal-Doku nennt resolution im Schema als Text ("1024"), im Beispiel als Zahl – bei Ablehnung einmal als Text versuchen
            if A["dienst"] == "trellis2" and getattr(e, "status_code", None) == 422 and isinstance(arg.get("resolution"), int):
                log("fal.ai lehnt die Eingabe ab – zweiter Versuch mit Auflösung als Text")
                arg["resolution"] = str(arg["resolution"])
                res = fal_client.subscribe(d["ep"], arguments=arg, with_logs=False, client_timeout=1800)
            else: raise
    except Fehler: raise
    except Exception as e:
        if type(e).__name__ == "MissingCredentialsError": raise Fehler("Schlüssel fehlt: Secret FAL_KEY ist leer.")
        if isinstance(e, TimeoutError): raise Fehler("fal.ai hat nach 30 Minuten kein Ergebnis geliefert (Zeitüberschreitung).")
        raise Fehler(fal_fehlertext(e))
    return herunterladen(glb_url(res), aus / "modell.glb")


def hf_erzeugen(A, aus: Path, log):
    try: from gradio_client import Client, handle_file
    except ImportError: raise Fehler("gradio_client ist in der Action nicht installiert.")
    tok = os.environ.get("HF_TOKEN", "").strip() or None
    log("Hugging Face Space microsoft/TRELLIS.2 (gratis, experimentell) läuft …")
    try:
        c = Client(DIENSTE["hf-trellis2"]["space"], token=tok, verbose=False, download_files=str(aus / "_hf"))
        c.predict(api_name="/start_session")
        bild = c.predict(handle_file(str(A["bilder"][0])), api_name="/preprocess_image")
        if isinstance(bild, dict): bild = bild.get("path") or bild.get("url")
        c.predict(image=handle_file(bild), seed=0, resolution=str(AUFLOESUNG[A["qualitaet"]]), api_name="/image_to_3d")
        r = c.predict(decimation_target=300000, texture_size=2048, api_name="/extract_glb")
    except Exception as e:
        t = geheim_weg(e)[:300]; k = t.lower()
        if "quota" in k or "exceeded" in k or "zerogpu" in k:
            raise Fehler("Das Gratis-Kontingent von Hugging Face ist für heute aufgebraucht. Morgen wieder versuchen oder einen fal-Dienst wählen.")
        if "401" in k or "token" in k and "invalid" in k: raise Fehler("Hugging Face lehnt HF_TOKEN ab – Token neu erzeugen und Secret ersetzen.")
        raise Fehler(f"Hugging Face Space meldet einen Fehler (Space kann sich geändert haben): {t}")
    kand = [x for x in (r if isinstance(r, (list, tuple)) else [r]) if isinstance(x, str) and x.lower().endswith(".glb")]
    if not kand: raise Fehler("Hugging Face hat kein 3D-Modell (GLB) zurückgegeben.")
    ziel = aus / "modell.glb"; shutil.copy(kand[0], ziel); shutil.rmtree(aus / "_hf", ignore_errors=True)
    return ziel


def herunterladen(url, ziel: Path):
    erlaubt = ("https:",) + (("file:",) if os.environ.get("DRUCKWERK_KI_TEST") else ())
    if not str(url).startswith(erlaubt): raise Fehler("Unerwartete Download-Adresse vom Dienst.")
    for versuch in range(3):
        try:
            with urllib.request.urlopen(url, timeout=300) as r, open(ziel, "wb") as f: shutil.copyfileobj(r, f, 1 << 20)
            if ziel.stat().st_size > 0: return ziel
        except Exception as e:
            if versuch == 2: raise Fehler(f"Modell konnte nicht heruntergeladen werden: {geheim_weg(e)[:200]}")
        time.sleep(5)
    raise Fehler("Heruntergeladene Datei ist leer.")


# ---------- Aufbereiten ----------
def netz_laden(glb: Path):
    import numpy as np, trimesh
    try: s = trimesh.load(str(glb), force="mesh", process=False)
    except Exception as e: raise Fehler(f"Die GLB-Datei vom Dienst lässt sich nicht lesen: {str(e)[:200]}")
    if not hasattr(s, "faces") or len(s.faces) == 0: raise Fehler("Die GLB-Datei enthält kein Netz.")
    # nur Geometrie behalten; process=True verschweißt Punkte, die an Textur-Nähten doppelt sind
    m = trimesh.Trimesh(vertices=np.asarray(s.vertices, dtype=np.float64), faces=np.asarray(s.faces), process=True)
    m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))   # glTF Y-oben -> Drucker Z-oben
    return m


def dezimieren(m, ziel_dreiecke, log):
    if len(m.faces) <= ziel_dreiecke: return m
    try:
        n = m.simplify_quadric_decimation(face_count=int(ziel_dreiecke))
        log(f"Netz vereinfacht: {len(m.faces):,} → {len(n.faces):,} Dreiecke".replace(",", "."))
        return n
    except Exception as e:
        log(f"Vereinfachen nicht möglich ({str(e)[:120]}) – Netz bleibt unverändert")
        return m


def skalieren_setzen(m, ziel_mm):
    import numpy as np
    ext = m.extents
    if max(ext) <= 0: raise Fehler("Das Modell hat keine Ausdehnung.")
    m.apply_scale(ziel_mm / float(max(ext)))
    lo, hi = m.bounds
    m.apply_translation([-(lo[0] + hi[0]) / 2, -(lo[1] + hi[1]) / 2, -lo[2]])   # mittig, Standfläche z = 0
    return m


def vorschau(m, pfad: Path):
    """Schattiertes Bild ohne GPU (Maler-Verfahren mit Pillow)."""
    import numpy as np
    from PIL import Image, ImageDraw
    v, f = np.asarray(m.vertices), np.asarray(m.faces)
    if len(f) > 120_000: f = f[np.random.default_rng(1).choice(len(f), 120_000, replace=False)]
    az, el = np.radians(35), np.radians(22)
    d = np.array([np.sin(az) * np.cos(el), -np.cos(az) * np.cos(el), np.sin(el)])     # zur Kamera
    rechts = np.cross(-d, [0, 0, 1]); rechts /= np.linalg.norm(rechts); oben = np.cross(rechts, -d)
    tri = v[f]; mitte = v.mean(axis=0)
    xy = np.stack([(tri - mitte) @ rechts, (tri - mitte) @ oben], axis=-1)
    tiefe = ((tri.mean(axis=1) - mitte) @ d)
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0]); l = np.linalg.norm(n, axis=1); l[l == 0] = 1; n /= l[:, None]
    licht = np.array([0.4, -0.5, 0.75]); licht /= np.linalg.norm(licht)
    hell = 0.28 + 0.72 * np.abs(n @ licht)
    B, H, rand = 1200, 900, 60
    s = min((B - 2 * rand) / max(np.ptp(xy[..., 0]), 1e-9), (H - 2 * rand) / max(np.ptp(xy[..., 1]), 1e-9))
    cx, cy = (xy[..., 0].max() + xy[..., 0].min()) / 2, (xy[..., 1].max() + xy[..., 1].min()) / 2
    px = np.stack([B / 2 + (xy[..., 0] - cx) * s, H / 2 - (xy[..., 1] - cy) * s], axis=-1)
    img = Image.new("RGB", (B, H), (242, 242, 247)); dr = ImageDraw.Draw(img)
    for i in np.argsort(tiefe):                                       # hinten zuerst
        h = hell[i]; c = (int(70 * h + 20), int(120 * h + 25), int(200 * h + 30))
        dr.polygon([tuple(p) for p in px[i]], fill=c)
    img.resize((B // 2, H // 2), Image.LANCZOS).save(pfad, optimize=True)


def stl_sichern(m, pfad: Path, log):
    m.export(str(pfad))
    while pfad.stat().st_size > MAX_MB * 1024 * 1024 and len(m.faces) > 20_000:
        m = dezimieren(m, int(len(m.faces) * 0.6), log); m.export(str(pfad))
    return m


def aufbereiten(A, glb: Path, aus: Path, log):
    """GLB -> druckbare STL in Zielgröße. Nutzt werkzeug/ki_rohling.py, wenn vorhanden."""
    import trimesh
    stl = aus / f"{A['datei']}.stl"; weg = "einfach"
    roh = W / "werkzeug" / "ki_rohling.py"
    m_roh = netz_laden(glb); dreiecke_roh = len(m_roh.faces)
    if roh.exists():
        try:
            vorher = set(aus.glob("*.stl"))
            r = subprocess.run([sys.executable, str(roh), str(glb), "--ziel-mm", f"{A['ziel_mm']:g}", "--aus", str(aus)],
                               capture_output=True, text=True, timeout=1800)
            neu = sorted(set(aus.glob("*.stl")) - vorher, key=lambda p: p.stat().st_size, reverse=True)
            if r.returncode == 0 and neu:
                if neu[0] != stl: neu[0].replace(stl)
                weg = "ki_rohling"; log("Aufbereitung mit werkzeug/ki_rohling.py")
            else: log(f"ki_rohling.py ohne Ergebnis (Code {r.returncode}) – einfacher Weg: {geheim_weg(r.stderr)[-300:]}")
        except Exception as e: log(f"ki_rohling.py gescheitert ({geheim_weg(e)[:150]}) – einfacher Weg")
    if weg == "ki_rohling":
        m = trimesh.load(str(stl), force="mesh")
        if len(m.faces) > MAX_DREIECKE or stl.stat().st_size > MAX_MB * 1024 * 1024:
            m = stl_sichern(dezimieren(m, MAX_DREIECKE, log), stl, log)
    else:
        m = skalieren_setzen(dezimieren(m_roh, MAX_DREIECKE, log), A["ziel_mm"])
        m = stl_sichern(m, stl, log)
    # GLB zu groß fürs Repo -> durch die (vereinfachte) Geometrie ersetzen
    glb_hinweis = ""
    if glb.stat().st_size > MAX_MB * 1024 * 1024:
        m.export(str(glb)); glb_hinweis = "GLB war größer als 95 MB und wurde durch die vereinfachte Geometrie ohne Textur ersetzt."
        log(glb_hinweis)
    try: vorschau(m, aus / "vorschau.png")
    except Exception as e: log(f"Vorschaubild nicht möglich: {str(e)[:150]}")
    wd = bool(m.is_watertight)
    info = {"dreiecke": int(len(m.faces)), "dreiecke_roh": int(dreiecke_roh),
            "masse_mm": [round(float(x), 1) for x in m.extents], "wasserdicht": wd,
            "volumen_cm3": round(float(m.volume) / 1000, 1) if wd else None, "aufbereitung": weg,
            "stl": stl.name, "glb": glb.name, "stl_mb": round(stl.stat().st_size / 1048576, 1)}
    if glb_hinweis: info["hinweis"] = glb_hinweis
    return info


# ---------- Ablauf ----------
def einer(ordner: Path, sid: str):
    t0 = time.time(); log = lambda t: print(f"[{sid}] {geheim_weg(t)}", flush=True)
    A = auftrag_lesen(ordner)
    d = DIENSTE[A["dienst"]]; preis = kosten(A["dienst"], A["qualitaet"], len(A["bilder"]))
    log(f"Dienst: {d['name']} · Qualität {A['qualitaet']} · {len(A['bilder'])} Foto(s) · Ziel {A['ziel_mm']:g} mm · ca. {preis:.2f} $")
    aus = W / "ki" / sid
    if aus.exists(): shutil.rmtree(aus)
    aus.mkdir(parents=True)
    try:
        glb = hf_erzeugen(A, aus, log) if A["dienst"] == "hf-trellis2" else fal_erzeugen(A, aus, log)
        if glb.stat().st_size > 500 * 1024 * 1024: raise Fehler("Das Modell vom Dienst ist größer als 500 MB.")
        info = aufbereiten(A, glb, aus, log)
    except BaseException:
        shutil.rmtree(aus, ignore_errors=True); raise
    info = {"name": A["name"], "dienst": A["dienst"], "dienst_name": d["name"], "qualitaet": A["qualitaet"],
            "fotos": len(A["bilder"]), "ziel_mm": A["ziel_mm"], "kosten_usd": preis,
            "kosten_text": preis_text(preis), **info,
            "dauer_s": round(time.time() - t0), "zeit": jetzt()}
    (aus / "info.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"fertig: {info['dreiecke']} Dreiecke, {info['masse_mm']} mm, wasserdicht: {info['wasserdicht']}")
    return {"ok": True, "art": "ki", "ordner": f"ki/{sid}", "stl": f"ki/{sid}/{info['stl']}", "name": A["name"],
            "info": {k: info[k] for k in ("dienst_name", "kosten_text", "dreiecke", "masse_mm", "wasserdicht")}}


def jetzt(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(notfall=False):
    (W / "status").mkdir(exist_ok=True); (W / "ki").mkdir(exist_ok=True)
    for a in sorted((W / "eingang").glob("*/ki.json")):
        ordner, sid = a.parent, re.sub(r"[^\w\-]+", "", a.parent.name)
        if notfall:
            st = {"ok": False, "art": "ki", "fehler": "Die Action konnte nicht vorbereitet werden (Installation fehlgeschlagen). Später erneut versuchen."}
        else:
            try: st = einer(ordner, sid)
            except Fehler as e: st = {"ok": False, "art": "ki", "fehler": geheim_weg(e)[:900]}
            except Exception as e:
                print(geheim_weg(traceback.format_exc())[-1500:], flush=True)
                st = {"ok": False, "art": "ki", "fehler": "Unerwarteter Fehler: " + geheim_weg(e)[:600]}
        st["zeit"] = jetzt()
        (W / "status" / f"{sid}.json").write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
        shutil.rmtree(ordner, ignore_errors=True)                     # Foto(s) wieder aus dem Eingang entfernen
        print(sid, "ok" if st["ok"] else "Fehler: " + st["fehler"][:200], flush=True)


if __name__ == "__main__":
    main(notfall="--notfall" in sys.argv)

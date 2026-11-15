#!/usr/bin/env python3
"""Bild → 3D-Rohling direkt in der Claude-Sitzung, ohne Dienst, ohne Schlüssel, ohne Kosten.

Nutzt das freie Modell TripoSR (Tripo AI & Stability AI, MIT-Lizenz, 1,7 GB). Es läuft ohne Grafikkarte:
gemessen am 15.11.2026 auf 2 Kernen / 7 GB: Laden 8 s, Form 14 s, Netz (Auflösung 256) 24 s.

Einordnung: deutlich gröber als TRELLIS.2, Hunyuan3D oder Rodin (die brauchen eine Grafikkarte und laufen
nur über fal.ai/MakerLab/Meshy). Gut für schnelle Entwürfe, einfache kompakte Figuren und zum Ausprobieren,
ob ein Bild taugt, bevor eine bezahlte Umwandlung läuft. Dünne Teile (Antennen, Finger) gehen verloren,
die Rückseite ist geraten.

Aufruf:
  python3 werkzeug/ki_lokal.py foto.png --name figur --ziel-mm 120 --aus /tmp/figur
  python3 werkzeug/ki_lokal.py foto.jpg --name figur --ziel-mm 150 --aus /tmp/figur --aufloesung 320 --rohling "--boden sockel"

Ablauf: Einrichten beim ersten Mal (~2 Min.: torch ohne GPU, TripoSR, Freisteller) → Motiv freistellen
(vorhandene Transparenz wird benutzt, sonst rembg) → TripoSR → <name>_ki.glb (mit Punktfarben) →
werkzeug/ki_rohling.py (aufrecht, skaliert, dicht, Standfläche) → <aus>/<name>.stl, vorschau.png, info.json.
Danach wie gewohnt: Bild ansehen, bei Farbe textur_farben.py, slicen.
"""
import argparse, json, os, subprocess, sys, time, types
from pathlib import Path

ORT = Path(os.environ.get("KI_LOKAL_ORT", "/tmp/ki_lokal"))
REPO, STAND = "https://github.com/VAST-AI-Research/TripoSR", "107cefd"
HIER = Path(__file__).resolve().parent


def sh(*a):
    r = subprocess.run(a, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"Fehler bei {' '.join(a[:4])} …\n{r.stderr[-800:]}")


def einrichten():
    try:
        import torch  # noqa: F401
    except ImportError:
        print("Einrichten: torch (ohne GPU) …", flush=True)
        sh(sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "torch", "torchvision",
           "--index-url", "https://download.pytorch.org/whl/cpu")
    fehlt = []
    for modul, paket in (("omegaconf", "omegaconf"), ("einops", "einops"), ("transformers", "transformers"),
                         ("huggingface_hub", "huggingface-hub"), ("skimage", "scikit-image"), ("trimesh", "trimesh"),
                         ("imageio", "imageio"), ("rembg", "rembg[cpu]")):
        try:
            __import__(modul)
        except ImportError:
            fehlt.append(paket)
    if fehlt:
        print("Einrichten:", ", ".join(fehlt), "…", flush=True)
        sh(sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", *fehlt)
    ziel = ORT / "TripoSR"
    if not ziel.exists():
        print("Einrichten: TripoSR holen …", flush=True)
        ORT.mkdir(parents=True, exist_ok=True)
        sh("git", "clone", "-q", REPO, str(ziel))
        sh("git", "-C", str(ziel), "checkout", "-q", STAND)
    return ziel


def freistellen(pfad, ohne):
    """RGBA mit Motiv auf 85 % der Bildfläche, quadratisch – so wie TripoSR es erwartet."""
    import numpy as np
    from PIL import Image
    im = Image.open(pfad)
    im.thumbnail((1400, 1400))
    hat_alpha = im.mode in ("RGBA", "LA") and np.asarray(im.convert("RGBA"))[:, :, 3].min() < 250
    if hat_alpha or ohne:
        im = im.convert("RGBA")
        art = "Transparenz aus der Datei" if hat_alpha else "nicht freigestellt"
    else:
        import rembg
        im = rembg.remove(im.convert("RGB"), session=rembg.new_session("u2net"))
        art = "freigestellt (rembg)"
    a = np.asarray(im)
    ys, xs = np.where(a[:, :, 3] > 12)
    if len(xs) < 50:
        sys.exit("Kein Motiv gefunden – Bild mit klarem, einfarbigem Hintergrund nehmen.")
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    seite = int(max(a.shape[:2]) / 0.85)
    feld = np.zeros((seite, seite, 4), np.uint8)
    y0, x0 = (seite - a.shape[0]) // 2, (seite - a.shape[1]) // 2
    feld[y0:y0 + a.shape[0], x0:x0 + a.shape[1]] = a
    anteil = float((feld[:, :, 3] > 12).mean())
    f = feld.astype(np.float32) / 255.0
    grau = (f[:, :, :3] * f[:, :, 3:4] + (1 - f[:, :, 3:4]) * 0.5) * 255
    return Image.fromarray(grau.astype(np.uint8)), Image.fromarray(feld), art, anteil


def modell_laden(ziel):
    import torch
    # torchmcubes müsste kompiliert werden – scikit-image liefert dieselbe Fläche.
    from skimage import measure

    def marching_cubes(vol, level):
        v, f, _, _ = measure.marching_cubes(vol.detach().cpu().numpy(), level)
        return torch.from_numpy(v[:, [2, 1, 0]].copy()), torch.from_numpy(f.astype("int64"))

    sys.modules.setdefault("torchmcubes", types.SimpleNamespace(marching_cubes=marching_cubes))
    sys.path.insert(0, str(ziel))
    from huggingface_hub import hf_hub_download
    from omegaconf import OmegaConf
    from tsr.system import TSR
    cfg = OmegaConf.load(hf_hub_download("stabilityai/TripoSR", "config.yaml"))
    OmegaConf.resolve(cfg)
    m = TSR(cfg)
    gew = torch.load(hf_hub_download("stabilityai/TripoSR", "model.ckpt"), map_location="cpu")
    if any(".attention.q_proj." in k for k in m.state_dict()):  # neuere transformers benennen den Bild-Teil um
        paare = ((".attention.attention.query.", ".attention.q_proj."), (".attention.attention.key.", ".attention.k_proj."),
                 (".attention.attention.value.", ".attention.v_proj."), (".attention.output.dense.", ".attention.o_proj."),
                 (".intermediate.dense.", ".mlp.fc1."), (".output.dense.", ".mlp.fc2."))

        def neu(k):
            if not k.startswith("image_tokenizer.model.encoder.layer."):
                return k
            k = k.replace("image_tokenizer.model.encoder.layer.", "image_tokenizer.model.layers.")
            for alt, n in paare:
                k = k.replace(alt, n)
            return k
        gew = {neu(k): v for k, v in gew.items()}
    bericht = m.load_state_dict(gew, strict=False)
    if bericht.missing_keys or bericht.unexpected_keys:
        sys.exit(f"Gewichte passen nicht zur installierten transformers-Version: {len(bericht.missing_keys)} fehlen, "
                 f"{len(bericht.unexpected_keys)} übrig. In ki_lokal.py die Umbenennung anpassen.")
    m.renderer.set_chunk_size(8192)
    return m.to("cpu").eval()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("bild")
    p.add_argument("--name", required=True)
    p.add_argument("--aus", required=True, help="Ergebnis-Ordner")
    p.add_argument("--ziel-mm", type=float, required=True, help="Zielhöhe in mm (immer angeben: groß bringt Details)")
    p.add_argument("--aufloesung", type=int, default=320, help="Raster für das Netz: 256 schnell, 320 Standard, 384 fein (langsamer)")
    p.add_argument("--ohne-freistellen", action="store_true", help="Bild so nehmen, wie es ist")
    p.add_argument("--drehen-z", type=float, default=0, help="Figur zusätzlich um die Hochachse drehen (Grad)")
    p.add_argument("--rohling", default="", help="weitere Optionen für ki_rohling.py in Anführungszeichen, z. B. \"--boden sockel --glatt 1\"")
    p.add_argument("--nur-netz", action="store_true", help="nur <name>_ki.glb erzeugen, ki_rohling.py nicht starten")
    a = p.parse_args()

    t0 = time.time()
    aus = Path(a.aus)
    aus.mkdir(parents=True, exist_ok=True)
    ziel = einrichten()
    grau, frei, art, anteil = freistellen(a.bild, a.ohne_freistellen)
    frei.save(aus / f"{a.name}_eingabe.png")
    print(f"[{time.time() - t0:5.1f}s] Bild: {art}, Motiv füllt {anteil:.0%} der Fläche", flush=True)

    import torch
    torch.set_grad_enabled(False)
    m = modell_laden(ziel)
    print(f"[{time.time() - t0:5.1f}s] Modell geladen", flush=True)
    codes = m([grau], device="cpu")
    print(f"[{time.time() - t0:5.1f}s] Form berechnet", flush=True)
    netz = m.extract_mesh(codes, True, resolution=a.aufloesung)[0]
    netz.fix_normals()
    glb = aus / f"{a.name}_ki.glb"
    netz.export(glb)
    print(f"[{time.time() - t0:5.1f}s] Netz: {len(netz.faces)} Dreiecke, dicht {netz.is_watertight} → {glb}", flush=True)
    json.dump({"modell": "TripoSR (stabilityai/TripoSR, MIT)", "stand": STAND, "aufloesung": a.aufloesung, "bild": art,
               "motiv_anteil": round(anteil, 2), "dreiecke": int(len(netz.faces)), "sekunden": round(time.time() - t0)},
              open(aus / f"{a.name}_ki.json", "w"), ensure_ascii=False, indent=1)
    if a.nur_netz:
        return
    # TripoSR liefert Z oben und die Vorderseite quer; ki_rohling erwartet die Vorderseite Richtung −Y.
    bef = [sys.executable, str(HIER / "ki_rohling.py"), str(glb), "--ziel-mm", str(a.ziel_mm), "--aus", str(aus), "--name", a.name,
           "--oben", "z", "--aufrichten", "aus", "--drehen", f"0,0,{90 + a.drehen_z:g}"] + a.rohling.split()
    sys.stdout.flush()
    os.execv(sys.executable, bef)  # Prozess ersetzen: gibt den Speicher des Modells frei (sonst reichen 7 GB nicht)


if __name__ == "__main__":
    main()

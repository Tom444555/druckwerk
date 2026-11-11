#!/usr/bin/env python3
"""Verarbeitet Slice-Aufträge aus der App: eingang/<id>/auftrag.json -> auftraege/<ordner>/ + status/<id>.json"""
import json, re, shutil, struct, subprocess, sys, datetime, traceback
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parent.parent
MAT_OK = re.compile(r"^[A-Z0-9+\-]{2,10}$")
EXTRA_OK = {"sparse_infill_pattern": {"grid", "gyroid", "honeycomb", "cubic", "triangles", "line", "adaptivecubic", "rectilinear"},
            "top_shell_layers": range(1, 13), "bottom_shell_layers": range(1, 13),
            "seam_position": {"aligned", "nearest", "back", "random"},
            "ironing_type": {"no ironing", "top", "topmost"}}


def stl_lesen(p: Path):
    d = p.read_bytes()
    n = struct.unpack("<I", d[80:84])[0] if len(d) >= 84 else -1
    if len(d) == 84 + n * 50:                                    # binär
        a = np.frombuffer(d, dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]), offset=84, count=n)
        return a["v"].astype(np.float64)
    z = re.findall(rb"vertex\s+(\S+)\s+(\S+)\s+(\S+)", d)        # ASCII (OpenSCAD)
    return np.array(z, dtype=np.float64).reshape(-1, 3, 3)


def stl_schreiben(p: Path, v):
    n = np.cross(v[:, 1] - v[:, 0], v[:, 2] - v[:, 0]); l = np.linalg.norm(n, axis=1, keepdims=True); l[l == 0] = 1
    a = np.zeros(len(v), dtype=np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")]))
    a["n"] = n / l; a["v"] = v
    p.write_bytes(b"druckwerk".ljust(80, b" ") + struct.pack("<I", len(v)) + a.tobytes())


def einer(ordner: Path):
    j = json.loads((ordner / "auftrag.json").read_text(encoding="utf-8"))
    name = re.sub(r"[^a-z0-9_]+", "_", str(j.get("name", "modell")).lower().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")).strip("_")[:40] or "modell"
    drucker = j.get("drucker", "kobrax")
    if drucker not in ("kobrax", "c5pro"): raise ValueError("Drucker unbekannt")
    datum = datetime.date.today().isoformat()
    basis, k = name, 2
    while (W / "auftraege" / f"{datum}_{name}_{drucker}").exists(): name = f"{basis}_{k}"; k += 1
    tmp = ordner / "_teile"; tmp.mkdir(exist_ok=True)
    M = None
    if j.get("matrix"):
        m = np.array(j["matrix"], dtype=np.float64).reshape(3, 4); M = (m[:, :3], m[:, 3])
    cmd = [sys.executable, str(W / "werkzeug" / "druck.py"), "--drucker", drucker, "--name", name]
    teile = j.get("teile") or []
    if not 1 <= len(teile) <= 16: raise ValueError("keine Teile")
    for i, t in enumerate(teile):
        mat = str(t.get("material", "PLA")).upper(); slot = int(t.get("slot", 1))
        if not MAT_OK.match(mat) or not 1 <= slot <= 4: raise ValueError("Material/Spule ungültig")
        tn = re.sub(r"[^\w\-]+", "_", str(t.get("name", f"teil{i+1}")))[:40] or f"teil{i+1}"
        ziel = tmp / f"{tn}.stl"
        if ziel.exists(): ziel = tmp / f"{tn}_{i+1}.stl"
        if t.get("aus"):                                         # Datei aus dem Lager (+ Matrix aus der Werkstatt)
            q = str(t["aus"])
            if ".." in q or not re.match(r"^auftraege/[\w\-.]+/[\w\-. ]+\.stl$", q): raise ValueError("Pfad ungültig")
            v = stl_lesen(W / q)
            if M is not None:
                v = v @ M[0].T + M[1]
                if np.linalg.det(M[0]) < 0: v = v[:, ::-1, :]
            stl_schreiben(ziel, v)
        else:                                                    # von der App hochgeladen (schon umgebaut)
            q = ordner / re.sub(r"[^\w\-.]+", "_", str(t.get("stl", "")))
            if q.suffix.lower() != ".stl" or not q.exists(): raise ValueError("Teil fehlt")
            shutil.copy(q, ziel)
        cmd += ["--teil", f"{ziel}:{mat}:{slot}"]
    if len(teile) > 1: cmd.append("--zusammen")
    farben = [re.sub(r"[^\w#äöüß]+", "", str(f))[:20] for f in (j.get("farben") or [])][:4]
    if farben: cmd += ["--farben", ",".join(farben)]
    cmd += ["--schicht", "%.2f" % float(j.get("schicht", 0.2)), "--infill", str(max(0, min(100, int(j.get("infill", 15)))))]
    if j.get("waende"): cmd += ["--waende", str(max(1, min(12, int(j["waende"]))))]
    if j.get("stuetzen") in ("aus", "auto", "baum"): cmd += ["--stuetzen", j["stuetzen"]]
    if j.get("brim") in ("aus", "auto", "an"): cmd += ["--brim", j["brim"]]
    for kx, wx in (j.get("extra") or {}).items():
        ok = EXTRA_OK.get(kx)
        if ok is None: continue
        if isinstance(ok, range): wx = int(wx)
        if wx in ok: cmd += ["--extra", f"{kx}={wx}"]
    if re.match(r"^https://[\w\-.]+/\S*$", str(j.get("quelle", ""))): cmd += ["--quelle", j["quelle"]]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=1800)
    out = W / "auftraege" / f"{datum}_{name}_{drucker}"
    if r.returncode != 0 or not (out / "auftrag.json").exists():
        log = (out / "slicer.log").read_text(errors="ignore")[-600:] if (out / "slicer.log").exists() else ""
        shutil.rmtree(out, ignore_errors=True)
        raise RuntimeError((r.stdout + r.stderr)[-500:].strip() + "\n" + log)
    return out.name


def main():
    (W / "status").mkdir(exist_ok=True)
    for a in sorted((W / "eingang").glob("*/auftrag.json")):
        ordner, sid = a.parent, re.sub(r"[^\w\-]+", "", a.parent.name)
        try:
            st = {"ok": True, "ordner": einer(ordner)}
        except Exception as e:
            traceback.print_exc(); st = {"ok": False, "fehler": str(e)[-900:]}
        st["zeit"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        (W / "status" / f"{sid}.json").write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
        shutil.rmtree(ordner, ignore_errors=True)
        print(sid, st)
    # alte Statusdateien aufräumen (nur die letzten 30 behalten)
    for f in sorted((W / "status").glob("*.json"), key=lambda p: p.stat().st_mtime)[:-30]: f.unlink()
    if (W / "auftraege").exists():
        sys.path.insert(0, str(W / "werkzeug")); import druck; druck.index_neu(W / "auftraege")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Verarbeitet Slice-Aufträge aus der App: eingang/<id>/auftrag.json -> auftraege/<ordner>/ + status/<id>.json"""
import json, re, shutil, struct, subprocess, sys, datetime, traceback
from pathlib import Path
import numpy as np

W = Path(__file__).resolve().parent.parent
MAT_OK = re.compile(r"^[A-Z0-9+\-]{2,10}$")
EXTRA_OK = {"sparse_infill_pattern": {"grid", "gyroid", "honeycomb", "cubic", "triangles", "line", "adaptivecubic", "rectilinear", "lightning"},
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


def zurueck(ordner: Path, j, sid=""):
    """Tom hat ein Teil selbst geändert (Flash Studio) und lädt .gcode und/oder .3mf zurück: ersetzt die Dateien im Auftrag, liest Zeit/Gramm neu, merkt die Notiz."""
    o = str(j.get("ordner", ""))
    if not re.match(r"^[\w\-]+$", o) or not (W / "auftraege" / o / "auftrag.json").exists(): raise ValueError("Auftrag unbekannt")
    ziel = W / "auftraege" / o
    info = json.loads((ziel / "auftrag.json").read_text(encoding="utf-8"))
    basis = info.get("datei") or f"{info['name']}_{info['drucker']}"
    neu = {}
    for feld, endung in (("gcode", ".gcode"), ("projekt", ".3mf")):
        if not j.get(feld): continue
        q = ordner / re.sub(r"[^\w\-.]+", "_", str(j[feld]))
        if q.suffix.lower() != endung or not q.exists(): raise ValueError(f"Datei fehlt: {j[feld]}")
        kopf = q.read_bytes()[:4096]
        if endung == ".3mf" and kopf[:2] != b"PK": raise ValueError("Das ist keine gültige 3MF-Datei")
        if endung == ".gcode" and (b"\x00" in kopf or not re.search(rb"(?m)^(;|G\d|M\d)", kopf)): raise ValueError("Das ist keine Druckdatei (.gcode als Text) – in Flash Studio „G-Code exportieren“ wählen")
        zname = info.get(feld) or basis + endung
        shutil.copy(q, ziel / zname); info[feld] = zname; neu[feld] = True
    if not neu: raise ValueError("keine Datei dabei")
    hinweis = ""
    if neu.get("gcode"):
        txt = (ziel / info["gcode"]).read_text(encoding="utf-8", errors="ignore")
        def wert(muster):
            m = re.search(muster, txt); return m.group(1).strip() if m else ""
        zeit = wert(r";\s*(?:estimated printing time \(normal mode\)|model printing time)\s*=\s*([^\n;]+)")
        gramm = wert(r";\s*filament used \[g\]\s*=\s*([^\n]+)")
        meter = wert(r";\s*filament used \[mm\]\s*=\s*([^\n]+)")
        if zeit: info["zeit"] = zeit
        g = [x.strip() for x in gramm.split(",")] if gramm else []
        if g and len(g) >= len(info.get("slots", [])):            # Flash Studio nennt alle Köpfe; druckwerk führt nur die belegten Slots
            g = [g[int(sl["slot"]) - 1] if int(sl["slot"]) <= len(g) else "0" for sl in info.get("slots", [])] if len(g) > len(info.get("slots", [])) else g
            info["gramm"] = ", ".join(g)
        elif g: hinweis = "Köpfe der neuen Datei passen nicht zur bisherigen Belegung – Gramm je Kopf nicht übernommen."
        if meter:
            try: info["meter"] = ", ".join(f"{float(x)/1000:.2f} m" for x in meter.split(","))
            except Exception: pass
        if not zeit: hinweis = (hinweis + " Druckzeit stand nicht in der Datei.").strip()
    datum = datetime.date.today().isoformat()
    info["geaendert"] = {"datum": datum, "notiz": str(j.get("notiz", "")).strip()[:500], "von": "Flash Studio", "gcode": bool(neu.get("gcode")), "projekt": bool(neu.get("projekt")), "id": sid, "hinweis": hinweis}
    (ziel / "auftrag.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(ziel / "BERICHT.md", "a", encoding="utf-8") as f:
        f.write(f"\n## Von Tom geändert am {datum} (Flash Studio)\n- Ersetzt: {', '.join(k for k in ('gcode', 'projekt') if neu.get(k))}\n- Notiz: {info['geaendert']['notiz'] or '–'}\n"
                + ("- Achtung: nur das Projekt (.3mf) wurde ersetzt, die Druckdatei (.gcode) ist noch die alte.\n" if not neu.get("gcode") else "") + (f"- {hinweis}\n" if hinweis else ""))
    return o


def anpassen(ordner: Path, j, sid=""):
    """Ein Teil ({ordner, koepfe}) oder ein ganzes Projekt ({liste: [{ordner, koepfe}, …]}) anpassen."""
    liste = j.get("liste") or [{"ordner": j.get("ordner"), "koepfe": j.get("koepfe")}]
    if not 1 <= len(liste) <= 24: raise ValueError("zu viele Teile")
    fertig, fehler = [], []
    for e in liste:
        try: fertig.append(anpassen_einer(e, sid))
        except Exception as ex: fehler.append(f"{e.get('ordner')}: {str(ex)[-300:]}")
    if fehler: raise RuntimeError(f"{len(fertig)} von {len(liste)} Teilen angepasst. Nicht gegangen: " + " | ".join(fehler))
    return fertig[0]


def anpassen_einer(j, sid=""):
    """„An meine Köpfe anpassen“: denselben Auftrag mit anderem Material / anderem Kopf / anderer Farbe neu slicen.
    Alle Slicer-Einstellungen kommen aus der Projekt-3MF des Auftrags (druck.py --wie); der Auftragsordner wird ersetzt."""
    o = str(j.get("ordner", ""))
    if not re.match(r"^[\w\-]+$", o) or not (W / "auftraege" / o / "auftrag.json").exists(): raise ValueError("Auftrag unbekannt")
    alt = W / "auftraege" / o
    info = json.loads((alt / "auftrag.json").read_text(encoding="utf-8"))
    if info.get("bemalt"): raise ValueError("Bemalte Modelle lassen sich so nicht anpassen – in der Werkstatt neu slicen.")
    if info.get("drucker") != "c5pro": raise ValueError("Nur Aufträge für den Creator 5 Pro lassen sich anpassen.")
    if info.get("duesen_mm"): raise ValueError("Auftrag mit gemischten Düsen – bitte im Chat anpassen lassen.")
    if not info.get("projekt") or not (alt / info["projekt"]).exists(): raise ValueError("Zu diesem Auftrag fehlt das Projekt – im Chat neu slicen lassen.")
    plan = {}                                                    # alter Kopf -> (neuer Kopf, Material, Farbe)
    for k in (j.get("koepfe") or []):
        von, nach = int(k.get("von", 0)), int(k.get("kopf", 0)); mat = str(k.get("material", "")).upper()
        if not (1 <= von <= 4 and 1 <= nach <= 4) or not MAT_OK.match(mat): raise ValueError("Kopf/Material ungültig")
        plan[von] = (nach, mat, re.sub(r"[^\w#äöüß]+", "", str(k.get("farbe", "")))[:20])
    alt_slots = {int(s["slot"]): s for s in info.get("slots", [])}
    benutzt = sorted({int(t["slot"]) for t in info.get("teile", [])})
    if not benutzt: raise ValueError("keine Teile")
    for s_ in benutzt:
        plan.setdefault(s_, (s_, str(alt_slots.get(s_, {}).get("material", "PLA")).upper(), alt_slots.get(s_, {}).get("farbe", "")))
    ziele = [plan[s_][0] for s_ in benutzt]
    if len(set(ziele)) != len(ziele): raise ValueError("Zwei Farben liegen auf demselben Kopf – jede Farbe braucht ihren eigenen Kopf.")
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="anpassen_")) / o
    shutil.copytree(alt, tmp)
    cmd = [sys.executable, str(W / "werkzeug" / "druck.py"), "--drucker", "c5pro", "--name", info["name"], "--ausgabe", str(tmp), "--wie", str(tmp)]
    for t in info["teile"]:
        q = tmp / t["datei"]
        if not q.exists(): raise ValueError(f"Modell-Datei fehlt im Lager: {t['datei']} – im Chat neu slicen lassen.")
        nach, mat, _ = plan[int(t["slot"])]
        cmd += ["--teil", f"{q}:{mat}:{nach}"]
    sys.path.insert(0, str(W / "werkzeug")); import druck
    if druck.wie_zusammen(tmp, info): cmd.append("--zusammen")
    farben = [""] * max(ziele)
    for s_ in benutzt: farben[plan[s_][0] - 1] = plan[s_][2] or alt_slots.get(s_, {}).get("farbe", "")
    for i, f in enumerate(farben):                               # unbenutzte Köpfe dazwischen: Platzhalter, damit die Reihenfolge stimmt
        if not f: farben[i] = "leer"
    cmd += ["--farben", ",".join(farben), "--schicht", str(info.get("schicht", "0.20")), "--stufe", str(info.get("stufe", "Standard")),
            "--infill", str(int(info.get("infill", 15))), "--stuetzen", info.get("stuetzen") if info.get("stuetzen") in ("aus", "auto", "baum") else "aus",
            "--brim", info.get("brim") if info.get("brim") in ("aus", "auto", "an") else "aus"]
    if info.get("waende"): cmd += ["--waende", str(int(info["waende"]))]
    if str(info.get("duese_mm") or "0.4") != "0.4": cmd += ["--duese", str(info["duese_mm"])]
    if info.get("quelle"): cmd += ["--quelle", info["quelle"]]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=2100)
    neu = tmp / "auftrag.json"
    ok = r.returncode == 0 and neu.exists() and json.loads(neu.read_text(encoding="utf-8")).get("slots") is not None and "OK  " in r.stdout
    if not ok:
        log = (tmp / "slicer.log").read_text(errors="ignore")[-600:] if (tmp / "slicer.log").exists() else ""
        shutil.rmtree(tmp.parent, ignore_errors=True)
        raise RuntimeError((r.stdout + r.stderr)[-500:].strip() + "\n" + log)
    n = json.loads(neu.read_text(encoding="utf-8"))
    n["ordner"] = o; n["datum"] = info.get("datum", n.get("datum"))
    n["angepasst"] = {"datum": datetime.date.today().isoformat(), "id": sid,
                      "koepfe": [{"von": s_, "kopf": plan[s_][0], "material": plan[s_][1], "farbe": plan[s_][2]} for s_ in benutzt],
                      "vorher": [{"slot": s_, "material": alt_slots.get(s_, {}).get("material", ""), "farbe": alt_slots.get(s_, {}).get("farbe", "")} for s_ in benutzt]}
    n.pop("geaendert", None)
    neu.write_text(json.dumps(n, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(tmp / "BERICHT.md", "a", encoding="utf-8") as f:
        f.write(f"\n## An meine Köpfe angepasst am {n['angepasst']['datum']} (aus der App)\n"
                + "".join(f"- Kopf {v['slot']} {v['material']} {v['farbe']} → Kopf {k['kopf']} {k['material']} {k['farbe']}\n" for v, k in zip(n["angepasst"]["vorher"], n["angepasst"]["koepfe"]))
                + "- Alle übrigen Einstellungen wie vorher (aus dem Projekt übernommen). Das Modell selbst ist unverändert.\n")
    for f in tmp.iterdir():                                       # liegengebliebene alte Dateinamen entfernen
        if f.name == "index.json": f.unlink()
    shutil.rmtree(alt); shutil.move(str(tmp), str(alt)); shutil.rmtree(tmp.parent, ignore_errors=True)
    return o


def einer(ordner: Path):
    j = json.loads((ordner / "auftrag.json").read_text(encoding="utf-8"))
    if j.get("art") == "zurueck": return zurueck(ordner, j, re.sub(r"[^\w\-]+", "", ordner.name))
    if j.get("art") == "anpassen": return anpassen(ordner, j, re.sub(r"[^\w\-]+", "", ordner.name))
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
    if j.get("bemalt"):                                          # bemalte 3MF aus der Werkstatt: Original + Matrix, Farben bleiben
        q = ordner / re.sub(r"[^\w\-.]+", "_", str(j["bemalt"]))
        if q.suffix.lower() != ".3mf" or not q.exists(): raise ValueError("Bemaltes Modell fehlt")
        if q.stat().st_size > 40 * 1024 * 1024: raise ValueError("Bemaltes Modell ist zu groß (über 40 MB)")
        mats = [str(x).upper() for x in (j.get("materialien") or [])][:4]
        if any(not MAT_OK.match(x) for x in mats): raise ValueError("Material ungültig")
        cmd += ["--bemalt", str(q)] + (["--materialien", ",".join(mats)] if mats else [])
        if M is not None and not np.allclose(np.hstack([M[0], M[1][:, None]]), np.eye(3, 4), atol=1e-6):
            cmd += ["--matrix", " ".join("%.6f" % x for x in np.hstack([M[0], M[1][:, None]]).ravel())]
        teile = []
    elif not 1 <= len(teile) <= 16: raise ValueError("keine Teile")
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
    if j.get("rau") in ("fein", "mittel", "grob"):
        cmd += ["--rau", j["rau"]] + (["--rau-wo", j["rau_wo"]] if j.get("rau_wo") in ("kontur", "loecher", "alle") else [])
    duese = str(j.get("duese", "0.4"))
    if duese not in ("0.4", "0.25"): raise ValueError("Düse ungültig")
    if duese != "0.4":
        if drucker != "c5pro": raise ValueError("Andere Düsen gibt es nur für den Creator 5 Pro")
        cmd += ["--duese", duese]
    if j.get("detail") is True: cmd.append("--detail")
    if j.get("schoen") is True and j.get("detail") is not True: cmd.append("--schoen")
    if j.get("stuetz_kopf"):                                     # Stützen-Kontaktschicht aus anderem Material (eigener Kopf)
        sk = int(j["stuetz_kopf"]); smat = str(j.get("stuetz_material", "")).upper()
        if not 1 <= sk <= 4 or (smat and not MAT_OK.match(smat)): raise ValueError("Stütz-Kopf ungültig")
        cmd += ["--stuetz-kopf", str(sk)] + (["--stuetz-material", smat] if smat and not j.get("bemalt") else [])
        if smat in ("PVA", "BVOH", "HIPS"): cmd.append("--stuetz-koerper")
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

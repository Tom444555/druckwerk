#!/usr/bin/env python3
"""Umriss eines flachen Teils aus einem Foto auf der Messmatte (modelle/foto_helfer.py) in echten mm.

  python3 werkzeug/messmatte.py foto.jpg --aus /tmp/m [--hell] [--dicke 3] [--glatt 0.2] [--name teil]

Ablauf: vier ArUco-Marker finden → Foto entzerren (10 px/mm, Draufsicht) → Messfeld freistellen
(Teil dunkel auf weiß; --hell für helle Teile) → Umriss + Löcher als Polygone in mm → Bericht, Vorschau,
SVG und auf Wunsch STL (--dicke, extrudiert). Genauigkeit hängt an Foto und Schattenkante: von oben, senkrecht,
weich ausgeleuchtet (Softboxen), Teil flach aufliegend; dicke Teile werfen eine Kante, die das Maß um ein paar
Zehntel vergrößert (Perspektive) – dafür --hoehe angeben (Teilhöhe in mm), dann wird die Oberkante gemessen.
"""
import argparse, json, os
import numpy as np
import cv2

PX = 10.0   # Pixel je mm im entzerrten Bild


def lade_matte():
    p = os.path.join(os.path.dirname(__file__), "..", "modelle", "messmatte.json")
    return json.load(open(p))


def entzerren(bild, matte):
    d = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, matte["woerterbuch"]))
    det = cv2.aruco.ArucoDetector(d, cv2.aruco.DetectorParameters())
    grau = cv2.cvtColor(bild, cv2.COLOR_BGR2GRAY)
    ecken, ids, _ = det.detectMarkers(grau)
    if ids is None or len(ids) < 3:
        raise SystemExit(f"nur {0 if ids is None else len(ids)} Marker gefunden – alle vier Ecken müssen im Bild sein")
    quelle, ziel = [], []
    L, B = matte["platte_mm"]
    for e, i in zip(ecken, ids.ravel()):
        if str(i) not in matte["ecken_mm"]:
            continue
        for (u, v), (x, y) in zip(e[0], matte["ecken_mm"][str(i)]):
            quelle.append([u, v]); ziel.append([x * PX, (B - y) * PX])
    H, _ = cv2.findHomography(np.float32(quelle), np.float32(ziel), cv2.RANSAC, 3.0)
    rest = np.linalg.norm(cv2.perspectiveTransform(np.float32(quelle)[None], H)[0] - np.float32(ziel), axis=1) / PX
    oben = cv2.warpPerspective(bild, H, (int(L * PX), int(B * PX)), flags=cv2.INTER_CUBIC, borderValue=(255, 255, 255))
    return oben, len(ids), float(rest.max())


def freistellen(oben, matte, hell):
    L, B = matte["platte_mm"]
    x0, y0, x1, y1 = matte["messfeld_mm"]
    grau = cv2.cvtColor(oben, cv2.COLOR_BGR2GRAY)
    grau = cv2.GaussianBlur(grau, (5, 5), 0)
    _, maske = cv2.threshold(grau, 0, 255, (cv2.THRESH_BINARY if hell else cv2.THRESH_BINARY_INV) + cv2.THRESH_OTSU)
    feld = np.zeros_like(maske)
    feld[int((B - y1) * PX):int((B - y0) * PX), int(x0 * PX):int(x1 * PX)] = 255
    maske = cv2.bitwise_and(maske, feld)
    maske = cv2.morphologyEx(maske, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    maske = cv2.morphologyEx(maske, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return maske


def umriss(maske, glatt):
    kont, hier = cv2.findContours(maske, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
    if not kont:
        raise SystemExit("kein Teil im Messfeld gefunden (Kontrast? --hell probieren)")
    aussen = max(range(len(kont)), key=lambda i: cv2.contourArea(kont[i]) if hier[0][i][3] < 0 else -1)
    def mm(c):
        c = cv2.approxPolyDP(c, glatt * PX, True)[:, 0, :].astype(float) / PX
        c[:, 1] = -c[:, 1]                     # y nach oben
        return c
    loecher = [mm(kont[i]) for i in range(len(kont)) if hier[0][i][3] == aussen and cv2.contourArea(kont[i]) > (1.0 * PX) ** 2]
    a = mm(kont[aussen])
    versatz = a.min(axis=0)
    return a - versatz, [l - versatz for l in loecher]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("foto"); ap.add_argument("--aus", required=True); ap.add_argument("--name", default="teil")
    ap.add_argument("--hell", action="store_true"); ap.add_argument("--glatt", type=float, default=0.15)
    ap.add_argument("--dicke", type=float); ap.add_argument("--hoehe", type=float, default=0.0)
    ap.add_argument("--kamera-abstand", type=float, default=600.0, help="mm Kamera–Matte (für --hoehe)")
    a = ap.parse_args()
    os.makedirs(a.aus, exist_ok=True)
    matte = lade_matte()
    bild = cv2.imread(a.foto)
    if bild is None:
        raise SystemExit("Foto nicht lesbar")
    oben, n, rest = entzerren(bild, matte)
    maske = freistellen(oben, matte, a.hell)
    aussen, loecher = umriss(maske, a.glatt)
    if a.hoehe:   # Oberkante liegt näher an der Kamera -> wirkt größer; auf Teilhöhe zurückrechnen
        f = (a.kamera_abstand - a.hoehe) / a.kamera_abstand
        m = aussen.mean(axis=0)
        aussen = (aussen - m) * f + m
        loecher = [(l - m) * f + m for l in loecher]
    groesse = aussen.max(axis=0) - aussen.min(axis=0)
    bericht = {"marker": n, "rest_mm": round(rest, 3), "breite_mm": round(float(groesse[0]), 2), "hoehe_mm": round(float(groesse[1]), 2),
               "loecher": [{"mitte_mm": [round(float(x), 2) for x in l.mean(axis=0)],
                            "durchmesser_mm": round(float(2 * np.sqrt(abs(cv2.contourArea(np.float32(l))) / np.pi)), 2)} for l in loecher],
               "flaeche_mm2": round(float(abs(cv2.contourArea(np.float32(aussen))) - sum(abs(cv2.contourArea(np.float32(l))) for l in loecher)), 1)}
    json.dump({"aussen": aussen.tolist(), "loecher": [l.tolist() for l in loecher], "bericht": bericht},
              open(os.path.join(a.aus, a.name + "_umriss.json"), "w"))
    cv2.imwrite(os.path.join(a.aus, a.name + "_entzerrt.jpg"), oben)
    # SVG in mm
    def pfad(p):
        return "M " + " L ".join(f"{x:.3f},{groesse[1] - y:.3f}" for x, y in p) + " Z"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{groesse[0]:.2f}mm" height="{groesse[1]:.2f}mm" viewBox="0 0 {groesse[0]:.3f} {groesse[1]:.3f}">'
           f'<path fill-rule="evenodd" fill="black" d="{pfad(aussen)} {" ".join(pfad(l) for l in loecher)}"/></svg>')
    open(os.path.join(a.aus, a.name + ".svg"), "w").write(svg)
    if a.dicke:
        import manifold3d as m3, trimesh
        cs = m3.CrossSection([aussen.tolist()] + [l.tolist() for l in loecher], m3.FillRule.EvenOdd)
        g = m3.Manifold.extrude(cs, a.dicke).to_mesh()
        trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts)).export(os.path.join(a.aus, a.name + ".stl"))
    print(json.dumps(bericht, ensure_ascii=False))


if __name__ == "__main__":
    main()

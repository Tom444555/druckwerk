#!/usr/bin/env python3
"""gitarre_rundum.py – E-Gitarre rundum (echte Korpusdicke, Halsprofil, geneigte Kopfplatte, Rückseite) als Schaustück in vier Farben.

Eigener Aufbau nach Toms Bildern und Maßblatt (T-Form, 24 Bünde, zwei Humbucker ohne Rähmchen, feste Brücke, sechs Mechaniken in Reihe):
Mensur 648, Sattel 42, Halsdicke 20/22, Korpus 45 dick, Saitenabstand 10,5 mm. Umriss, Wolkung der Decke und Lage der Teile stammen aus der
Vermessung einer geraden Vorderansicht (gitarre_rundum_daten.json, Perspektive über die 24 Bundabstände herausgerechnet). Kein Schriftzug, kein Logo.

  python3 modelle/gitarre_rundum.py [--laenge 200] [--wolken 1] [--ziel /tmp/g] → <name>_{grau,rot,schwarz,weiss}.stl
  Drucklage: Rücken auf dem Bett, Decke oben; Hals und Kopfplatte schweben → Stützen (auto).

Gebaut wird in echten mm (x quer, y vom Korpusende zum Kopf, z ab Korpusrücken), am Ende gleichmäßig skaliert. p(mm) = Druckmaß → echtes Maß.
Farben berühren sich nur an Flächen; wo ein Teil in ein anderes ragt, wird mit einem größeren „Schneider“ abgezogen (keine deckungsgleichen Flächen).
"""
import argparse, json, math
from pathlib import Path
import numpy as np
import manifold3d as m3
import trimesh

CS, M = m3.CrossSection, m3.Manifold
RUND, NZ = m3.JoinType.Round, m3.FillRule.NonZero
HIER = Path(__file__).resolve().parent
MENSUR, N_BUND = 648.0, 24
T_B = 44.5                      # Korpusdicke
ZF = T_B + 9.0                  # Griffbrett-Oberseite
ZFB = ZF - 6.0                  # Griffbrett-Unterseite = Hals-Oberseite
KOPF_WINKEL, KOPF_DICKE = 10.0, 14.0


def bund_s(n): return MENSUR * (1 - 2 ** (-n / 12))
def halb(s): return 21.0 + 7.25 * s / bund_s(24)            # halbe Griffbrettbreite (42 am Sattel, 56,5 am 24. Bund)


def rechteck(b, h, r=0.0, n=0):
    c = CS.square((b, h)).translate((-b / 2, -h / 2))
    return c.offset(-r, RUND, 2.0, n or 24).offset(r, RUND, 2.0, n or 24) if r > 0 else c


def kreis(r, n=40): return CS.circle(r, n)
def poly(p): return CS([np.asarray(p, float)], NZ)
def prisma(cs, z0, z1):
    cs = cs.simplify(0.05)
    return cs.extrude(z1 - z0).translate((0, 0, z0)) if not cs.is_empty() and z1 > z0 else M()
def vereint(l):
    l = [k for k in l if not k.is_empty()]
    return M.batch_boolean(l, m3.OpType.Add) if l else M()
def vereint2(l):
    l = [k for k in l if not k.is_empty()]
    return CS.batch_boolean(l, m3.OpType.Add) if l else CS()
def glatt(cs, r): return cs.offset(-r, RUND, 2.0, 24).offset(2 * r, RUND, 2.0, 24).offset(-r, RUND, 2.0, 24)


def band(cs, profil, innen, schritt=1.2):
    """Geschlossener Ring entlang des Umrisses als EIN Netz: außen folgt er dem Profil [(Einzug, z), …] von unten nach oben,
    innen ist er eine senkrechte Wand beim Einzug `innen`. Alle Linien haben gleich viele Punkte (Versatz je Punkt entlang der Normalen),
    deshalb entstehen keine fast deckungsgleichen Kanten. Der Umriss muss glatter sein als der größte Einzug (Radius > innen)."""
    pts = np.asarray(max(cs.to_polygons(), key=len), float)
    if np.sum(pts[:, 0] * np.roll(pts[:, 1], -1) - np.roll(pts[:, 0], -1) * pts[:, 1]) < 0: pts = pts[::-1]     # gegen den Uhrzeigersinn
    d = np.linalg.norm(np.roll(pts, -1, 0) - pts, axis=1); L = d.sum(); n = int(L / schritt)
    u = np.concatenate([[0], np.cumsum(d)]); q = np.linspace(0, L, n, endpoint=False); zu = np.vstack([pts, pts[:1]])
    P = np.stack([np.interp(q, u, zu[:, 0]), np.interp(q, u, zu[:, 1])], 1)
    for _ in range(3): P = (np.roll(P, 1, 0) + 2 * P + np.roll(P, -1, 0)) / 4                                    # Ecken der Abtastung glätten
    tg = np.roll(P, -1, 0) - np.roll(P, 1, 0); tg /= np.linalg.norm(tg, axis=1)[:, None]
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)                                                                     # zeigt nach innen
    linien = [(e, z) for e, z in profil] + [(innen, profil[-1][1]), (innen, profil[0][1])]
    V = np.vstack([np.column_stack([P + e * nrm, np.full(n, z)]) for e, z in linien]); m = len(linien); T = []
    for j in range(m):
        a0, b0 = j * n, ((j + 1) % m) * n
        for i in range(n):
            i2 = (i + 1) % n
            T += [(a0 + i, a0 + i2, b0 + i2), (a0 + i, b0 + i2, b0 + i)]
    k = M(m3.Mesh(V.astype(np.float32), np.array(T, np.uint32)))
    if k.volume() < 0: k = M(m3.Mesh(V.astype(np.float32), np.array(T, np.uint32)[:, ::-1]))
    assert k.status() == m3.Error.NoError and k.volume() > 0, k.status()
    return k


def zylinder(r, p0, p1, n=32):
    """Zylinder von p0 nach p1."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float); v = p1 - p0; L = np.linalg.norm(v); v /= L
    z = M.cylinder(L, r, r, n)
    a = np.cross([0, 0, 1], v); s = np.linalg.norm(a)
    if s > 1e-9:
        w = math.degrees(math.atan2(s, v[2])); a /= s
        R = trimesh.transformations.rotation_matrix(math.radians(w), a)[:3, :]
        z = z.transform(R)
    elif v[2] < 0:
        z = z.mirror((0, 0, 1))
    return z.translate(tuple(p0))


ZIFFERN = {3: "III", 5: "V", 7: "VII", 9: "IX", 12: "XII", 15: "XV", 17: "XVII", 19: "XIX", 21: "XXI", 24: "XXIV"}
def strich(a, b, w):
    a, b = np.asarray(a, float), np.asarray(b, float); v = b - a; L = np.linalg.norm(v)
    return rechteck(L, w).translate((L / 2, 0)).rotate(math.degrees(math.atan2(v[1], v[0]))).translate(tuple(a)) + kreis(w / 2, 12).translate(tuple(a)) + kreis(w / 2, 12).translate(tuple(b))


# Fette gebrochene Schrift nach Toms Nahaufnahme der „III“: breite, oben und unten schräg geschnittene Balken mit kleinen Zacken.
# Flächen im Einheitskasten (Höhe 1); Wert = (Breite, [Polygone]).
GLYPH = {
    "I": (0.40, [[(0.04, 0.10), (0.38, 0.00), (0.38, 0.30), (0.46, 0.36), (0.38, 0.44), (0.38, 0.90), (0.04, 1.00), (0.04, 0.66), (-0.05, 0.58), (0.04, 0.50)]]),
    "X": (0.92, [[(0.00, 1.00), (0.34, 0.92), (0.92, 0.08), (0.92, 0.00), (0.58, 0.08), (0.00, 0.92)],                       # fetter Balken links oben → rechts unten
                 [(0.02, 0.04), (0.20, 0.00), (0.90, 0.92), (0.88, 1.00), (0.72, 0.98), (0.04, 0.10)],                       # dünner Balken links unten → rechts oben
                 [(0.20, 0.50), (0.46, 0.60), (0.72, 0.50), (0.46, 0.40)]]),                                                 # Raute in der Mitte
    "V": (0.90, [[(0.00, 1.00), (0.34, 0.92), (0.50, 0.30), (0.66, 0.84), (0.60, 0.98), (0.90, 0.92), (0.62, 0.00), (0.34, 0.00), (0.04, 0.90)]]),
}
DUENN = {"I": 0.34, "X": 0.14, "V": 0.16}                                           # dünnste Stelle je Zeichen (Anteil der Zeichenbreite bzw. Höhe)


def ziffer(text, h, t_min, breite_max):
    """Römische Ziffer, mittig um (0, 0). h = Höhe im echten Maß, t_min = dünnster druckbarer Strich.
    Kleine Zeichen werden breiter gezogen und so weit aufgedickt, dass der dünnste Strich noch druckbar ist."""
    sx = max(h, 3.4 * t_min)                                                         # Zeichenbreite je Einheit: nie schmaler, als die Düse auflösen kann
    d = max(0.0, max((t_min - DUENN[c] * min(sx, h)) / 2 for c in set(text)))        # Aufdickung
    luecke = max(0.16 * sx, 1.1 * t_min + 2 * d)
    ges = sum(GLYPH[c][0] * sx for c in text) + luecke * (len(text) - 1)
    if ges > breite_max:
        f = (breite_max - luecke * (len(text) - 1)) / (ges - luecke * (len(text) - 1)); sx *= f; ges = breite_max
    teile, x = [], 0.0
    for c in text:
        b, polys = GLYPH[c]
        g = vereint2([CS([np.array(pl, float) * (sx, h)], m3.FillRule.NonZero) + CS([np.array(pl, float) * (sx, h)], m3.FillRule.Negative) for pl in polys])
        if d > 0: g = g.offset(d, RUND, 2.0, 8) ^ CS.square((b * sx + 2 * d, h)).translate((-d, 0))     # oben/unten nicht höher werden
        teile.append(g.translate((x, 0))); x += b * sx + luecke
    return vereint2(teile).translate((-ges / 2, -h / 2))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--laenge", type=float, default=200.0); ap.add_argument("--wolken", type=int, default=3, help="0 keine · 1 grob · 2 ruhig · 3 fein (wie im Bild, für Dunkelrot)")
    ap.add_argument("--duese", type=float, default=0.25, help="Düse, auf die die Feinheiten abgestimmt werden: 0.25 (alle Köpfe, Standard seit 16.11.) oder 0.4")
    ap.add_argument("--breite", type=float, default=320.0, help="größte Korpusbreite in echten mm")
    ap.add_argument("--bauch", type=int, default=1, help="Bauch-Ausfräsung auf der Rückseite (braucht Stützen)")
    ap.add_argument("--pruef", action="store_true"); ap.add_argument("--ziel", default=str(HIER)); ap.add_argument("--name", default="gitarre_rundum")
    a = ap.parse_args()
    D = json.load(open(HIER / "gitarre_rundum_daten.json"))
    # Quermaß des Korpus: aus dem Bild 316 mm, Maßblatt 320 mm, Vergleichs-CAD einer T-Form 324 mm → auf 320 mm gestellt (Hals und Mittelteile bleiben)
    QX = a.breite / 316.0
    for kx in ("korpus", "regler", "schalter", "gurt"): D[kx] = [[q[0] * QX, q[1]] for q in D[kx]]
    for kx in ("wolken", "wolken_viel", "wolken_fein"): D[kx] = [[[q[0] * QX, q[1]] for q in pl] for pl in D[kx]]
    S_END = D["s_ende"]; Y = lambda s: S_END - s
    F0 = a.laenge / 978.0; p = lambda mm: mm / F0                 # Druckmaß → echtes Maß
    D25 = a.duese < 0.3; FEIN = 0.28 if D25 else 0.46                               # dünnster Strich im Druck
    FUGE = p(0.03); E = p(0.32 if D25 else 0.36); SLAB = p(0.60)                     # E = Tiefe der Einlagen (4 Schichten 0,08 bzw. 3 × 0,12)
    xy = lambda q: (q[0], Y(q[1]))

    # ---------------- Korpus-Umriss: unterer Bogen rechts = Spiegel von links (rechts war das Foto gestört) ----------------
    K = poly([xy(q) for q in D["korpus"]])
    unten_r = CS.square((400, Y(690) + 50)).translate((0, -50))
    unten_l = (K ^ CS.square((400, Y(690) + 50)).translate((-400, -50)))
    K = (K - unten_r) + unten_l.mirror((1, 0))
    K = glatt(K, 5.0) + rechteck(2 * halb(440), 70).translate((0, Y(440)))            # Halsbereich sicher geschlossen
    K = K.offset(-14, RUND, 2.0, 48).offset(14, RUND, 2.0, 48)                         # Nase vom Gurtknopf im Foto und kleine Wellen weg
    K = glatt(K, 6.0).simplify(0.05)
    kb = K.bounds(); print(f"Korpus {kb[2] - kb[0]:.0f} × {kb[3] - kb[1]:.0f} mm")

    # ---------------- 2D-Flächen auf der Decke ----------------
    def pu_fuss(s): return (rechteck(73, 41, 4) + rechteck(90, 13, 5)).translate((0, Y(s)))
    PU = [D["tonabnehmer"][0][1], D["tonabnehmer"][1][1]]
    steg_fl = rechteck(84, 43, 3).translate((0, Y(MENSUR + 13.5)))
    regler = [(q[0], Y(q[1])) for q in D["regler"]]
    sA, sB = (np.array(xy(q)) for q in D["schalter"])                                  # Klingenschalter: zwei Schrauben, dazwischen Schlitz mit Hebel
    schlitz = vereint2([strich(sA + 0.24 * (sB - sA), sA + 0.76 * (sB - sA), p(0.55))] + [kreis(p(0.55), 20).translate(tuple(q)) for q in (sA, sB)])
    gb_ende = bund_s(24) + 7.0
    gb = poly([(-21, Y(0)), (21, Y(0)), (halb(gb_ende), Y(gb_ende)), (-halb(gb_ende), Y(gb_ende))])
    hals_fl = poly([(-halb(380) - 0.02, Y(380)), (halb(380) + 0.02, Y(380)), (halb(gb_ende) + 0.02, Y(gb_ende) - 0.02), (-halb(gb_ende) - 0.02, Y(gb_ende) - 0.02)])
    koepfe = vereint2([kreis(2.4, 16).translate(((i - 2.5) * 10.5, Y(MENSUR + 36.0))) for i in range(6)])
    hw = vereint2([pu_fuss(s) for s in PU] + [steg_fl, koepfe] + [kreis(9.5).translate(q) for q in regler] + [schlitz])
    innen = K.offset(-(p(0.38 + 0.45) if a.duese < 0.3 else SLAB + p(0.9)), RUND, 2.0, 24)
    wl = {2: D["wolken_viel"], 3: D["wolken_fein"]}.get(a.wolken, D["wolken"])
    W = CS()
    if a.wolken:
        W = CS([np.array([xy(q) for q in pl]) for pl in wl], m3.FillRule.EvenOdd) ^ innen
        W = W - hw.offset(p(0.5), RUND) - hals_fl.offset(p(0.5), RUND)
        fw = 0.5 * FEIN - 0.01; W = W.offset(p(fw), RUND).offset(-p(2 * fw), RUND).offset(p(fw), RUND)          # erst schmale rote Stege schließen, dann schmale schwarze Zungen weg
        W = vereint2([c for c in W.decompose() if c.area() > p(1.3 * FEIN) ** 2])
        W = W.offset(0.07, RUND, 2.0, 12).simplify(0.06)                                   # Engstellen ohne Breite verschmelzen (sonst Kanten mit vier Flächen)
    z_slab = T_B - SLAB
    if D25:                                                                           # feine Düse: schmale gerundete Kante als schwarzer Rand, Decke bis dorthin rot
        RK, RB = p(0.30), p(0.38)
        decke_in = K.offset(-(RB + FUGE), RUND, 2.0, 24) - hw - hals_fl - W.offset(FUGE, RUND)
        rund = [(0.0, z_slab)] + [(RK * (1 - math.cos(w)), T_B - RK + RK * math.sin(w)) for w in np.linspace(0, math.pi / 2, 6)]
        rot = [prisma(decke_in, z_slab, T_B), band(K, rund, RB) - prisma(hals_fl, z_slab - 1, T_B + 1)]
        schwarz = [prisma(hw.offset(-FUGE), z_slab, T_B)]; dunkel = [prisma(W, z_slab, T_B)]
    else:
        decke_in = K.offset(-(SLAB + 0.35), RUND, 2.0, 24) - hw - hals_fl - W.offset(FUGE, RUND)
        rund = [(SLAB * (1 - math.cos(w)), z_slab + SLAB * math.sin(w)) for w in np.linspace(0, math.pi / 2, 7)]
        rot = [prisma(decke_in, z_slab, T_B), band(K, rund, SLAB + 0.6) - prisma(hals_fl, z_slab - 1, T_B + 1)]
        schwarz = [prisma(W, z_slab, T_B), prisma(hw.offset(-FUGE), z_slab, T_B)]; dunkel = []
    grau, weiss, schneider = [], [], []

    # ---------------- Korpus-Kern (grau) mit Fase unten ----------------
    FASE = p(0.6)
    kern = vereint([prisma(K.offset(-FASE - 0.9, RUND, 2.0, 24), 0, z_slab), band(K, [(FASE, 0.0), (0.0, FASE), (0.0, z_slab)], FASE + 1.5)])
    grau.append(prisma(hals_fl, z_slab - 0.5, ZFB))
    # Rückseite: Deckel und sechs Saitenhülsen (schwarz, bündig)
    deckel = rechteck(38, 100, 18).translate((92, Y(661)))
    huelsen = vereint2([kreis(p(0.8), 24).translate(((i - 2.5) * 10.5, Y(MENSUR + 11))) for i in range(6)])
    schwarz.append(prisma(deckel + huelsen, 0, E)); schneider.append(prisma(deckel + huelsen, -5, E))
    if a.bauch:                                                                         # Bauch-Ausfräsung: flache Mulde am oberen Bogen der Bassseite
        ex = K.bounds()[0]
        schneider.append(M.sphere(1.0, 64).scale((62, 115, 15)).translate((ex - 4, Y(520), -1.0)))

    # ---------------- Tonabnehmer, Steg, Regler, Schalter ----------------
    for i, s in enumerate(PU):
        hoch = T_B + (9.0 if i == 0 else 10.5); c = (0, Y(s))
        schwarz.append(prisma(rechteck(70, 38, 3).translate(c), T_B - 0.3, T_B + 3))
        for dy in (-9.6, 9.6):
            sp = rechteck(68, 18.2, 9.0).translate((0, Y(s) + dy))
            ring = sp.offset(-p(0.5), RUND, 2.0, 24) - sp.offset(-p(1.0), RUND, 2.0, 24)
            schwarz += [prisma(sp, T_B + 2.7, hoch - E), prisma(sp.offset(-0.05) - ring.offset(FUGE), hoch - E - 0.3, hoch)]
            rot.append(prisma(ring, hoch - E, hoch))
            pole = vereint2([kreis(p(0.42), 16).translate(((j - 2.5) * 10.2, Y(s) + dy)) for j in range(6)])
            schwarz.append(prisma(pole, hoch - 0.3, hoch + p(0.24)))
    # --- Brücke nach Toms Nahaufnahme: Grundplatte, hochgezogene Rückwand mit runden Ecken, sechs U-förmige Reiter, Federn, Schraubenköpfe hinten ---
    zs = T_B + 3.2; ys = Y(MENSUR + 13.5); WD = p(1.6 * FEIN)                          # WD = Wandstärke der Rückwand
    platte = rechteck(84, 43, 3).translate((0, ys))
    schwarz.append(prisma(platte.offset(-0.05), T_B - 0.3, zs))
    wand = platte - rechteck(84 - 2 * WD, 43, 2).translate((0, ys + WD + 9))           # Rückwand und kurze Seitenwangen
    schwarz.append(prisma(wand, zs - 0.3, zs + 9.5))
    wange = platte - rechteck(84 - 2 * WD, 43, 2).translate((0, ys + WD - 6))          # Wangen laufen nach vorn niedriger aus
    schwarz.append(prisma(wange, zs - 0.3, zs + 4.5))
    for i in range(6):
        x = (i - 2.5) * 10.5; y_v, y_h = Y(MENSUR - 7), Y(MENSUR + 17)                  # Reiter von vorn (Saitenauflage) bis hinten (rundes Ende)
        rt = (rechteck(9.3, 24, 0.6).translate((x, (y_v + y_h) / 2)) - rechteck(9.3, 6).translate((x, y_h + 3))) + kreis(4.65, 28).translate((x, y_h + 4.65))
        rt = rt ^ rechteck(9.3, 40).translate((x, (y_v + y_h) / 2))
        lang = (rechteck(3.2, 10.5).translate((x, Y(MENSUR + 8.2))) + kreis(1.6, 16).translate((x, Y(MENSUR + 13.4))) + kreis(1.6, 16).translate((x, Y(MENSUR + 3.0))))   # Langloch im U
        schwarz += [prisma(rt, zs - 0.3, zs + 4.6), prisma(rt.offset(-0.05) - lang, zs + 4.3, zs + 7.4)]
        schwarz.append(prisma(rechteck(9.3, p(1.3 * FEIN)).translate((x, Y(MENSUR + 0.3))), zs + 7.1, zs + 8.3))                # Auflagekante der Saite
        for dx in (-2.6, 2.6): schwarz.append(prisma(kreis(p(0.6 * FEIN), 10).translate((x + dx, Y(MENSUR - 4.2))), zs + 7.1, zs + 7.4 + p(0.16)))   # zwei Madenschrauben
        yf0, yf1 = Y(MENSUR + 29.5), Y(MENSUR + 17.5)                                   # Feder zwischen Reiter und Rückwand
        schwarz.append(prisma(rechteck(3.0, yf1 - yf0 + 1.5).translate((x, (yf0 + yf1) / 2)), zs - 0.3, zs + 3.4))
        for j in range(5): schwarz.append(prisma(rechteck(4.6, p(0.95 * FEIN)).translate((x, yf0 + 1.6 + j * (yf1 - yf0 - 3.2) / 4)), zs - 0.3, zs + 4.4))
        yk = Y(MENSUR + 36.0)                                                           # Schraubenkopf hinter der Rückwand (als Zapfen bis zur Decke, damit nichts frei schwebt)
        schwarz += [prisma(kreis(2.4, 16).translate((x, yk)), T_B - 0.3, zs + 5.2), M.sphere(2.4, 16).scale((1, 1, 0.6)).translate((x, yk, zs + 5.2))]
    # --- Regler: unten glatt, drei schmale Ringe, oben Kappe mit Fase, Madenschraube seitlich ---
    for q in regler:
        r = 9.5; g = p(0.8 * FEIN); kz = lambda r0, r1, z0, z1: M.cylinder(z1 - z0, r0, r1, 48).translate((q[0], q[1], z0))
        teile_r = [kz(r, r, T_B - 0.3, T_B + 6.8), kz(r - g, r - g, T_B + 6.5, T_B + 18.0)]
        for z0 in (8.6, 11.3, 14.0):                                                    # Ringe: unten 45° angeschrägt (stützfrei), oben flach
            teile_r += [kz(r - g, r, T_B + z0 - g, T_B + z0), kz(r, r, T_B + z0 - 0.02, T_B + z0 + 1.0)]
        teile_r += [kz(r - g, r, T_B + 16.2 - g, T_B + 16.2), kz(r, r, T_B + 16.18, T_B + 18.3), kz(r, r - 1.1, T_B + 18.28, T_B + 19.4)]   # Kappe mit Fase
        knopf = vereint(teile_r)
        ri = np.array([0.55, -0.83]); m0 = np.array([q[0], q[1], T_B + 4.2]); r3 = np.array([ri[0], ri[1], 0.0])
        schwarz.append(knopf - zylinder(p(0.6 * FEIN), m0 + (r - 2.0) * r3, m0 + (r + 3) * r3, 12))
    # --- Klingenschalter: zwei Schrauben, Schlitz, dünner heller Schaft, schwarze Kegelkappe ---
    for q in (sA, sB): schwarz += [prisma(kreis(p(0.55), 20).translate(tuple(q)), T_B - 0.3, T_B + p(0.16)), M.sphere(p(0.55), 20).scale((1, 1, 0.45)).translate((q[0], q[1], T_B + p(0.16)))]
    ach = (sA - sB) / np.linalg.norm(sA - sB); w = math.radians(66)                     # Hebel lehnt zur oberen Schraube, 66° steil (stützfrei)
    ri3 = np.array([ach[0] * math.cos(w), ach[1] * math.cos(w), math.sin(w)])
    f0 = np.array([*(sA + 0.62 * (sB - sA)), T_B - 0.3])
    schaft = zylinder(p(0.8 * FEIN), f0, f0 + 9.5 * ri3, 14)
    kappe = M.batch_hull([M.sphere(p(0.8 * FEIN) + 0.05, 16).translate(tuple(f0 + 9.3 * ri3)), M.sphere(p(0.6), 20).translate(tuple(f0 + 16.0 * ri3)),
                          M.sphere(p(0.34), 16).translate(tuple(f0 + 21.5 * ri3))])                 # Kegel weitet sich flach genug für den Druck ohne Stützen
    schwarz.append(kappe); schaft_k = schaft - kappe
    # ---------------- Gurtknöpfe und Buchse an der Zarge ----------------
    def gurt(pt, n):
        pt, n = np.array([pt[0], pt[1], T_B / 2]), np.array([n[0], n[1], 0.0]) / np.hypot(*n)
        k = vereint([zylinder(4.5, pt - 4 * n, pt + 9 * n), zylinder(7.0, pt + 8 * n, pt + 12 * n)])
        return k, zylinder(4.5, pt - 4 * n, pt + 30 * n)
    rand = np.vstack([np.asarray(c) for c in K.to_polygons()])
    def am_rand(ziel): return rand[np.argmin(np.linalg.norm(rand - np.asarray(ziel), axis=1))]
    for ziel, n in ((xy(D["gurt"][0]), (-0.35, 1.0)), ((0.0, 0.0), (0.0, -1.0))):
        k, s_ = gurt(am_rand(ziel), n); schwarz.append(k); schneider.append(s_)
    bp = am_rand((118, 28)); mitte = np.array([0.0, Y(690)]); nb = (bp - mitte); nb /= np.linalg.norm(nb)
    b3, n3 = np.array([bp[0], bp[1], T_B / 2]), np.array([nb[0], nb[1], 0.0])
    buchse = zylinder(9.5, b3 - 3.0 * n3, b3 + p(0.2) * n3, 40) - zylinder(p(0.8), b3 - 2.4 * n3, b3 + 5 * n3, 24)
    schwarz.append(buchse); schneider.append(zylinder(9.5, b3 - 3.0 * n3, b3 + 30 * n3, 40))

    # ---------------- Griffbrett, Bünde, Ziffern, Sattel ----------------
    wb = p(0.55); bund_fl = []
    for n in range(1, N_BUND + 1):
        s = bund_s(n); bund_fl.append(rechteck(2 * (halb(s) - 0.02), wb).translate((0, Y(s))))
    buende = vereint2(bund_fl)
    zf = []                                                                             # Ziffern wie am Original, auch XIX, XXI, XXIV (dort nur so fein, wie die Düse es kann)
    for n, text in ZIFFERN.items():
        s0, s1 = bund_s(n - 1), bund_s(n); zelle = s1 - s0 - wb - p(0.4)
        h = min(max(0.62 * zelle, min(0.94 * zelle, p(1.0))), p(3.6))
        g = ziffer(text, h, p(FEIN), 2 * halb(s0) - p(1.3))
        zf.append(g.translate((0, Y((s0 + s1) / 2))))
    ziffern = vereint2(zf) ^ gb.offset(-p(0.3))
    schwarz += [prisma(gb, ZFB, ZF - E), prisma(gb.offset(-0.05) - (buende + ziffern).offset(FUGE, RUND), ZF - E - 0.3, ZF)]
    weiss += [prisma(buende, ZF - E, ZF + p(0.3)), prisma(ziffern, ZF - E, ZF)]
    schwarz.append(prisma(rechteck(42, 5.2).translate((0, Y(-2.3))), ZFB, ZF + p(0.36)))          # Sattel (schwarz)

    # ---------------- Hals (grau): Schnitte, konvex verbunden ----------------
    def schnitt(s, n=30, d=None, e=0.75):
        w = halb(max(s, 0)); d = d or 14.0 + 2.0 * np.clip((s - bund_s(1)) / (bund_s(12) - bund_s(1)), 0, 1.0)
        th = np.linspace(0, math.pi, n)
        return np.stack([w * np.cos(th), np.full(n, Y(s)), ZFB - d * np.sin(th) ** e], 1)
    ss = [-5.5, 0, 36, 80, 130, 180, 230, 280, 324, 400, gb_ende - 1]
    grau.append(vereint([M.hull_points(np.vstack([schnitt(s0), schnitt(s1)])) for s0, s1 in zip(ss[:-1], ss[1:])]))
    fuss = prisma(rechteck(2 * halb(445), 76, 10).translate((0, Y(447))), 4.0, z_slab - 4)
    frei = prisma(CS.square((600, 700)).translate((-300, -50)) - hals_fl.offset(-0.02), z_slab, 300)      # über Deckenhöhe bleibt nur der Hals selbst
    ferse = [(318, None, 0.75), (345, 17.5, 0.70), (366, 21.5, 0.62), (384, 28.0, 0.52), (398, 36.0, 0.42)]        # Halsfuß: wird zum Korpus hin tiefer und kantiger
    fs = [schnitt(s, d=d, e=e) for s, d, e in ferse]
    grau.append(vereint([M.hull_points(np.vstack([a_, b_])) for a_, b_ in zip(fs[:-1], fs[1:])] + [M.batch_hull([M.hull_points(fs[-1]), fuss])]) - frei)
    # rote Streifen im Halsrücken (wie verleimte Streifen, von hinten eingelassen)
    zs_top = ZFB - 15.3 + p(0.7)
    box = vereint([M.cube((p(0.62), 372, 60)).translate((x - p(0.31), Y(382), zs_top - 60)) for x in (-7.5, 7.5)])
    hals_roh = vereint(grau[1:]); streifen = hals_roh ^ box
    streifen = streifen - prisma(K.offset(3), -10, 200) ; rot.append(streifen)
    grau = [grau[0], hals_roh - (box ^ prisma(CS.square((100, 500)).translate((-50, Y(382) - 0.01)) - K.offset(3), -100, 200))]

    # ---------------- Kopfplatte (im eigenen Rahmen: x quer, y = Abstand vom Sattel, Fläche bei z = 0), dann kippen ----------------
    HS = p(0.5); KR = 0.34 if D25 else 0.5                                             # KR = Breite des hellen Kopfplatten-Rands
    ko = poly([(q[0], -q[1]) for q in D["kopf"]])
    ko = glatt(ko + rechteck(40, 8).translate((0.6, 9.0)), 3.0) ^ CS.square((300, 300)).translate((-150, 6.2))
    mech = [np.array([q[0], -q[1]]) for q in D["mechaniken"]]
    achse = (mech[-1] - mech[0]) / np.linalg.norm(mech[-1] - mech[0]); raus = np.array([-achse[1], achse[0]])      # zeigt nach links außen
    scheiben = vereint2([kreis(5.4, 24).translate(tuple(m_)) for m_ in mech])
    deckelchen = poly([(-6.5, 7.2), (6.5, 7.2), (4.2, 32), (0, 37), (-4.2, 32)]).offset(-1.5, RUND).offset(1.5, RUND).translate((0.6, 0))
    k_rot = ko.offset(-p(KR), RUND, 2.0, 24) - CS.square((300, 14.5)).translate((-150, 0)) - scheiben - deckelchen.offset(FUGE, RUND)
    kg = [prisma(ko, -KOPF_DICKE, -HS), prisma(ko - ko.offset(-p(KR), RUND, 2.0, 24) + (ko ^ CS.square((300, 14.5)).translate((-150, 0))) - deckelchen.offset(FUGE, RUND) - scheiben, -HS - 0.4, 0)]
    kr = [prisma(k_rot, -HS, 0)]
    ks = [prisma(deckelchen, -HS, p(0.3)), prisma(scheiben.offset(-FUGE), -HS, 1.6)]
    for m_ in mech:
        ks.append(prisma(kreis(3.3, 20).translate(tuple(m_)), 1.3, 8.5))
        ks.append(prisma(kreis(8.6, 28).translate(tuple(m_)), -KOPF_DICKE - 11, -KOPF_DICKE))                    # Gehäuse hinten
        c = m_ + 24.5 * raus; zc = -KOPF_DICKE - 5.6
        ks.append(zylinder(2.7, (m_[0], m_[1], zc), (c[0], c[1], zc), 20))
        fl = CS.circle(1.0, 32).scale((8.5, 7.0)).rotate(math.degrees(math.atan2(raus[1], raus[0]))).translate(tuple(c))
        ks.append(prisma(fl, zc - 3.2, zc + 3.2))
    wurzel = prisma(rechteck(40, 26, 6).translate((0.6, 19)), -KOPF_DICKE, -HS - 0.8)
    Z_H = ZFB + 1.0
    def kippen(k): return k.translate((0, -5.5, 0)).rotate((-KOPF_WINKEL, 0, 0)).translate((0, Y(0) + 5.5, Z_H))
    ueber = kippen(M.cube((300, 400, 80)).translate((-150, 5.5, -HS - 0.6)))                             # Übergang bleibt unter der Kopf-Deckschicht
    grau += [kippen(vereint(kg)), M.batch_hull([M.hull_points(np.vstack([schnitt(-5.5), schnitt(6)])), kippen(wurzel)]) - ueber]
    rot.append(kippen(vereint(kr))); schwarz.append(kippen(vereint(ks)))

    # ---------------- zusammensetzen ----------------
    if a.pruef:
        for nm, l in (("rot", rot), ("schwarz", schwarz), ("grau", grau)):
            for i, k in enumerate(l):
                me = k.to_mesh(); tt = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts, process=True)
                if not tt.is_watertight or k.status() != m3.Error.NoError: print("   undicht:", nm, i, k.status(), k.volume())
    if a.pruef:
        def kn(k):
            me = k.to_mesh(); tt = trimesh.Trimesh(me.vert_properties[:, :3].astype(np.float32), me.tri_verts, process=True)
            u, c = np.unique(tt.edges_sorted, axis=0, return_counts=True)
            if (c != 2).any(): print("      ", np.round(tt.vertices[u[c != 2]][:5].reshape(-1, 6), 2).tolist(), np.unique(c))
            return int((c != 2).sum())
        print("   Kantenfehler rot0", kn(rot[0]), "rot1", kn(rot[1]), "rot0+1", kn(rot[0] + rot[1]), "decke_in Teile", len(decke_in.decompose()), "W", len(W.decompose()))
    # ---------------- echte Saiten zum Einfädeln (Draht bis 0,3 mm): Löcher durch den Korpus, Kerben in Reitern und Sattel, Löcher in der Kopfplatte ----------------
    RL = p(0.36); KB = p(0.34); bohr = []                                             # Lochradius und Kerbenbreite im Druckmaß
    for i in range(6):
        xs_, xn = (i - 2.5) * 10.5, (i - 2.5) * 7.0
        bohr.append(M.cylinder(T_B + 30, RL, RL, 14).translate((xs_, Y(MENSUR + 11), -5)))                                  # durch Korpus und Reiter-Langloch
        bohr.append(M.cube((KB, 8, 6)).translate((xs_ - KB / 2, Y(MENSUR + 0.3) - 4, zs + 8.3 - p(0.2))))                   # Kerbe in der Saitenauflage
        bohr.append(M.cube((KB, 9, 6)).translate((xn - KB / 2, Y(-2.3) - 4.5, ZF + p(0.36) - p(0.22))))                     # Kerbe im Sattel
        v = mech[i] - np.array([xn, 2.0]); v /= np.linalg.norm(v); hq = mech[i] - 6.2 * v                                   # Loch kurz vor der Mechanik-Achse
        bohr.append(kippen(M.cylinder(KOPF_DICKE + 30, RL, RL, 14).translate((hq[0], hq[1], -KOPF_DICKE - 18))))
    bohr = vereint(bohr)
    rot_k, schwarz_k, weiss_k = vereint(rot), vereint(schwarz) - zylinder(p(0.8 * FEIN), f0 - 3 * ri3, f0 + 9.5 * ri3, 14), vereint(weiss)
    grau.append(schaft_k - prisma(CS.square((900, 1200)).translate((-450, -100)), -50, z_slab))
    grau_k = vereint([kern - vereint(schneider)] + grau)
    koerper = {"grau": grau_k, "rot": rot_k, "schwarz": schwarz_k, "weiss": weiss_k}
    if dunkel: koerper["dunkelrot"] = vereint(dunkel)
    koerper = {n: k - bohr for n, k in koerper.items()}
    namen = list(koerper)
    for i in range(len(namen)):
        for j in range(i + 1, len(namen)):
            v = (koerper[namen[i]] ^ koerper[namen[j]]).volume()
            if v > 0.5 and a.pruef:
                for ii, k1 in enumerate({"grau": [kern] + grau, "rot": rot, "schwarz": schwarz, "weiss": weiss, "dunkelrot": dunkel}[namen[i]]):
                    for jj, k2 in enumerate({"grau": [kern] + grau, "rot": rot, "schwarz": schwarz, "weiss": weiss, "dunkelrot": dunkel}[namen[j]]):
                        vv = (k1 ^ k2).volume()
                        if vv > 0.3: print("     ", namen[i], ii, namen[j], jj, round(vv, 1))
            if v > 0.5: print(f"  Überschneidung {namen[i]}/{namen[j]}: {v:.1f} mm³ (echt)")
    boden = M.cube((2000, 3000, 200)).translate((-1000, -500, -200))                                   # Mechaniken enden plan auf dem Bett
    koerper = {n: k - boden for n, k in koerper.items()}
    alle = vereint(list(koerper.values())); bb = alle.bounding_box()
    f = a.laenge / (bb[4] - bb[1]); print(f"Gesamtlänge echt {bb[4] - bb[1]:.0f} mm → Faktor {f:.4f} (Maßstab 1:{1 / f:.2f}); Annahme war {F0:.4f}")
    ziel = Path(a.ziel); ziel.mkdir(parents=True, exist_ok=True)
    for n, k in koerper.items():
        k = k.translate((-(bb[0] + bb[3]) / 2, -bb[1], -bb[2])).scale((f, f, f))
        teile = [t_ for t_ in k.decompose() if t_.volume() > 0.004]
        k = vereint(teile)
        me = k.to_mesh(); t = trimesh.Trimesh(me.vert_properties[:, :3], me.tri_verts, process=True)
        t.update_faces(t.nondegenerate_faces()); t.remove_unreferenced_vertices()        # in 32 Bit zusammengefallene Punkte: leere Dreiecke weg
        pf = ziel / f"{a.name}_{n}.stl"; t.export(pf)
        print(f"{pf.name}: dicht={t.is_watertight}, {t.volume / 1000:.2f} cm³, {len(t.faces)} Dreiecke, Teile {len(teile)}, Maße {np.round(t.extents, 1).tolist()}")


if __name__ == "__main__":
    main()

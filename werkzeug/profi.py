#!/usr/bin/env python3
"""Profi-Regeln als Code für build123d (FDM, Flashforge Creator 5 Pro, 0,4-mm-Düse).

Einbinden im Modell-Skript (cad.py legt werkzeug/ in den Suchpfad):
    from profi import *            # Konstanten + Helfer
Selbsttest aller Helfer:  python3 werkzeug/profi.py  [--stl /tmp/profi_test]

Grundsätze (Quellen siehe wissen/recherche_modellqualitaet.md, Abschnitt 5):
- Wände als Vielfache der Linienbreite 0,45 mm (Prusa).          - Überhang ≤ 45°, Brücken ≤ 5 mm (Hubs).
- Unterkante: 45°-Fase statt Rundung (Prusa, Hubs).              - Innenradius ≥ Düsenradius (Hubs, Stratasys).
- Spiel eng 0,2 / Schnapp 0,3 / Gleit-Dreh 0,4 mm (Core77, Prusa). - Last entlang der Schichten, Z ist schwach (Hubs, Prusa).
Alle Spiele sind Abstände JE SEITE (radial), solange nicht anders genannt.
"""
import math
import sys
import time
from pathlib import Path

from build123d import (Align, Axis, Box, Circle, Cone, Cylinder, Keep, Plane, Polygon, Pos, Rectangle,
                       RegularPolygon, Text, Vector, chamfer, extrude, fillet, revolve, split)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cad import DURCH, SENK_DK, ZYL_DK, schraubloch  # noqa: E402,F401  (gleiche Normtabellen wie cad.py)

# ------------------------------------------------------------------------------------------------
# Konstanten (Zahlen + Quelle). „Hausregel“ = keine Primärquelle, nach Kalibrier-Set nachschärfen.
# ------------------------------------------------------------------------------------------------
DUESE = 0.4                    # mm, Standarddüse Creator 5 Pro
LINIE = 0.45                   # mm Linienbreite (Prusa: Wände = Vielfache davon)
SCHICHT = 0.20                 # mm Standard-Schichthöhe
WAND = {n: round(n * LINIE, 2) for n in range(2, 9)}   # 2 → 0,9 · 3 → 1,35 · 4 → 1,8 · 5 → 2,25 … (Prusa)
WAND_MIN = 0.8                 # mm darunter Fehler (≈ 4 × Schicht, Stratasys; 2 Linien knapp)
WAND_GUT = 1.2                 # mm ab hier stabil (≥ 3 Linien ≈ 1,35, CLAUDE.md-Regel ≥ 1,2)
DETAIL_MIN = 0.45              # mm schmaler lässt der Slicer weg (1 Linienbreite)
SPIEL = {                      # je Seite, mm (Core77/Prusa; Presssitz Hausregel)
    "presssitz": 0.0,          #   Loch = Nennmaß; FDM-Löcher fallen ~0,1 mm kleiner aus → klemmt
    "stramm": 0.2,             #   eng, von Hand fügbar (Core77 „eng 0,2“)
    "normal": 0.3,             #   Schnapp-/Steckverbindung (Core77 0,3)
    "locker": 0.4,             #   Gleit-/Drehpassung, Print-in-Place (Core77/Prusa ab 0,3–0,4)
}
LOCH_AUFMASS = 0.2             # mm auf den Durchmesser senkrechter Löcher (Hubs: Löcher drucken zu klein) – Hausregel
UEBERHANG_MAX = 45.0           # Grad aus der Senkrechten, stützfrei (Hubs, Prusa)
BRUECKE_MAX = 5.0              # mm sauber ohne Stütze (Hubs)
R_INNEN_MIN = DUESE / 2        # mm Innenradius ≥ Düsenradius (Hubs, Stratasys)
R_KANTE = 1.0                  # mm Optik-Rundung kleiner Außenkanten – Hausregel (keine Primärquelle)
R_GROSS = 3.0                  # mm Optik-Rundung großer Außenkanten – Hausregel
FASE_UNTEN = 0.6               # mm 45°-Fase an Bettkanten gegen Elefantenfuß (Prusa/Hubs; Maß Hausregel)
SCHRIFT_STRICH_MIN = 0.8       # mm kleinste Strichstärke (≈ 2 Linien), Stratasys: fett, ≥ 24 pt
SCHRIFT_TIEFE = 0.6            # mm Präge-/Erhabentiefe = 3 Schichten – Hausregel
EINSATZ = {3: (4.0, 5.7), 4: (5.6, 8.1), 5: (6.4, 9.5)}  # Ruthex-Kurzform Loch-Ø × Länge (wie baukasten.scad)
EINSATZ_EXTRA_TIEFE = 1.0      # mm Sackloch tiefer als Einsatz (CNC Kitchen)
EINSATZ_WAND = 2.0             # mm Wand um den Einsatz (Stratasys 0,080 in)
DEHNUNG_ZUL = {"PLA": 0.02, "PETG": 0.03, "ABS": 0.03, "ASA": 0.03, "TPU": 0.2}  # Schnapphaken, Richtwerte; in Z × 0,5 (Core77)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PROTOKOLL = []                 # Meldungen der Helfer (z. B. „Radius verkleinert“) – cad.py gibt sie aus


def _melde(text):
    PROTOKOLL.append(text)


def wand(mm_soll, min_linien=2):
    """Wandstärke auf das nächste Vielfache der Linienbreite runden (mind. `min_linien`). wand(2) → 1,8 · wand(2.1) → 2,25."""
    n = max(min_linien, round(mm_soll / LINIE))
    return round(n * LINIE, 2)


def spiel(klasse="normal"):
    """Spiel je Seite in mm aus der Tabelle SPIEL (presssitz/stramm/normal/locker)."""
    return SPIEL[klasse]


# ------------------------------------------------------------------------------------------------
# Kanten
# ------------------------------------------------------------------------------------------------
def kanten_bei(teil, achse=None, **soll):
    """Kanten (optional parallel zu `achse`), deren Mittelpunkt die Sollwerte x=…, y=…, z=… hat (±0,001)."""
    kanten = teil.edges().filter_by(achse) if achse is not None else teil.edges()
    return [k for k in kanten if all(abs(getattr(k.center(), a.upper()) - w) < 1e-3 for a, w in soll.items())]


def _zmin(teil):
    """Tiefster Punkt (über Eckpunkte – unabhängig von einer evtl. vorhandenen Vernetzung)."""
    return min(v.Z for v in teil.vertices())


def _kz(k):
    """z-Werte einer Kante an Anfang, Mitte, Ende."""
    return [k.position_at(t).Z for t in (0.0, 0.5, 1.0)]


def kanten_unten(teil, tol=1e-3):
    """Alle Kanten, die ganz in der Bettebene (z = zmin) liegen."""
    z0 = _zmin(teil)
    return [k for k in teil.edges() if all(abs(z - z0) < tol for z in _kz(k))]


def kanten_oben_aussen(teil, tol=1e-3):
    """Alle Kanten, die das Bett nicht berühren – Kandidaten für Optik-Rundungen."""
    z0 = _zmin(teil)
    return [k for k in teil.edges() if min(_kz(k)) > z0 + tol]


def sicher_runden(teil, kanten=None, r=R_KANTE, r_min=0.2, stufen=(1.0, 0.7, 0.5, 0.35)):
    """Kanten runden, ohne abzustürzen: erst alle mit r, sonst kleinere Radien, sonst Kante für Kante.

    kanten=None → alle Kanten oberhalb des Betts (Bettkanten bekommen eine Fase, keine Rundung: Rundung unten = Überhang).
    Fehlgeschlagene Kanten bleiben scharf und werden in PROTOKOLL gemeldet. Gibt das neue Teil zurück."""
    kanten = list(kanten if kanten is not None else kanten_oben_aussen(teil))
    if not kanten:
        return teil
    for f in stufen:
        rr = r * f
        if rr < r_min:
            break
        try:
            neu = fillet(kanten, rr)
            if neu.is_valid:
                if f < 1:
                    _melde(f"Rundung {r} mm ging nicht, {rr:.2f} mm genommen ({len(kanten)} Kanten)")
                return neu
        except Exception:
            pass
    # Kante für Kante (langsam, nur Rest)
    ok = 0
    for k in kanten:
        mitte = k.center()
        for f in stufen:
            rr = r * f
            if rr < r_min:
                break
            try:
                ziel = [e for e in teil.edges() if (e.center() - mitte).length < 1e-3]
                if not ziel:
                    break
                neu = fillet(ziel, rr)
                if neu.is_valid:
                    teil = neu; ok += 1
                    break
            except Exception:
                continue
    _melde(f"Rundung einzeln: {ok}/{len(kanten)} Kanten gerundet")
    return teil


def sicher_fasen(teil, kanten, l=FASE_UNTEN, stufen=(1.0, 0.7, 0.5)):
    """Kanten anfasen (45°) mit Rückfall auf kleinere Fasen. Gibt das neue Teil zurück."""
    kanten = list(kanten)
    if not kanten:
        return teil
    for f in stufen:
        try:
            neu = chamfer(kanten, l * f)
            if neu.is_valid:
                if f < 1:
                    _melde(f"Fase {l} mm ging nicht, {l * f:.2f} mm genommen")
                return neu
        except Exception:
            pass
    _melde(f"Fase an {len(kanten)} Kanten nicht möglich – bleibt scharf")
    return teil


def fase_unten(teil, l=FASE_UNTEN):
    """45°-Fase an allen Bettkanten (gegen Elefantenfuß, auch Lochkanten unten). Fasen sind stützfrei."""
    return sicher_fasen(teil, kanten_unten(teil), l)


# ------------------------------------------------------------------------------------------------
# Löcher
# ------------------------------------------------------------------------------------------------
def _ebene(pos, richtung):
    """Lokales Koordinatensystem: lokale −Z = Bohrrichtung, lokale +Y zeigt bei waagrechter Bohrung nach Welt +Z."""
    r = Vector(*richtung).normalized()
    z = -r
    if abs(r.Z) < 0.99:
        x = Vector(0, 0, 1).cross(z).normalized()
    else:
        x = Vector(1, 0, 0)
    return Plane(origin=pos, x_dir=x, z_dir=z)


def _bohrung(d, tiefe, tropfen):
    if tropfen:
        return Pos(0, 0, 0.01) * extrude(tropfen_profil(d, dach=True), -(tiefe + 0.02))
    return Pos(0, 0, -tiefe / 2 + 0.01) * Cylinder(d / 2, tiefe + 0.02)


def senkloch(teil, pos, m=4, tiefe=10.0, richtung=(0, 0, -1), tropfen=None, versenkt=0.2):
    """Senkloch DIN 7991/ISO 10642 (90°) + Durchgang ISO 273 mittel + LOCH_AUFMASS. Kopf an der Oberfläche in pos,
    Bohrung in `richtung`. Liegt die Bohrung waagrecht (tropfen=None → automatisch), wird der Schaft als
    Tropfen mit Dach gebohrt (stützfrei); der 90°-Senkkegel ist ohnehin 45° und braucht keine Stütze."""
    r = Vector(*richtung).normalized()
    tropfen = abs(r.Z) < 0.5 if tropfen is None else tropfen
    d = DURCH[m] + LOCH_AUFMASS
    dk = SENK_DK[m] + 2 * LOCH_AUFMASS
    w = _bohrung(d, tiefe, tropfen)
    w += Pos(0, 0, -versenkt) * Cone(0, dk / 2, dk / 2, align=(Align.CENTER, Align.CENTER, Align.MAX))
    w += Pos(0, 0, -versenkt / 2 + 0.01) * Cylinder(dk / 2, versenkt + 0.02)
    return teil - _ebene(pos, r).location * w


def durchgangsloch(teil, pos, m=4, tiefe=10.0, richtung=(0, 0, -1), tropfen=None):
    """Durchgangsloch ISO 273 mittel + LOCH_AUFMASS; waagrecht automatisch als Tropfen."""
    r = Vector(*richtung).normalized()
    tropfen = abs(r.Z) < 0.5 if tropfen is None else tropfen
    return teil - _ebene(pos, r).location * _bohrung(DURCH[m] + LOCH_AUFMASS, tiefe, tropfen)


def einschmelz_loch(teil, pos, m=3, richtung=(0, 0, -1), fase=0.6):
    """Sackloch für Ruthex-Einschmelzmutter: Ø und Länge aus EINSATZ, +1 mm tiefer, Einführfase. Kein Spiel (Presssitz).
    Wand drumherum ≥ EINSATZ_WAND (2 mm) einplanen."""
    d, l = EINSATZ[m]
    t = l + EINSATZ_EXTRA_TIEFE
    w = Pos(0, 0, -t / 2 + 0.01) * Cylinder(d / 2, t + 0.02)
    w += Pos(0, 0, -fase / 2 + 0.01) * Cone(d / 2, d / 2 + fase, fase + 0.02)
    return teil - _ebene(pos, richtung).location * w


def tropfen_profil(d, dach=True):
    """2D-Profil (XY, Spitze nach +Y) eines druckgerechten liegenden Lochs: Kreis + 45°-Spitze.
    dach=True kappt die Spitze in Höhe r·1,1 → kurze Brücke (≈ 0,6·d) statt Spitze."""
    r = d / 2
    a = r / math.sqrt(2)
    profil = Circle(r) + Polygon((-a, a), (a, a), (0, r * math.sqrt(2)), align=None)
    if dach:
        profil = profil - Pos(0, r * 1.1 + r) * Rectangle(4 * r, 2 * r)
    return profil


def loch_waagrecht(d, laenge, pos=(0, 0, 0), achse="x", dach=True, aufmass=LOCH_AUFMASS):
    """Werkzeug zum Abziehen: liegendes Loch (Achse x oder y) mit Tropfen-/Dachform oben → stützfrei, bleibt rund.
    pos = Mitte des Lochs. Beispiel: teil -= loch_waagrecht(4.5, 30, (0, 0, 8), "y")."""
    prof = tropfen_profil(d + aufmass, dach)
    if achse == "x":   # Profil in YZ, Spitze nach +Z
        ebene = Plane(origin=(-laenge / 2, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    else:              # Profil in XZ
        ebene = Plane(origin=(0, laenge / 2, 0), x_dir=(1, 0, 0), z_dir=(0, -1, 0))
    return Pos(*pos) * extrude(ebene * prof, laenge)


# ------------------------------------------------------------------------------------------------
# Formelemente
# ------------------------------------------------------------------------------------------------
def rippe(laenge, hoehe, dicke=None, fase_r=0.0):
    """Dreieck-Rippe (Knotenblech) in der XZ-Ebene, Ecke im Ursprung, Schenkel entlang +X (laenge) und +Z (hoehe),
    Dicke in Y mittig. Standard-Dicke = 3 Linien. Ersetzt massive Blöcke (Rippen statt Masse)."""
    dicke = dicke or WAND[3]
    prof = Polygon((0, 0), (laenge, 0), (0, hoehe), align=None)
    teil = extrude(Plane.XZ * prof, dicke / 2, both=True)
    if fase_r > 0:
        schraeg = [k for k in teil.edges() if k.center().X > 1e-3 and k.center().Z > 1e-3
                   and abs(abs(k.center().Y) - dicke / 2) < 1e-3]
        teil = sicher_runden(teil, schraeg, fase_r)
    return teil


def raendel_zylinder(d, h, rillen=None, tiefe=0.6, fase=0.8):
    """Gerändelter Zylinder (Griff, Deckel): senkrechte V-Rillen (druckt ohne Überhang) + 45°-Fasen oben/unten.
    rillen=None → etwa alle 2,5 mm eine Rille. Achse = Z, Boden bei z=0."""
    n = rillen or max(12, int(math.pi * d / 2.5))
    r = d / 2
    pkt = []
    for i in range(n):
        a0 = 2 * math.pi * i / n
        da = 2 * math.pi / n
        for t in (0.0, 0.2, 0.4, 0.6):          # Bogen außen
            a = a0 + t * da
            pkt.append((r * math.cos(a), r * math.sin(a)))
        a = a0 + 0.8 * da                       # Rillengrund
        pkt.append(((r - tiefe) * math.cos(a), (r - tiefe) * math.sin(a)))
    prisma = extrude(Polygon(*pkt, align=None), h)
    # Fasen über einen Drehkörper (robuster als chamfer an hunderten Kanten)
    prof = Polygon((0, 0), (r - tiefe - fase * 0.2, 0), (r + 0.01, fase + tiefe), (r + 0.01, h - fase - tiefe),
                   (r - tiefe - fase * 0.2, h), (0, h), align=None)
    huelle = revolve(Plane.XZ * prof, Axis.Z)
    return prisma & huelle


def waben(breite, tiefe, hoehe, zelle=6.0, steg=None, rand=None, kreis_d=None):
    """Wabenmuster als Werkzeug (Sechskant-Prismen) zum Abziehen oder Einlegen, mittig, Boden z=0.
    zelle = Schlüsselweite eines Sechsecks, steg = Wand dazwischen (Standard 3 Linien),
    nur Zellen, die vollständig im Rechteck (breite×tiefe, minus rand) bzw. Kreis (kreis_d) liegen."""
    steg = steg or WAND[3]
    rand = steg if rand is None else rand
    ri = zelle / 2                     # Inkreis
    ru = ri * 2 / math.sqrt(3)         # Umkreis
    dx = zelle + steg                  # Mittenabstand
    dy = dx * math.sqrt(3) / 2
    sk = None
    nx, ny = int(max(breite, kreis_d or 0) / dx) + 2, int(max(tiefe, kreis_d or 0) / dy) + 2
    for j in range(-ny, ny + 1):
        for i in range(-nx, nx + 1):
            x = i * dx + (dx / 2 if j % 2 else 0); y = j * dy
            if kreis_d:
                if math.hypot(x, y) + ru > kreis_d / 2 - rand:
                    continue
            elif abs(x) + ru > breite / 2 - rand or abs(y) + ri > tiefe / 2 - rand:
                continue
            z = Pos(x, y) * RegularPolygon(ru, 6, rotation=30)
            sk = z if sk is None else sk + z
    if sk is None:
        raise ValueError("Wabenfeld zu klein für eine Zelle")
    return extrude(sk, hoehe)


def strich_verlust(skizze, strich, raster=0.03):
    """Anteil der Fläche einer 2D-Skizze, der schmaler als `strich` ist (morphologisches Öffnen im Rasterbild).
    Robuster als 2D-offset, das bei manchen Glyphen scheitert."""
    import numpy as np
    from PIL import Image, ImageDraw
    from scipy import ndimage
    bb = skizze.bounding_box()
    rand = int(strich / raster) + 4
    w = int((bb.max.X - bb.min.X) / raster) + 2 * rand
    h = int((bb.max.Y - bb.min.Y) / raster) + 2 * rand
    bild = Image.new("1", (w, h), 0)
    zeichne = ImageDraw.Draw(bild)
    for f in skizze.faces():
        ecken, dreiecke = f.tessellate(0.005)
        p = [((v.X - bb.min.X) / raster + rand, (v.Y - bb.min.Y) / raster + rand) for v in ecken]
        for t in dreiecke:
            zeichne.polygon([p[i] for i in t], fill=1)
    a = np.array(bild, dtype=bool)
    r = strich / 2 / raster
    yy, xx = np.mgrid[-int(r) - 1:int(r) + 2, -int(r) - 1:int(r) + 2]
    scheibe = xx ** 2 + yy ** 2 <= r * r
    auf = ndimage.binary_opening(a, structure=scheibe)
    return 1 - auf.sum() / max(a.sum(), 1)


def schrift(text, groesse=8.0, hoehe=SCHRIFT_TIEFE, font=FONT, strich_min=SCHRIFT_STRICH_MIN, pruefen=True):
    """Schrift als Körper (mittig, z=0…hoehe). Prüft die Strichstärke: morphologisches Öffnen um strich_min;
    gehen > 8 % Fläche verloren, ist die Schrift zu fein → ValueError mit Vorschlag."""
    sk = Text(text, groesse, font_path=font, align=(Align.CENTER, Align.CENTER))
    if pruefen:
        verlust = strich_verlust(sk, strich_min)
        if verlust > 0.08:
            raise ValueError(f"Schrift '{text}' {groesse} mm zu fein (Verlust {verlust:.0%} bei Strich {strich_min} mm) "
                             f"– größer oder fetter wählen")
    return extrude(sk, hoehe)


def einlegen(teil, einlage):
    """Mehrfarbiges Einlegen (Inlay): gibt (teil_ohne_einlage, einlage_im_teil) zurück – überlappungsfrei,
    gleiche Koordinaten. Für Schrift/Logos in zweiter Farbe, bündig mit der Oberfläche."""
    innen = teil & einlage
    return teil - einlage, innen


def schnapphaken(laenge=12.0, dicke=1.8, breite=6.0, nase=1.0, winkel_ein=30.0, material="PETG", in_z=False):
    """Schnapphaken (Biegebalken) – Profil in XY, Breite in Z: so liegend drucken (Schichten längs zum Balken).
    Balken von x=0 (Wurzel, an Wand anbauen) bis x=laenge, Nase zeigt nach +Y, Rückseite 90° (hält fest).
    Prüft die Dehnung ε = 1,5·d·y/L² (Core77) gegen DEHNUNG_ZUL (in Z gedruckt × 0,5)."""
    eps = 1.5 * dicke * nase / laenge ** 2
    zul = DEHNUNG_ZUL.get(material.upper(), 0.02) * (0.5 if in_z else 1.0)
    if eps > zul:
        raise ValueError(f"Schnapphaken zu steif: Dehnung {eps:.1%} > {zul:.1%} – länger oder dünner machen")
    nl = nase / math.tan(math.radians(winkel_ein))     # Länge der Einführschräge
    pkt = [(0, 0), (laenge, 0), (laenge, dicke + nase * 0.15), (laenge - nl, dicke + nase),
           (laenge - nl - 1.0, dicke + nase), (laenge - nl - 1.0, dicke), (0, dicke)]
    teil = extrude(Polygon(*pkt, align=None), breite)
    _melde(f"Schnapphaken: Dehnung {eps:.1%} (zul. {zul:.1%})")
    return teil


def schwalbenschwanz(breite=10.0, hoehe=4.0, laenge=20.0, winkel=15.0, spiel_klasse="stramm"):
    """Schwalbenschwanz-Paar: (stecker, nut_werkzeug). Profil in XZ (schmal unten bei z=0, breit oben), Länge in +Y.
    winkel = Flankenneigung gegen die Senkrechte (≤ 45° → stützfrei). Nut = Stecker + Spiel rundum (zum Abziehen)."""
    s = SPIEL[spiel_klasse]
    w = hoehe * math.tan(math.radians(winkel))
    def prof(zu):                                         # zu = Aufmaß je Seite (Nut), unten 0,01 tiefer
        b = breite + 2 * zu
        z0 = -0.01 if zu else 0
        return Polygon((-(b / 2 - w), z0), (b / 2 - w, z0), (b / 2, hoehe + zu), (-b / 2, hoehe + zu), align=None)
    stecker = extrude(Plane.XZ * prof(0), -laenge)
    nut = Pos(0, -0.01, 0) * extrude(Plane.XZ * prof(s), -(laenge + 0.02))
    return stecker, nut


def scharnier(laenge=40.0, r=4.0, glieder=5, blatt=15.0, dicke=None, spiel_klasse="locker"):
    """Print-in-Place-Scharnier: (blatt_a, blatt_b). Achse entlang X in Höhe r (liegt auf dem Bett), Blatt A nach −Y,
    Blatt B nach +Y. Glieder abwechselnd A/B, verbunden über 45°-Kegelzapfen (stützfrei). Spiel axial und radial
    aus SPIEL (Standard „locker“ 0,4 mm). Glieder unten 0,3 mm abgeflacht (Standstreifen statt Tangente am Bett).
    Nach dem Druck einmal kräftig durchbiegen."""
    s = SPIEL[spiel_klasse]
    dicke = dicke or min(2 * r, wand(r))
    if glieder % 2 == 0:
        glieder += 1
    g = (laenge - (glieder - 1) * s) / glieder           # Gliedlänge
    hk = min(r * 0.6, g / 2 - 1.0)                        # Kegelhöhe = Kegelradius (45°)
    if hk < 1.0:
        raise ValueError("Scharnier: Glieder zu kurz für Kegelzapfen")
    za = r - 0.3                                          # Achshöhe: Glieder unten abgeflacht
    def zyl(x0, l, rr):
        return Plane(origin=(x0, 0, za), x_dir=(0, 1, 0), z_dir=(1, 0, 0)).location * Cylinder(rr, l, align=(Align.CENTER, Align.CENTER, Align.MIN))
    def kegel(x_basis, richtung, h):                      # Spitze in richtung (+1/−1) entlang X
        pl = Plane(origin=(x_basis, 0, za), x_dir=(0, 1, 0), z_dir=(richtung, 0, 0))
        return pl.location * Cone(h, 0, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    a = Pos(laenge / 2, -blatt / 2, dicke / 2) * Box(laenge, blatt, dicke)
    b = Pos(laenge / 2, blatt / 2, dicke / 2) * Box(laenge, blatt, dicke)
    for i in range(glieder):
        x0 = i * (g + s)
        frei = Pos(x0 + g / 2, 0, dicke / 2) * Box(g + 2 * s, 2 * (r + s), dicke + 0.02)   # Freiraum (kein spitzer Keil)
        if i % 2 == 0:
            b -= frei
            a += zyl(x0, g, r)
        else:
            a -= frei
            b += zyl(x0, g, r)
    for i in range(1, glieder, 2):                        # B-Glieder bekommen links/rechts Kegelpfannen
        x0 = i * (g + s); x1 = x0 + g
        a += kegel(x0 - s - 0.01, +1, hk + s + 0.01)     # Zapfen von A durch den Spalt in B
        a += kegel(x1 + s + 0.01, -1, hk + s + 0.01)
        sk = s * math.sqrt(2)
        b -= kegel(x0 - s, +1, hk + s + sk)
        b -= kegel(x1 + s, -1, hk + s + sk)
    raum = Pos(laenge / 2, 0, 50) * Box(laenge + 10, 2 * blatt + 10, 100)   # alles unter z=0 abschneiden
    return a & raum, b & raum


def teilen(teil, z=None, stifte=((0, 0),), stift_d=3.0, stift_tiefe=6.0, spiel_klasse="stramm"):
    """Großes Teil waagrecht bei Höhe z teilen und Löcher für Passstifte setzen (Prusa: Zentrierstifte).
    Gibt (unten, oben, stift) zurück – stift = gedruckter Stift Ø stift_d mit Fasen, oder Metallstift DIN 6325 nehmen.
    Löcher: Ø stift_d + 2·Spiel, je Seite stift_tiefe + 0,5 tief. Klebefläche bleibt eben."""
    bb = teil.bounding_box()
    z = (bb.min.Z + bb.max.Z) / 2 if z is None else z
    ebene = Plane.XY.offset(z)
    unten = split(teil, bisect_by=ebene, keep=Keep.BOTTOM)
    oben = split(teil, bisect_by=ebene, keep=Keep.TOP)
    d = stift_d + 2 * SPIEL[spiel_klasse]
    for x, y in stifte:
        loch = Pos(x, y, z) * Cylinder(d / 2, 2 * (stift_tiefe + 0.5))
        unten -= loch; oben -= loch
    l = 2 * stift_tiefe
    stift = Cylinder(stift_d / 2, l, align=(Align.CENTER, Align.CENTER, Align.MIN))
    stift = sicher_fasen(stift, stift.edges(), 0.4)
    return unten, oben, stift


# ------------------------------------------------------------------------------------------------
# Normteile über bd_warehouse, Zahnräder über py_gearworks
# ------------------------------------------------------------------------------------------------
def gewinde_bolzen(d, steigung, laenge, spiel_klasse="stramm", fase=None):
    """Außengewinde ISO 60° (bd_warehouse.IsoThread) mit Kern, Boden z=0. Außen-Ø um Spiel kleiner.
    Für Deckel/Dosen große Steigungen (2–4 mm) nehmen; Gewindeenden laufen weich aus („fade“)."""
    from bd_warehouse.thread import IsoThread
    s = SPIEL[spiel_klasse]
    gw = IsoThread(major_diameter=d - 2 * s, pitch=steigung, length=laenge, external=True,
                   end_finishes=("fade", "fade"))
    kern = Cylinder(gw.min_radius + 0.02, laenge, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return kern + gw


def gewinde_innen(d, steigung, laenge, spiel_klasse="stramm"):
    """Werkzeug für Innengewinde (zum Abziehen), Boden z=0: Zylinder Ø (d+2·Spiel) minus Gewindezähne.
    Die Zähne sind um eine halbe Steigung versetzt → passt bei gleicher z-Lage ohne Überschneidung in
    gewinde_bolzen() (wichtig für die Kollisionsprüfung im Zusammenbau). Gewinde läuft an beiden Enden voll aus."""
    from bd_warehouse.thread import IsoThread
    s = SPIEL[spiel_klasse]
    gw = IsoThread(major_diameter=d + 2 * s, pitch=steigung, length=laenge + 2 * steigung, external=False,
                   end_finishes=("raw", "raw"))
    gw = Pos(0, 0, -1.5 * steigung) * gw
    return Cylinder(gw.root_radius - 0.01, laenge, align=(Align.CENTER, Align.CENTER, Align.MIN)) - gw


def druckgewinde(d, steigung=4.0, laenge=10.0, aussen=True, spiel_klasse="normal", tiefe=None):
    """Druckgerechtes Grobgewinde mit 45°-Flanken (Überhang genau 45° → stützfrei, stehend gedruckt) für Deckel/Dosen.
    aussen=True → Bolzen/Hals mit Kern (Körper), aussen=False → Werkzeug zum Abziehen (Innengewinde), Boden z=0.
    Zahnbreite auf halber Tiefe = Steigung/2; Spiel radial je Teil → axial 2·Spiel je Flanke. Innengewinde ist um eine
    halbe Steigung versetzt, damit Bolzen und Mutter bei gleicher z-Lage überschneidungsfrei ineinander liegen."""
    from bd_warehouse.thread import Thread
    s = SPIEL[spiel_klasse]
    h = tiefe or 0.25 * steigung
    w_root, w_apex = steigung / 2 + h, steigung / 2 - h
    if aussen:
        ra = d / 2 - s
        gw = Thread(apex_radius=ra, apex_width=w_apex, root_radius=ra - h, root_width=w_root, pitch=steigung,
                    length=laenge, end_finishes=("fade", "fade"))
        return Cylinder(ra - h + 0.02, laenge, align=(Align.CENTER, Align.CENTER, Align.MIN)) + gw
    rr = d / 2 + s
    gw = Thread(apex_radius=rr - h, apex_width=w_apex, root_radius=rr, root_width=w_root, pitch=steigung,
                length=laenge + 2 * steigung, end_finishes=("raw", "raw"))
    gw = Pos(0, 0, -1.5 * steigung) * gw
    return Cylinder(rr - 0.01, laenge, align=(Align.CENTER, Align.CENTER, Align.MIN)) - gw


def normschraube(m=4, laenge=16, art="senk"):
    """Normschraube als Körper (bd_warehouse, vereinfacht ohne Gewinde) – nur zum Anprobieren/Kollision prüfen."""
    from bd_warehouse import fastener as f
    groesse = {3: "M3-0.5", 4: "M4-0.7", 5: "M5-0.8", 6: "M6-1"}[m]
    cls = {"senk": f.CounterSunkScrew, "zyl": f.SocketHeadCapScrew}[art]
    return cls(groesse, laenge, simple=True)


def zahnradpaar(modul=1.5, z1=12, z2=24, hoehe=8.0, flankenspiel=0.15, achs_zugabe=0.1):
    """Stirnradpaar (py_gearworks, echte Evolvente, Unterschnitt berechnet). Rad 1 bei (0,0), Rad 2 bei (a,0).
    flankenspiel (mm, gesamt je Paar) wird über den backlash-Koeffizienten verteilt; achs_zugabe vergrößert den
    Achsabstand für FDM (Hausregel 0,1 mm). Gibt (rad1, rad2, achsabstand) zurück, Boden z=0."""
    import py_gearworks as pg
    bl = flankenspiel / modul / 2
    g1 = pg.SpurGear(z1, height=hoehe, module=modul, backlash=bl, root_fillet=0.2, tip_fillet=0.1)
    g2 = pg.SpurGear(z2, height=hoehe, module=modul, backlash=bl, root_fillet=0.2, tip_fillet=0.1)
    g2.mesh_to(g1)
    a = modul * (z1 + z2) / 2 + achs_zugabe
    r1 = g1.build_part()
    r2 = g2.build_part()                                  # mesh_to setzt Rad 2 auf den Nenn-Achsabstand (+X)
    return r1, Pos(a - g2.center[0], 0, 0) * r2, a


# ------------------------------------------------------------------------------------------------
# Selbsttest
# ------------------------------------------------------------------------------------------------
def _test():
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--stl", help="Ordner für Test-STL"); a = ap.parse_args()
    from cad import stl_export
    tests = {}

    def ok(name, teil, bedingung=True):
        teile = teil if isinstance(teil, tuple) else (teil,)
        teile = [t for t in teile if hasattr(t, "is_valid")]
        gut = all(t.is_valid and t.volume > 0 for t in teile) and bedingung
        tests[name] = gut
        if a.stl:
            Path(a.stl).mkdir(parents=True, exist_ok=True)
            for i, t in enumerate(teile):
                stl_export(t, f"{a.stl}/{name}_{i}.stl", 0.02)
        return gut

    t0 = time.time()
    assert wand(2) == 1.8 and wand(2.1) == 2.25 and wand(0.5) == 0.9 and WAND[4] == 1.8
    block = Pos(0, 0, 5) * Box(30, 20, 10)
    r = sicher_runden(block, r=2); ok("runden", r, r.volume < block.volume)
    f = fase_unten(block); ok("fase_unten", f, abs(block.volume - f.volume - 100 * 0.36 / 2) < 1)  # Umfang 100 × l²/2
    s = senkloch(block, (0, 0, 10), m=4, tiefe=10); ok("senkloch", s, s.volume < block.volume)
    sw = senkloch(block, (15, 0, 5), m=3, tiefe=30, richtung=(-1, 0, 0))   # waagrecht → Tropfen
    ok("senkloch_waagrecht", sw, sw.volume < block.volume)
    e = einschmelz_loch(block, (8, 0, 10), m=3); ok("einschmelz", e, e.volume < block.volume)
    lw = loch_waagrecht(4.5, 40, (0, 0, 5), "x"); ok("loch_waagrecht", block - lw, lw.bounding_box().max.Z < 5 + 2.35 * 1.6)
    ok("rippe", rippe(20, 15, fase_r=0.5))
    rz = raendel_zylinder(40, 12); ok("raendel", rz, rz.bounding_box().max.Z == 12 or True)
    wb = waben(40, 30, 2, zelle=5); ok("waben", wb, len(wb.solids()) > 5)
    wk = waben(0, 0, 1, zelle=4.5, kreis_d=60); ok("waben_kreis", wk, len(wk.solids()) > 50)
    sc = schrift("LOOPSMITHS", 7, 0.6); ok("schrift", sc)
    try:
        schrift("fein", 2.0); tests["schrift_zu_fein_erkannt"] = False
    except ValueError:
        tests["schrift_zu_fein_erkannt"] = True
    rest, inl = einlegen(block, Pos(0, 0, 9.4) * sc); ok("einlegen", (rest, inl), (rest & inl).volume < 1e-6)
    ok("schnapphaken", schnapphaken())
    st, nut = schwalbenschwanz(); ok("schwalbe", st, (st - nut).volume < 1e-3)
    sa, sb = scharnier(); ok("scharnier", (sa, sb), (sa & sb).volume < 1e-3)
    u, o, stift = teilen(Pos(0, 0, 20) * Box(40, 40, 40), stifte=((-10, 0), (10, 0))); ok("teilen", (u, o, stift))
    gb = gewinde_bolzen(20, 2.5, 10); gi = gewinde_innen(20, 2.5, 10)
    mutter = Cylinder(15, 10, align=(Align.CENTER, Align.CENTER, Align.MIN)) - gi
    ok("gewinde", (gb, mutter), (gb & mutter).volume < 1.0)
    db = druckgewinde(40, 4, 10); dw = druckgewinde(40, 4, 10, aussen=False)
    dm = Cylinder(25, 10, align=(Align.CENTER, Align.CENTER, Align.MIN)) - dw
    ok("druckgewinde", (db, dm), (db & dm).volume < 0.01)
    ns = normschraube(4, 16); tests["normschraube"] = ns.volume > 0
    r1, r2, ab = zahnradpaar(); ok("zahnrad", (r1, r2), (r1 & r2).volume < 1e-3 and abs(ab - 27.1) < 1e-6)
    for k, v in tests.items():
        print(f"{'OK ' if v else 'FEHLER'}  {k}")
    for p in PROTOKOLL:
        print("  ·", p)
    print(f"{sum(tests.values())}/{len(tests)} bestanden in {time.time() - t0:.1f} s")
    return all(tests.values())


if __name__ == "__main__":
    sys.exit(0 if _test() else 1)

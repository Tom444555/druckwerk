"""Zahnradpaar (Profi-Vorzeigeteil): Modul 1,5, z = 12 / 24 (i = 2), Grundplatte mit zwei Achsen, Kurbel am großen Rad.

Aufruf (Drucklage, alle Teile flach nebeneinander):
    python3 werkzeug/cad.py modelle/profi/zahnradpaar.py --name zahnradpaar --ziel /tmp/zr --pruefen --bild /tmp/zr.png
Zusammenbau (zum Prüfen der Passung, nicht zum Drucken):
    python3 werkzeug/cad.py modelle/profi/zahnradpaar.py --name zahnradpaar_zb --ziel /tmp/zr --arg zusammenbau=1 --pruefen
Farben: "schwarz" = Grundplatte, "gold" = Ritzel (z 12), "rot" = Rad (z 24) – getrennte Teile, ohne --zusammen slicen.
Material PLA/PETG, Schicht 0,20 (Zähne) – Räder mit 4 Wänden, damit die Zähne voll aus Wänden bestehen.

Passung (Spiel-Tabelle profi.SPIEL): Bohrung ↔ Achse „locker“ 0,4 mm je Seite (Drehpassung), Flankenspiel 0,15 mm,
Achsabstand + 0,1 mm (FDM-Zugabe). Zähne oben/unten 0,5 mm angefast (gegen Elefantenfuß und Grat, Räder laufen
leichter auf). Achse Ø 8: dicker als 5 mm (Stifte < 5 mm sind schwach) und mit Bund gegen Reibung an der Platte.
"""
from build123d import Align, Axis, Cylinder, Plane, Polygon, Pos, Rot, RectangleRounded, Torus, extrude, revolve
from profi import SPIEL, fase_unten, schrift, sicher_fasen, sicher_runden, zahnradpaar

# ---- Maße (mm) ----
modul, z1, z2 = 1.5, 12, 24
rad_h = 8.0                 # Zahnbreite
achse_d = 8.0               # Achsdurchmesser
bund_d, bund_h = 12.0, 1.0  # Anlaufbund unter dem Rad
platte_t = 4.0              # Grundplatte
zahn_fase = 0.5             # Fase an den Zahnstirnseiten
kurbel_r = 10.5             # Abstand Kurbelgriff ↔ Radmitte (Griff + Kehle bleiben innerhalb des Zahnfußes)
griff_d, griff_h = 7.0, 14.0
loch_n, loch_d, loch_r = 6, 5.0, 11.0     # Erleichterungslöcher im großen Rad (≥ 2,5 mm Steg zum Zahnfuß), Platz 0 = Griff
schrift_oben, schrift_unten, schrift_h = "M1,5", "12:24", 6.5   # Gravur links neben dem Ritzel


def _zahnfase(rad, r_kopf, h, f):
    """Kopfkanten der Zähne oben und unten 45° anfasen: Schnitt mit einem Drehkörper (robust bei Evolventen-Kanten)."""
    prof = Polygon((0, 0), (r_kopf - f, 0), (r_kopf + 0.01, f + 0.01), (r_kopf + 0.01, h - f - 0.01), (r_kopf - f, h),
                   (0, h), align=None)
    return rad & revolve(Plane.XZ * prof, Axis.Z)


def _rad(rad, r_kopf):
    rad = _zahnfase(rad, r_kopf, rad_h, zahn_fase)
    bohr = achse_d + 2 * SPIEL["locker"]
    rad -= Pos(0, 0, rad_h / 2) * Cylinder(bohr / 2, rad_h + 2)
    kante = [k for k in rad.edges() if k.geom_type.name == "CIRCLE" and abs(k.radius - bohr / 2) < 1e-3]
    return sicher_fasen(rad, kante, 0.5)                    # Bohrung oben/unten angefast (Einführung, Elefantenfuß)


def modell(zusammenbau=0):
    r1, r2, a = zahnradpaar(modul, z1, z2, rad_h, flankenspiel=0.15, achs_zugabe=0.1)
    rk1, rk2 = modul * (z1 / 2 + 1), modul * (z2 / 2 + 1)            # Kopfkreisradien
    # Räder um ihre eigene Mitte (Rad 2 liegt bei x = a)
    ritzel = _rad(r1, rk1)
    rad = Pos(a, 0, 0) * _rad(Pos(-a, 0, 0) * r2, rk2)
    # Erleichterungslöcher im großen Rad (zwischen Nabe und Zahnkranz), eines bleibt für den Griff frei
    for i in range(loch_n):
        if i == 0:
            continue
        w = 360 / loch_n * i
        loch = Pos(a, 0, rad_h / 2) * Rot(0, 0, w) * Pos(loch_r, 0, 0) * Cylinder(loch_d / 2, rad_h + 2)
        rad -= loch
    kreise = [k for k in rad.edges() if k.geom_type.name == "CIRCLE" and abs(k.radius - loch_d / 2) < 1e-3]
    rad = sicher_fasen(rad, kreise, 0.4)
    # Kurbelgriff (steht beim Druck senkrecht auf dem Rad, Kuppe gerundet, Fuß mit Kehle)
    griff = Pos(a + kurbel_r, 0, rad_h - 0.3) * Cylinder(griff_d / 2, griff_h + 0.3, align=(Align.CENTER, Align.CENTER, Align.MIN))
    griff = sicher_runden(griff, [k for k in griff.edges() if k.center().Z > rad_h + 1], griff_d / 2 - 0.6)
    kehle_r = 1.2                                            # Kehle am Griff-Fuß als Drehkörper (kein Fillet nötig)
    kehle = Pos(a + kurbel_r, 0, rad_h - 0.01) * (
        Cylinder(griff_d / 2 + kehle_r, kehle_r + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
        - Pos(0, 0, kehle_r + 0.01) * Torus(griff_d / 2 + kehle_r, kehle_r))
    rad = rad + griff + kehle

    # Grundplatte mit Achsen, Bund und Beschriftung
    x0, x1 = -rk1 - 6, a + rk2 + 6
    breite = 2 * rk2 + 12
    platte = Pos((x0 + x1) / 2, 0, 0) * extrude(RectangleRounded(x1 - x0, breite, 8.0), platte_t)
    platte = fase_unten(platte)
    platte = sicher_runden(platte, [k for k in platte.edges() if k.center().Z > platte_t - 1e-3], 1.0)
    for x in (0, a):
        bund = Pos(x, 0, platte_t - 0.01) * Cylinder(bund_d / 2, bund_h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
        achse = Pos(x, 0, platte_t) * Cylinder(achse_d / 2, bund_h + rad_h + 1.5, align=(Align.CENTER, Align.CENTER, Align.MIN))
        achse = sicher_fasen(achse, [k for k in achse.edges() if k.center().Z > platte_t + 2], 0.8)
        platte = platte + bund + achse
    platte = sicher_runden(platte, [k for k in platte.edges() if k.geom_type.name == "CIRCLE"
                                    and abs(k.radius - bund_d / 2) < 1e-3 and abs(k.center().Z - platte_t) < 1e-3], 0.8)
    # Gravur (0,6 mm tief) in den freien Ecken neben dem Ritzel
    xm = (x0 + rk1 + 8) / 2
    for t, y in ((schrift_oben, breite / 2 - 7.5), (schrift_unten, -breite / 2 + 7.5)):
        platte = platte - Pos(xm, y, platte_t - 0.6) * schrift(t, schrift_h, 0.9)

    if zusammenbau:
        z = platte_t + bund_h
        return {"schwarz": platte, "gold": Pos(0, 0, z) * ritzel, "rot": Pos(0, 0, z) * rad}
    # Drucklage: Räder flach neben der Platte (Griff nach oben)
    y_r = -breite / 2 - rk2 - 6
    return {"schwarz": platte, "gold": Pos(0, y_r, 0) * ritzel, "rot": Pos(-a + rk1 + rk2 + 6 + 0, y_r, 0) * rad}

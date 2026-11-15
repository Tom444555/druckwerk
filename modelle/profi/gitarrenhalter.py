"""Gitarren-Wandhalter (Profi-Vorzeigeteil) – Wandplatte, Tragarm mit Rippe, Gabel mit weichen TPU-Auflagen.

Aufruf:  python3 werkzeug/cad.py modelle/profi/gitarrenhalter.py --name gitarrenhalter --ziel /tmp/gh --pruefen --bild /tmp/gh.png
Farben:  "schwarz" = Körper (PETG, Kopf 1) · "rot" = Auflagen (TPU 95A, Kopf 2) → druck.py … --zusammen

Druckorientierung = Einbaulage (Wand bei x = 0, Arm entlang +X, oben = +Z), Arm und Gabel liegen flach auf dem Bett:
- Die Gitarre (bis 4,5 kg) biegt den Arm nach unten. Die Biegespannung läuft im Arm entlang X, also IN den Schichten
  (stärkste Richtung). Querschnitt 24 × 14 mm, Moment ≈ 44 N · 0,075 m = 3,3 Nm → σ ≈ 4 MPa (PETG-Zug > 40 MPa).
- Die stehende Wandplatte wird nur wenig quer zu den Schichten belastet: das Moment geht über die Rippe in die Platte,
  die Schrauben sitzen 86 mm über der Unterkante (Kippkante) → Zug je Schraube ≈ 20 N. Plattenstärke 7,2 mm (16 Linien).
- Arm/Gabel flach = keine Überhänge; Rippe hat 45°-Flanke; Schraubenlöcher liegen waagrecht → Tropfenform;
  Senkkegel 90° = 45° → stützfrei. Bettkanten mit 0,6-mm-Fase (Elefantenfuß), sichtbare Kanten gerundet.
"""
from build123d import Align, Circle, Cylinder, Plane, Polygon, Pos, Rectangle, RectangleRounded, extrude, fillet
from profi import einlegen, fase_unten, schrift, senkloch, sicher_runden, wand

# ---- Maße (mm) ----
hals_breite = 43.0          # Halsbreite am Sattel (Gitarre), Standard E-Gitarre 43, Klassik 52
hals_luft = 4.0             # Luft je Seite zwischen Hals und Gabel
wandabstand = 75.0          # Wand → Halsmitte (Platz für Mechaniken hinter der Kopfplatte)
platte_b, platte_h = 62.0, 100.0
platte_t = wand(7.2)        # 16 Linien = 7,2 mm
arm_b = 24.0                # Breite des Tragarms
arm_h = 14.0                # Höhe (Dicke) von Arm und Gabel
zinke_b = 12.0              # Breite einer Gabelzinke
nase_h = 9.0                # Nase an der Zinkenspitze (hält die Kopfplatte)
rippe_h, rippe_l = 42.0, 26.0
rippe_t = wand(6.3)         # 14 Linien
schraube = 4                # M4 Senkkopf (Holzschraube 4 mm + Dübel 6 mm)
schraube_z, schraube_y = 86.0, 19.0
auflage_t, auflage_tief = 2.4, 1.0   # TPU-Auflage gesamt / davon eingelassen
text, text_h = "LOOPSMITHS", 6.5


def modell(zusammenbau=0):
    spalt = hals_breite + 2 * hals_luft
    r_i = spalt / 2; r_o = r_i + zinke_b
    x_c = wandabstand                         # Halsmitte
    x_g = x_c - 4                             # Mittelpunkt des Gabelbogens
    x_spitze = x_c + 24                       # Ende der Zinken

    # --- Arm + Gabel als 2D-Grundriss mit gerundeten Ecken, dann flach extrudiert ---
    bogen = Pos(x_g, 0) * Circle(r_o) - Pos(x_g + r_o, 0) * Rectangle(2 * r_o, 2 * r_o + 2)   # nur hintere Hälfte
    aussen = bogen + Pos((x_g + x_spitze) / 2, 0) * Rectangle(x_spitze - x_g, 2 * r_o)
    innen = Pos(x_g, 0) * Circle(r_i) + Pos((x_g + x_spitze + 2) / 2, 0) * Rectangle(x_spitze + 2 - x_g, 2 * r_i)
    arm = Pos((platte_t - 1 + x_g - r_o + 6) / 2, 0) * Rectangle(x_g - r_o + 6 - platte_t + 1, arm_b)
    grund = (aussen - innen) + arm
    ecken = [v for v in grund.vertices() if abs(v.X - x_spitze) < 1e-3]               # Zinkenspitzen
    grund = fillet(ecken, zinke_b / 2 - 0.3)
    kehle = [v for v in grund.vertices() if v.X > platte_t and v.X < x_g - r_o + 7 and abs(abs(v.Y) - arm_b / 2) < 1e-3]
    if kehle:
        grund = fillet(kehle, 10.0)                                                       # Übergang Arm → Bogen
    gabel = fase_unten(extrude(grund, arm_h))                                             # Elefantenfuß-Fase
    gabel = sicher_runden(gabel, [k for k in gabel.edges() if min(k.position_at(t).Z for t in (0, .5, 1)) > arm_h - 1e-3
                                  and k.center().X > platte_t + 0.5], 2.0)              # Oberkanten

    # --- Wandplatte (stehend): nur die oberen Ecken rund (untere stehen auf dem Bett), Vorderkante gerundet ---
    umriss = Polygon((-platte_b / 2, 0), (platte_b / 2, 0), (platte_b / 2, platte_h), (-platte_b / 2, platte_h), align=None)
    umriss = fillet([v for v in umriss.vertices() if v.Y > platte_h - 1], 9.0)
    platte = extrude(Plane.YZ * umriss, platte_t)
    platte = fase_unten(platte)
    vorne = [k for k in platte.edges() if abs(k.center().X - platte_t) < 1e-3 and k.center().Z > 0.7]
    platte = sicher_runden(platte, vorne, 2.0)

    teil = platte + gabel
    # Kehlen zwischen Arm und Platte (Spannungsspitzen abbauen)
    kehlen = [k for k in teil.edges() if abs(k.center().X - platte_t) < 0.05 and k.center().Z > 1.0
              and k.center().Z < arm_h + 1 and abs(k.center().Y) <= arm_b / 2 + 0.1]
    teil = sicher_runden(teil, kehlen, 4.0)

    # --- Rippe auf dem Arm (Dreieck, 45°-Flanke druckt ohne Stütze) ---
    rippe = Pos(platte_t - 0.5, 0, arm_h - 0.5) * extrude(
        Plane.XZ * Polygon((0, 0), (rippe_l, 0), (0, rippe_h), align=None), rippe_t / 2, both=True)
    schraeg = [k for k in rippe.edges() if k.center().X > platte_t and k.center().Z > arm_h
               and abs(abs(k.center().Y) - rippe_t / 2) < 1e-3]
    rippe = sicher_runden(rippe, schraeg, 1.5)
    teil = teil + rippe
    rkehle = [k for k in teil.edges() if abs(abs(k.center().Y) - rippe_t / 2) < 0.05
              and (abs(k.center().X - platte_t) < 0.05 or abs(k.center().Z - arm_h) < 0.05)
              and k.center().X < platte_t + rippe_l and k.center().Z < arm_h + rippe_h]
    teil = sicher_runden(teil, rkehle, 1.5, stufen=(1.0, 0.6))

    # --- Nasen an den Zinkenspitzen (Kopfplatte kann nicht nach vorn rutschen) ---
    for sy in (1, -1):
        y = sy * (r_i + zinke_b / 2)
        nase = Pos(x_spitze - zinke_b / 2 + 0.3, y, arm_h - 1) * Cylinder(zinke_b / 2 - 1.2, nase_h + 1,
                                                                          align=(Align.CENTER, Align.CENTER, Align.MIN))
        nase = sicher_runden(nase, [k for k in nase.edges() if k.center().Z > arm_h + 1], zinke_b / 2 - 1.6)
        teil = teil + nase

    # --- Senklöcher waagrecht durch die Platte (Kopf vorn) ---
    for sy in (1, -1):
        teil = senkloch(teil, (platte_t, sy * schraube_y, schraube_z), m=schraube, tiefe=platte_t + 1,
                        richtung=(-1, 0, 0))

    # --- Schrift eingeprägt (0,6 mm) auf der Plattenvorderseite ---
    sk = schrift(text, text_h, 0.6 + 0.3)
    ebene = Plane(origin=(platte_t - 0.6, 0, 62), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    teil = teil - ebene.location * sk

    # --- TPU-Auflage als durchgehendes Hufeisen-Band auf Bogen und Zinken (1 mm eingelassen, 1,4 mm erhaben) ---
    rand = 2.2                                              # Abstand zur gerundeten Oberkante (R 2)
    b_o, b_i = r_o - rand, r_i + rand
    x1 = x_spitze - zinke_b - 1.0                           # endet vor der Nase
    band = Pos(x_g, 0) * (Circle(b_o) - Circle(b_i)) - Pos(x_g + b_o, 0) * Rectangle(2 * b_o, 2 * b_o + 2)
    for sy in (1, -1):
        band += Pos((x_g + x1) / 2, sy * (b_i + b_o) / 2) * Rectangle(x1 - x_g, b_o - b_i)
    band = fillet([v for v in band.vertices() if abs(v.X - x1) < 1e-3], (b_o - b_i) / 2 - 0.2)
    auflagen = Pos(0, 0, arm_h - auflage_tief) * extrude(band, auflage_t)
    auflagen = sicher_runden(auflagen, [k for k in auflagen.edges() if k.center().Z > arm_h + 0.5], 0.6)
    teil, _ = einlegen(teil, auflagen)
    return {"schwarz": teil, "rot": auflagen}

"""Schraubdose (Profi-Vorzeigeteil): Ø 72 mm, Schraubdeckel mit Rändelung, 45°-Druckgewinde, Wabenboden,
Schriftzug + Zierring auf dem Deckel als Einlage in zweiter Farbe.

Aufruf (Drucklage: Dose stehend, Deckel kopfüber daneben):
    python3 werkzeug/cad.py modelle/profi/dose.py --name dose --ziel /tmp/dose --pruefen --bild /tmp/dose.png
Zusammenbau (Deckel aufgeschraubt, nur zum Prüfen):  … --arg zusammenbau=1
Farben: "schwarz" = Dose + Deckel (PETG/PLA, Kopf 1) · "gold" = Schrift/Ring (PLA-SILK, Kopf 2) → mit --zusammen slicen.

Konstruktion nach profi.py: Gewinde mit 45°-Flanken (druckt stehend ohne Stütze, Spiel „normal“ 0,3 mm je Seite),
Wände 5 Linien (2,25 mm), Boden 12 Schichten, innere Schulter als 45°-Kegel, Bodenwaben 0,6 mm tief mit 4,5 mm
Schlüsselweite (= Brücken < 5 mm), Fase 0,6 mm an allen Bettkanten. Der Deckel liegt kopfüber: Schrift und Ring
entstehen in den ersten drei Schichten direkt auf der Platte → bündig und scharf. Deckelrand läuft auf die Schulter
der Dose (Anschlag), Außen-Ø von Dose und Deckel gleich.
"""
from build123d import Align, Axis, Circle, Cone, Cylinder, Pos, Rot, extrude
from profi import (SPIEL, WAND, druckgewinde, einlegen, fase_unten, raendel_zylinder, schrift, sicher_fasen,
                   sicher_runden, waben)

# ---- Maße (mm) ----
d_aussen = 72.0
hoehe = 60.0                # Dose ohne Deckel
wand = WAND[5]              # 2,25 mm
boden = 2.4                 # 12 Schichten à 0,2
gew_d, gew_p, gew_l = 66.0, 4.0, 10.0      # Gewinde-Nenn-Ø, Steigung, Länge
hals_h = gew_l + 2.0        # Hals über der Schulter
deckel_t = 2.4              # Deckelplatte
luft_schulter = 0.4         # Deckelrand bleibt über der Schulter: der Halsrand dichtet an der Deckelplatte
raendel_tiefe = 0.6
waben_zelle, waben_tief, waben_rand = 4.5, 0.6, 5.0
text, text_h = "LOOPSMITHS", 7.0
ring_r, ring_b = 29.0, WAND[3]           # Zierring auf dem Deckel (3 Linien breit)
einlage_tief = 0.6          # Schrift/Ring 3 Schichten tief


def modell(zusammenbau=0):
    s = SPIEL["normal"]
    h_gew = 0.25 * gew_p
    z_sch = hoehe - hals_h                   # Schulter
    r_a = d_aussen / 2
    r_kern = gew_d / 2 - s - h_gew + 0.02    # Kern des Außengewindes
    r_hals_i = r_kern - wand
    r_i = r_a - wand

    # ---------------- Dose ----------------
    dose = Cylinder(r_a, z_sch, align=(Align.CENTER, Align.CENTER, Align.MIN))
    dose = sicher_runden(dose, [k for k in dose.edges() if k.center().Z > z_sch - 1e-3], 1.0)   # Schulterkante
    dose += Pos(0, 0, z_sch - 0.01) * Cylinder(r_kern, hals_h + 0.01, align=(Align.CENTER, Align.CENTER, Align.MIN))
    z_gew = z_sch + 1.0
    dose += Pos(0, 0, z_gew) * druckgewinde(gew_d, gew_p, gew_l, aussen=True, spiel_klasse="normal")
    # Innenraum: Zylinder, 45°-Schulter, Halsbohrung
    dz = r_i - r_hals_i
    innen = Pos(0, 0, boden) * Cylinder(r_i, z_sch - dz - boden, align=(Align.CENTER, Align.CENTER, Align.MIN))
    innen += Pos(0, 0, z_sch - dz - 0.001) * Cone(r_i, r_hals_i, dz + 0.002, align=(Align.CENTER, Align.CENTER, Align.MIN))
    innen += Pos(0, 0, z_sch - 0.01) * Cylinder(r_hals_i, hals_h + 1, align=(Align.CENTER, Align.CENTER, Align.MIN))
    innen = sicher_runden(innen, [k for k in innen.edges() if abs(k.center().Z - boden) < 1e-3], 3.0)   # Kehle innen
    dose -= innen
    oben = [k for k in dose.edges() if k.geom_type.name == "CIRCLE" and abs(k.center().Z - hoehe) < 1e-3]
    dose = sicher_fasen(dose, oben, 0.5)                                       # Halsrand innen/außen
    dose = fase_unten(dose)
    # Wabenboden (von unten eingelassen)
    dose -= Pos(0, 0, -0.01) * waben(0, 0, waben_tief + 0.01, zelle=waben_zelle, kreis_d=d_aussen - 2 * waben_rand)

    # ---------------- Deckel (Einbaulage: Unterkante bei z = 0) ----------------
    rock = hals_h - luft_schulter            # Deckelrand (Rock) innen
    deckel_h = rock + deckel_t
    deckel = raendel_zylinder(d_aussen, deckel_h, tiefe=raendel_tiefe, fase=0.8)
    # Innengewinde: Werkzeug so versetzt, dass es mit dem Außengewinde der Dose in Phase liegt
    basis = (z_gew - gew_p) - (z_sch + luft_schulter)
    deckel -= Pos(0, 0, basis) * druckgewinde(gew_d, gew_p, rock - basis, aussen=False, spiel_klasse="normal")
    rand = [k for k in deckel.edges() if k.geom_type.name == "CIRCLE" and abs(k.center().Z) < 1e-3
            and k.radius < r_a - 1.5]
    deckel = sicher_fasen(deckel, rand, 0.8)                                    # Einführfase Gewinde
    # Einlage: Schrift + Ring auf der Deckeloberseite
    einl = Pos(0, 0, deckel_h - einlage_tief) * schrift(text, text_h, einlage_tief + 0.5)
    ring = Pos(0, 0, deckel_h - einlage_tief) * extrude(Circle(ring_r + ring_b / 2) - Circle(ring_r - ring_b / 2),
                                                       einlage_tief + 0.5)
    deckel, einlage = einlegen(deckel, einl + ring)

    if zusammenbau:
        z_d = z_sch + luft_schulter
        return {"schwarz": dose, "grau": Pos(0, 0, z_d) * deckel, "gold": Pos(0, 0, z_d) * einlage}   # getrennt → Kollision prüfbar
    # Drucklage: Deckel kopfüber neben der Dose
    kopf = Pos(d_aussen + 8, 0, deckel_h) * Rot(180, 0, 0)
    return {"schwarz": dose + kopf * deckel, "gold": kopf * einlage}

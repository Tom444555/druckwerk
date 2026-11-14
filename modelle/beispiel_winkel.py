"""Beispiel für werkzeug/cad.py: Montagewinkel 40×40×30 mm, 4 mm stark, mit Rundungen, Fasen und zwei M4-Senklöchern.

Aufruf:  python3 werkzeug/cad.py modelle/beispiel_winkel.py --name winkel
Druckt so wie er liegt (Fuß auf dem Bett, Schenkel senkrecht), PETG/ASA, Schicht 0.20, Wände 4, Infill 30–40 %.
"""
from build123d import Axis, Box, Pos
from cad import fase, rundung, schraubloch

# ---- Maße (mm) ----
fuss_l = 40      # Länge des liegenden Schenkels (X)
wand_h = 40      # Höhe des stehenden Schenkels (Z)
breite = 30      # Breite (Y)
dicke = 4        # Materialstärke
r_innen = 5      # Rundung innen in der Ecke (Kerbe entlasten)
r_aussen = 6     # Rundung der freien Ecken
f_kante = 1.5    # Fase an der Außenkante unten (gegen Elefantenfuß) und an den Außenkanten des Schenkels
m = 4            # Schraubengröße (Senkkopf)


def _kanten(teil, achse, **soll):
    """Kanten parallel zu `achse`, deren Mittelpunkt die Sollwerte (x=…, y=…, z=…) hat."""
    def passt(k):
        c = k.center()
        return all(abs(getattr(c, a.upper()) - w) < 1e-3 for a, w in soll.items())
    return [k for k in teil.edges().filter_by(achse) if passt(k)]


def modell():
    teil = Pos(fuss_l / 2, breite / 2, dicke / 2) * Box(fuss_l, breite, dicke)
    teil += Pos(dicke / 2, breite / 2, wand_h / 2) * Box(dicke, breite, wand_h)
    teil = rundung(teil, _kanten(teil, Axis.Y, x=dicke, z=dicke), r_innen)                       # Innenecke
    for y in (0, breite):
        teil = rundung(teil, _kanten(teil, Axis.Z, x=fuss_l, y=y), r_aussen)                     # Fußspitze
        teil = rundung(teil, _kanten(teil, Axis.X, z=wand_h, y=y), r_aussen)                     # Schenkel oben
    teil = fase(teil, _kanten(teil, Axis.Y, x=0, z=0), f_kante)                                  # Ferse unten
    teil = schraubloch(teil, (fuss_l * 0.6, breite / 2, dicke), m=m, art="senk", tiefe=dicke)    # Loch im Fuß, Kopf oben
    teil = schraubloch(teil, (dicke, breite / 2, wand_h * 0.6), m=m, art="senk", tiefe=dicke,
                       richtung=(-1, 0, 0))                                                      # Loch im Schenkel, Kopf innen
    return teil

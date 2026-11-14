// Kalibrierung 3 – Kopf-Versatz (Vier-Kopf-Passermarke). Gemeinsame Geometrie für versatz_k1…k4.scad.
// Grundplatte + Hauptskalen = Kopf 1. Je Kopf 2–4 ein Nonius in X (Zeilen) und in Y (Spalten) + Beschriftung.
// Hauptskala Teilung 2,0 mm, Nonius 1,9 mm → Ablesung 0,1 mm, Bereich ±1,0 mm (Index −10…+10).
// Die Strichreihen von Kopf 1 und Kopf n stoßen an einer gemeinsamen Linie aneinander (nie überlappend).
platte = [112, 80, 1.2];    // Grundplatte (6 Schichten à 0,2)
erhaben = 0.6;              // Strich- und Schrifthöhe über der Platte
strich_b = 0.6;             // Strichbreite (≥ 1,5 × Düse)
strich_l = 3.0;             // Strichlänge je Reihe
haupt = 2.0; nonius = 1.9; n = 10;
schrift = "DejaVu Sans:style=Bold";
zeilen_y = [14, 38, 62];    // X-Nonien: Grenzlinie bei diesem y (Kopf 1 darunter, Kopf n darüber)
x_mitte = 32;
spalten_x = [78, 92, 106];  // Y-Nonien: Grenzlinie bei diesem x (Kopf 1 links, Kopf n rechts)
y_mitte = 36;

function _lang(i) = (i == 0) ? 2.0 : (i % 5 == 0) ? 1.0 : 0;   // längere Striche bei 0, ±5, ±10

module _striche_x(teil, aussen) {   // Striche senkrecht, entlang X; aussen = +1 nach oben, −1 nach unten
  for (i = [-n:n]) let(l = strich_l + _lang(i))
    translate([x_mitte + i*teil - strich_b/2, aussen > 0 ? 0 : -l]) square([strich_b, l]);
}
module _striche_y(teil, aussen) {
  for (i = [-n:n]) let(l = strich_l + _lang(i))
    translate([aussen > 0 ? 0 : -l, y_mitte + i*teil - strich_b/2]) square([l, strich_b]);
}
module _beschr(t, s=4) text(t, size=s, font=schrift, halign="center", valign="center");

module versatz(kopf) {
  if (kopf == 1) {
    cube(platte);
    translate([0,0,platte[2]-0.01]) linear_extrude(erhaben+0.01) {
      for (y = zeilen_y) translate([0, y]) _striche_x(haupt, -1);
      for (x = spalten_x) translate([x, 0]) _striche_y(haupt, -1);
      translate([x_mitte + n*haupt + 4.5, zeilen_y[0] - 6]) _beschr("+X", 3);
      translate([spalten_x[0] - 6, y_mitte + n*haupt + 4.5]) _beschr("+Y", 3);
      translate([8, 75]) _beschr("K1", 4);
    }
  } else {
    k = kopf - 2;
    translate([0,0,platte[2]]) linear_extrude(erhaben) {
      translate([0, zeilen_y[k]]) _striche_x(nonius, +1);
      translate([spalten_x[k], 0]) _striche_y(nonius, +1);
      translate([6, zeilen_y[k] + 2.5]) _beschr(str("K", kopf), 4);
      translate([spalten_x[k] + 2.5, y_mitte + n*haupt + 8]) _beschr(str("K", kopf), 3.5);
    }
  }
}

// Kalibrierung 5 – Brücken 10/20/30/40 mm und Überhänge 45/55/65° (gemessen ab der Senkrechten).
// Grundplatte 2 mm mit eingeprägter Beschriftung. Einfarbig, ohne Stützen drucken.
grund = [160, 70, 2]; tief = 0.6; schrift = "DejaVu Sans:style=Bold";
pfeiler = [4, 8]; bh = 6; deck = 1.2;               // Pfeiler Breite × Tiefe, Höhe bis Brückenunterkante, Brückendicke
spannen = [10, 20, 30, 40];
winkel = [45, 55, 65]; uh = 10; ub = 8;             // Überhang: Höhe, Breite
function _x(i) = 6 + i*4 + (i==0?0:spannen[0]) + (i>1?spannen[1]:0) + (i>2?spannen[2]:0) + i*(2*pfeiler[0]) ;
difference() {
  cube(grund);
  for (i = [0:3]) translate([_x(i) + pfeiler[0] + spannen[i]/2, 6, grund[2]-tief])
    linear_extrude(tief+0.01) text(str(spannen[i]), size=5, font=schrift, halign="center", valign="center");
  for (j = [0:2]) translate([12 + j*46 + 8, 44, grund[2]-tief])
    linear_extrude(tief+0.01) text(str(winkel[j], "°"), size=5, font=schrift, halign="center", valign="center");
}
// Brücken
for (i = [0:3]) translate([_x(i), 12, grund[2]-0.01]) {
  cube([pfeiler[0], pfeiler[1], bh+deck+0.01]);
  translate([pfeiler[0]+spannen[i], 0, 0]) cube([pfeiler[0], pfeiler[1], bh+deck+0.01]);
  translate([0, 0, bh]) cube([2*pfeiler[0]+spannen[i], pfeiler[1], deck+0.01]);
}
// Überhänge: senkrechte Rückwand, Vorderseite neigt sich um den Winkel nach +X über
for (j = [0:2]) translate([12 + j*46, 52, grund[2]-0.01])
  rotate([90,0,0]) translate([0,0,-ub]) linear_extrude(ub)
    polygon([[0,0], [3,0], [3 + uh*tan(winkel[j]), uh], [0, uh]]);

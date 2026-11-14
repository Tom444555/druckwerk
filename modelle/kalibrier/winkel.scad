// Kalibrierung 2 – Rechtwinkligkeit X/Y: Rahmen 100×100 mm außen, Steg 6 mm, 2 mm hoch.
// Beide Diagonalen außen (Ecke zu Ecke) messen. Pfeil + „X“ auf dem unteren Steg zeigt die X-Richtung,
// „Y“ auf dem linken Steg. Ecke A (unten links) ist mit einem Punkt markiert. Einfarbig.
aussen = 100; steg = 6; hoehe = 2; erhaben = 0.6; schrift = "DejaVu Sans:style=Bold";
difference() {
  cube([aussen, aussen, hoehe]);
  translate([steg, steg, -1]) cube([aussen-2*steg, aussen-2*steg, hoehe+2]);
}
translate([0,0,hoehe-0.01]) linear_extrude(erhaben+0.01) {
  // Pfeil in +X auf dem unteren Steg
  translate([30, steg/2]) { translate([0,-0.5]) square([28,1]); translate([28,0]) polygon([[0,-2],[4,0],[0,2]]); }
  translate([68, steg/2]) text("X", size=4, font=schrift, halign="center", valign="center");
  // Pfeil in +Y auf dem linken Steg
  translate([steg/2, 30]) { translate([-0.5,0]) square([1,28]); translate([0,28]) polygon([[-2,0],[0,4],[2,0]]); }
  translate([steg/2, 68]) text("Y", size=4, font=schrift, halign="center", valign="center");
  translate([steg/2, steg/2]) circle(d=2.5, $fn=24);          // Ecke A
}

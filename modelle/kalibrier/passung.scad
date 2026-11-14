// Kalibrierung 4 – Passung: Leiste mit Löchern Ø 8 mm + Spiel 0 / 0,1 / 0,15 / 0,2 / 0,3 / 0,4 mm,
// Spielwert eingeprägt, dazu ein Stift Ø 8 mm (stehend gedruckt). Einfarbig.
d = 8; spiele = [0, 0.1, 0.15, 0.2, 0.3, 0.4]; namen = ["0", ".1", ".15", ".2", ".3", ".4"];
abstand = 14; leiste = [len(spiele)*abstand + 4, 24, 5]; tief = 0.6; fase = 0.4;
schrift = "DejaVu Sans:style=Bold";
difference() {
  cube(leiste);
  for (i = [0:len(spiele)-1]) translate([2 + abstand/2 + i*abstand, 9, 0]) {
    dd = d + spiele[i];
    translate([0,0,-1]) cylinder(d=dd, h=leiste[2]+2, $fn=128);
    translate([0,0,-0.01]) cylinder(d1=dd+2*fase, d2=dd, h=fase, $fn=128);                 // gegen Elefantenfuß
    translate([0,0,leiste[2]-fase+0.01]) cylinder(d1=dd, d2=dd+2*fase, h=fase, $fn=128);
    translate([0, 10.5, leiste[2]-tief]) linear_extrude(tief+0.01) text(namen[i], size=3.6, font=schrift, halign="center", valign="center");
  }
}
// Stift Ø 8 × 16 mm, Enden 0,5 mm angefast, steht neben der Leiste
translate([leiste[0] + 8, 12, 0]) {
  cylinder(d1=d-1, d2=d, h=0.5, $fn=128);
  translate([0,0,0.5]) cylinder(d=d, h=15, $fn=128);
  translate([0,0,15.5]) cylinder(d1=d, d2=d-1, h=0.5, $fn=128);
}

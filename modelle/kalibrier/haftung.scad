// Kalibrierung 1 – Haftung/Bettnivellierung: fünf Felder 30×30 mm, eine Schicht (0,25 mm) (Ecken + Mitte) auf 200×200 mm.
// Einfarbig, eine Schicht. Nach dem Druck: Felder ablösen und vergleichen (siehe LIESMICH.md).
feld = 30; flaeche = 200; dicke = 0.25;   // = genau eine Erstschicht im Profil „0.20mm Standard @FF C5“ (0,25 mm)
for (p = [[0,0], [flaeche-feld,0], [0,flaeche-feld], [flaeche-feld,flaeche-feld], [(flaeche-feld)/2,(flaeche-feld)/2]])
  translate([p[0], p[1], 0]) cube([feld, feld, dicke]);

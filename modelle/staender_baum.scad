// „Lebensbaum“ – Hänge-Ständer für die 20-cm-Gitarre (Eigenentwurf, zweifarbig)
// Gedrehter Stamm, Krone mit eingerollten Ästen im Ring, Wurzeln laufen als Relief über die Plektrum-Fußplatte.
// Koordinaten „stehend“: X Breite, Y nach vorn, Z hoch. Gedruckt liegend auf dem Rücken.  teil = "schwarz" | "gold" | "alles"
teil = "alles";  liegend = true;  $fn = 32;
hals_b = 10.4;  sattel_h = 160;  kopf_d = 4.1;  luft_unten = 10;  fuss_d = 4;  abstand = 11;
spalt = hals_b + 0.8;  zinke_b = 5;  bg = spalt + 2*zinke_b;  zg = fuss_d + luft_unten + sattel_h;
t = 5.5;                       // Materialdicke (Y) von Baum und Ring
kz = 138;  kr = 37;            // Kronen-Ring: Mitte (Höhe), Außenradius
stamm_o = 103;                 // Stamm-Ende / Beginn der Krone

module hoch(h, y0=0){ translate([0,y0,0]) rotate([90,0,0]) translate([0,0,-h]) linear_extrude(h) children(); }
// Ast: wächst in +Y (2D), krümmt sich, teilt sich; Spitzen rollen sich ein
module ast(l, w, tiefe, n, kr_, seite){
  s = l / n;
  hull(){ circle(d=w); translate([0, s]) circle(d=w*0.94); }
  translate([0, s]) rotate(kr_)
    if (n > 1) ast(l - s, w*0.94, tiefe, n-1, kr_, seite);
    else if (tiefe > 0) { rotate(27)  ast(l*4.3, w*0.86, tiefe-1, 6, -seite*5.5, -seite);
                          rotate(-25) ast(l*3.9, w*0.86, tiefe-1, 6, seite*6.5, seite); }
    else locke(w, seite);
}
module locke(w, seite){ for (i = [0 : 12 : 400]) hull(){ for (j = [i, i+12]) let(r = 3.6 - 2.6*j/412)
    translate([seite*(-3.6 + r*cos(j)), r*sin(j)]) circle(d = w*(1 - 0.45*j/412)); } }
module krone2d(){
  intersection(){ translate([0, kz]) circle(kr - 1.2, $fn=120);
    translate([0, stamm_o]) for (m = [0, 1]) mirror([m, 0]) {      // spiegelbildlich = ruhige, runde Krone
      for (a = [[-14, 38, -1], [-40, 37, 1], [-70, 31, -1]]) rotate(a[0]) ast(a[1], 3.6, 2, 6, a[2]*4.5, a[2]); } }
  translate([-2, stamm_o]) square([4, zg - 26 - stamm_o]);         // Mittelast trägt die Gabel
}
module ring2d(){ translate([0, kz]) difference(){ circle(kr, $fn=160); circle(kr - 3, $fn=160); } }
module stamm2d(){
  for (i = [0:2]) for (z = [16 : 1.5 : stamm_o])
    hull(){ for (q = [z, z+1.5]) translate([3.0*sin(360*q/44 + i*120) * min(1, (stamm_o + 4 - q)/14), q]) circle(d=4.2); }
  // Wurzelansatz hinten (flach an der Rückseite)
  for (a = [[-52, 24, 1], [-24, 19, -1], [24, 19, 1], [52, 24, -1]])
    intersection(){ translate([-60, 0]) square([120, 40]); translate([0, 20]) rotate(180 + a[0]) ast(a[1], 4.4, 0, 7, a[2]*5, a[2]); }
}
module wurzeln_relief(){   // auf der Fußplatte nach vorn laufend
  for (a = [[-62, 30, 1], [-34, 40, -1], [-8, 47, 1], [18, 44, -1], [44, 36, 1], [68, 27, -1]])
    translate([0, t - 1, fuss_d - 0.01]) linear_extrude(1.5) intersection(){ offset(-1.6) fuss2d();
      rotate(-a[0]) for (y = [0 : 1.5 : a[1]]) hull(){ for (q = [y, y+1.5])
        translate([a[2]*2.6*sin(q*9), q]) circle(d = 4.2 - 2.9*q/a[1]); } }
}
module klotz(){
  hull(){ translate([-bg/2, 0, zg-14]) cube([bg, abstand, 14]); translate([-6, 0, zg-27]) cube([12, t, 1]); }
  for (s = [-1,1]) translate([s*(spalt/2 + zinke_b/2), 0, 0]) {
    hull(){ translate([-zinke_b/2, abstand-0.1, zg-6]) cube([zinke_b, 0.1, 6]);
            for (dz = [1.6, 4.4]) translate([0, abstand+kopf_d+3.2, zg-dz]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true); }
    hull(){ translate([0, abstand+kopf_d+3.2, zg-1.6]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true);
            translate([0, abstand+kopf_d+3.6, zg+2.2]) rotate([0,90,0]) cylinder(r=1.2, h=zinke_b, center=true); } }
}
module fuss2d(){ hull(){ for (x = [-33,33]) { translate([x, 2.5]) circle(2.5); translate([x*0.985, 10]) circle(3); }
                         for (x = [-27,27]) translate([x, 27]) circle(8); for (x = [-13,13]) translate([x, 47]) circle(9); translate([0, 56]) circle(8); } }
module fuss(){ linear_extrude(fuss_d) fuss2d();
  translate([0,0,fuss_d-0.01]) linear_extrude(0.6) difference(){ fuss2d(); offset(-1.4) fuss2d(); } }   // feiner Rand
module schwarz(){ fuss(); klotz(); hoch(t) ring2d(); }
module gold(){ hoch(t) { krone2d(); stamm2d(); } wurzeln_relief(); }
module dreh(){ if (liegend) rotate([90,0,0]) children(); else children(); }
dreh(){ if (teil == "schwarz") difference(){ schwarz(); gold(); }
        else if (teil == "gold") difference(){ gold(); translate([-bg/2-0.01, -1, zg-14]) cube([bg+0.02, 30, 30]); }
        else { color([0.13,0.13,0.13]) difference(){ schwarz(); gold(); } color([0.83,0.63,0.15]) gold(); } }

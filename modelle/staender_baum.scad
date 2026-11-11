// „Lebensbaum“ v2 – Hänge-Ständer für die 20-cm-Gitarre (Eigenentwurf, drei Farben, sehr fein)
// Breite Krone mit vielfach verzweigten, eingerollten Ästen und Blättern, Stamm aus fünf gedrehten Strängen,
// Wurzeln fächern hinten aus und laufen als Relief über die Fußplatte; vorn eine „Blume des Lebens“ als Einlage.
// Koordinaten „stehend“: X Breite, Y nach vorn, Z hoch. Gedruckt liegend auf dem Rücken.
// teil = "schwarz" | "gold" | "blatt" | "alles"
teil = "alles";  liegend = true;  $fn = 20;
hals_b = 10.4;  sattel_h = 160;  kopf_d = 4.1;  luft_unten = 10;  fuss_d = 4;  abstand = 11;
spalt = hals_b + 0.8;  zinke_b = 5;  bg = spalt + 2*zinke_b;  zg = fuss_d + luft_unten + sattel_h;
kz = 138;  krx = 47;  kry = 36;     // Krone: Mitte (Höhe), Halbachsen
stamm_o = 100;                      // Stamm-Ende / Beginn der Krone
dicke = [3.0, 3.8, 4.6, 5.5];       // Materialdicke (Y) je Ast-Generation: feine Zweige flacher -> Tiefe
blatt_d = 2.4;

module hoch(h){ rotate([90,0,0]) translate([0,0,-h]) linear_extrude(h) children(); }
module blatt2d(){ hull(){ translate([0, 0.5]) circle(d=0.8); translate([0, 2.1]) circle(d=1.75); translate([0, 4.0]) circle(d=0.6); } }
module locke(w, seite){ for (i = [0 : 20 : 380]) hull(){ for (j = [i, i+20]) let(r = 2.6 - 1.9*j/400)
    translate([seite*(-2.6 + r*cos(j)), r*sin(j)]) circle(d = max(0.75, w*(1 - 0.3*j/400))); } }
// Ast: L Gesamtlänge (6 Stücke), teilt sich am Ende; zeige = welche Generation gezeichnet wird; blatt = nur Blätter
module ast(L, w, tiefe, i, kr_, seite, zeige, blatt){
  s = L / 6;  ww = max(0.8, w);
  if (!blatt && zeige == tiefe) hull(){ circle(d=ww); translate([0, s]) circle(d=max(0.8, w*0.93)); }
  if (blatt && tiefe <= 1 && i % 2 == 0) translate([0, s*0.5]) rotate(-seite*(i % 4 == 0 ? 1 : -1)*58) blatt2d();
  translate([0, s]) rotate(kr_)
    if (i > 1) ast(L, w*0.93, tiefe, i-1, kr_, seite, zeige, blatt);
    else if (tiefe > 0) { rotate(25)  ast(L*0.70, w*0.9, tiefe-1, 6, -seite*6.5, -seite, zeige, blatt);
                          rotate(-23) ast(L*0.66, w*0.9, tiefe-1, 6,  seite*7.5,  seite, zeige, blatt); }
    else { if (!blatt && zeige == 0) locke(ww, seite); if (blatt) rotate(seite*25) blatt2d(); }
}
aeste = [[-17, 26, -1], [-47, 27, 1], [-77, 25, -1], [-103, 15, 1]];
module krone2d(zeige, blatt){
  intersection(){ union(){ translate([0, kz]) scale([krx + (blatt ? 2 : 0), kry + (blatt ? 2 : 0)]) circle(1, $fn=120);
                         translate([-krx, stamm_o - 16]) square([2*krx, kz - stamm_o + 16]); }   // unten nicht beschneiden
    translate([0, stamm_o]) for (m = [0, 1]) mirror([m, 0]) for (a = aeste) rotate(a[0]) ast(a[1], 3.4, 3, 6, a[2]*4.5, a[2], zeige, blatt); }
}
function stamm_a(z) = 2.2 + 6.5 * pow(abs(z - 58) / 44, 3);
module stamm2d(){
  for (i = [0:4]) for (z = [14 : 1.5 : stamm_o + 1])
    hull(){ for (q = [z, z+1.5]) translate([stamm_a(q) * sin(360*q/40 + i*72), q]) circle(d=2.5); }
  translate([-1.8, stamm_o - 2]) square([3.6, zg - 26 - stamm_o + 2]);         // Mittelast trägt die Gabel
}
wurzeln = [[32, 20, 1], [58, 26, -1], [80, 30, 1], [100, 26, -1]];
module wurzeln2d(zeige){   // hinten, flach an der Rückseite
  intersection(){ translate([-47, 0.3]) square([94, 40]);
    translate([0, 21]) for (m = [0, 1]) mirror([m, 0]) for (a = wurzeln) rotate(180 - a[0]) ast(a[1], 3.6, 1, 6, a[2]*5, a[2], zeige, false); }
}
module wurzel_relief(){    // auf der Fußplatte nach vorn
  for (g = [0, 1]) translate([0, 4.5, fuss_d - 0.01]) linear_extrude(g == 1 ? 1.6 : 1.1) intersection(){ offset(-1.8) fuss2d();
    for (m = [0, 1]) mirror([m, 0]) for (a = [[-78, 24, 1], [-50, 26, -1], [-22, 21, 1]]) rotate(a[0]) ast(a[1], 3.4, 1, 6, a[2]*5, a[2], g, false); }
}
module blume2d(){ r = 4.1;  b = 0.56;    // „Blume des Lebens“: 7 Kreise im Doppelring
  module k(rr){ difference(){ circle(rr + b/2, $fn=64); circle(rr - b/2, $fn=64); } }
  intersection(){ circle(2*r + b/2, $fn=64); union(){ k(r); for (a = [0:60:300]) rotate(a) translate([r, 0]) k(r); } }
  k(2*r); k(2*r + 1.5); for (a = [0:30:330]) rotate(a) translate([2*r + 0.75, 0]) circle(d=0.9);
}
module klotz(){
  hull(){ translate([-bg/2, 0, zg-14]) cube([bg, abstand, 14]); translate([-5, 0, zg-27]) cube([10, 5.5, 1]); }
  for (s = [-1,1]) translate([s*(spalt/2 + zinke_b/2), 0, 0]) {
    hull(){ translate([-zinke_b/2, abstand-0.1, zg-6]) cube([zinke_b, 0.1, 6]);
            for (dz = [1.6, 4.4]) translate([0, abstand+kopf_d+3.2, zg-dz]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true); }
    hull(){ translate([0, abstand+kopf_d+3.2, zg-1.6]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true);
            translate([0, abstand+kopf_d+3.6, zg+2.2]) rotate([0,90,0]) cylinder(r=1.2, h=zinke_b, center=true); } }
}
module fuss2d(){ hull(){ for (x = [-36,36]) { translate([x, 2.5]) circle(2.5, $fn=24); translate([x*0.985, 10]) circle(3, $fn=24); }
                         for (x = [-29,29]) translate([x, 28]) circle(9, $fn=48); for (x = [-14,14]) translate([x, 50]) circle(10, $fn=48); translate([0, 58]) circle(9, $fn=48); } }
module fuss(){ linear_extrude(fuss_d) fuss2d();
  translate([0,0,fuss_d-0.01]) linear_extrude(0.6) difference(){ fuss2d(); offset(-1.3) fuss2d(); } }
module einlage(){ translate([0, 50, fuss_d - 0.7]) linear_extrude(0.7) blume2d(); }
module schwarz(){ fuss(); klotz(); }
module gold(){ for (g = [0:3]) hoch(dicke[g]) krone2d(g, false);
  hoch(5.5) stamm2d(); for (g = [0, 1]) hoch(g == 1 ? 5.5 : 4.2) wurzeln2d(g);
  wurzel_relief(); einlage(); }
module blatt(){ hoch(blatt_d) krone2d(-1, true); }
module dreh(){ if (liegend) rotate([90,0,0]) children(); else children(); }
module gold_frei(){ difference(){ gold(); translate([-bg/2-0.01, -1, zg-14]) cube([bg+0.02, 30, 30]); } }
dreh(){ if (teil == "schwarz") difference(){ schwarz(); gold(); }
        else if (teil == "gold") gold_frei();
        else if (teil == "blatt") difference(){ blatt(); gold(); schwarz(); }
        else { color([0.13,0.13,0.13]) difference(){ schwarz(); gold(); } color([0.83,0.63,0.15]) gold_frei(); color([0.8,0.82,0.85]) difference(){ blatt(); gold(); schwarz(); } } }

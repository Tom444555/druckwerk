// „Die Schleife“ – geflochtener Hänge-Ständer für die 20-cm-Gitarre (Eigenentwurf, zweifarbig)
// Zwei Bänder winden sich als Zopf nach oben (abwechselnd über/unter), enden in Schnecken neben der Gabel.
// Fußplatte in Plektrum-Form mit Schallwellen-Rillen und Schriftzug. Gedruckt liegend auf dem Rücken.
// Koordinaten „stehend“: X Breite, Y nach vorn, Z hoch.   teil = "schwarz" | "gold" | "alles"
use <../schriften/Pacifico-Regular.ttf>
teil = "alles";  liegend = true;  $fn = 40;
// --- Gitarre / Gabel (Maße wie gitarrenstaender.scad, Passung geprüft) ---
hals_b = 10.4;  sattel_h = 160;  kopf_d = 4.1;  luft_unten = 10;
fuss_d = 4;  abstand = 11;                     // Fußdicke; Halsrücken liegt bei Y = abstand an
spalt = hals_b + 0.8;  zinke_b = 5;  bg = spalt + 2*zinke_b;
zg = fuss_d + luft_unten + sattel_h;           // Oberkante Gabel
// --- Zopf ---
band_b = 4.2;  band_t = 5.5;  hub = 1.0;       // Bandbreite, Dicke, Erhöhung des oberen Bands an Kreuzungen
z_u = fuss_d;  z_o = zg - 16;  wellen = 4;  lam = (z_o - z_u) / wellen;
function amp(z) = 14 - 8 * (z - z_u) / (z_o - z_u);
function xa(z) = amp(z) * cos(360 * (z - z_u) / lam);
kreuz = [for (k = [0 : 2*wellen-1]) z_u + lam/4 + k*lam/2];

module band2d(s){ st = 1.2; for (z = [z_u : st : z_o - st]) hull(){ translate([s*xa(z), z]) circle(d=band_b); translate([s*xa(z+st), z+st]) circle(d=band_b); } }
module scheiben(par){ for (k = [0 : len(kreuz)-1]) if (k % 2 == par) translate([0, kreuz[k]]) circle(r=6.5); }
module hoch(h){ rotate([90,0,0]) translate([0,0,-h]) linear_extrude(h) children(); }   // 2D (X,Z) -> Körper Y 0..h
module band(s){   // s=+1: Band A (oben bei geraden Kreuzungen), s=-1: Band B
  par = s > 0 ? 0 : 1;
  difference(){ hoch(band_t) band2d(s); translate([0,1,0]) hoch(20) intersection(){ band2d(-s); scheiben(1-par); } }
  hoch(band_t + hub) intersection(){ band2d(s); scheiben(par); }
}
module schnecke(s){   // Spirale neben dem Gabelklotz
  hoch(band_t) for (i = [0 : 5 : 560]) hull(){
    for (j = [i, i+5]) let(r = 7.2 - 5.6*j/565, w = 3.0 - 1.3*j/565)
      translate([s*(bg/2 + 6.2 + r*cos(j+180)), zg - 9.5 + r*sin(j+180)*1.0]) circle(d=w); }
  hoch(band_t) hull(){ translate([s*(bg/2 - 1), zg - 9.5]) circle(d=3); translate([s*(bg/2 + 6.2 - 7.2), zg - 9.5]) circle(d=3); }
}
module klotz(){
  hull(){ translate([-bg/2, 0, zg-14]) cube([bg, abstand, 14]); translate([-8, 0, z_o-6]) cube([16, band_t, 1]); }
  for (s = [-1,1]) translate([s*(spalt/2 + zinke_b/2), 0, 0]) {
    hull(){ translate([-zinke_b/2, abstand-0.1, zg-6]) cube([zinke_b, 0.1, 6]);
            for (dz = [1.6, 4.4]) translate([0, abstand+kopf_d+3.2, zg-dz]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true); }
    hull(){ translate([0, abstand+kopf_d+3.2, zg-1.6]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true);
            translate([0, abstand+kopf_d+3.6, zg+2.2]) rotate([0,90,0]) cylinder(r=1.2, h=zinke_b, center=true); } }
}
module fuss2d(){ hull(){ for (x = [-32,32]) { translate([x, 2.5]) circle(2.5); translate([x*0.97, 12]) circle(3); }
                         for (x = [-25,25]) translate([x, 30]) circle(7); translate([0, 54]) circle(9); } }
module schrift2d(){ translate([0, 38]) rotate(180) text("Loopsmiths", size=6.2, font="Pacifico", halign="center", valign="center"); }
module wellen2d(){ for (r = [20, 26, 32]) difference(){ circle(r+0.45, $fn=96); circle(r-0.45, $fn=96); } }
module fuss(){
  difference(){
    linear_extrude(fuss_d) fuss2d();
    translate([0,0,fuss_d-0.5]) linear_extrude(1) intersection(){ offset(-2.5) fuss2d(); translate([0,-2]) wellen2d(); translate([-40, 6]) square([80, 22]); }
    translate([0,0,fuss_d-0.8]) linear_extrude(1) schrift2d();
  }
  for (s = [-1,1]) translate([s*14, 0, 0]) hull(){ translate([-2.1, band_t-0.1, fuss_d-0.1]) cube([4.2, 17, 0.1]); translate([-2.1, band_t-0.1, fuss_d]) cube([4.2, 0.1, 8.5]); }
}
module schwarz(){ fuss(); klotz(); band(1); schnecke(1); }
module gold(){ band(-1); schnecke(-1); translate([0,0,fuss_d-0.8]) linear_extrude(0.8) schrift2d(); }
module dreh(){ if (liegend) rotate([90,0,0]) children(); else children(); }
dreh(){ if (teil == "schwarz") difference(){ schwarz(); gold(); }
        else if (teil == "gold") gold();
        else { color([0.13,0.13,0.13]) difference(){ schwarz(); gold(); } color([0.83,0.63,0.15]) gold(); } }

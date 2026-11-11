// „Note“ – Hänge-Ständer für die 20-cm-Gitarre in Form einer Sechzehntelnote (Eigenentwurf, zweifarbig)
// Notenkopf = gewölbter Fuß, Hals = geschwungener Stiel mit rundem Querschnitt, zwei Fähnchen wellen sich plastisch.
// Koordinaten „stehend“: X Breite (von vorn gesehen ist +X links), Y nach vorn, Z hoch. Gedruckt liegend auf dem Rücken.
use <../schriften/Pacifico-Regular.ttf>
teil = "alles";  liegend = true;  $fn = 40;
hals_b = 10.4;  sattel_h = 160;  kopf_d = 4.1;  luft_unten = 10;  fuss_d = 4;  abstand = 11;
spalt = hals_b + 0.8;  zinke_b = 5;  bg = spalt + 2*zinke_b;  zg = fuss_d + luft_unten + sattel_h;

// Halbrunder „Wulst“ zwischen zwei Punkten (X,Z) mit Breite w und Höhe h (in Y) – liegt flach auf Y=0
module perle(p, w, h){ translate([p[0], 0, p[1]]) intersection(){ scale([w/2, h, w/2]) sphere(1); translate([-w, 0, -w]) cube([2*w, 2*h, 2*w]); } }
module wulst(pts, ws, hs){ for (i = [0 : len(pts)-2]) hull(){ perle(pts[i], ws[i], hs[i]); perle(pts[i+1], ws[i+1], hs[i+1]); } }
// Stiel: leichte S-Kurve, unten kräftig, oben schlank
sz = [for (z = [3 : 4 : zg-20]) z];
stiel_p = [for (z = sz) [1.6*sin((z-3)*360/(zg-23)), z]];
module stiel(){ wulst(stiel_p, [for (z = sz) 8.5 - 2.5*z/zg], [for (z = sz) 6.2 - 0.9*z/zg]); }
// Fähnchen: schwingt vom Stiel nach außen/unten, Breite wie mit der Feder gezogen, Höhe wellt sich
function fahne(z0, l, i, n) = let(u = i/n) [ -(3 + l*0.62*pow(u, 0.75) + 5*sin(u*180)), z0 - l*u*0.95 - 7*sin(u*200)*u ];
module faehnchen(z0, l){ n = 26;
  wulst([for (i = [0:n]) fahne(z0, l, i, n)], [for (i = [0:n]) 1.6 + 8.5*sin(180*pow(i/n, 0.8))*(1 - 0.35*i/n)],
        [for (i = [0:n]) 3.2 + 2.4*sin(i/n*400 + 30)]);
  // eingerollte Spitze
  e = fahne(z0, l, n, n);
  for (j = [0 : 15 : 330]) hull(){ for (q = [j, j+15]) let(r = 3.4 - 2.4*q/345) perle([e[0] + 3.4 - r*cos(q), e[1] - r*sin(q)], 2.2 - 0.9*q/345, 3.0); }
}
// Notenkopf als Fuß: schräges Oval, hinten gerade (Druckauflage), nach vorn gewölbt
module kopf2d(){ hull(){ for (x = [-12, 44]) translate([x, 2.5]) circle(2.5); translate([-17, 16]) circle(9); translate([49, 22]) circle(11);
                         translate([4, 44]) circle(12); translate([34, 46]) circle(13); } }
module kopf(){
  linear_extrude(fuss_d) kopf2d();
  intersection(){ linear_extrude(20) offset(-1.2) kopf2d(); translate([17, 27, fuss_d - 26]) scale([1.25, 1, 1]) sphere(31.5, $fn=120); }   // Wölbung
}
module schrift(){ translate([18, 33, 0]) rotate(180) linear_extrude(20) text("Loopsmiths", size=5.6, font="Pacifico", halign="center", valign="center"); }
module klotz(){
  hull(){ translate([-bg/2, 0, zg-14]) cube([bg, abstand, 14]); perle([0, zg-27], 6, 5.3); }
  for (s = [-1,1]) translate([s*(spalt/2 + zinke_b/2), 0, 0]) {
    hull(){ translate([-zinke_b/2, abstand-0.1, zg-6]) cube([zinke_b, 0.1, 6]);
            for (dz = [1.6, 4.4]) translate([0, abstand+kopf_d+3.2, zg-dz]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true); }
    hull(){ translate([0, abstand+kopf_d+3.2, zg-1.6]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true);
            translate([0, abstand+kopf_d+3.6, zg+2.2]) rotate([0,90,0]) cylinder(r=1.2, h=zinke_b, center=true); } }
}
module koerper(){ intersection(){ koerper_roh(); translate([-200,-1,0]) cube([400,200,400]); } }   // nichts ragt unter die Standfläche
module koerper_roh(){ kopf(); stiel(); klotz(); faehnchen(zg - 6, 52); faehnchen(zg - 30, 44);
  hull(){ perle([0, 4], 9, 6.5); translate([-3, 0, fuss_d-0.1]) cube([6, 22, 0.1]); }   // Stütze Stiel -> Kopf
}
module einlage(){ intersection(){ schrift(); difference(){ translate([0,0,0.8]) kopf(); kopf_tief(); } } }
module kopf_tief(){ translate([0,0,-0.8]) kopf(); }
module gold(){ intersection(){ schrift(); difference(){ kopf(); translate([0,0,-0.9]) kopf(); } } }   // Schriftzug 0,9 mm tief eingelegt
module dreh(){ if (liegend) rotate([90,0,0]) children(); else children(); }
dreh(){ if (teil == "schwarz") difference(){ koerper(); gold(); }
        else if (teil == "gold") gold();
        else { color([0.13,0.13,0.13]) difference(){ koerper(); gold(); } color([0.83,0.63,0.15]) gold(); } }

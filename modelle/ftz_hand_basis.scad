// „FTZ“ steht auf „Fritz“ und wird von einer Hand gehalten – gemeinsame Maße/Module
// Schrift: UnifrakturMaguntia (OFL). Alle Teile (eine Datei pro Farbe) nutzen diese Datei.
use <../schriften/UnifrakturMaguntia-Book.ttf>
schrift = "UnifrakturMaguntia";
$fn = 20;

// --- Maße ---
s_breite = 124;  s_tiefe = 48;  s_hoehe = 6;  s_radius = 6;   // Sockel (schwarz)
rand_b = 3;  rand_h = 1.2;                                    // weißer Rand
yc = 20;  tiefe = 12;                                         // Buchstaben: Mitte/Tiefe in Y
y0 = yc - tiefe/2;  y1 = yc + tiefe/2;                        // Vorder-/Rückseite der Schrift
g_fritz = 34;  g_ftz = 30;                                    // Schriftgrößen
zF = s_hoehe + 9.5;                // Grundlinie „Fritz“ (Unterlängen stehen auf der Leiste)
brett_u = zF + 30;  brett_d = 6;   // Brett auf „Fritz“, auf dem „FTZ“ steht
zT = brett_u + brett_d;            // Grundlinie „FTZ“
ftz_oben = zT + 30.6;              // Oberkante „FTZ“

// --- Hilfsmodule ---
module rund(b,h,r){ translate([r,r]) offset(r) square([b-2*r,h-2*r]); }
module kugel(p,r){ translate(p) sphere(r); }
module ei(p,r,s){ translate(p) scale(s) sphere(r); }               // gestauchte Kugel
module rohr(pts,r){ for(i=[0:len(pts)-2]) hull(){ kugel(pts[i],r); kugel(pts[i+1],r); } }
// Ader: Pfad unterteilen (n Stücke je Abschnitt) und seitlich in X leicht wellen
function _lerp(a,b,t) = a + (b-a)*t;
function welle(pts, n=6, a=0.45) = [ for(i=[0:len(pts)-2]) for(k=[0:n-1])
  let(t=k/n, q=_lerp(pts[i],pts[i+1],t)) q + [a*sin(30*(i*n+k)), 0, 0] , pts[len(pts)-1] ];
module ader(pts, r){ rohr(welle(pts), r); }
module rohr_v(pts,rs){ for(i=[0:len(pts)-2]) hull(){ kugel(pts[i],rs[i]); kugel(pts[i+1],rs[i+1]); } }
module text3d(t,g,z){ translate([0,y1,z]) rotate([90,0,0]) linear_extrude(tiefe) text(t,size=g,font=schrift,halign="center"); }

// --- Sockel / Leisten (Sockel X von -s_breite/2 bis +s_breite/2) ---
module sockel(){ translate([-s_breite/2,0]) linear_extrude(s_hoehe) rund(s_breite,s_tiefe,s_radius); }
module rand(){ translate([-s_breite/2,0,s_hoehe]) linear_extrude(rand_h) difference(){
  rund(s_breite,s_tiefe,s_radius);
  translate([rand_b,rand_b]) rund(s_breite-2*rand_b,s_tiefe-2*rand_b,s_radius-rand_b/2); } }
module leiste(){ translate([-40, y1-4, s_hoehe]) cube([82, 4, zF - s_hoehe + 1.5]); }   // hinter „Fritz“
module brett(){ translate([-46, y0, brett_u]) cube([92, tiefe, brett_d]); }              // unter „FTZ“

// --- Schrift ---
module fritz(){ text3d("Fritz", g_fritz, zF);
  translate([13.2, y0, zF+23]) cube([3, tiefe, 5]); }      // Steg zum i-Punkt
module ftz(){ text3d("FTZ", g_ftz, zT); }
module schrift_fertig(){ difference(){ union(){ fritz(); ftz(); } leiste(); brett(); } }

// ================= HAND (rechte Hand, von hinten greifend) =================
hy = 29.5;                 // Mittelebene der Handfläche in Y
hb = hy + 4;               // Handrücken-Oberfläche
k_z = zT + 23;             // Höhe der Fingerknöchel

module handflaeche(){
  hull(){
    ei([ 1, hy, zT-5], 4, [1,1,1.2]);  ei([35, hy, zT-6], 4, [1,1,1.2]);
    ei([ 3, hy, k_z-1], 4.2, [1.1,1,1]); ei([12, hy, k_z+0.8], 4.2, [1.1,1,1]);
    ei([21, hy, k_z+1], 4.2, [1.1,1,1]); ei([30, hy, k_z], 4.2, [1.1,1,1]);
    ei([39, hy, zT+8], 4.5, [1,1,1.3]);              // Daumenballen
  }
}
// Unterarm: ovaler Querschnitt, unten breiter, steckt im Sockel
module unterarm(){
  hull(){ ei([19, 34.5, s_hoehe-1], 9, [1.25,0.85,0.3]);  ei([19, 33, zT-12], 7.5, [1.25,0.75,0.4]); }
  hull(){ ei([19, 33, zT-12], 7.5, [1.25,0.75,0.4]);  ei([19, hy+0.5, zT-6], 6.5, [1.6,0.65,0.5]); }
  // Handgelenk-Knochen (Elle) als kleiner Höcker
  kugel([10.5, 36, zT-10], 3);
}
// Finger: x-Position, Länge (Faktor), Dicke
module finger(x, l, d){
  pk = [x, hy, k_z];                                 // Grundgelenk
  p1 = [x, hy-1.2, ftz_oben + 1.5 + 1.5*l];          // Mittelgelenk (über der Schrift)
  p2 = [x, yc + 0.5, ftz_oben + 3.4*d];              // über der Kante
  p3 = [x, y0 - 2.4*d, ftz_oben + 0.5];              // Endgelenk vorne
  p4 = [x, y0 - 2.1*d, ftz_oben - 4 - 5*l];          // Fingerkuppe vor der Schrift
  rohr_v([pk,p1,p2,p3,p4], [3.7*d, 3.4*d, 3.2*d, 2.9*d, 2.5*d]);
  // Knöchel/Gelenkpolster
  kugel(pk + [0, 1.6, 0.5], 3.7*d);
  kugel(p1 + [0, 0.8, 0.8], 3.55*d);
  kugel(p3 + [0, -0.6, 0.6], 3.15*d);
  // Fingernagel vorne an der Kuppe (flach, leicht erhaben)
  translate(p4 + [0, -1.6*d, 2.2]) rotate([8,0,0]) scale([0.95,0.3,1.35]) sphere(2.2*d);
  translate(p4 + [0, -2.05*d, 4.6*d]) rotate([0,90,0]) scale([0.4,0.6,1]) cylinder(r=1.4*d, h=3.6*d, center=true);  // Nagelhaut
  // Querfalten über den Gelenken (Hautfalten)
  for(p=[p1,p3]) for(o=[-0.9,0.9]) translate(p+[0,1.2,3.1*d+o]) rotate([0,90,0]) cylinder(r=0.45,h=4*d,center=true);
}
module daumen(){
  pa = [37, hy, zT+6];  pb = [44, yc+5, zT+11];  pc = [47.2, yc-1, zT+15];  pd = [43.5, y0-3, zT+17];
  rohr_v([pa,pb,pc,pd],[5.2,4.0,3.6,3.0]);
  kugel(pb+[0.8,0.6,0],4.2);  kugel(pc+[0.6,0,0],3.7);
  translate(pd+[0.2,-2.4,0.8]) rotate([0,0,-20]) scale([1,0.32,1.2]) sphere(2.4);   // Daumennagel
}
// Sehnen auf dem Handrücken (zu jedem Fingerknöchel)
module sehnen(){
  for(x=[3,12,21,30]) rohr([[19+(x-19)*0.35, hb-0.4, zT-6], [x, hb-0.2, k_z-2]], 1.0);
}
// Adern: verzweigte, leicht gewellte Venen auf Handrücken und Unterarm (Ø ca. 1,6–2 mm)
module adern(){
  r = 0.95;  ya = hb - 0.15;
  // Unterarm-Rückseite folgt der Verjüngung (y der Oberfläche abhängig von z)
  function yu(z) = 42.1 + (38.6-42.1)*(z-s_hoehe)/(zT-12-s_hoehe) - 0.35;
  // Hauptvenen Unterarm
  ader([[16, yu(s_hoehe+3), s_hoehe+3], [15, yu(s_hoehe+12), s_hoehe+12], [17, yu(s_hoehe+20), s_hoehe+20], [16, yu(zT-14), zT-14], [14, ya+1.5, zT-8]], 1.1);
  ader([[23, yu(s_hoehe+6), s_hoehe+6], [24.5, yu(s_hoehe+16), s_hoehe+16], [22.5, yu(zT-16), zT-16], [24, ya+1.3, zT-9]], 1.0);
  ader([[17, yu(s_hoehe+20), s_hoehe+20], [21, yu(s_hoehe+26), s_hoehe+26], [22.5, yu(zT-16), zT-16]], 0.8);   // Querverbindung
  // Venennetz Handrücken
  ader([[14, ya, zT-8], [10, ya, zT-2], [8, ya, zT+5], [5.5, ya, zT+12], [4, ya, k_z-4]], r);
  ader([[24, ya, zT-9], [26, ya, zT-2], [29, ya, zT+6], [31, ya, zT+13], [30.5, ya, k_z-4]], r);
  ader([[8, ya, zT+5], [12, ya, zT+9], [17, ya, zT+10], [22, ya, zT+12], [29, ya, zT+6]], 0.85);  // Venenbogen
  ader([[12, ya, zT+9], [12.5, ya, zT+15], [11.5, ya, k_z-4]], 0.75);
  ader([[22, ya, zT+12], [21, ya, zT+17], [21.5, ya, k_z-4]], 0.75);
  ader([[26, ya, zT-2], [33, ya, zT+2], [37, ya-0.5, zT+7]], 0.8);                       // zum Daumen
}
module hand_roh(){ handflaeche(); unterarm(); daumen(); sehnen(); adern();
  finger(30, 1.00, 1.00);   // Zeigefinger (neben dem Daumen)
  finger(21, 1.10, 1.03);   // Mittelfinger
  finger(12, 1.02, 0.98);   // Ringfinger
  finger( 3, 0.85, 0.88);   // kleiner Finger
}
// Hand ohne Überschneidung mit Schrift/Brett/Leiste (saubere Farbtrennung)
module hand(){ difference(){ hand_roh(); union(){ fritz(); ftz(); brett(); leiste(); } sockel(); } }

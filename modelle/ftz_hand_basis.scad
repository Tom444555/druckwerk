// „FTZ“ steht auf „Fritz“ und wird von einer realistischen Hand (MakeHuman, CC0) gehalten
// Schrift: UnifrakturMaguntia (OFL). Alle Teile (eine Datei pro Farbe) nutzen diese Datei.
use <../schriften/UnifrakturMaguntia-Book.ttf>
schrift = "UnifrakturMaguntia";
$fn = 20;

// --- Maße ---
s_breite = 190;  s_tiefe = 66;  s_hoehe = 6;  s_radius = 6;   // Sockel (schwarz)
rand_b = 3;  rand_h = 1.2;                                    // weißer Rand
yc = 20;  tiefe = 14;   // Tiefe „Fritz“ und Brett
tiefe_ftz = 8;          // Tiefe „FTZ“ = Spalt im Griff der Hand (werkzeug/hand/baue_hand.py)
y0 = yc - tiefe/2;  y1 = yc + tiefe/2;                        // Vorder-/Rückseite der Schrift
g_fritz = 50;  g_ftz = 56;                                    // Schriftgrößen
zF = s_hoehe + 14;                // Grundlinie „Fritz“ (Unterlängen stehen auf der Leiste)
brett_u = zF + 45;  brett_d = 10;   // Brett auf „Fritz“, auf dem „FTZ“ steht
zT = brett_u + brett_d;            // Grundlinie „FTZ“
ftz_oben = zT + 57.1;              // Oberkante „FTZ“

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
module text3d(t,g,z,tf=tiefe){ translate([0,yc+tf/2,z]) rotate([90,0,0]) linear_extrude(tf) text(t,size=g,font=schrift,halign="center"); }

// --- Sockel / Leisten (Sockel X von -s_breite/2 bis +s_breite/2) ---
module sockel(){ translate([-s_breite/2,0]) linear_extrude(s_hoehe) rund(s_breite,s_tiefe,s_radius); }
module rand(){ translate([-s_breite/2,0,s_hoehe]) linear_extrude(rand_h) difference(){
  rund(s_breite,s_tiefe,s_radius);
  translate([rand_b,rand_b]) rund(s_breite-2*rand_b,s_tiefe-2*rand_b,s_radius-rand_b/2); } }
module leiste(){ translate([-59, y1-4, s_hoehe]) cube([121, 4, zF - s_hoehe + 2]); }   // hinter „Fritz“
module brett(){ translate([-84, y0, brett_u]) cube([168, tiefe, brett_d]); }              // unter „FTZ“

// --- Schrift ---
module fritz(){ text3d("Fritz", g_fritz, zF);
  translate([19.4, y0, zF+33.5]) cube([4.4, tiefe, 7.5]); }      // Steg zum i-Punkt
module ftz(){ text3d("FTZ", g_ftz, zT, tiefe_ftz); }
module schrift_fertig(){ difference(){ union(){ fritz(); ftz(); } leiste(); brett(); } }


echo(MASSE=[ftz_oben, yc, s_hoehe, tiefe_ftz]);

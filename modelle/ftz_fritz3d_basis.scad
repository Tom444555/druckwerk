// „FTZ Fritz“ als stehende 3D-Fraktur-Buchstaben auf Sockel – gemeinsame Maße
use <../schriften/UnifrakturMaguntia-Book.ttf>
schrift   = "UnifrakturMaguntia";
text_     = "FTZ Fritz";
groesse   = 30;     // Schrifthöhe (mm)
tiefe     = 12;     // Buchstabentiefe (Y)
s_breite  = 200;    // Sockel X
s_tiefe   = 36;     // Sockel Y
s_hoehe   = 8;      // Sockel Z (schwarz)
rand_b    = 3;      // weißer Rand oben am Sockel
rand_h    = 1.2;
radius    = 5;
unterlaenge = 8;    // Schrift so weit angehoben, dass Unterlängen (z, F) sichtbar bleiben
leiste_t  = 4;      // Tiefe der weißen Standleiste hinter den Buchstaben

module rund(b,h,r){ translate([r,r]) offset(r) square([b-2*r,h-2*r]); }
module schrift2d(){
  translate([s_breite/2,0]) text(text_, size=groesse, font=schrift, halign="center", valign="baseline");
  // Steg zum i-Punkt, damit er im aufrechten Druck nicht frei schwebt
  translate([161.5,20]) square([3,5]);
}
// Buchstaben aufgestellt: Text in X/Z, Tiefe in Y (mittig auf dem Sockel)
module buchstaben3d(){
  translate([0, s_tiefe/2 + tiefe/2, s_hoehe + unterlaenge])
    rotate([90,0,0]) linear_extrude(tiefe) schrift2d();
}
// Weiße Standleiste hinten: alle Buchstaben stehen darauf / lehnen daran
module leiste(){ translate([14, s_tiefe/2 + tiefe/2 - leiste_t, s_hoehe]) cube([173, leiste_t, unterlaenge + 1.5]); }
module buchstaben_fertig(){ difference(){ buchstaben3d(); leiste(); } }
module sockel(){ linear_extrude(s_hoehe) rund(s_breite,s_tiefe,radius); }
module rand(){ translate([0,0,s_hoehe]) linear_extrude(rand_h) difference(){
  rund(s_breite,s_tiefe,radius);
  translate([rand_b,rand_b]) rund(s_breite-2*rand_b,s_tiefe-2*rand_b,radius-rand_b/2); } }

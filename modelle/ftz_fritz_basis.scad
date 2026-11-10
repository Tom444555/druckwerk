// Schild „FTZ Fritz“ in Fraktur (UnifrakturMaguntia, OFL) – gemeinsame Maße
use <../schriften/UnifrakturMaguntia-Book.ttf>
schrift   = "UnifrakturMaguntia";
text_     = "FTZ Fritz";
groesse   = 30;     // Schrifthöhe (mm)
breite    = 200;    // Platte X
hoehe     = 70;     // Platte Y
platte_d  = 4;      // Dicke Grundplatte (schwarz)
rand_b    = 4;      // Breite Rahmen (weiß)
rand_h    = 2;      // Rahmen-Überstand
schrift_h = 2.4;    // Schrift-Überstand (rot)
radius    = 6;      // Eckenradius

module rund(b,h,r){ translate([r,r]) offset(r) square([b-2*r,h-2*r]); }
module schrift2d(){
  translate([breite/2,hoehe/2]) text(text_, size=groesse, font=schrift, halign="center", valign="center");
}

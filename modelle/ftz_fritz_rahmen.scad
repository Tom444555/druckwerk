// Farbe 3: weißer Rahmen auf der Platte
include <ftz_fritz_basis.scad>
translate([0,0,platte_d]) linear_extrude(rand_h) difference(){
  rund(breite,hoehe,radius);
  translate([rand_b,rand_b]) rund(breite-2*rand_b,hoehe-2*rand_b,radius-rand_b/2);
}

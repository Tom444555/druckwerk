// Farbe 2: rote Frakturschrift auf der Platte
include <ftz_fritz_basis.scad>
translate([0,0,platte_d]) linear_extrude(schrift_h) schrift2d();

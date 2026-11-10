// 20-mm-Testwürfel mit eingelassenem "T"
difference(){ cube(20); translate([6,6,18]) linear_extrude(3) union(){translate([0,5])square([8,2]);translate([3,0])square([2,7]);} }

// Gridfinity-Kiste 4 × 2 × 5 (168 × 84 × 35 mm) für die Kleinteile vom Drehteller (20.11.2026).
// Fächer (vorn = y 0):  hinten: Walzen | Stifte | Spitzen + Säulen (2 breit)
//                       vorn:   Klemmen + V-Auflage (2 breit) | Visier + Maßwürfel (2 breit)
// Bibliothek: gridfinity-rebuilt-openscad (kennetek, MIT, siehe LICENSE).
include <src/core/standard.scad>
use <src/core/gridfinity-rebuilt-utility.scad>
use <src/core/gridfinity-rebuilt-holes.scad>
use <src/core/bin.scad>
use <src/core/cutouts.scad>
use <src/helpers/generic-helpers.scad>
use <src/helpers/grid.scad>
use <src/helpers/grid_element.scad>

$fa = 4; $fs = 0.25;

kiste = new_bin(
    grid_size = [4, 2],
    height_mm = fromGridfinityUnits(5),
    include_lip = true,
    hole_options = bundle_hole_options(refined_hole=false, magnet_hole=false, screw_hole=false,
                                       crush_ribs=false, chamfer=true, supportless=true)
);

// OpenSCAD 2021 kennt die $-Variablen von cgs() nicht -> Fachgröße selbst rechnen
innen = bin_get_infill_size_mm(kiste);
zelle = [innen.x / 4, innen.y / 2];
function fg(b, t) = [b * zelle.x - d_div / 2, t * zelle.y - d_div / 2, innen.z];

bin_render(kiste) {
    bin_translate(kiste, [0, 1]) compartment_cutter(fg(1, 1), scoop_percent=1, tab_width=TAB_WIDTH_NOMINAL, center_top=false);  // Walzen (48 Stück)
    bin_translate(kiste, [1, 1]) compartment_cutter(fg(1, 1), scoop_percent=1, tab_width=TAB_WIDTH_NOMINAL, center_top=false);  // Steckstifte (8 Stück)
    bin_translate(kiste, [2, 1]) compartment_cutter(fg(2, 1), scoop_percent=1, tab_width=TAB_WIDTH_NOMINAL, center_top=false);  // Spitzen + Säulen
    bin_translate(kiste, [0, 0]) compartment_cutter(fg(2, 1), scoop_percent=1, tab_width=TAB_WIDTH_NOMINAL, center_top=false);  // Klemmen + V-Auflage
    bin_translate(kiste, [2, 0]) compartment_cutter(fg(2, 1), scoop_percent=1, tab_width=TAB_WIDTH_NOMINAL, center_top=false);  // Visier + Maßwürfel
}

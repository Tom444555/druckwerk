// Beispiel: alle Bausteine aus baukasten.scad nebeneinander (als Probestücke druckbar).
// Liegt flach, keine Stützen nötig. Gesamt ca. 230 × 95 mm.
use <baukasten.scad>

// Reihe 1: Schraublöcher in 16-mm-Klötzen (Oberfläche bei z=10)
module klotz(x) translate([x,0,0]) difference() { translate([-9,-9,0]) cube([18,18,10]); translate([0,0,10]) children(); }
klotz(0)   loch_durchgang(m=3, tiefe=10);
klotz(22)  loch_durchgang(m=8, tiefe=10);
klotz(44)  loch_senkkopf(m=4, tiefe=10);
klotz(66)  loch_zylinderkopf(m=4, tiefe=10);
klotz(88)  loch_einschmelz(m=3);
klotz(110) loch_einschmelz(m=5);
klotz(132) mutterntasche(m=4, tasche_tief=3, seitlich=10);
translate([154,0,0]) difference() { translate([-9,-9,0]) cube([30,18,10]); translate([0,0,10]) langloch(d=4.5, laenge=12, tiefe=10); }

// Reihe 2: Gewinde, Mutter, Quader
translate([0,32,0])   gewinde_bolzen(m=8, laenge=20);
translate([20,32,0])  gewinde_mutter(m=8);
translate([44,32,0])  gewinde_bolzen(m=12, laenge=20);
translate([68,32,0])  gewinde_mutter(m=12);
translate([88,24,0])  rund_quader([24,16,8], r=3);
translate([118,24,0]) rund_quader([24,16,8], r=3, kanten="alle");
translate([148,24,0]) fase_quader([24,16,8], f=1.5);
translate([178,24,0]) difference() { cube([36,16,8]); translate([10,8,0]) schluesselloch(laenge=12); }   // Rückseite unten

// Reihe 3: Verbinder und Halter
translate([0,58,0]) { translate([-5,-4,0]) cube([5,10,6]); schnapphaken(); }        // Haken am Fuß
translate([28,58,0]) difference() {                                                // Gegenstück: Wand mit Rastfenster
  translate([-2,2.0,0]) cube([20,3,6]); schnapphaken_ausschnitt(durch=10);
}
translate([60,52,0]) { translate([-10,0,0]) cube([20,20,3]); translate([0,0,3]) schwalbe_stecker(breite=8, hoehe=4, laenge=20); }
translate([82,52,0]) difference() { translate([-10,0,0]) cube([20,20,7]); schwalbe_nut(breite=8, hoehe=4, laenge=20); }
translate([100,62,0]) wandlasche(breite=20, laenge=18, dicke=4, m=4, anzahl=2);
translate([140,52,0]) kabelclip(d=6);
translate([180,52,0]) kabelclip(d=10, breite=10);

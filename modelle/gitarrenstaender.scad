// Hänge-Ständer für die 20-cm-Gitarre (modelle/strat_*.stl): Gabel hält die Kopfplatte, Korpus hängt frei.
// Koordinaten „stehend“: X Breite, Y nach vorn, Z hoch. Gedruckt wird liegend auf dem Rücken (siehe unten).
$fn = 48;
liegend     = true;   // true = Druckausrichtung, false = stehend (Vorschau)
// --- Gitarre ---
hals_b      = 10.4;   // Halsbreite am Sattel
sattel_h    = 160;    // Abstand Korpus-Unterkante -> Auflagepunkt der Kopfplatte
kopf_d      = 4.1;    // Dicke der Kopfplatte
// --- Ständer ---
luft_unten  = 10;     // Abstand Gitarre -> Fußplatte
fuss        = [70, 60, 4];
pfosten     = [14, 5];           // Breite, Dicke
spalt       = hals_b + 0.8;      // Gabelöffnung
zinke_b     = 5;                 // Breite je Gabelzinke
abstand     = 5;                 // Klotz vor dem Pfosten (damit der Korpus frei hängt)
zg = fuss[2] + luft_unten + sattel_h;   // Oberkante Gabel
bg = spalt + 2*zinke_b;                 // Gesamtbreite Gabel

module rund(b, t, h, r){ hull() for(x=[-b/2+r, b/2-r], y=[r, t-r]) translate([x, y, 0]) cylinder(r=r, h=h); }
module staender(){
  rund(fuss[0], fuss[1], fuss[2], 6);                                         // Fußplatte
  translate([-pfosten[0]/2, 0, 0]) cube([pfosten[0], pfosten[1], zg]);        // Pfosten
  hull(){ translate([-2.5, pfosten[1]-0.1, fuss[2]-0.1]) cube([5, 26, 0.1]);  // Stützrippe unten
          translate([-2.5, pfosten[1]-0.1, fuss[2]]) cube([5, 0.1, 9]); }
  hull(){ translate([-bg/2, 0, zg-14]) cube([bg, pfosten[1]+abstand, 14]);    // Gabelklotz mit Schräge nach unten
          translate([-pfosten[0]/2, 0, zg-30]) cube([pfosten[0], pfosten[1], 1]); }
  for(s=[-1,1]) translate([s*(spalt/2 + zinke_b/2), 0, 0]) {                  // Zinken + Nase gegen Herausrutschen
    hull(){ translate([-zinke_b/2, pfosten[1]+abstand-0.1, zg-6]) cube([zinke_b, 0.1, 6]);
            translate([0, pfosten[1]+abstand+kopf_d+3.2, zg-1.6]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true);
            translate([0, pfosten[1]+abstand+kopf_d+3.2, zg-4.4]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true); }
    hull(){ translate([0, pfosten[1]+abstand+kopf_d+3.2, zg-1.6]) rotate([0,90,0]) cylinder(r=1.6, h=zinke_b, center=true);
            translate([0, pfosten[1]+abstand+kopf_d+3.6, zg+2.2]) rotate([0,90,0]) cylinder(r=1.2, h=zinke_b, center=true); }
  }
  translate([-pfosten[0]/2, pfosten[1]-0.1, 48]) hull(){ cube([pfosten[0], 0.1, 16]); translate([0, 1.1, 2]) cube([pfosten[0], 0.1, 12]); }  // Anlage für den Korpus
}
if (liegend) rotate([90, 0, 0]) staender(); else staender();

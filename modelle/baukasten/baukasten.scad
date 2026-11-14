// =====================================================================
// druckwerk – Technik-Baukasten für den Creator 5 Pro (0,4-mm-Düse)
// Einbinden:  use <baukasten/baukasten.scad>      (aus modelle/)
// Einheiten mm. Alle Module haben Parameter mit Vorgabewerten.
//
// Regeln:
//  * „Loch“-Module (loch_*, *_ausschnitt, *_nut, *_tasche) sind Körper zum
//    ABZIEHEN: difference(){ teil(); translate(...) loch_...(); }
//    Bezug: Bauteil-Oberfläche liegt bei z = 0, das Loch geht nach unten (−z).
//    Ausnahme schluesselloch(): Rückseite (Wandseite, liegt auf dem Bett) bei z = 0.
//  * Das Spiel ist global 0,2 mm. Mit `use` gilt immer 0,2 – pro Aufruf
//    überschreiben: loch_durchgang(m=4, spiel=0.3). Mit `include` kann man
//    `spiel = 0.3;` in der eigenen Datei setzen.
//  * Runde Löcher werden als umschriebenes Vieleck erzeugt (Vieleck liegt
//    außen am Kreis), damit sie nicht zu klein drucken.
// =====================================================================

spiel = 0.2;      // globales Spiel (Durchmesser-/Breitenzugabe je Seite siehe Modul)
fn_loch = 48;     // Ecken je Loch

// ---------- Normtabellen [M, Wert] ----------
// Durchgangsloch ISO 273 „mittel“
function _durch(m) = lookup(m, [[3,3.4],[4,4.5],[5,5.5],[6,6.6],[8,9.0]]);
// Senkkopf ISO 10642 / DIN 7991: Kopfdurchmesser (90°)
function _senk_dk(m) = lookup(m, [[3,6.72],[4,8.96],[5,11.2],[6,13.44],[8,17.92]]);
// Zylinderkopf ISO 4762 / DIN 912: Kopf-Ø und Kopfhöhe (= M)
function _zyl_dk(m) = lookup(m, [[3,5.5],[4,7.0],[5,8.5],[6,10.0],[8,13.0]]);
// Mutter ISO 4032: Schlüsselweite und Höhe
function _mut_s(m) = lookup(m, [[3,5.5],[4,7.0],[5,8.0],[6,10.0],[8,13.0],[10,16.0],[12,18.0]]);
function _mut_h(m) = lookup(m, [[3,2.4],[4,3.2],[5,4.7],[6,5.2],[8,6.8],[10,8.4],[12,10.8]]);
// Einschmelzmuttern (übliche Kurzform, z. B. Ruthex): Loch-Ø, Länge
function _ein_d(m) = lookup(m, [[3,4.0],[4,5.6],[5,6.4]]);
function _ein_l(m) = lookup(m, [[3,5.7],[4,8.1],[5,9.5]]);
// Regelgewinde Steigung
function _steigung(m) = lookup(m, [[6,1.0],[8,1.25],[10,1.5],[12,1.75]]);

// Zylinder mit umschriebenem Vieleck (für Löcher)
module _zyl(d, h, fn=fn_loch) { cylinder(r=d/2/cos(180/fn), h=h, $fn=fn); }

// =====================================================================
// 1) Durchgangsloch M3–M8
// =====================================================================
module loch_durchgang(m=3, tiefe=10, spiel=spiel) {
  translate([0,0,-tiefe-0.01]) _zyl(_durch(m)+spiel, tiefe+0.02);
}

// =====================================================================
// 2) Senkkopf-Senkung (90°) inkl. Durchgangsloch
//    versenkt = wie weit der Kopf unter der Oberfläche liegt (0 = bündig)
// =====================================================================
module loch_senkkopf(m=3, tiefe=10, versenkt=0.2, spiel=spiel) {
  dk = _senk_dk(m) + 2*spiel;
  loch_durchgang(m, tiefe, spiel);
  translate([0,0,-versenkt-dk/2]) cylinder(r1=0, r2=dk/2/cos(180/fn_loch), h=dk/2+0.001, $fn=fn_loch);
  if (versenkt > 0) translate([0,0,-versenkt]) _zyl(dk, versenkt+0.01);
  else translate([0,0,-0.001]) _zyl(dk, 0.011);
}

// =====================================================================
// 3) Zylinderkopf-Senkung (DIN 912) inkl. Durchgangsloch
// =====================================================================
module loch_zylinderkopf(m=3, tiefe=10, kopf_tiefe=undef, spiel=spiel) {
  kt = is_undef(kopf_tiefe) ? m + 0.4 : kopf_tiefe;
  loch_durchgang(m, tiefe, spiel);
  translate([0,0,-kt]) _zyl(_zyl_dk(m) + 0.8 + spiel, kt+0.01);
}

// =====================================================================
// 4) Loch für Einschmelzmutter M3/M4/M5 mit Einführfase
//    Kein Spiel (Presssitz). tiefe_extra = Luft unter der Mutter.
// =====================================================================
module loch_einschmelz(m=3, tiefe_extra=1.0, fase=0.6) {
  d = _ein_d(m); l = _ein_l(m) + tiefe_extra;
  translate([0,0,-l]) _zyl(d, l+0.01);
  translate([0,0,-fase]) cylinder(r1=d/2/cos(180/fn_loch), r2=(d/2+fase+0.01)/cos(180/fn_loch), h=fase+0.01, $fn=fn_loch);
}

// =====================================================================
// 5) Sechskant-Mutterntasche (ISO 4032), optional seitlich einschiebbar
//    tasche_tief = Oberkante der Tasche unter z=0 (0 = offen von oben)
//    seitlich    = Länge des Einschubkanals in +X (0 = keiner)
//    loch        = Schraubenschaft durch die Tasche (Länge tiefe)
// =====================================================================
module mutterntasche(m=3, tasche_tief=0, seitlich=0, loch=true, tiefe=10, spiel=spiel) {
  s = _mut_s(m) + 2*spiel; h = _mut_h(m) + spiel; r = s/sqrt(3);
  translate([0,0,-tasche_tief-h]) {
    cylinder(r=r, h=h+(tasche_tief==0?0.01:0), $fn=6);
    if (seitlich > 0) translate([0,-s/2,0]) cube([seitlich+0.01, s, h]);
  }
  if (loch) loch_durchgang(m, tiefe, spiel);
}

// =====================================================================
// 6) Langloch (z. B. zum Nachjustieren): d = Breite, laenge = Mittenabstand in X
// =====================================================================
module langloch(d=4.5, laenge=10, tiefe=10, spiel=spiel) {
  r = (d+spiel)/2/cos(180/fn_loch);
  translate([0,0,-tiefe-0.01]) linear_extrude(tiefe+0.02)
    hull() { circle(r=r, $fn=fn_loch); translate([laenge,0]) circle(r=r, $fn=fn_loch); }
}

// =====================================================================
// 7) Schnapphaken – flach druckbar (Federweg in Y, Schichten längs)
//    Balken von x=0 bis laenge, Dicke in Y, Höhe in Z; Nase an der Spitze in +Y.
//    Der Fuß (x<0) gehört zum eigenen Teil – Haken dort anbauen.
//    Faustregel: Dehnung = 1,5·dicke·nase/laenge² < 0,03 (PLA/PETG).
// =====================================================================
module schnapphaken(laenge=15, dicke=1.8, hoehe=6, nase=1.0, nase_l=3, kehle=1.2) {
  L = laenge; d = dicke; n = nase;
  linear_extrude(hoehe) {
    translate([-0.01,0]) square([L+0.01, d]);
    // Nase: senkrechte Rastfläche zum Fuß hin, Rampe zur Spitze
    polygon([[L-nase_l, d-0.01], [L-nase_l, d+n], [L-nase_l+0.6, d+n], [L, d+0.25], [L, d-0.01]]);
    // Kehle am Fuß gegen Bruch (beidseitig)
    polygon([[-0.01, d-0.01], [kehle, d-0.01], [-0.01, d+kehle]]);
    polygon([[-0.01, 0.01], [kehle, 0.01], [-0.01, -kehle]]);
  }
}
// Gegenstück: Rastfenster in einer Wand, deren Innenfläche bei y = dicke + spiel liegt.
// In GLEICHER Lage wie der Haken abziehen. durch = wie weit das Fenster nach +Y reicht.
module schnapphaken_ausschnitt(laenge=15, dicke=1.8, hoehe=6, nase=1.0, nase_l=3, durch=10, spiel=spiel) {
  translate([laenge-nase_l-spiel, dicke, -spiel]) cube([nase_l+2*spiel, nase+durch, hoehe+2*spiel]);
}

// =====================================================================
// 8) Schwalbenschwanz (Profil in XZ, Länge in +Y)
//    breite = Breite am Fuß (z=0), hoehe, winkel = Flankenneigung ab senkrecht
// =====================================================================
function _schwalbe(b, h, w, o=0) =
  [[-b/2-o, -0.01], [b/2+o, -0.01], [b/2+h*tan(w)+o, h+o], [-b/2-h*tan(w)-o, h+o]];
module schwalbe_stecker(breite=8, hoehe=4, laenge=20, winkel=15) {
  rotate([90,0,0]) translate([0,0,-laenge]) linear_extrude(laenge) polygon(_schwalbe(breite, hoehe, winkel));
}
// Nut: Spiel rundum; Öffnung bei z=0, reicht in +Z. Teil mit Nut wird gewendet oder die
// Nut liegt an der Unterseite (Flanken neigen nur 15° – druckt ohne Stützen).
module schwalbe_nut(breite=8, hoehe=4, laenge=20, winkel=15, spiel=spiel) {
  rotate([90,0,0]) translate([0,0,-laenge-0.01]) linear_extrude(laenge+0.02) polygon(_schwalbe(breite, hoehe, winkel, spiel));
}

// =====================================================================
// 9) Druckbares Regelgewinde M6–M12 (ISO-Profil 60°, rechtsgängig)
//    Der Radius wird punktweise aus dem Profil berechnet → ein dichter Körper.
//    Bolzen −spiel/2, Mutter +spiel/2 im Radius.  Schicht 0,12–0,16 empfohlen.
// =====================================================================
function _profil(u) =        // 0 = Spitze (Außen-Ø), 1 = Grund (Kern-Ø)
  u < 1/8 ? 0 : u < 7/16 ? (u-1/8)/(5/16) : u < 11/16 ? 1 : 1-(u-11/16)/(5/16);
function _frac(x) = x - floor(x);
function _gew_r(m, z, a, off) = let(P=_steigung(m), t=0.5413*P)
  m/2 + off - t*_profil(_frac(z/P - a/360));
function _gew_punkte(m, L, off, fn, nz, fase) = [
  for (k=[0:nz]) let(z = L*k/nz) for (j=[0:fn-1]) let(a = 360*j/fn,
     r0 = _gew_r(m, z, a, off), rk = m/2 + off - 0.5413*_steigung(m),
     r  = fase ? min(r0, rk + 0.2 + z, rk + 0.2 + (L-z)) : r0)
  [r*cos(a), r*sin(a), z]];
function _gew_flaechen(fn, nz) = concat(
  [[for (j=[0:fn-1]) j]],                                             // Boden
  [for (k=[0:nz-1]) for (j=[0:fn-1]) let(a=k*fn+j, b=k*fn+(j+1)%fn, c=a+fn, d=b+fn) each [[a,d,b],[a,c,d]]],
  [[for (j=[fn-1:-1:0]) nz*fn+j]]);                                    // Deckel
module _gewinde(m, L, off, fase, fn=64) {
  P = _steigung(m); nz = ceil(L/(P/12));
  polyhedron(_gew_punkte(m, L, off, fn, nz, fase), _gew_flaechen(fn, nz), convexity=6);
}
// Gewindebolzen (Gewinde von z=0 bis laenge, Enden angefast)
module gewinde_bolzen(m=8, laenge=20, spiel=spiel) { _gewinde(m, laenge, -spiel/2, true); }
// Mutter-Ausschnitt: Oberfläche bei z=0, nach unten tiefe; mit Senkfase oben und unten
module gewinde_ausschnitt(m=8, tiefe=10, spiel=spiel) {
  P = _steigung(m); rk = m/2 + spiel/2 - 0.5413*P;
  translate([0,0,-tiefe-0.5]) _gewinde(m, tiefe+1, spiel/2, false);
  translate([0,0,-P*0.6]) cylinder(r1=rk, r2=m/2+spiel/2+0.3, h=P*0.6+0.01, $fn=64);
  translate([0,0,-tiefe-0.01]) cylinder(r1=m/2+spiel/2+0.3, r2=rk, h=P*0.6, $fn=64);
}
// Fertige Sechskantmutter zum Drucken (Schlüsselweite ISO 4032)
module gewinde_mutter(m=8, spiel=spiel) {
  s = _mut_s(m); h = max(_mut_h(m), m*0.8);
  difference() { cylinder(r=s/sqrt(3), h=h, $fn=6); translate([0,0,h]) gewinde_ausschnitt(m, h, spiel); }
}

// =====================================================================
// 10) Quader mit Kantenrundung bzw. Fase (Ecke bei 0,0,0 wie cube())
//     kanten = "senkrecht" (nur stehende Kanten – druckt ohne Überhang)
//              "alle"      (alle Kanten, Unterkante wird zur Rundung → leichter Überhang)
// =====================================================================
module rund_quader(g=[30,20,10], r=2, kanten="senkrecht", fn=32) {
  if (kanten == "senkrecht")
    linear_extrude(g[2]) offset(r=r, $fn=fn) offset(delta=-r) square([g[0], g[1]]);
  else
    hull() for (x=[r, g[0]-r], y=[r, g[1]-r], z=[r, g[2]-r]) translate([x,y,z]) sphere(r=r, $fn=fn);
}
module fase_quader(g=[30,20,10], f=1) {
  hull() {
    translate([f,f,0]) cube([g[0]-2*f, g[1]-2*f, g[2]]);
    translate([f,0,f]) cube([g[0]-2*f, g[1], g[2]-2*f]);
    translate([0,f,f]) cube([g[0], g[1]-2*f, g[2]-2*f]);
  }
}

// =====================================================================
// 11) Wandhalter-Lasche: Platte in XY, Anbaukante bei x=0, Senklöcher
// =====================================================================
module wandlasche(breite=20, laenge=18, dicke=4, m=4, anzahl=1, senk=true, spiel=spiel) {
  difference() {
    linear_extrude(dicke) hull() {
      translate([-0.01,-breite/2]) square([0.01, breite]);
      for (y=[-breite/2+breite/4, breite/2-breite/4]) translate([laenge-breite/4, y]) circle(r=breite/4, $fn=48);
    }
    for (i=[0:anzahl-1]) let(y = anzahl==1 ? 0 : -breite/4 + i*(breite/2)/(anzahl-1))
      translate([laenge-breite/4-0.5, y, dicke])
        if (senk) loch_senkkopf(m, dicke, 0.2, spiel); else loch_durchgang(m, dicke, spiel);
  }
}

// =====================================================================
// 12) Schlüsselloch-Aufhängung (zum Abziehen). Rückseite bei z=0 liegt auf dem Bett.
//     Schraube steckt in der Wand; Kopf durch das große Loch, dann nach +X schieben.
//     steg = Materialstärke hinter dem Kopf (hält das Teil); Dach der Kopftasche wird gebrückt.
// =====================================================================
module schluesselloch(kopf_d=8, schaft_d=4, kopf_h=3, laenge=10, steg=2, spiel=spiel) {
  K = kopf_d + 2*spiel; S = schaft_d + 2*spiel;
  translate([0,0,-0.01]) {
    _zyl(K, steg + kopf_h + spiel + 0.01);                                         // Einführloch
    linear_extrude(steg + 0.02) hull() { circle(d=S, $fn=32); translate([laenge,0]) circle(d=S, $fn=32); }
    translate([0,0,steg]) linear_extrude(kopf_h + spiel + 0.01)
      hull() { circle(d=K, $fn=48); translate([laenge,0]) circle(d=K, $fn=48); }
  }
}

// =====================================================================
// 13) Kabel-Clip mit Schraublasche (liegend drucken: Profil in XY, Breite in Z)
//     d = Kabel-Ø, oeffnung = Spaltbreite als Anteil von d
// =====================================================================
module kabelclip(d=6, breite=8, wand=1.6, oeffnung=0.75, lasche=7, lasche_d=2.4, m=3, spiel=spiel) {
  ri = d/2; ra = ri + wand; yc = ra + lasche_d - wand;     // Kabelmitte
  difference() {
    linear_extrude(breite) {
      translate([0, yc]) difference() {
        circle(r=ra, $fn=64); circle(r=ri, $fn=64);
        translate([-d*oeffnung/2, 0]) square([d*oeffnung, ra+1]);
      }
      // Lippen rund an der Öffnung
      for (s=[-1,1]) translate([s*(d*oeffnung/2 + wand/2), yc + sqrt(pow(ri+wand/2,2) - pow(d*oeffnung/2+wand/2,2))]) circle(r=wand/2, $fn=24);
      translate([-ra-lasche, 0]) square([2*(ra+lasche), lasche_d]);
    }
    for (s=[-1,1]) translate([s*(ra+lasche/2), lasche_d, breite/2]) rotate([-90,0,0]) loch_durchgang(m, lasche_d, spiel);
  }
}

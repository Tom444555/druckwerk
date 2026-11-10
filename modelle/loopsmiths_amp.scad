// „Loopsmiths“ – eigener Mini-Verstärker als Plektrumhalter (12 Fächer), Eigenentwurf
// Jedes Bauteil einzeln exportierbar:  openscad -D 'teil="korpus"' -o korpus.stl loopsmiths_amp.scad
// Farben werden danach in werkzeug/loopsmiths_farben.py zusammengesetzt (Überschneidungen werden abgezogen).
use <../schriften/Pacifico-Regular.ttf>
use <../schriften/Oswald.ttf>

teil = "vorschau";
$fn = 48;

// ---------- Maße (mm) ----------
B = 110;  T = 55;  H = 62;      // Korpus Breite (X), Tiefe (Y), Höhe (Z)
R = 5;                          // Kantenradius
fuss = 0;                       // Korpus steht direkt auf der Druckplatte (Füße nur als Ring-Andeutung)
z0 = fuss;                      // Unterkante Korpus
zt = z0 + H;                    // Oberkante Korpus
// Front (Y = 0 ist die Vorderseite)
gr_x = 47;  gr_z1 = z0 + 6;  gr_z2 = z0 + 38;   // Lautsprecher-Fenster
gr_tief = 4;                                     // Tasche für Stoff + Gitter
bd_z1 = z0 + 41.5;  bd_z2 = z0 + 55;             // Logo-Band
// Bedienfeld oben
pf_y1 = 3;  pf_y2 = 21;  pf_x = 48;  pf_d = 1.6;
kn_y = 10;
knoepfe = [[-31,"GAIN"],[-19,"BASS"],[-7,"MID"],[5,"TREBLE"],[17,"FX"],[29,"MASTER"]];
// Plektrum-Fächer
f_anz = 12;  f_teil = 7.6;  f_b = 2.4;  f_y1 = 25;  f_y2 = 52;  f_tief = 21;

// ---------- Hilfsmodule ----------
module rundbox(b,t,h,r){ hull() for(x=[-b/2+r,b/2-r], y=[r,t-r], z=[r,h-r]) translate([x,y,z]) sphere(r); }
module rundplatte(b,t,d,r){ hull() for(x=[-b/2+r,b/2-r], y=[-t/2+r,t/2-r]) translate([x,y,0]) cylinder(r=r,h=d); }
// Kreuzschlitz-Linsenkopfschraube, Achse +Z
module schraube(d=2.6){
  difference(){ scale([1,1,0.45]) sphere(d/2, $fn=24);
    for(a=[0,90]) rotate([0,0,a]) translate([0,0,d*0.18]) cube([d*0.8,d*0.16,d], center=true);
    translate([0,0,-d]) cube(2*d, center=true); }
}

// ---------- Korpus (schwarz) ----------
module korpus(){
  difference(){
    translate([0,0,z0]) rundbox(B,T,H,R);
    // Lautsprecher-Tasche
    translate([-gr_x,-1,gr_z1]) cube([2*gr_x, gr_tief+1, gr_z2-gr_z1]);
    // Plektrum-Fächer mit Einführtrichter
    for(i=[0:f_anz-1]) let(x = -(f_anz-1)*f_teil/2 + i*f_teil) {
      hull(){ translate([x-f_b/2, f_y1, zt-f_tief]) cube([f_b, f_y2-f_y1, 1]);
              translate([x-f_b/2, f_y1, zt-3]) cube([f_b, f_y2-f_y1, 0.1]); }
      hull(){ translate([x-f_b/2, f_y1, zt-3]) cube([f_b, f_y2-f_y1, 0.1]);
              translate([x-f_b/2-0.9, f_y1-0.9, zt+0.01]) cube([f_b+1.8, f_y2-f_y1+1.8, 0.1]); }
    }
    // Rückseite: Lüftungsschlitze
    for(i=[0:7]) translate([-30, T-1.6, z0+12+i*4]) rundschlitz(60, 1.8);
    // Rückseite: Kabeldurchführung
    translate([38, T-3, z0+10]) rotate([-90,0,0]) cylinder(d=4.2, h=5);
  }
  // Seitengriffe (Riemen) – schwarz
  for(s=[-1,1]) seitengriff_riemen(s);
}
module rundschlitz(l, h){ hull(){ translate([h/2,0,0]) rotate([-90,0,0]) cylinder(d=h, h=3, $fn=16);
                                  translate([l-h/2,0,0]) rotate([-90,0,0]) cylinder(d=h, h=3, $fn=16); } }

// ---------- Lautsprecher: Stoff (rot) + Lochgitter (schwarz) + Keder (weiß) ----------
module stoff(){   // Bespannung hinten in der Tasche, mit feiner Webstruktur
  translate([-gr_x, 3, gr_z1]) cube([2*gr_x, 1.01, gr_z2-gr_z1]);
  for(z=[gr_z1+0.6:0.9:gr_z2-0.5]) translate([-gr_x, 2.75, z]) cube([2*gr_x, 0.3, 0.35]);
}
gl_r = 1.3;  gl_p = 3.15;   // Sechskant-Löcher: Umkreisradius, Raster
module gitter(){
  difference(){
    translate([-gr_x, 0.9, gr_z1]) cube([2*gr_x, 1.9, gr_z2-gr_z1]);
    for(row=[0:floor((gr_z2-gr_z1-2)/(gl_p*0.866))], col=[0:floor((2*gr_x-2)/gl_p)])
      let(x = -gr_x + 2 + col*gl_p + (row%2)*gl_p/2, z = gr_z1 + 2 + row*gl_p*0.866)
        if (x < gr_x-1.8 && z < gr_z2-1.6)
          translate([x, 0, z]) rotate([-90,0,0]) rotate([0,0,30]) cylinder(r=gl_r, h=5, $fn=6);
  }
}
module keder_rahmen(x1,z1,x2,z2,y,d=1.3,r=2.5){   // runder Keder um ein Rechteck (in XZ-Ebene)
  for(p=[[x1+r,z1,x2-r,z1],[x1+r,z2,x2-r,z2]]) hull(){ translate([p[0],y,p[1]]) sphere(d/2,$fn=16); translate([p[2],y,p[3]]) sphere(d/2,$fn=16); }
  for(p=[[x1,z1+r,x1,z2-r],[x2,z1+r,x2,z2-r]]) hull(){ translate([p[0],y,p[1]]) sphere(d/2,$fn=16); translate([p[2],y,p[3]]) sphere(d/2,$fn=16); }
  for(c=[[x1+r,z1+r,180],[x2-r,z1+r,270],[x2-r,z2-r,0],[x1+r,z2-r,90]])
    translate([c[0],y,c[1]]) rotate([90,0,0]) rotate([0,0,c[2]]) rotate_extrude(angle=90,$fn=24) translate([r,0]) circle(d/2,$fn=16);
}
module keder(){ keder_rahmen(-gr_x-0.6, gr_z1-0.6, gr_x+0.6, gr_z2+0.6, 0.15); }

// ---------- Logo-Band (rot) + Schriftzug (weiß) ----------
module band(){
  difference(){
    translate([0, 1.2, (bd_z1+bd_z2)/2]) rotate([90,0,0]) rundplatte(2*gr_x, bd_z2-bd_z1, 1.6, 2);
  }
  // feine Zierlinien oben/unten (rot, erhaben)
}
module logo(){
  translate([0, -0.35, (bd_z1+bd_z2)/2 - 2.6]) rotate([90,0,0]) linear_extrude(1.1)
    text("Loopsmiths", size=8.2, font="Pacifico", halign="center", valign="baseline");
  // Unterstrich-Schwung
  translate([0,-0.35,bd_z1+2.1]) rotate([90,0,0]) linear_extrude(0.8)
    hull(){ translate([-26,0]) circle(0.35,$fn=12); translate([26,0.25]) circle(0.6,$fn=12); }
}

// ---------- Ecken-Schoner (weiß) mit Schrauben ----------
module ecken(){
  for(sx=[-1,1], sy=[0,1], sz=[0,1]) let(cx = sx*(B/2-R), cy = sy ? T-R : R, cz = sz ? zt-R : z0+R)
    difference(){
      intersection(){ translate([cx,cy,cz]) sphere(R+0.8, $fn=40);
        translate([sx>0 ? cx-1.2 : cx-20+1.2, sy ? cy-1.2 : cy-20+1.2, sz ? cz-1.2 : cz-20+1.2]) cube(20); }
      translate([0,0,z0]) rundbox(B,T,H,R);
    }
}
module ecken_schrauben(){
  for(sx=[-1,1], sz=[0,1]) let(cx = sx*(B/2-R), cz = sz ? zt-R : z0+R)
    translate([cx + sx*1.9, -0.25, cz + (sz?1.9:-1.9)]) rotate([90,0,0]) schraube(1.8);
}

// ---------- Bedienfeld (weiß) mit Beschriftung/Skalen (schwarz) ----------
module panel(){ translate([0,(pf_y1+pf_y2)/2,zt-pf_d+0.3]) rundplatte(2*pf_x, pf_y2-pf_y1, pf_d, 1.5); }
module panel_druck(){   // schwarze Einlagen, 0.6 mm tief, bündig mit der Oberfläche
  zz = zt+0.3-0.6;
  for(k=knoepfe){
    for(i=[0:10]) let(a = -135 + i*27) translate([k[0], kn_y, zz]) rotate([0,0,-a]) translate([-0.22, 4.6, 0])
      linear_extrude(0.6) square([i%5==0 ? 0.55 : 0.42, i%5==0 ? 1.3 : 0.9]);
    translate([k[0], kn_y-0.0, zz]) for(n=[0,10]) let(a=-135+n*27) rotate([0,0,-a]) translate([0,6.9,0]) rotate([0,0,a])
      linear_extrude(0.6) text(n==0?"0":"10", size=1.5, font="Oswald", halign="center", valign="center");
    translate([k[0], 18.2, zz]) linear_extrude(0.6) text(k[1], size=2.3, font="Oswald", halign="center", valign="center");
  }
  translate([-42, 18.2, zz]) linear_extrude(0.6) text("INPUT", size=2.0, font="Oswald", halign="center", valign="center");
  translate([40.5, 18.2, zz]) linear_extrude(0.6) text("ON", size=2.0, font="Oswald", halign="center", valign="center");
  translate([45.6, 18.2, zz]) linear_extrude(0.6) text("PWR", size=1.6, font="Oswald", halign="center", valign="center");
}

// ---------- Regler: Rock (schwarz, Skala), Knopf (weiß, geriffelt), Kappe (rot), Zeiger (schwarz) ----------
kn_h = 5.2;  kn_d = 6.6;
module regler_rock(){ for(k=knoepfe) translate([k[0],kn_y,zt+0.3]) { cylinder(d1=8.0, d2=7.6, h=0.9);
    for(i=[0:23]) rotate([0,0,i*15]) translate([3.75,0,0.45]) cube([0.5,0.35,0.9], center=true); } }
module regler_knopf(){ for(k=knoepfe) translate([k[0],kn_y,zt+1.2]) difference(){
    union(){ cylinder(d1=kn_d+0.3, d2=kn_d-0.5, h=kn_h);
             // Riffelung
             for(i=[0:29]) rotate([0,0,i*12]) translate([kn_d/2-0.15,0,0]) cylinder(d1=0.7, d2=0.45, h=kn_h-0.8, $fn=8); }
    // Mulde für die Kappe
    translate([0,0,kn_h-0.5]) cylinder(d=3.8, h=1);
    // Zeigernut
    translate([0, kn_d/4+0.3, kn_h-0.4]) cube([0.7, kn_d/2+0.6, 1], center=true);
  } }
module regler_kappe(){ for(k=knoepfe) translate([k[0],kn_y,zt+1.2+kn_h-0.5]) { cylinder(d=3.8, h=0.5); translate([0,0,0.5]) scale([1,1,0.25]) sphere(1.9,$fn=32); } }
module regler_zeiger(){ for(k=knoepfe) translate([k[0], kn_y + kn_d/4+0.3, zt+1.2+kn_h-0.4]) translate([0,0,0.2]) cube([0.7, kn_d/2-0.2, 0.6], center=true); }

// ---------- Buchse, Schalter, Lampe ----------
module buchse_schwarz(){ translate([-42,kn_y,zt+0.3]) difference(){ cylinder(d=6.6, h=1.0, $fn=6); translate([0,0,-1]) cylinder(d=2.7,h=5); } }
module buchse_weiss(){ translate([-42,kn_y,zt+1.3]) difference(){ cylinder(d=4.6, h=1.3); translate([0,0,-1]) cylinder(d=2.7,h=5);
    for(i=[0:11]) rotate([0,0,i*30]) translate([2.3,0,0.65]) cube([0.4,0.3,1.4],center=true); } }
module buchse_loch(){ translate([-42,kn_y,zt-2.5]) cylinder(d=2.7,h=5.2); }
module schalter_schwarz(){ translate([40.5,kn_y,zt+0.3]) cylinder(d=5.2, h=1.1, $fn=6); }
module schalter_weiss(){ translate([40.5,kn_y,zt+1.4]) { cylinder(d=3.4,h=0.9);
    translate([0,0,0.9]) rotate([18,0,0]) { cylinder(d1=1.5, d2=1.1, h=5.2, $fn=20); translate([0,0,5.2]) sphere(0.75,$fn=16); } } }
module lampe_weiss(){ translate([45.6,kn_y,zt+0.3]) difference(){ cylinder(d=4.2,h=0.9); translate([0,0,-1]) cylinder(d=2.8,h=3); } }
module lampe_rot(){ translate([45.6,kn_y,zt+0.3]) { cylinder(d=2.8,h=0.9); translate([0,0,0.9]) scale([1,1,0.8]) sphere(1.4,$fn=24); } }

// ---------- Seitengriffe: Riemen (schwarz) + Endkappen (weiß) ----------
module seitengriff_riemen(s){
  translate([s*(B/2-0.6), T/2, z0+H-17]) rotate([0,s*90,0]) {
    // Riemen mit leichtem Bogen
    hull(){ for(y=[-14,14]) translate([0,y,0]) cylinder(d=6, h=1.6); }
    translate([0,0,1.2]) hull(){ for(y=[-11,11]) translate([0,y,0]) scale([1,1,0.6]) cylinder(d=5.2, h=2.4); }
  }
}
module seitengriff_kappen(){
  for(s=[-1,1], y=[-14,14]) translate([s*(B/2-0.6), T/2+y, z0+H-17]) rotate([0,s*90,0]) {
    translate([0,0,1.1]) cube([8,7,2.6],center=true);
    for(d=[-2,2]) translate([d,0,2.4]) schraube(1.6);
  }
}

// ---------- Rückseite: Typenschild (rot) + Schrift/Schrauben (weiß) ----------
module typenschild(){ translate([0,T-0.6,z0+47]) rotate([-90,0,0]) rundplatte(56, 11, 1.4, 1.5); }
module typenschild_text(){
  translate([0,T+0.75,z0+48.8]) rotate([90,0,180]) linear_extrude(0.7)
    text("LOOPSMITHS", size=3.6, font="Oswald", halign="center", valign="center", spacing=1.25);
  translate([0,T+0.75,z0+44.2]) rotate([90,0,180]) linear_extrude(0.7)
    text("PICK AMP 12  ·  HANDMADE  ·  No. 001", size=1.9, font="Oswald", halign="center", valign="center");
  for(x=[-25,25]) translate([x, T+0.7, z0+47]) rotate([-90,0,0]) schraube(1.8);
  for(x=[-44,44], z=[z0+7, z0+56]) translate([x, T-0.1, z]) rotate([-90,0,0]) schraube(2.2);
}

// ---------- Ausgabe ----------
if (teil=="korpus") korpus();
else if (teil=="stoff") stoff();
else if (teil=="gitter") gitter();
else if (teil=="keder") keder();
else if (teil=="band") band();
else if (teil=="logo") logo();
else if (teil=="ecken") { ecken(); ecken_schrauben(); }
else if (teil=="panel") panel();
else if (teil=="panel_druck") panel_druck();
else if (teil=="rock") regler_rock();
else if (teil=="knopf") regler_knopf();
else if (teil=="kappe") regler_kappe();
else if (teil=="zeiger") regler_zeiger();
else if (teil=="buchse_s") { buchse_schwarz(); }
else if (teil=="buchse_w") buchse_weiss();
else if (teil=="buchse_loch") buchse_loch();
else if (teil=="schalter_s") schalter_schwarz();
else if (teil=="schalter_w") schalter_weiss();
else if (teil=="lampe_w") lampe_weiss();
else if (teil=="lampe_r") lampe_rot();
else if (teil=="griff_kappen") seitengriff_kappen();
else if (teil=="schild") typenschild();
else if (teil=="schild_text") typenschild_text();
else {
  color([0.12,0.12,0.12]) { korpus(); gitter(); panel_druck(); regler_rock(); regler_zeiger(); buchse_schwarz(); schalter_schwarz(); }
  color([0.8,0.1,0.1]) { stoff(); band(); regler_kappe(); lampe_rot(); typenschild(); }
  color([0.95,0.95,0.93]) { keder(); logo(); ecken(); ecken_schrauben(); panel(); regler_knopf(); buchse_weiss(); schalter_weiss(); lampe_weiss(); seitengriff_kappen(); typenschild_text(); }
}

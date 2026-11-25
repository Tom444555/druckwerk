#!/usr/bin/env python3
"""Druckwerk-Brücke: schickt Druckdateien vom Rechner direkt an den Flashforge Creator 5 Pro.

Läuft auf Toms Mac (nur Python-Standardbibliothek):   python3 bruecke.py
Öffnet http://localhost:8787 – dort Drucker einrichten (IP, Seriennummer, Check Code),
Status ansehen, eine .gcode hochladen und (eigener Knopf) starten.

Warum eine Brücke: die Druckwerk-App ist eine https-Seite und darf im Browser nicht mit
http://<Drucker> im Heimnetz reden. Dieses Programm darf es.

Schnittstelle des Druckers: HTTP auf Port 8898 (Beschreibung: Parallel-7/flashforge-api-docs).
Zugangsdaten liegen NUR auf diesem Rechner in ~/.druckwerk/drucker.json – nie im Lager.
Stand 25.11.2026: nur gegen einen nachgestellten Drucker geprüft, am echten Gerät ungetestet.
"""
import argparse, http.client, json, os, re, socket, sys, tempfile, threading, time, urllib.parse, urllib.request, uuid, webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ORDNER = Path(os.environ.get("DRUCKWERK_ORDNER", Path.home() / ".druckwerk"))
DATEI = ORDNER / "drucker.json"
# Von hier darf die Brücke Druckdateien holen (sonst könnte eine fremde Seite beliebige Dateien einschleusen).
QUELLEN_FEST = ("https://tom444555.github.io/druckwerk/", "https://raw.githubusercontent.com/Tom444555/")
PAGES = os.environ.get("DRUCKWERK_PAGES", "https://tom444555.github.io/druckwerk/")   # zum Testen umstellbar
LAGER = {"t": 0, "liste": []}
NETZ = {"an": False, "port": 8787}
LAUF = {}      # id -> {stufe, anteil, text, fertig, fehler, name}


def lade():
    try:
        return json.loads(DATEI.read_text())
    except Exception:
        return {}


def merke(d):
    ORDNER.mkdir(parents=True, exist_ok=True)
    DATEI.write_text(json.dumps(d, indent=1))
    try:
        os.chmod(DATEI, 0o600)
    except OSError:
        pass


def drucker(pfad, daten=None, zeit=8):
    """POST JSON an den Drucker; serialNumber/checkCode kommen aus der Datei."""
    c = lade()
    if not c.get("ip"):
        raise RuntimeError("Drucker ist noch nicht eingerichtet.")
    host, _, port = c["ip"].partition(":")
    koerper = {"serialNumber": c.get("serial", ""), "checkCode": c.get("check", "")}
    koerper.update(daten or {})
    v = http.client.HTTPConnection(host, int(port or 8898), timeout=zeit)
    try:
        v.request("POST", pfad, json.dumps(koerper), {"Content-Type": "application/json"})
        a = v.getresponse()
        roh = a.read()
    finally:
        v.close()
    if not roh.strip():
        return {"code": -1, "message": "Leere Antwort – Seriennummer prüfen."}
    return json.loads(roh)      # Kopfzeile der Firmware ist falsch geschrieben, Inhalt ist JSON


def lager():
    """Auftragsliste aus dem öffentlichen Lager (60 s gemerkt)."""
    if time.time() - LAGER["t"] > 60 or not LAGER["liste"]:
        with urllib.request.urlopen(PAGES + "auftraege/index.json", timeout=20) as q:
            roh = json.loads(q.read())
        aus = []
        for a in roh:
            if a.get("drucker") != "c5pro" or not a.get("gcode"):
                continue
            aus.append({"ordner": a["ordner"], "titel": a.get("titel") or a.get("name") or a["gcode"], "projekt": a.get("gruppe_titel") or "",
                        "nr": a.get("nr") or 0, "gcode": a["gcode"], "zeit": a.get("zeit", ""), "datum": a.get("datum", ""),
                        "bild": PAGES + "auftraege/" + a["ordner"] + "/" + a["vorschau"] if a.get("vorschau") else "",
                        "koepfe": [f"Kopf {k.get('slot')}: {k.get('material', '')} {k.get('farbe', '')}".strip() for k in a.get("slots") or []]})
        aus.sort(key=lambda a: (a["datum"], a["projekt"], -a["nr"]), reverse=True)
        LAGER.update(t=time.time(), liste=aus)
    return LAGER["liste"]


def adressen():
    """Unter welchen Adressen andere Geräte im Heimnetz die Brücke erreichen."""
    if not NETZ["an"]:
        return []
    aus = []
    name = socket.gethostname().split(".")[0]
    if name:
        aus.append(f"http://{name}.local:{NETZ['port']}")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.0.2.1", 9))          # schickt nichts, verrät nur die eigene Netz-Adresse
        aus.append(f"http://{s.getsockname()[0]}:{NETZ['port']}")
        s.close()
    except OSError:
        pass
    return aus


FEHLER = {-2: "Der Drucker lehnt ab: „Nur LAN“-Modus am Drucker einschalten (Netzwerk-Einstellungen).",
          1: "Seriennummer oder Check Code stimmen nicht.",
          2: "Der Drucker ist beschäftigt.", 3: "Die Datei liegt nicht auf dem Drucker."}


def klartext(a):
    k = a.get("code", -1)
    return FEHLER.get(k, f"{a.get('message', 'Unbekannte Antwort')} (Code {k})")


def status():
    a = drucker("/detail")
    if a.get("code") != 0:
        return {"ok": False, "text": klartext(a)}
    d = a.get("detail", a)
    anteil = d.get("printProgress") or 0
    if anteil > 1.0001:
        anteil /= 100
    return {"ok": True, "name": d.get("name") or d.get("model") or "Drucker", "firmware": d.get("firmwareVersion", ""),
            "zustand": d.get("status", ""), "datei": d.get("printFileName", ""), "anteil": anteil,
            "rest_s": d.get("estimatedTime") or 0, "schicht": d.get("printLayer"), "schichten": d.get("targetPrintLayer"),
            "koepfe": d.get("nozzleTemps") or [], "koepfe_soll": d.get("nozzleTargetTemps") or [],
            "bett": d.get("platTemp"), "bett_soll": d.get("platTargetTemp"), "kammer": d.get("chamberTemp"),
            "fehler": d.get("errorCode", ""),
            "kamera": d.get("cameraStreamUrl") or f"http://{lade()['ip'].partition(':')[0]}:8080/?action=stream"}


def hochladen(lid, url, name):
    """Datei von Pages holen und an den Drucker schicken – OHNE zu starten."""
    L = LAUF[lid]
    tmp = None
    try:
        if not url.startswith(QUELLEN_FEST + (PAGES,)):
            raise RuntimeError("Diese Adresse ist keine Druckwerk-Datei.")
        name = re.sub(r"[^A-Za-z0-9._-]", "_", name or url.rsplit("/", 1)[-1].split("?")[0])
        if not name.lower().endswith((".gcode", ".3mf")):
            raise RuntimeError("Nur .gcode oder .3mf.")
        L.update(stufe="laden", text="Hole die Datei aus dem Lager …", name=name)
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".teil")
        with urllib.request.urlopen(url, timeout=60) as q:
            ges = int(q.headers.get("Content-Length") or 0)
            n = 0
            while True:
                b = q.read(1 << 18)
                if not b:
                    break
                tmp.write(b)
                n += len(b)
                L["anteil"] = n / ges * 0.5 if ges else 0
        tmp.close()
        gr = os.path.getsize(tmp.name)
        if gr < 200:
            raise RuntimeError("Die Datei ist leer.")
        c = lade()
        host, _, port = c["ip"].partition(":")
        grenze = "----druckwerk" + uuid.uuid4().hex
        kopf = (f"--{grenze}\r\nContent-Disposition: form-data; name=\"gcodeFile\"; filename=\"{name}\"\r\n"
                "Content-Type: application/octet-stream\r\n\r\n").encode()
        fuss = f"\r\n--{grenze}--\r\n".encode()
        L.update(stufe="senden", text="Schicke die Datei an den Drucker …")
        v = http.client.HTTPConnection(host, int(port or 8898), timeout=120)
        try:
            v.putrequest("POST", "/uploadGcode")
            for k, w in (("serialNumber", c.get("serial", "")), ("checkCode", c.get("check", "")), ("fileSize", str(gr)),
                         ("printNow", "false"), ("levelingBeforePrint", "false"), ("flowCalibration", "false"),
                         ("timeLapseVideo", "false"), ("useMatlStation", "false"), ("gcodeToolCnt", "0"),
                         ("Content-Type", f"multipart/form-data; boundary={grenze}"),
                         ("Content-Length", str(len(kopf) + gr + len(fuss)))):
                v.putheader(k, w)
            v.endheaders()
            v.send(kopf)
            n = 0
            with open(tmp.name, "rb") as f:
                while True:
                    b = f.read(1 << 18)
                    if not b:
                        break
                    v.send(b)
                    n += len(b)
                    L["anteil"] = 0.5 + n / gr * 0.5
            v.send(fuss)
            roh = v.getresponse().read()
        finally:
            v.close()
        a = json.loads(roh) if roh.strip() else {"code": -1, "message": "Leere Antwort"}
        if a.get("code") != 0:
            raise RuntimeError(klartext(a))
        L.update(stufe="fertig", anteil=1, fertig=True, text=f"„{name}“ liegt auf dem Drucker ({gr / 1e6:.1f} MB). Noch nicht gestartet.")
    except Exception as e:
        L.update(stufe="fehler", fertig=True, fehler=str(e), text=str(e))
    finally:
        if tmp:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass


SEITE = r"""<!doctype html><html lang="de"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Druckwerk-Brücke</title><style>
body{font:16px -apple-system,system-ui,sans-serif;margin:0;background:#f2f2f7;color:#1c1c1e}
main{max-width:520px;margin:0 auto;padding:16px}h1{font-size:22px;margin:8px 0 14px}h2{font-size:15px;margin:0 0 8px;color:#6b6b70;font-weight:600}
.k{background:#fff;border-radius:14px;padding:14px;margin:0 0 14px}
label{display:block;font-size:13px;color:#6b6b70;margin:8px 0 3px}input[type=text]{width:100%;box-sizing:border-box;font:inherit;padding:9px;border:1px solid #d1d1d6;border-radius:9px}
button{font:inherit;font-weight:600;border:0;border-radius:11px;padding:11px 14px;background:#0a84ff;color:#fff;margin:8px 8px 0 0}
button.z{background:#e5e5ea;color:#1c1c1e}button.r{background:#ff3b30}button:disabled{opacity:.4}
.b{height:8px;background:#e5e5ea;border-radius:4px;overflow:hidden;margin:8px 0}.b i{display:block;height:100%;background:#0a84ff;width:0}
.t{display:flex;gap:8px;flex-wrap:wrap;font-size:14px}.t span{background:#f2f2f7;border-radius:8px;padding:5px 8px}
.z2{display:flex;gap:10px;align-items:center;padding:8px 0;border-top:1px solid #e5e5ea;cursor:pointer}.z2 img{width:54px;height:42px;object-fit:contain;background:#f2f2f7;border-radius:8px}.z2 b{display:block;color:#1c1c1e;font-size:15px}
.h{font-size:13px;color:#6b6b70;margin:6px 0 0}.f{color:#c0271d}.g{color:#1c7c3a}
</style><main><h1>Druckwerk-Brücke</h1>
<div class="k" id="auftrag" hidden><h2>Druckdatei</h2><div id="aName" style="font-weight:600"></div><div id="aKopf" class="h"></div>
<div class="b"><i id="aBalken"></i></div><div id="aText" class="h"></div>
<button id="aHoch">Auf den Drucker laden</button>
<div id="aStart" hidden><label><input type="checkbox" id="aNiv" checked> vorher nivellieren</label>
<label><input type="checkbox" id="aFrei"> Platte ist leer, Köpfe 1–4 sind wie im Bericht bestückt</label>
<button id="aDruck" disabled>Jetzt drucken</button></div></div>
<div class="k"><h2>Drucker</h2><div id="sText">…</div><div class="b"><i id="sBalken"></i></div><div class="t" id="sTemp"></div>
<div id="sKnopf" hidden><button class="z" data-a="pause">Pause</button><button class="z" data-a="continue">Weiter</button><button class="r" data-a="cancel">Abbrechen</button></div></div>
<div class="k"><h2>Kamera</h2><button class="z" id="kAn" style="margin-top:0">Kamera zeigen</button><img id="kBild" hidden style="width:100%;border-radius:10px;margin-top:8px" alt=""></div>
<div class="k"><h2>Aus dem Lager</h2><input type="text" id="lSuch" placeholder="Suchen …"><div id="lager" class="h">…</div></div>
<div class="k"><h2>Auf dem Drucker</h2><div id="liste" class="h">…</div></div>
<div class="k" id="andere" hidden><h2>Auf iPad und iPhone öffnen</h2><div id="aAdr"></div><p class="h">Im selben WLAN in Safari öffnen und „Zum Home-Bildschirm“ wählen. Der Mac muss an sein.</p><a id="aApp" class="h" target="_blank" rel="noopener">Diese Brücke in der Druckwerk-App merken</a></div>
<details class="k" id="ein"><summary><b>Einrichten</b></summary>
<label>Adresse des Druckers (IP)</label><input type="text" id="eIp" placeholder="192.168.178.50">
<label>Seriennummer</label><input type="text" id="eSn"><label>Check Code</label><input type="text" id="eCc">
<button id="eOk">Speichern und prüfen</button><div id="eText" class="h"></div>
<p class="h">Alle drei stehen am Drucker in den Netzwerk-Einstellungen. Sie bleiben nur auf diesem Rechner.</p></details>
</main><script>
const $=i=>document.getElementById(i),P=new URLSearchParams(location.search);
const ruf=(p,d)=>fetch(p,{method:d?"POST":"GET",headers:{"Content-Type":"application/json"},body:d?JSON.stringify(d):undefined}).then(r=>r.json());
const zeit=s=>{s=Math.round(s/60);return s>=60?Math.floor(s/60)+" h "+(s%60)+" min":s+" min"};
let datei=P.get("datei"),name=P.get("name")||"",oben="",ordner="",LG=[],kam="";
function waehle(a){ordner=a.ordner;datei="";name=a.gcode;oben="";$("auftrag").hidden=false;$("aName").textContent=a.titel+(a.zeit?" · "+a.zeit:"");$("aKopf").textContent=a.koepfe.join(" · ");
 $("aBalken").style.width="0";$("aText").textContent="";$("aText").className="h";$("aHoch").disabled=false;$("aStart").hidden=true;$("aFrei").checked=false;$("aDruck").disabled=true;scrollTo({top:0,behavior:"smooth"})}
function zeige(){const q=$("lSuch").value.toLowerCase(),z=$("lager");z.textContent="";
 LG.filter(a=>(a.titel+" "+a.projekt+" "+a.ordner).toLowerCase().includes(q)).slice(0,40).forEach(a=>{const d=document.createElement("div");d.className="z2";
  const i=document.createElement("img");i.loading="lazy";i.src=a.bild;i.alt="";const t=document.createElement("div"),b=document.createElement("b");b.textContent=a.titel;
  t.append(b,document.createTextNode([a.projekt,a.zeit,a.datum].filter(Boolean).join(" · ")));d.append(i,t);d.onclick=()=>waehle(a);z.append(d)})}
$("lSuch").oninput=zeige;
ruf("/api/lager").then(l=>{if(l.adressen&&l.adressen.length){$("andere").hidden=false;l.adressen.forEach(x=>{const d=document.createElement("div");d.style.fontWeight="600";d.textContent=x;$("aAdr").append(d)});
  $("aApp").href="https://tom444555.github.io/druckwerk/#bruecke="+encodeURIComponent(l.adressen[0])}
 if(!l.ok){$("lager").textContent=l.text;return}LG=l.liste;zeige()});
$("kAn").onclick=()=>{const b=$("kBild");if(b.hidden){b.src=kam;b.hidden=false;$("kAn").textContent="Kamera aus"}else{b.removeAttribute("src");b.hidden=true;$("kAn").textContent="Kamera zeigen"}};
$("kBild").onerror=()=>{if(!$("kBild").hidden){$("kBild").hidden=true;$("kAn").textContent="Kamera nicht erreichbar – nochmal"}};
if(datei){$("auftrag").hidden=false;$("aName").textContent=P.get("titel")||name||datei}
async function stand(){try{const s=await ruf("/api/status");
 if(!s.ok){$("sText").innerHTML='<span class="f"></span>';$("sText").firstChild.textContent=s.text;$("sKnopf").hidden=true;if(s.leer)$("ein").open=true;return}
 const laeuft=s.zustand&&!/ready|idle|completed|cancel/i.test(s.zustand);
 $("sText").textContent=s.name+" · "+(s.zustand||"?")+(laeuft&&s.datei?" · "+s.datei+" · "+Math.round(s.anteil*100)+" %"+(s.rest_s?" · noch "+zeit(s.rest_s):""):"");
 kam=s.kamera||"";$("sBalken").style.width=(laeuft?s.anteil*100:0)+"%";$("sKnopf").hidden=!laeuft;
 const t=$("sTemp");t.textContent="";(s.koepfe||[]).forEach((w,i)=>{const e=document.createElement("span");e.textContent="Kopf "+(i+1)+": "+Math.round(w)+"° / "+Math.round((s.koepfe_soll||[])[i]||0)+"°";t.append(e)});
 if(s.bett!=null){const e=document.createElement("span");e.textContent="Bett: "+Math.round(s.bett)+"° / "+Math.round(s.bett_soll||0)+"°";t.append(e)}
 if(s.kammer!=null&&s.kammer>-50){const e=document.createElement("span");e.textContent="Kammer: "+Math.round(s.kammer)+"°";t.append(e)}
}catch(e){$("sText").textContent="Brücke antwortet nicht."}}
async function liste(){try{const l=await ruf("/api/liste");const z=$("liste");z.textContent="";
 if(!l.ok){z.textContent=l.text;return}if(!l.dateien.length){z.textContent="Keine Dateien.";return}
 l.dateien.slice(0,12).forEach(n=>{const d=document.createElement("div");d.textContent=n;z.append(d)})}catch(e){}}
$("aHoch").onclick=async()=>{$("aHoch").disabled=true;const a=await ruf("/api/hochladen",ordner?{ordner}:{url:datei,name});
 if(!a.ok){$("aText").textContent=a.text;$("aText").className="h f";$("aHoch").disabled=false;return}
 const t=setInterval(async()=>{const l=await ruf("/api/lauf?id="+a.id);$("aBalken").style.width=(l.anteil*100)+"%";$("aText").textContent=l.text;
  if(l.fertig){clearInterval(t);if(l.fehler){$("aText").className="h f";$("aHoch").disabled=false}else{$("aText").className="h g";oben=l.name;$("aStart").hidden=false;liste()}}},500)};
$("aFrei").onchange=()=>$("aDruck").disabled=!$("aFrei").checked;
$("aDruck").onclick=async()=>{$("aDruck").disabled=true;const a=await ruf("/api/drucken",{name:oben,nivellieren:$("aNiv").checked});
 $("aText").textContent=a.text;$("aText").className="h "+(a.ok?"g":"f");if(!a.ok)$("aDruck").disabled=false;stand()};
document.querySelectorAll("#sKnopf button").forEach(b=>b.onclick=async()=>{if(b.dataset.a=="cancel"&&!confirm("Druck wirklich abbrechen?"))return;await ruf("/api/steuern",{aktion:b.dataset.a});stand()});
$("eOk").onclick=async()=>{const a=await ruf("/api/einrichten",{ip:$("eIp").value.trim(),serial:$("eSn").value.trim(),check:$("eCc").value.trim()});
 $("eText").textContent=a.text;$("eText").className="h "+(a.ok?"g":"f");stand();liste()};
ruf("/api/einrichtung").then(e=>{$("eIp").value=e.ip||"";$("eSn").value=e.serial||"";if(!e.ip)$("ein").open=true});
stand();liste();setInterval(stand,4000);
</script></html>"""


class Anfrage(BaseHTTPRequestHandler):
    server_version = "DruckwerkBruecke/1"

    def log_message(self, *a):
        pass

    def antwort(self, d, code=200, art="application/json"):
        roh = d.encode() if isinstance(d, str) else json.dumps(d).encode()
        self.send_response(code)
        self.send_header("Content-Type", art + "; charset=utf-8")
        self.send_header("Content-Length", str(len(roh)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(roh)

    def eigen(self):
        """Nur Aufrufe von der eigenen Seite annehmen (keine fremde Webseite darf den Drucker steuern)."""
        o = self.headers.get("Origin")
        return bool(o) and urllib.parse.urlsplit(o).netloc == self.headers.get("Host")

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(u.query)
        try:
            if u.path == "/":
                return self.antwort(SEITE, art="text/html")
            if u.path == "/api/einrichtung":
                c = lade()
                return self.antwort({"ip": c.get("ip", ""), "serial": c.get("serial", ""), "check": bool(c.get("check"))})
            if u.path == "/api/status":
                if not lade().get("ip"):
                    return self.antwort({"ok": False, "leer": True, "text": "Noch nicht eingerichtet – unten „Einrichten“ ausfüllen."})
                return self.antwort(status())
            if u.path == "/api/liste":
                a = drucker("/gcodeList")
                if a.get("code") != 0:
                    return self.antwort({"ok": False, "text": klartext(a)})
                return self.antwort({"ok": True, "dateien": a.get("gcodeList") or []})
            if u.path == "/api/lager":
                try:
                    return self.antwort({"ok": True, "liste": lager(), "adressen": adressen()})
                except Exception as e:
                    return self.antwort({"ok": False, "text": f"Lager nicht erreichbar ({e}).", "adressen": adressen()})
            if u.path == "/api/lauf":
                return self.antwort(LAUF.get(q.get("id", [""])[0], {"fertig": True, "fehler": "unbekannt", "text": "Unbekannter Lauf", "anteil": 0}))
            self.antwort({"ok": False, "text": "Gibt es nicht."}, 404)
        except Exception as e:
            self.antwort({"ok": False, "text": f"Drucker nicht erreichbar ({e}). Ist er an und im selben Netz?"})

    def do_POST(self):
        if not self.eigen() or "json" not in (self.headers.get("Content-Type") or ""):
            return self.antwort({"ok": False, "text": "Abgelehnt."}, 403)
        try:
            d = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)) or b"{}")
            p = self.path
            if p == "/api/einrichten":
                c = lade()
                c.update(ip=d.get("ip", ""), serial=d.get("serial", ""))
                if d.get("check"):
                    c["check"] = d["check"]
                merke(c)
                s = status()
                return self.antwort({"ok": s["ok"], "text": f"Verbunden mit {s['name']} (Firmware {s['firmware']})." if s["ok"] else s["text"]})
            if p == "/api/hochladen":
                if not lade().get("ip"):
                    return self.antwort({"ok": False, "text": "Erst den Drucker einrichten."})
                lid = uuid.uuid4().hex[:10]
                LAUF[lid] = {"stufe": "start", "anteil": 0, "text": "…", "fertig": False, "fehler": "", "name": ""}
                url, name = d.get("url", ""), d.get("name", "")
                if d.get("ordner"):
                    a = next((x for x in lager() if x["ordner"] == d["ordner"]), None)
                    if not a:
                        return self.antwort({"ok": False, "text": "Diesen Auftrag gibt es im Lager nicht."})
                    url, name = PAGES + "auftraege/" + a["ordner"] + "/" + urllib.parse.quote(a["gcode"]), a["gcode"]
                threading.Thread(target=hochladen, args=(lid, url, name), daemon=True).start()
                return self.antwort({"ok": True, "id": lid})
            if p == "/api/drucken":
                a = drucker("/printGcode", {"fileName": d.get("name", ""), "levelingBeforePrint": bool(d.get("nivellieren", True)),
                                            "flowCalibration": False, "timeLapseVideo": False})
                return self.antwort({"ok": a.get("code") == 0, "text": "Druck gestartet." if a.get("code") == 0 else klartext(a)})
            if p == "/api/steuern":
                akt = d.get("aktion")
                if akt not in ("pause", "continue", "cancel"):
                    return self.antwort({"ok": False, "text": "Unbekannt."})
                a = drucker("/control", {"payload": {"cmd": "jobCtl_cmd", "args": {"jobID": "", "action": akt}}})
                return self.antwort({"ok": a.get("code") == 0, "text": klartext(a) if a.get("code") else "Gesendet."})
            self.antwort({"ok": False, "text": "Gibt es nicht."}, 404)
        except Exception as e:
            self.antwort({"ok": False, "text": f"Drucker nicht erreichbar ({e})."})


def main():
    ap = argparse.ArgumentParser(description="Druckwerk-Brücke zum Creator 5 Pro")
    ap.add_argument("--port", type=int, default=8787)
    ap.add_argument("--netz", action="store_true", help="auch für andere Geräte im Heimnetz (iPad) erreichbar machen")
    ap.add_argument("--still", action="store_true", help="keinen Browser öffnen")
    a = ap.parse_args()
    NETZ.update(an=a.netz, port=a.port)
    srv = ThreadingHTTPServer(("0.0.0.0" if a.netz else "127.0.0.1", a.port), Anfrage)
    print(f"Druckwerk-Brücke läuft: http://localhost:{a.port}   (beenden mit Ctrl+C)")
    for x in adressen():
        print(f"  iPad / iPhone im selben WLAN: {x}")
    if not a.netz:
        print("  Nur an diesem Rechner. Für iPad und iPhone mit --netz starten.")
    if not a.still:
        threading.Timer(0.6, lambda: webbrowser.open(f"http://localhost:{a.port}")).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nBeendet.")


if __name__ == "__main__":
    main()

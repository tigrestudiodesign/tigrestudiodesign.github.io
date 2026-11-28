"""Single source of truth for the UNIT 1024 design system.
Writes tokens.json (DTCG format), tokens.css, tokens.js and icons.svg into ../system/."""
import json, os, sys
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

prim = {
  "teal":  {"50":"#e8f5f4","100":"#c6e7e5","300":"#6cc2be","500":"#2fa39e","700":"#1f807c","800":"#17625f","900":"#0f4744"},
  "ink":   {"50":"#f4f5f5","100":"#e4e8ea","200":"#cfd6da","300":"#9fb0b8","500":"#5c6a72","700":"#22363f","800":"#132630","900":"#0b1317"},
  "white": "#ffffff",
  "safety":{"red":"#e23b2e","red-700":"#b42318","yellow":"#f2c230","yellow-700":"#8a6a00","green":"#39d353","green-700":"#1b7f30"},
}
# semantic roles -> primitive refs
sem = {
  "bg": {"default":"ink.50","raised":"white","sunken":"ink.100","inverse":"ink.800","deep":"ink.900","brand":"teal.500"},
  "fg": {"default":"ink.800","muted":"ink.500","subtle":"ink.300","inverse":"white","brand":"teal.800","on-brand":"ink.900"},
  "border": {"default":"ink.200","strong":"ink.800","brand":"teal.500","focus":"teal.800"},
  "status": {"working":"safety.green","working-text":"safety.green-700","caution":"safety.yellow","caution-text":"safety.yellow-700",
             "stop":"safety.red","stop-text":"safety.red-700","info":"teal.500","info-text":"teal.800","offline":"ink.300"},
  "data": {"1":"teal.700","2":"ink.800","3":"ink.500","4":"teal.900","5":"teal.300"},
}
space = {"0":0,"1":4,"2":8,"3":12,"4":16,"5":24,"6":32,"7":48,"8":64,"9":96,"10":128}
radius = {"xs":4,"sm":8,"md":14,"lg":22,"tile":"13.125%","pill":999}
font = {"display":"Inter Display","mono":"JetBrains Mono"}
type_ = {
  "display-1":{"family":"display","size":120,"weight":900,"line":0.88,"track":-0.03,"case":"upper"},
  "display-2":{"family":"display","size":64,"weight":900,"line":0.9,"track":-0.03,"case":"upper"},
  "heading-1":{"family":"display","size":40,"weight":900,"line":0.95,"track":-0.02,"case":"upper"},
  "heading-2":{"family":"display","size":28,"weight":700,"line":1.1,"track":-0.01,"case":"none"},
  "body":     {"family":"display","size":16,"weight":700,"line":1.5,"track":0,"case":"none"},
  "mono-1":   {"family":"mono","size":14,"weight":400,"line":1.45,"track":0.08,"case":"upper"},
  "mono-2":   {"family":"mono","size":11,"weight":700,"line":1.3,"track":0.12,"case":"upper"},
}
motion = {"duration":{"instant":80,"fast":140,"base":220,"slow":420,"sweep":900},
          "easing":{"standard":[0.2,0,0,1],"enter":[0,0,0,1],"exit":[0.4,0,1,1],"linear":[0,0,1,1]}}
elev = {"0":"none","1":"0 1px 0 rgba(19,38,48,.08), 0 2px 6px rgba(19,38,48,.06)","2":"0 2px 0 rgba(19,38,48,.06), 0 12px 28px rgba(19,38,48,.12)","3":"0 24px 60px rgba(11,19,23,.28)"}

def resolve(ref):
    a,b = ref.split(".") if "." in ref else (ref,None)
    v = prim[a] if b is None else prim[a][b]
    return v

# ---- DTCG json
def ctok(v,desc=None):
    d={"$type":"color","$value":v}
    if desc: d["$description"]=desc
    return d
dt = {"$description":"UNIT 1024 design system v1.0. Unofficial concept by Tigre Studio; not affiliated with Agility Robotics.",
  "color":{"primitive":{}, "semantic":{}},
  "space":{k:{"$type":"dimension","$value":f"{v}px"} for k,v in space.items()},
  "radius":{k:{"$type":"dimension","$value":(v if isinstance(v,str) else f"{v}px")} for k,v in radius.items()},
  "font":{"family":{k:{"$type":"fontFamily","$value":v} for k,v in font.items()}},
  "type":{k:{"$type":"typography","$value":{"fontFamily":"{font.family.%s}"%v["family"],"fontSize":f'{v["size"]}px',"fontWeight":v["weight"],"lineHeight":v["line"],"letterSpacing":f'{v["track"]}em'}} for k,v in type_.items()},
  "motion":{"duration":{k:{"$type":"duration","$value":f"{v}ms"} for k,v in motion["duration"].items()},
            "easing":{k:{"$type":"cubicBezier","$value":v} for k,v in motion["easing"].items()}},
  "shadow":{k:{"$type":"shadow","$value":v} for k,v in elev.items()},
}
for g,vals in prim.items():
    if isinstance(vals,str): dt["color"]["primitive"][g]=ctok(vals)
    else: dt["color"]["primitive"][g]={k:ctok(v) for k,v in vals.items()}
for g,vals in sem.items():
    dt["color"]["semantic"][g]={k:ctok("{color.primitive.%s}"%r) for k,r in vals.items()}
json.dump(dt,open(f"{OUT}/tokens.json","w"),indent=2)

# ---- CSS
L=[":root{","  /* UNIT 1024 design system v1.0 · generated from tokens.json · unofficial concept */"]
for g,vals in prim.items():
    if isinstance(vals,str): L.append(f"  --c-{g}:{vals};")
    else:
        for k,v in vals.items(): L.append(f"  --c-{g}-{k}:{v};")
for g,vals in sem.items():
    for k,r in vals.items():
        a,b=r.split(".") if "." in r else (r,None)
        L.append(f"  --{g}-{k}:var(--c-{a}{'-'+b if b else ''});")
for k,v in space.items(): L.append(f"  --space-{k}:{v}px;")
for k,v in radius.items(): L.append(f"  --radius-{k}:{v if isinstance(v,str) else str(v)+'px'};")
L.append(f'  --font-display:"{font["display"]}",system-ui,sans-serif;')
L.append(f'  --font-mono:"{font["mono"]}",ui-monospace,monospace;')
for k,v in type_.items():
    L.append(f'  --type-{k}:{v["weight"]} {v["size"]}px/{v["line"]} var(--font-{v["family"]});')
    L.append(f'  --track-{k}:{v["track"]}em;')
for k,v in motion["duration"].items(): L.append(f"  --dur-{k}:{v}ms;")
for k,v in motion["easing"].items(): L.append(f"  --ease-{k}:cubic-bezier({','.join(str(x) for x in v)});")
for k,v in elev.items(): L.append(f"  --shadow-{k}:{v};")
L.append("}")
L.append("@media (prefers-reduced-motion:reduce){:root{--dur-fast:0ms;--dur-base:0ms;--dur-slow:0ms;--dur-sweep:0ms}}")
open(f"{OUT}/tokens.css","w").write("\n".join(L)+"\n")

# ---- JS
flat={"primitive":prim,"semantic":{g:{k:{"ref":r,"hex":resolve(r)} for k,r in v.items()} for g,v in sem.items()},
      "space":space,"radius":radius,"type":type_,"motion":motion,"shadow":elev}
open(f"{OUT}/tokens.js","w").write("window.TOKENS="+json.dumps(flat)+";\n")

# ---- icons (24 grid, 2px stroke, square caps, miter joins, 45/90 degrees only)
I = {
 "go":      '<path d="M8 4l8 8-8 8"/>',
 "stop":    '<path d="M8 2h8l6 6v8l-6 6H8l-6-6V8z"/><path d="M8 12h8"/>',
 "caution": '<path d="M12 3l10 18H2z"/><path d="M12 10v5"/><path d="M12 18v.01"/>',
 "check":   '<path d="M4 12l5 5L20 6"/>',
 "pause":   '<path d="M8 5v14M16 5v14"/>',
 "slow":    '<path d="M3 17a9 9 0 0 1 18 0"/><path d="M12 17l-4-4"/>',
 "person":  '<path d="M12 3.5h.01"/><circle cx="12" cy="4.5" r="2"/><path d="M12 9v7M7 12h10M12 16l-4 6M12 16l4 6"/>',
 "unit":    '<rect x="8" y="2" width="8" height="5"/><rect x="6" y="9" width="12" height="7"/><rect x="3" y="18" width="18" height="4"/>',
 "tote":    '<path d="M3 9h18l-2 11H5z"/><path d="M8 9V5h8v4"/>',
 "lift":    '<path d="M12 13V3M7 8l5-5 5 5"/><rect x="4" y="16" width="16" height="5"/>',
 "charge":  '<path d="M13 2L5 13h6l-1 9 8-11h-6z"/>',
 "battery": '<rect x="2" y="7" width="18" height="10"/><path d="M22 10v4M6 10v4M10 10v4M14 10v4"/>',
 "zone":    '<rect x="3" y="3" width="18" height="18" stroke-dasharray="3 3"/><path d="M9 12h6"/>',
 "scan":    '<path d="M3 8V3h5M16 3h5v5M21 16v5h-5M8 21H3v-5M3 12h18"/>',
 "route":   '<path d="M4 21v-6h6V9h6V5"/><path d="M13 5h7v7"/>',
 "signal":  '<path d="M4 20v-3M9 20v-7M14 20V9M19 20V4"/>',
 "walkway": '<path d="M5 21L9 3M19 21L15 3M12 5v3M12 11v3M12 17v3"/>',
 "handoff": '<path d="M3 12h7M14 12h7M7 8l-4 4 4 4M17 8l4 4-4 4"/>',
}
sym=['<svg xmlns="http://www.w3.org/2000/svg" style="display:none">']
for k,v in I.items():
    sym.append(f'<symbol id="i-{k}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="square" stroke-linejoin="miter">{v}</symbol>')
sym.append('</svg>')
open(f"{OUT}/icons.svg","w").write("\n".join(sym)+"\n")
open(f"{OUT}/icons.js","w").write("window.ICONS="+json.dumps(I)+";\n")
print("ok", len(I), "icons")

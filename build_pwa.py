"""Gera a pasta pwa/ (site instalável e offline) a partir de painel-martim.html.
Uso: python3 build_pwa.py
"""
import os, re, struct, zlib, json

SRC = "painel-martim.html"
OUT = "pwa"
VERSION = "v1"
THEME = "#0B6E7F"

def png(size, path):
    """Ícone simples: quadrado teal com uma lente branca (sem dependências)."""
    bg = (11, 110, 127); fg = (255, 255, 255); mid = (11, 110, 127)
    c = size / 2
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            d = ((x - c) ** 2 + (y - c) ** 2) ** 0.5
            if d < size * 0.30: col = fg
            elif d < size * 0.22 + size * 0.0: col = mid
            else: col = bg
            if d < size * 0.18: col = mid
            if d < size * 0.09: col = fg
            row += bytes(col)
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(t, d):
        b = t + d
        return struct.pack(">I", len(d)) + b + struct.pack(">I", zlib.crc32(b) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(data)

os.makedirs(OUT, exist_ok=True)
src = open(SRC, encoding="utf-8").read()
src = re.sub(r"<title>.*?</title>\s*", "", src, count=1, flags=re.S)

head = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="{THEME}">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Painel do Martim">
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="icon-192.png">
<link rel="apple-touch-icon" href="icon-192.png">
<title>Painel do Martim</title>
<style>:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
</head>
<body>
"""
reg = """
<script>
if("serviceWorker" in navigator){window.addEventListener("load",function(){navigator.serviceWorker.register("sw.js").catch(function(){})})}
</script>
</body>
</html>
"""
open(f"{OUT}/index.html", "w", encoding="utf-8").write(head + src + reg)

manifest = {
    "name": "Painel do Martim",
    "short_name": "Painel",
    "description": "Kits de captação, legendas e regras do mês.",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#F2F6F5",
    "theme_color": THEME,
    "lang": "pt-BR",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
    ],
}
json.dump(manifest, open(f"{OUT}/manifest.webmanifest", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

sw = f"""const CACHE = "painel-{VERSION}";
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => {{
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
}});
self.addEventListener("activate", e => {{
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
// Páginas: rede primeiro (pega a versão nova), cache quando estiver sem internet. Fontes e demais arquivos: cache primeiro.
self.addEventListener("fetch", e => {{
  const req = e.request;
  if (req.method !== "GET") return;
  const sameOrigin = new URL(req.url).origin === location.origin;
  if (req.mode === "navigate" || (sameOrigin && req.url.endsWith("index.html"))) {{
    e.respondWith(fetch(req).then(r => {{ const copy = r.clone(); caches.open(CACHE).then(c => c.put("index.html", copy)); return r; }}).catch(() => caches.match("index.html")));
    return;
  }}
  e.respondWith(caches.match(req).then(hit => hit || fetch(req).then(r => {{ const copy = r.clone(); caches.open(CACHE).then(c => c.put(req, copy)); return r; }}).catch(() => hit)));
}});
"""
open(f"{OUT}/sw.js", "w", encoding="utf-8").write(sw)
png(192, f"{OUT}/icon-192.png")
png(512, f"{OUT}/icon-512.png")
print("pwa/ pronta:", sorted(os.listdir(OUT)))

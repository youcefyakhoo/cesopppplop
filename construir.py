#!/usr/bin/env python3
"""
Constructor del catálogo Canales Latinos.

Lee las dos fuentes de belkaperu/belkafut (data1.json + data2.json) y genera:
  - canales.json   catálogo unificado (esquema: title/image/category/options)
  - canales.m3u    el mismo catálogo en M3U (primera opción por canal)
  - categorias.json  las 6 categorías con su conteo

Reglas:
  - dedupe de canales por nombre normalizado (sin acentos/mayúsculas/calidad)
  - enlaces de data1 desenvueltos (?r=...?r=...) hasta la URL real
  - opciones ordenadas: streams directos (.m3u8/.mpd/.mp4) primero, embeds después
  - categorías unificadas en los 6 temas de data2; las sucias de data1
    (general/all) se deducen por palabras clave del nombre

Uso:  python3 construir.py            (descarga las fuentes)
      python3 construir.py D1 D2      (usa copias locales)
"""
import json, sys, unicodedata, urllib.request, urllib.parse as up
from collections import Counter

URL1 = "https://raw.githubusercontent.com/belkaperu/belkafut/refs/heads/main/data1.json"
URL2 = "https://raw.githubusercontent.com/belkaperu/belkafut/refs/heads/main/data2.json"

TEMAS = ["Deportes", "Entretenimiento", "Películas", "Infantiles",
         "Noticias", "Internacionales"]

MAPA_D1 = {
    "deportes": "Deportes", "peliculas": "Películas", "películas": "Películas",
    "noticias": "Noticias", "entretenimiento": "Entretenimiento",
    "infantiles": "Infantiles",
}
CLAVES = [
    ("Deportes", ["espn", "fox sport", "tudn", "goltv", "gol tv", "sport", "futbol",
                  "deporte", "nba", "ufc", "dazn", "tyc", "win+", "liga", "f1",
                  "bein", "directv sport", "dsports", "claro sport"]),
    ("Noticias", ["noticia", "news", "cnn", "bbc", "ntn24", "telesur", "dw ",
                  "euronews", "france 24", "al jazeera", "rt en", "milenio",
                  "telemundo noticias", "univision noticias"]),
    ("Infantiles", ["cartoon", "nick", "disney", "kids", "infantil", "boomerang",
                    "junior", "baby", "toonc", "paka", "nat geo kids"]),
    ("Películas", ["cine", "cinema", "movie", "hbo", "tnt", "space", "studio",
                   "golden", "de pelicula", "multipremier", "cinemax", "amc",
                   "fxm", "paramount", "cinecanal", "cinelatino"]),
]

def bajar(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn")

def clave_nombre(s):
    t = sin_acentos((s or "").lower())
    t = "".join(c if c.isalnum() else " " for c in t)
    toks = [x for x in t.split()
            if x not in ("hd", "fhd", "sd", "uhd", "4k", "full", "hd720", "hd1080")]
    return " ".join(toks)

def desenvolver(u):
    for _ in range(5):
        r = up.parse_qs(up.urlparse(u).query).get("r", [None])[0]
        if not r:
            break
        u = up.unquote(r)
    return u

def es_directo(u):
    p = up.urlparse(u).path.lower()
    return p.endswith((".m3u8", ".mpd", ".mp4", ".ts")) or "/index.m3u8" in p

def deducir(titulo):
    t = " " + clave_nombre(titulo) + " "
    for tema, palabras in CLAVES:
        if any(p in t for p in palabras):
            return tema
    return None

def tema_data1(cat, titulo):
    c = (cat or "").strip().lower()
    if c in MAPA_D1:
        return MAPA_D1[c]
    return deducir(titulo) or "Entretenimiento"

def main():
    if len(sys.argv) >= 3:
        d1 = json.load(open(sys.argv[1], encoding="utf-8"))
        d2 = json.load(open(sys.argv[2], encoding="utf-8"))
    else:
        d1, d2 = bajar(URL1), bajar(URL2)

    catalogo = {}          # clave -> canal
    orden = []             # claves en orden de aparición
    stats = Counter()

    def obtener(titulo):
        k = clave_nombre(titulo)
        if k not in catalogo:
            catalogo[k] = {"title": " ".join((titulo or "").split()),
                           "image": "", "category": "Entretenimiento",
                           "options": [], "_urls": set()}
            orden.append(k)
        return catalogo[k]

    def agregar_opcion(canal, etiqueta, url):
        url = (url or "").strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            stats["url_descartada"] += 1
            return
        if url in canal["_urls"]:
            return
        canal["_urls"].add(url)
        canal["options"].append({
            "label": " ".join((etiqueta or "").split()) or up.urlparse(url).netloc,
            "url": url})

    def poner_logo(canal, img):
        img = (img or "").strip()
        if not img:
            return
        if not canal["image"] or (img.startswith("https://")
                                  and not canal["image"].startswith("https://")):
            canal["image"] = img

    # data2 primero: categorías limpias y servers directos
    for ch in d2.get("channels", []):
        c = obtener(ch.get("name", ""))
        cat = (ch.get("category") or "").strip()
        if cat in TEMAS:
            c["category"] = cat
        poner_logo(c, ch.get("imageUrl", ""))
        for s in ch.get("servers", []):
            agregar_opcion(c, s.get("name", ""), s.get("url", ""))
        stats["de_data2"] += 1

    # data1 después: desenvuelve y suma opciones/canales nuevos
    for ch in d1.get("canales", []):
        c = obtener(ch.get("title", ""))
        if c["category"] == "Entretenimiento":
            c["category"] = tema_data1(ch.get("category", ""), ch.get("title", ""))
        poner_logo(c, ch.get("image", ""))
        for o in ch.get("options", []):
            agregar_opcion(c, o.get("label", ""), desenvolver(o.get("url", "")))
        stats["de_data1"] += 1

    canales = []
    for k in orden:
        c = catalogo[k]
        if not c["options"]:
            stats["sin_enlaces"] += 1
            continue
        # directos primero, manteniendo el orden relativo
        c["options"].sort(key=lambda o: 0 if es_directo(o["url"]) else 1)
        del c["_urls"]
        # Internacionales es el cajón de data2: si el nombre delata el tema,
        # el canal va a su tema real (ESPN -> Deportes, CNN -> Noticias...)
        if c["category"] == "Internacionales":
            d = deducir(c["title"])
            if d:
                c["category"] = d
        canales.append(c)

    canales.sort(key=lambda c: (TEMAS.index(c["category"]), clave_nombre(c["title"])))
    conteo = Counter(c["category"] for c in canales)

    with open("canales.json", "w", encoding="utf-8") as f:
        json.dump({"categorias": TEMAS, "total": len(canales), "canales": canales},
                  f, ensure_ascii=False, indent=1)

    with open("canales.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U x-tvg-url=\"\"\n")
        for c in canales:
            logo = c["image"].replace('"', "'")
            f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{c["category"]}",'
                    f'{c["title"]}\n{c["options"][0]["url"]}\n')

    with open("categorias.json", "w", encoding="utf-8") as f:
        json.dump([{"name": t, "canales": conteo.get(t, 0)} for t in TEMAS],
                  f, ensure_ascii=False, indent=1)

    directos = sum(1 for c in canales if es_directo(c["options"][0]["url"]))
    print(f"canales unicos: {len(canales)}  (fusionados de "
          f"{stats['de_data2']} + {stats['de_data1']} entradas)")
    print(f"con stream directo como 1a opcion: {directos} | solo embed: "
          f"{len(canales) - directos}")
    print(f"sin logo: {sum(1 for c in canales if not c['image'])} | "
          f"urls descartadas: {stats['url_descartada']} | "
          f"canales sin enlaces utilizables: {stats['sin_enlaces']}")
    print("por categoria:", dict(conteo))
    print(f"opciones totales: {sum(len(c['options']) for c in canales)}")

if __name__ == "__main__":
    main()

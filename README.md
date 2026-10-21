# 📺 Canales Latinos

Catálogo unificado de canales latinos construido desde
[belkaperu/belkafut](https://github.com/belkaperu/belkafut)
(`data1.json` + `data2.json`).

**479 canales · 938 enlaces** — fusionados y sin duplicados, con los streams
directos (`.m3u8`) primero y los reproductores web (embeds, ya desenvueltos)
como respaldo.

| Categoría | Canales |
|---|---|
| Deportes | 93 |
| Películas | 49 |
| Noticias | 42 |
| Entretenimiento | 34 |
| Infantiles | 13 |
| Internacionales | 248 |

## Archivos

| Archivo | Qué es |
|---|---|
| `canales.m3u` | Lista M3U lista para cualquier reproductor IPTV (logo + grupo por canal, primera opción). |
| `canales.json` | Catálogo completo: `{title, image, category, options:[{label,url}]}` con **todas** las opciones por canal. |
| `categorias.json` | Las 6 categorías con su conteo. |
| `construir.py` | El constructor: regenera todo desde las fuentes. |

## Uso rápido (URL cruda)

```
https://raw.githubusercontent.com/youcefyakhoo/cesopppplop/main/canales.m3u
https://raw.githubusercontent.com/youcefyakhoo/cesopppplop/main/canales.json
```

Pega la primera en tu reproductor IPTV favorito, o en BLABONGO como fuente por URL.

## Regenerar

Cuando `data1.json` / `data2.json` de belkafut cambien:

```bash
python3 construir.py
git add -A && git commit -m "actualiza catalogo" && git push
```

El script descarga las fuentes, desenvuelve los enlaces `?r=…?r=…` hasta la URL
real, fusiona duplicados por nombre normalizado, unifica las categorías en los
6 temas y ordena cada canal con sus streams directos primero.

> Los enlaces pertenecen a sus respectivos emisores; este repo solo ordena
> y deduplica un índice público.

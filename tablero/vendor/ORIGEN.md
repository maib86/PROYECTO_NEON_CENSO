# Origen de las bibliotecas embebidas (D-28)

El tablero v2 embebe Leaflet dentro del HTML (sin CDN: la red de la sala puede bloquearlo).

| Archivo | URL | Fecha de descarga | SHA-256 |
|---|---|---|---|
| `leaflet-1.9.4/leaflet.js` | https://unpkg.com/leaflet@1.9.4/dist/leaflet.js | 2026-10-16 08:45 (hora de Costa Rica) | `db49d009c841f5ca34a888c96511ae936fd9f5533e90d8b2c4d57596f4e5641a` |
| `leaflet-1.9.4/leaflet.css` | https://unpkg.com/leaflet@1.9.4/dist/leaflet.css | 2026-10-16 08:45 (hora de Costa Rica) | `a7837102824184820dfa198d1ebcd109ff6d0ff9a2672a074b9a1b4d147d04c6` |

Comando (Git Bash, desde `tablero/vendor/leaflet-1.9.4/`):

```bash
for f in leaflet.js leaflet.css; do curl -sSfL -o $f "https://unpkg.com/leaflet@1.9.4/dist/$f"; done
sha256sum leaflet.js leaflet.css
```

Licencia: BSD-2-Clause (© 2010-2023 Vladimir Agafonkin, © 2010-2011 CloudMade); el aviso
`@preserve` va dentro de `leaflet.js` y se conserva al embeberlo.

Las imágenes del CSS (`images/layers.png`, `marker-icon.png`) no se embeben: el tablero
no usa marcadores con icono y el botón del control de capas se dibuja con CSS propio.

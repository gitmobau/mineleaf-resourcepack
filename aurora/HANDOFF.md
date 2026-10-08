# Aurora Pack — traspaso de contexto (para continuar en una sesión nueva)

## Qué es
Resource pack temático "Aurora" (pastel iridiscente: cian→lavanda→rosa→melocotón→menta) para
Minecraft Java **26.3** (resource pack format **97.1**; pack.mcmeta usa min_format 84 / max_format 97).
Inspirado en la capa Aurora y la skin del usuario (skin_aurora_v2.png).

## Dónde está todo (en el PC del usuario)
- Packs instalados: `%APPDATA%\.minecraft\resourcepacks\Aurora Pack\` y `...\Aurora Outline\`
- Zips: `%APPDATA%\.minecraft\Aurora_export\Aurora Pack v3.zip`, `Aurora Outline.zip`
- Scripts generadores: `Aurora_export\scripts\` (Python + Pillow)
  - `gen.py`   v1: HUD, agua, crosshair, herramientas (base)
  - `magic.py` "Marco mágico": menús (inventario, crafteo, hornos, cofres, shulker) + sprites animados
  - `gear.py`  herramientas animadas, aura de encantamiento, armaduras, túnica galáctica + capa
  - `outline_shaders/` rendertype_lines.vsh/.fsh (borde de bloque neón Aurora)
- Referencias vanilla: extraer de `versions\26.3\26.3.jar` (el jar NO está ofuscado en 26.x).
  Los scripts esperan las texturas vanilla en `~/ref63/assets/minecraft/...`.

## Decisiones técnicas ya verificadas en el jar 26.3
- Fondos de contenedor (`textures/gui/container/*.png`) NO se pueden animar; `position_tex_color`
  (pipeline gui_textured) no tiene uniform Globals/GameTime → no forzar animación por shader.
- SÍ animables (mcmeta): sprites GUI (hotbar, hotbar_selection, slot_highlight_back/front,
  recipe_book/button, furnace lit/burn_progress, xp bar) y texturas de item/bloque.
- Sprites no cuadrados necesitan `"width"/"height"` en la animación (p.ej. hotbar_selection 24x23).
- Borde de bloque: core shader `rendertype_lines` (vsh+fsh comparten id). Outline vanilla = negro alpha 0.4.
  Compila en todas las variantes OIT (validado con glslangValidator).
- Aura de encantamiento: `items/*.json` con condition `has_component` enchantments,
  `"ignore_default": true`, `composite` [modelo base, plano 24x24 animado], `"oversized_in_gui": true`,
  elemento con `light_emission: 15`.
- Capa 3D sin mods: `equipment/netherite.json` + capa `"wings"` → `entity/equipment/wings/aurora_cloak.png`
  (WingsLayer no comprueba GLIDER).
- Armadura puesta no se anima (texturas de entidad fuera de atlas). Geometría extra → necesita mods
  Entity Model Features + Entity Texture Features (Fabric).
- Detección de casillas: borde 55 arriba/izq (run de 17/25), relleno 139, blanco abajo/der (18 y 26 px).

## Repositorio (desde la sesión del 2026-10-07)
Todo vive ahora en `gitmobau/mineleaf-resourcepack`, carpeta `aurora/` (ver `aurora/README.md`).
- `python3 aurora/scripts/build.py --ref ~/ref63` regenera, valida y crea `aurora/dist/*.zip`.
- Las rutas de los scripts se pueden cambiar con variables de entorno (`AURORA_REF`, `AURORA_RP`, `AURORA_PREVIEWS`).
  Sin variables, usan las rutas de siempre (`~/ref63`, `~/mnt/.minecraft/resourcepacks`).
- Las previews ya no se meten en la carpeta del pack, van a `aurora/previews/`.
- `ref63/` (assets de Mojang) NO se sube al repo. `python3 aurora/scripts/fetch_ref.py ~/ref63` la baja de
  misode/mcmeta (tag `26.3-assets`, github sí es accesible desde la nube). Comprobado: idéntica a la del zip.
- En la nube no hay acceso a los servidores de Mojang (piston-meta y libraries dan 403), así que
  no se puede arrancar el cliente. La validación es solo estática (`validate.py`).

### Cambios de esta sesión
- `gen.py` leía `~/ref` en vez de `~/ref63` y escribía `max_format` 99. Corregido a `ref63` y 97.
- Comprobado que `gen → magic → gear` reproduce exactamente, píxel a píxel, el pack que había.
- Nuevo `other_worn()` en `gear.py`: la armadura de diamante y la de netherita en `humanoid_baby`
  (los bebés usan la capa `humanoid_baby` en la 26.3), `horse_body` y `nautilus_body`, con un
  recoloreado que no depende del layout de la textura.
- Nuevo `validate.py`. Detalle para compilar los shaders: el juego inyecta `OIT`, `OIT_COEFF_COUNT`,
  `OIT_WAVELET_RANK` y `OIT_COEFF_ATTACHMENT_COUNT`. El validador usa 8, 3 y 2, y el
  `rendertype_lines` vanilla compila con esa misma configuración (sirve de control).

### Aurora HUD XL (sesión del 2026-10-08)
- Pack nuevo y opcional `packs/Aurora HUD XL`: hotbar, selección y mano secundaria más grandes que su rectángulo vanilla.
  Explicación del truco (marcadores en las esquinas + `position_tex_color.vsh`) en `aurora/README.md`.
- Supuesto NO verificado en el jar: los quads de la GUI se emiten en orden arriba-izq, abajo-izq, abajo-dcha, arriba-dcha
  (como `innerBlit` de siempre) y `gl_VertexIndex % 4` da esa esquina. Si no fuera así, los marcos XL saldrían
  deformados o aplastados: desactivar el pack y revisar el orden en `BlitRenderState.buildVertices`.
- `position_tex_color` se usa al arrancar, así que no puede llevar `#include` (el validador lo comprueba).
- Simulación del shader sobre un atlas con vecinos pegados por todos los lados: los sprites XL crecen exactos y el resto no se mueve.

### Corazones, estrellas y menús XL (sesión del 2026-10-08, 2ª parte)
- `icons.py` (Aurora Pack): corazones Aurora animados (8 frames × 4 ticks, todos iguales para ir sincronizados) y comida = estrellas.
- `menus_xl.py` (Aurora HUD XL): 7 menús temáticos que sobresalen 14 px a los lados, 20-22 arriba y 10-12 abajo.
- Supuestos NO verificados en el jar, además del orden de vértices:
  - los fondos se dibujan con `blit(GUI_TEXTURED, tex, x, y, 0, 0, 176, h, 256, 256)` por `position_tex_color`;
  - el cofre hace dos blits: filas (v 0..rows·18+17) e inventario (v 126..222), dibujado justo debajo;
  - el título y la etiqueta del inventario van donde siempre (placas en `SCREENS` de `menus_xl.py`).
- El shader ya no se limita a la franja inferior de la pantalla (los menús están en medio); la esquina por
  `gl_VertexIndex` evita leer marcadores de sprites vecinos (simulado con vecinos pegados por todos los lados).
- Si Aurora HUD XL está desactivado se ven los menús pastel normales de Aurora Pack.

### Resto de pantallas (sesión del 2026-10-08, 3ª parte)
- Todas las pantallas con fondo propio de la 26.3 tienen tema XL (25 texturas, tabla en `aurora/README.md`).
  Temas en `menu_themes.py`; `menus_xl.py` saca ancho, alto y tamaño de textura del vanilla.
- El creativo solo sobresale por los lados (las pestañas van encima y debajo) y su barra/caja de búsqueda van oscuras
  porque el juego escribe ahí en blanco. La baliza no lleva placas: sus textos son claros.
- Las placas de los títulos se pintan antes que casillas y decoraciones, así nunca tapan nada del juego.
- Supuestos de posiciones de títulos sin verificar en el jar para: yunque (60,6), herrería (44,15), telar y
  cartografía (y=4), aldeano (centrado + etiqueta del inventario en 107,72). Si un título queda fuera de su placa,
  se ajusta en `SCREENS`.

### Pantallas sin contenedor (sesión del 2026-10-08, 4ª parte)
- Con shader (Aurora HUD XL): libro de recetas (blit desde (1,1), soportado con `origin`), ventana de progresos
  (hueco interior conservado: el árbol se dibuja por debajo) y selector de modo de juego (fondo translúcido conservado).
  Las dos últimas casi llenan su textura (252 de 256 y 125 de 128): solo sobresalen arriba/abajo.
- Sin shader (Aurora Pack, `screens.py`): libro (cabe en los márgenes libres de su ventana de 192), carteles, fondos
  y separadores de menús, todos los widgets (mismos nine-slice, color solo según luminancia), tooltips y logo.
- No tocados a propósito: panoramas del título, logo de Mojang Studios, imágenes de Realms, toasts y barras de jefe.

### Barras de jefe y toasts (sesión del 2026-10-08, 5ª parte)
- Aurora Pack (`screens.py`): los 7 colores de barra en pastel (el progreso animado 16×2 ticks, 182×5 por frame) y toasts.
  Los toasts de recetas y tutorial siguen claros (el juego escribe en morado/negro); progreso, sistema y "sonando ahora"
  oscuros (texto blanco/amarillo).
- Aurora HUD XL (`hud_xl.py`): fondo de barra de jefe 182×5 → 198×11 (gemas dentro del margen, el progreso tapa el resto)
  y toast de progreso 160×32 → 172×32 (solo hacia la izquierda: entran por la derecha y se apilan sin hueco).

## Estado / pendiente
- Nada probado aún DENTRO del juego. Siguiente paso recomendado: activar los packs
  (Aurora Outline, Aurora HUD XL, Aurora Pack, de arriba a abajo), comprobar capa, aura, borde, menús y HUD XL con capturas.
- Ideas pendientes ofrecidas: versión EMF/ETF de la túnica con vuelo 3D; ajustar intensidad/velocidad.
- Limpieza en el PC: sobra el archivo temporal `Aurora_export\ziJhG1Z5`. Las previews antiguas
  (`preview*.png`, `anim_*.gif`) que hay dentro de la carpeta instalada `Aurora Pack` se pueden borrar.


## Cómo usar este paquete en una sesión en la nube (sin acceso al PC)
1. Descomprime `Aurora_handoff.zip` en el HOME de la sesión (`unzip Aurora_handoff.zip -d ~`).
   Así quedan exactamente las rutas que usan los scripts:
   - `~/ref63/assets/minecraft/...`  (texturas/shaders vanilla 26.3 de referencia)
   - `~/mnt/.minecraft/resourcepacks/Aurora Pack/` y `Aurora Outline/` (packs actuales)
   - `~/work/*.py` (scripts)
2. `pip install pillow` y ejecuta p.ej. `cd ~/work && python3 gear.py`.
3. Para devolver el resultado: comprimir `~/mnt/.minecraft/resourcepacks/Aurora Pack` en .zip y dárselo al
   usuario, que lo copia a `%APPDATA%\.minecraft\resourcepacks`.

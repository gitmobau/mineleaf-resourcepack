# Aurora — resource pack para Minecraft Java 26.3

Tema pastel iridiscente (cian → lavanda → rosa → melocotón → menta) inspirado en la capa Aurora.
Formato de resource pack 97 (`min_format` 84 / `max_format` 97).

| Carpeta | Qué hay |
|---|---|
| `dist/` | **Los zips listos para instalar**: `Aurora Pack.zip`, `Aurora Outline.zip` y `Aurora HUD XL.zip` |
| `packs/Aurora Pack/` | Pack principal. Se genera entero con los scripts (no editar a mano) |
| `packs/Aurora Outline/` | Borde de bloque neón (core shader `rendertype_lines`). Escrito a mano |
| `packs/Aurora HUD XL/` | Opcional: marcos del HUD más grandes que sobresalen (hotbar, selección, mano secundaria). Texturas generadas por `hud_xl.py` + core shader `position_tex_color` escrito a mano |
| `scripts/` | Generadores en Python + Pillow, validador y `build.py` |
| `previews/` | Capturas y GIFs para ver el resultado sin abrir el juego |
| `HANDOFF.md` | Contexto técnico completo, decisiones verificadas y pendientes |

## Instalar
1. Copia los zips de `dist/` a `%APPDATA%\.minecraft\resourcepacks`.
2. En el juego, actívalos en este orden (de arriba a abajo): **Aurora Outline**, **Aurora HUD XL**, **Aurora Pack**.
   Aurora HUD XL es opcional: si los marcos salen aplastados o raros, desactívalo y vuelves al HUD normal de Aurora.

## Regenerar
```bash
pip install pillow
python3 scripts/build.py --ref ~/ref63
```
`--ref` apunta a una carpeta con las texturas vanilla de la 26.3 (`assets/minecraft/...`).
No están en el repo porque son assets de Mojang. Para conseguirlas:
`python3 scripts/fetch_ref.py ~/ref63` (unos 3 s; baja solo lo necesario del espejo
[misode/mcmeta](https://github.com/misode/mcmeta), tag `26.3-assets`). Es byte a byte igual que la
`ref63/` del zip de traspaso y genera exactamente los mismos zips. También vale el
`versions/26.3/26.3.jar`.

`build.py` borra y regenera `packs/Aurora Pack`, ejecuta `gen.py → magic.py → gear.py` (en ese
orden, porque los últimos sobrescriben a los primeros), luego `hud_xl.py`, pasa `validate.py` y crea los zips.
La salida es determinista: con la misma entrada salen los mismos bytes.

### Qué hace cada script
- `gen.py`: base v1 (agua, mira, fondo de la barra de XP, indicadores de ataque, `pack.png` y `pack.mcmeta`).
- `magic.py`: "Marco mágico". Menús (inventario, mesa de crafteo, hornos, cofre grande y shulker) y sprites animados (hotbar, selección, casilla resaltada, botón del libro de recetas, fuego y flecha del horno, XP).
- `gear.py`: herramientas animadas, aura de encantamiento, brillo de encantamiento, armaduras de diamante (cristal) y de netherita (túnica galáctica + capa 3D), también puestas en bebés, caballos y nautilus.
- `hud_xl.py`: texturas de Aurora HUD XL (hotbar con alas de cristal, selección con corona y halo, mano secundaria con aguja) y previsualización del HUD en `previews/`.
- `validate.py`: validación estática contra la 26.3. Revisa JSON, tamaños y frames de las animaciones, nine-slice, referencias de modelos y texturas, definiciones de items, capas de equipamiento, compilación de los shaders en las 5 variantes OIT con `glslangValidator` y que las salidas del vsh coincidan con las entradas del fsh.
- `fetch_ref.py`: descarga la referencia vanilla 26.3 desde misode/mcmeta.

Recursos externos útiles (espejos de assets, esquemas, shaders, EMF/ETF y pixel art): ver `RECURSOS.md`.

## Aurora HUD XL: cómo sobresalen los marcos
El juego siempre mete un sprite de la GUI en su rectángulo fijo (la hotbar ocupa 182×22 pase lo que pase), así que una
textura más grande solo se vería aplastada. Para que sobresalga:
- Cada sprite XL lleva en las 4 esquinas de cada frame un píxel marcador casi invisible: RGBA = (sobresale_x,
  sobresale_y, 167, esquina) con esquina 1 = arriba-izq, 2 = arriba-dcha, 3 = abajo-izq, 4 = abajo-dcha.
- `shaders/core/position_tex_color.vsh` (el shader de los sprites de la GUI) lee en cada vértice el texel de su propia
  esquina y, si es el marcador de esa esquina, empuja el vértice hacia fuera esos píxeles. El `.fsh` descarta los marcadores.
- La esquina de cada vértice sale del orden en que el juego emite los quads de la GUI (arriba-izq, abajo-izq, abajo-dcha,
  arriba-dcha). Así un sprite normal pegado a uno XL en el atlas nunca lee el marcador del vecino.
- Cuánto sobresale cada uno: hotbar 12 px a los lados y 18 hacia arriba (las alas suben junto a la XP y los corazones),
  selección 4 a los lados y 2 arriba, mano secundaria 5 hacia fuera y 18 arriba. Nada sobresale por abajo (borde de pantalla).
- `validate.py` acepta un sprite de la GUI más grande que el vanilla solo si sus marcadores son coherentes en todos los
  frames, el tamaño es vanilla + márgenes, no usa nine-slice y el pack trae el shader.

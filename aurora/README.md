# Aurora — resource pack para Minecraft Java 26.3

Tema pastel iridiscente (cian → lavanda → rosa → melocotón → menta) inspirado en la capa Aurora.
Formato de resource pack 97 (`min_format` 84 / `max_format` 97).

| Carpeta | Qué hay |
|---|---|
| `dist/` | **Los zips listos para instalar**: `Aurora Pack.zip`, `Aurora Outline.zip`, `Aurora HUD XL.zip` y `Aurora EMF.zip` |
| `packs/Aurora Pack/` | Pack principal. Se genera entero con los scripts (no editar a mano) |
| `packs/Aurora Outline/` | Borde de bloque neón (core shader `rendertype_lines`). Escrito a mano |
| `packs/Aurora HUD XL/` | Opcional: marcos del HUD y menús temáticos que sobresalen de su tamaño vanilla. Texturas generadas por `hud_xl.py` y `menus_xl.py` + core shader `position_tex_color` escrito a mano |
| `packs/Aurora EMF/` | Opcional, necesita los mods **Entity Model Features** y **Entity Texture Features**: armadura de netherita en 3D (cresta y alas en el casco, joya en la frente y en el pecho, hombreras y faldones de láminas, cinturón, rodilleras, punteras). Generado por `emf.py` |
| `packs/Aurora Celestial/` | Prototipo opcional (EMF + ETF), **en lugar de** Aurora EMF: la netherita y el diamante dejan de parecer armadura. Aureola que gira y flota, estrella en el pecho, anillo en la cadera y aros en los tobillos; netherita en luz pastel, diamante oscuro con puntos que brillan. Generado por `celestial.py` |
| `scripts/` | Generadores en Python + Pillow, validador y `build.py` |
| `previews/` | Capturas y GIFs para ver el resultado sin abrir el juego |
| `HANDOFF.md` | Contexto técnico completo, decisiones verificadas y pendientes |
| `PROMPT_CODEX.md` | Prompt listo para pegar en Codex y seguir con el pack |
| `PROMPT_CODEX_ARMAS.md` | Prompt para Codex: arco, ballesta, maza, tótem, flechas, perla y escudo en estilo Aurora |
| `PROMPT_CODEX_AUREOLA.md` | Prompt para Codex: netherita "celestial" con aureola y anillos de luz (EMF + ETF) |

## Instalar
1. Copia los zips de `dist/` a `%APPDATA%\.minecraft\resourcepacks`.
2. En el juego, actívalos en este orden (de arriba a abajo): **Aurora EMF** (o **Aurora Celestial**, nunca los dos), **Aurora Outline**, **Aurora HUD XL**, **Aurora Pack**.
   Aurora EMF solo hace algo con los mods Entity Model Features + Entity Texture Features instalados (Fabric o NeoForge 26.3).
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

`build.py` borra y regenera `packs/Aurora Pack`, ejecuta `gen.py → magic.py → gear.py → icons.py → extras.py → screens.py` (en ese
orden, porque los últimos sobrescriben a los primeros), luego `hud_xl.py → menus_xl.py → emf.py`, pasa `validate.py` y crea los zips.
La salida es determinista: con la misma entrada salen los mismos bytes.

### Qué hace cada script
- `gen.py`: base v1 (agua, mira, fondo de la barra de XP, indicadores de ataque, `pack.png` y `pack.mcmeta`).
- `icons.py`: corazones con la paleta Aurora (cada estado con sus colores: veneno, wither, congelado, absorción, montura, hardcore) y la comida convertida en estrellas, todo animado y sincronizado.
- `extras.py`: arco (4 estados), ballesta (6 estados), maza, tótem, flechas, perla de ender y las dos bases de escudo en Aurora. Reutiliza los pintores de `gear.py`, mantiene exactamente tamaños y canales alpha vanilla y comprueba esa igualdad al generar. Texturas estáticas; madera/cuerda lavanda-perla y cristal iridiscente. La punta de la flecha con poción queda casi neutra para conservar el tinte del juego; también se recolorea su astil. Genera `previews/extras.png` con comparaciones vanilla/Aurora. Solo requiere volver a copiar `dist/Aurora Pack.zip`.
- `magic.py`: "Marco mágico". Menús (inventario, mesa de crafteo, hornos, cofre grande y shulker) y sprites animados (hotbar, selección, casilla resaltada, botón del libro de recetas, fuego y flecha del horno, XP).
- `gear.py`: herramientas animadas, aura de encantamiento, brillo de encantamiento, armaduras de diamante (cristal) y de netherita (ópalo claro, iconos y armadura puesta con el mismo estilo: contorno lavanda, ribete iridiscente pastel por dentro y metal perla en 4 tonos suaves sobre la silueta vanilla), también puestas en bebés, caballos y nautilus. Sin capa.
- `hud_xl.py`: texturas de Aurora HUD XL (hotbar con alas de cristal, selección con corona y halo, mano secundaria con aguja, fondo de las barras de jefe con gemas en los extremos) y previsualización del HUD en `previews/`.
- `menus_xl.py`: menús temáticos de Aurora HUD XL (ver abajo): lista de pantallas, construcción de cada fondo y una emulación del shader que comprueba que cada pantalla sale al píxel. Genera `previews/menus_xl.png` y `menus_xl_2.png`.
- `screens.py`: pantallas sin contenedor, retocadas en su sitio (sin shader): libro (cuero violeta, papel perla, cinta y amuleto), carteles y carteles colgantes de las 13 maderas en pastel, fondos de opciones y menús, separadores, botones y demás controles (deslizadores, campos de texto, casillas, pestañas, barras), tooltips, iconos del selector de modo y el logo del título. También las barras de jefe (los 7 colores en pastel, progreso con brillo animado y muescas violeta) y los toasts (recetas a medida, sistema, tutorial y "sonando ahora" por luminancia; iconos grises del tutorial en Aurora). Los logros (ventana de progresos y su toast) se dejan vanilla a propósito. Genera `previews/pantallas.png`.
- `menu_themes.py`: utilidades de dibujo y los 25 temas (marco, fondo, casillas, placas y adornos que sobresalen).
- `emf.py`: pack Aurora EMF (modelos `.jem` de EMF para la netherita, con sus `.properties`) y vista 3D en `previews/emf_netherite.png` con un pequeño renderizador propio.
- `celestial.py`: pack Aurora Celestial (modelos `.jem` animados por pieza, texturas casi transparentes con capa emisiva `_e.png`) y vista previa animada en `previews/celestial.gif`.
- `validate.py`: validación estática contra la 26.3. Revisa JSON, tamaños y frames de las animaciones, nine-slice, referencias de modelos y texturas, definiciones de items, capas de equipamiento, compilación de los shaders en las 5 variantes OIT con `glslangValidator` y que las salidas del vsh coincidan con las entradas del fsh.
- `fetch_ref.py`: descarga la referencia vanilla 26.3 desde misode/mcmeta, incluida `textures/entity/shield/` (en la 26.3 contiene `shield_base.png` y `shield_base_nopattern.png`).

Recursos externos útiles (espejos de assets, esquemas, shaders, EMF/ETF y pixel art): ver `RECURSOS.md`.

## Aurora HUD XL: menús temáticos
| Pantalla | Estética |
|---|---|
| Inventario | Observatorio estelar: lunas en las esquinas, rosa de los vientos, cielo nocturno y ventana de aurora |
| Mesa de crafteo | Taller del fabricador: engranajes de latón, martillo y llave cruzados, fondo de plano |
| Horno | Infierno celestial: llamas pastel con núcleo dorado, halo, alas de ángel y brasas |
| Alto horno | Forja de supernova: estallido estelar, pernos, rejillas de plasma y grietas brillantes |
| Ahumador | Ahumador de nubes: nubes esponjosas, bocanadas de humo, luna y cielo pastel |
| Cofre (todos los tamaños) | Bóveda del tesoro: candado, gemas, montones de monedas y terciopelo |
| Caja de shulker | Caparazón del End: cúpula de concha, shulker asomándose, flores coral y vacío estrellado |
| Yunque | Herrería celestial: yunque con martillo y chispas, remaches y cadenas colgando |
| Baliza | Santuario del faro: haz de luz hacia arriba, pirámides de bloques y gemas |
| Soporte para pociones | Laboratorio alquímico: matraces, burbujas y estantes con viales |
| Mesa de cartografía | Mesa del cartógrafo: rosa de los vientos, mapas enrollados y pergamino con rutas |
| Crafteador | Taller autómata: antorchas de redstone, repetidor, pistones y circuitos |
| Dispensador y soltador | Lanzadera: diana con flechas clavadas y flechas saliendo por los lados |
| Mesa de encantamientos | Biblioteca arcana: libro abierto brillante, estanterías, velas y runas |
| Afiladora | Piedra lunar del afilador: rueda de piedra con chispas y clavijas de madera |
| Tolva | Recolector de estrellas: embudo con estrellas cayendo y cielo nocturno |
| Caballo | Caballeriza: herradura de la suerte, balas de paja, valla y ventana al atardecer |
| Telar | Taller de la tejedora: banderines, ovillos, carretes y tela tejida |
| Nautilus | Arrecife abisal: concha en espiral, corales, burbujas y océano |
| Mesa de herrería | Armería real: escudo con espadas cruzadas, oro y filigrana |
| Cortapiedras | Geoda del cantero: sierra circular y racimos de amatista |
| Aldeano | Mercado: toldo de rayas festoneado, esmeralda y cajas |
| Inventario creativo (3 pestañas) | Estudio del creador: cristales arcoíris por la derecha (arriba y abajo van las pestañas, y el juego vuelve a dibujar la rejilla recortando la textura, así que el dibujo vanilla no se puede desplazar) |
| Libro de recetas (panel) | Recetario estelar: libro abierto con estrellas, esquinas doradas y cintas marcapáginas colgando |
| Selector de modo de juego (F3+F4) | Portal de modos: estrella portal arriba y flecos de cristal abajo |

Los títulos de los menús los pinta el juego en gris oscuro (no se puede cambiar con un resource pack), así que
cada tema pone una placa clara (perla con borde del color del tema) detrás de cada título para que se lea.

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
- Los fondos de menú no son sprites del atlas: el juego recorta siempre una ventana fija (176×166 casi siempre, 230×219
  la baliza, 276×166 el aldeano en una textura de 512×256, 195×136 el creativo). Por eso el dibujo grande empieza en (0,0) de la textura y, junto a cada marcador, hay un segundo texel
  (du, dv, 168, esquina) que dice cuánto se desplaza la UV de esa esquina. El cofre se dibuja en dos trozos (filas +
  inventario) y su textura lleva marcadores para 1 a 6 filas. El `.fsh` sustituye los texels marcadores por el de al lado.
- `validate.py` acepta un sprite de la GUI más grande que el vanilla solo si sus marcadores son coherentes en todos los
  frames, el tamaño es vanilla + márgenes, no usa nine-slice y el pack trae el shader.

## Aurora EMF: netherita en 3D
- Desde la 1.21.9 la armadura es un modelo por pieza: `helmet`, `chestplate`, `leggings` y `boots` (EMF busca
  `player_helmet.jem`… y si no existe usa `helmet.jem`; los nombres viejos `player_outer_armor`/`player_inner_armor` ya
  no se usan). El pack trae `player_helmet2.jem`, `player_slim_helmet2.jem` y `helmet2.jem` (respaldo para mobs), cada uno con su `.properties`, y lo mismo para las demás piezas. Cada `.properties` elige la variante 2 solo
  mientras se lleva esa pieza de netherita (`items=netherite_helmet`, ...); si no, EMF usa el modelo vanilla. Vale para
  el jugador (normal y slim) y para cualquier mob bípedo con netherita. Las demás armaduras no cambian.
- Las piezas nuevas se añaden a las partes vanilla (`attach: true`) y sus caras usan UV por cara sobre "muestras de
  material" (metal, ribete, gemas...) que `gear.py` pinta en las texturas de netherita, en texels que ninguna caja de
  armadura vanilla usa. Sin EMF no se ven.
- Las placas planas (hombreras, faldones, punteras) usan en sus cantos la muestra `lame` (brillo arriba, metal, contorno
  abajo), así cada lámina se separa de la siguiente. Las piezas del lado izquierdo son el espejo de las del derecho.
- `HUMANOID_BOXES`/`opal_regions()` en `gear.py`: los contornos solo se dibujan donde la placa termina dentro de una cara,
  no en las costuras entre caras de la caja.

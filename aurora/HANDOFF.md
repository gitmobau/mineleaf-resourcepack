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

## Primera prueba en el juego (capturas del usuario, 2026-10-07)
Funcionan: inventario (cielo nocturno, gato dormido, botón gato), cofre grande (gato asomado), horno,
hotbar animada, selección, barra de XP, aura de encantamiento en la espada, iconos de herramientas y armaduras,
y la armadura de diamante puesta.
El usuario usa además algún mod o pack que pone la GUI en 3D inclinada y cambia el libro de recetas (verde
y beige) y el inventario creativo (oscuro). Esas dos pantallas no las tocaba Aurora, por eso salía lo del otro pack.
Ahora las cubre `extra.py`. Para que se vean, Aurora tiene que estar por encima de ese pack.
Queda por ver en el juego: la túnica de netherita y la capa, el borde de bloque, y los nuevos libro de recetas, creativo y HUD.

## Sesión 2026-10-08
- `menus.py`: todos los fondos de contenedor que quedaban y sus sprites, más los widgets comunes y los tooltips.
- `build_container()` (magic.py) ahora clasifica el arte vanilla que sobra por zonas conectadas:
  - zona pequeña (flechas, iconos): colores aurora, como antes;
  - zona grande y densa oscura (campo de texto del yunque, faro, listas, scroll): cielo nocturno;
  - zona grande y densa clara (rejilla del crafter): grises de casilla lavanda;
  - marcos finos (el del jugador en el inventario): como antes.
  Comprobado: los 7 menús que ya había siguen idénticos byte a byte. El lienzo usa ya el tamaño vanilla (villager.png es de 512x256).
- `polish.py`: hierro (piedra lunar) y oro (oro rosa), tótem y élitros. `gear.finish_tool()` se ha sacado de `tools()`
  para reutilizarlo (con diamante y netherita la salida es idéntica).
- `palette.py`: `cyc()` interpola en OKLab.
- Armadura de diamante puesta: rampa por rangos de tono (`crystal_worn`), con más contraste que antes, que se veía lavada en el juego.

## Túnica 3D EMF descartada (2026-10-08)
Al usuario le pareció muy mala (paneles de 1 px y bloques sueltos, aspecto tosco) y se ha retirado. El add-on ahora
es "Aurora Glow" y solo lleva los mapas emisivos de ETF. El código sigue en `emf.py` (`GEOMETRY = False`).
Un modelo 3D que quede bien tiene que hacerse a mano en Blockbench, o salir de un pack 3D cuya licencia permita
adaptarlo. No se puede copiar el trabajo de otro pack sin permiso.
`showcase.py` genera vistas previas de todo; el render 3D de la armadura usa el mapeo UV exacto de ModelPart.Cube.

## Armadura puesta v2 (2026-10-08)
Al usuario no le convencían las armaduras (sobre todo la netherita). `armor.py` ya no recolorea el ruido vanilla: pinta
placas por cara de caja, con cobertura propia (abertura de la cara con protector nasal, mangas hasta la fila 6, botas
desde la 7), contorno, ribete, una sola junta en el peto, cuello en V, rodilleras, remaches, cresta, gemas y paleta corta.
La netherita pasa de "túnica galáctica" a "noche aurora": placas índigo, ribetes iridiscentes, pocas estrellas y capa
de seda nocturna con dobladillo aurora. Antes y después en `previews/armor_antes_ahora.png`.
Ojo: `gear.hsh` tiene los bits bajos correlacionados por fila (pintaba rayas al hacer `% n`); `armor.py` usa su propio hash.

## Estado / pendiente
- Nada probado aún DENTRO del juego. Siguiente paso recomendado: activar ambos packs
  (Aurora Outline encima de Aurora Pack), comprobar capa, aura, borde y menús con capturas.
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

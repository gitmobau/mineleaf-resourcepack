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
  - `gear.py`  herramientas animadas, aura de encantamiento, armaduras (netherita en ópalo claro)
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
- (Quitado el 2026-10-10) Capa sin mods con `equipment/netherite.json` + capa `"wings"`: el usuario no la quiere.
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
- El creativo solo sobresale por la derecha (ver la 6ª parte) y su barra/caja de búsqueda van oscuras
  porque el juego escribe ahí en blanco. La baliza no lleva placas: sus textos son claros.
- Las placas de los títulos se pintan antes que casillas y decoraciones, así nunca tapan nada del juego.
- Supuestos de posiciones de títulos sin verificar en el jar para: yunque (60,6), herrería (44,15), telar y
  cartografía (y=4), aldeano (centrado + etiqueta del inventario en 107,72). Si un título queda fuera de su placa,
  se ajusta en `SCREENS`.

### Pantallas sin contenedor (sesión del 2026-10-08, 4ª parte)
- Con shader (Aurora HUD XL): libro de recetas (blit desde (1,1), soportado con `origin`) y selector de modo de juego
  (fondo translúcido conservado; casi llena su textura, 125 de 128, así que solo sobresale arriba/abajo). El motor también
  conserva huecos del fondo vanilla (alpha 0).
- Sin shader (Aurora Pack, `screens.py`): libro (cabe en los márgenes libres de su ventana de 192), carteles, fondos
  y separadores de menús, todos los widgets (mismos nine-slice, color solo según luminancia), tooltips y logo.
- No tocados a propósito: panoramas del título, logo de Mojang Studios, imágenes de Realms, toasts y barras de jefe.

### Barras de jefe y toasts (sesión del 2026-10-08, 5ª parte)
- Aurora Pack (`screens.py`): los 7 colores de barra en pastel (el progreso animado 16×2 ticks, 182×5 por frame) y toasts.
  Los toasts de recetas y tutorial siguen claros (el juego escribe en morado/negro); sistema y "sonando ahora"
  oscuros (texto blanco/amarillo).
- Aurora HUD XL (`hud_xl.py`): fondo de barra de jefe 182×5 → 198×11 (gemas dentro del margen, el progreso tapa el resto).

### Primera prueba en el juego (sesión del 2026-10-08, 6ª parte)
- Capturas del usuario: el truco del shader FUNCIONA (los marcos sobresalen y la mesa de encantamientos cuadra), así que
  el orden de vértices supuesto es correcto.
- Creativo: el juego dibuja el fondo entero y además vuelve a dibujar la zona de la rejilla recortando la misma textura
  en sus coordenadas vanilla. Con el dibujo desplazado (margen izquierdo) esa segunda pasada salía corrida 14 px.
  Regla: si una pantalla vuelve a recortar su textura, su zona vanilla debe quedarse en su sitio (solo márgenes a la
  derecha y abajo). El creativo ahora solo sobresale por la derecha. Si otra pantalla sale desplazada, igual.
- El usuario usa además un pack de modo oscuro (pestañas del creativo y caja de efectos negras, títulos en blanco):
  las placas de los títulos pasan a ser oscuras con borde claro.
- Logros: el usuario NO quiere que se toquen. Ventana de progresos y toast de progreso vuelven a vanilla.
- Netherita puesta: la "túnica galáctica" no gustaba nada. Ahora se recolorea la textura vanilla (y los élitros para la
  capa) con el estilo del icono: ciruela oscuro, contorno violeta, reflejos iridiscentes y algún destello.
- Versión 3D de la netherita hecha (ver Aurora EMF).

### Aurora EMF (sesión del 2026-10-09)
- Pack opcional para Entity Model Features 3.3.x (tiene versión 26.3 Fabric/NeoForge) + Entity Texture Features.
- Revisado en el código de EMF (github Traben-0/Entity_Model_Features, master): nombres `player_outer_armor`,
  `player_inner_armor`, `player_slim_*`, `elytra`; variantes sin .jem base permitidas por defecto (la 1 = vanilla);
  piezas `attach` = hijas de la parte vanilla, posicionadas con la fórmula del exportador de EMF; `rx` se asigna tal cual
  a xRot (positivo = la capa se abre hacia atrás); la propiedad `items=` de ETF mira armadura y manos.
- Sin verificar en el juego: que los pivotes de la armadura de la 26.3 sigan siendo los de HumanoidModel
  (cabeza/cuerpo 0,0,0; brazos ±5,2,0; piernas ±1.9,12,0) y el ala del élitro (5,0,0). Si algo sale desplazado, se
  corrige en `PIVOT` de `emf.py`.

### Sin capa y netherita clara (sesión del 2026-10-10)
- El usuario no quiere la capa: fuera la textura `wings/aurora_cloak.png` y la variante `elytra` de Aurora EMF.
  (El `equipment/netherite.json` que la activaba ya se había perdido sin querer al quitar la túnica galáctica.)
- Netherita puesta en ópalo claro: perla/lavanda, contorno lavanda, reflejos iridiscentes pastel; las muestras de EMF
  también pasan a tonos claros. Los iconos de netherita siguen como estaban (ciruela oscuro).

### Iconos a juego y 3D pulido (sesión del 2026-10-10, 2)
- Un solo pintor (`opal_paint` en `gear.py`) para iconos y armadura puesta: contorno donde acaba la placa, ribete
  iridiscente pastel justo dentro y metal perla en 4 tonos (`OPAL_TONES`) según el brillo vanilla suavizado + degradado
  de arriba a abajo. Se acabaron las manchas de colores al azar. Iconos: 12 frames, el ribete se desplaza y 3 destellos.
- Hombreras sin dientes sueltos de 1-2 px (las caras del brazo terminan en línea recta en la fila 25); `opal_clean()`
  quita píxeles colgando y rellena muescas.
- Aurora EMF rehecho: cresta escalonada iridiscente, alas de 4 plumas en los lados del casco, joya en la frente con
  engaste dorado, pecho con joya, cuello, espina dorsal y omóplatos; hombreras de tapa + 2 láminas + ribete + gema;
  cinturón que da la vuelta con hebilla; faldones de 2 láminas, placa lateral y rodillera con gema; punteras y alas
  en los tobillos. Nueva muestra `lame` (36,16,8,3), libre en la textura vanilla.
- Las "manchitas" raras que salían en el pecho de las vistas previas eran z-fighting del renderizador (cara del brazo
  coplanar con la del pecho), no de la textura: ahora usa LEQUAL como el juego.
- Prompt de traspaso para Codex en `PROMPT_CODEX.md`.

### Segunda prueba en el juego (2026-10-10)
- El 3D no salía: desde la 1.21.9 la armadura es un modelo por pieza (capas `player_helmet`, `player_chestplate`,
  `player_leggings`, `player_boots`) y EMF busca `<capa>.jem` con respaldo `helmet.jem`, etc. (EMFManager, rama
  `MC >= 12109`). Los `player_outer_armor*.jem` de antes se ignoraban. Ahora: `helmet2.jem`, `chestplate2.jem`,
  `leggings2.jem`, `boots2.jem` + sus `.properties`; validate.py rechaza los nombres viejos.
  `enforceOptifineVariationRequiresDefaultModel_v2` es false por defecto, así que las variantes sin .jem base valen.
- Captura del creativo con cristales a ambos lados y casillas corridas = el usuario tenía un Aurora HUD XL anterior al
  arreglo del 2026-10-08 (le dije que ese zip no había cambiado en la sesión; había que reinstalarlo igualmente).
- Tercera prueba: con solo los nombres genéricos (`helmet2.jem`...) el 3D seguía sin salir. La lista de modelos de EMF
  del usuario muestra `player_helmet.jem`, `player_slim_helmet.jem`, etc., así que ahora el pack trae también esos
  nombres exactos (sin depender del respaldo). Si aún no sale: pedir captura del detalle de `player_helmet.jem` en
  los ajustes de EMF, o activar "log model creation data" y mirar el log.

### Armas y objetos de combate (2026-10-10, codex/aurora-armas)
- Nuevo `extras.py`, ejecutado justo después de `icons.py`: 19 texturas estáticas en Aurora Pack
  (4 de arco, 6 de ballesta, maza, tótem, 4 capas de flechas, perla y 2 bases del escudo).
- Importa `cyc`, `mix`, `C`, `hsv`, `P`, `VIVID` y `crystal_px` de `gear.py`, sin modificarlo.
  Arco y ballesta usan una transformación por color vanilla independiente de la posición/estado para
  mantener la coherencia al tensar. Comprueba tamaño y canal alpha completo en cada textura.
- `tipped_arrow_head` queda perla casi neutra: el motor multiplica esa capa por el color de la poción.
  `tipped_arrow_base` lleva el astil lavanda. Se conservan modelos y tintes vanilla.
- Referencia comprobada: `atlases/shield_patterns.json` de `misode/mcmeta`, tag `26.3-assets`.
  Las bases están dentro de `textures/entity/shield/`, añadida a `FOLDERS` de `fetch_ref.py`.
  Los patrones de estandarte del escudo siguen vanilla; solo se repintan sus dos texturas base.
- Vista previa antes/después: `previews/extras.png`. Para instalar este cambio basta `dist/Aurora Pack.zip`.
- Verificado con Python 3.12 y Pillow 11.3.0 en Ubuntu: `validate.py` da `0 errors, 0 warnings`
  con glslangValidator; la emulación de los 27 menús pasa y dos builds completas dan MD5 idénticos
  en los cuatro ZIP. MD5 de Aurora Pack: `cd022d54d6d5acfae95bc8941a8d6c51`.
  Sus archivos anteriores son idénticos byte a byte; solo añade las 19 texturas. Vista previa revisada.
- Pendiente de comprobación visual dentro del juego; la lámina no sustituye una prueba del escudo con estandarte.

### Netherita celestial (2026-10-10, codex/aurora-aureola)
- Base: última rama de Claude al iniciar, `8ca123e`. El usuario confirma que el 3D anterior funciona en Fabric 26.3;
  no está determinado si era con Aurora EMF o Aurora EMF PRUEBA. Se generan ahora bases vacías explícitas y variantes 2
  para los 12 nombres (jugador normal, slim y respaldo genérico; 4 piezas): no depende de permitir variantes sin base.
- Sustituye placas, hombreras, faldones y casco por aureola (16 lados, grosor 0,22), estrella pequeña pulsante,
  anillo de cintura (0,18) y tobillos (12 lados, 0,17). Ciclo de giro 320 ticks, flotación 80 ticks, pulso 40 ticks.
- El padre mantiene la fórmula del exportador. Un anclaje estático cancela su traslación, y el efecto se anima en
  coordenadas locales. No animar el padre exportado: haría orbitar las piezas alrededor del desplazamiento de 24.
- Importante: `EMFJemData` solo recoge los bloques `animations` de los modelos principales; los destinos sí pueden
  ser descendientes. `emf.py` eleva los bloques a ese nivel. `cem_math.py` replica inversión de ejes y T*Rz*Ry*Rx*S,
  con un parser AST limitado a age/pi, sin/cos y operaciones aritméticas. No usa eval.
- `gear.py`: solo cambia netherita humanoide puesta y muestras EMF. Más del 92 % de las UV vanilla quedan con alpha 0;
  detalles opacos de un texel porque la armadura usa cutout. Iconos, herramientas, diamante y variantes animales intactos.
  `_e.png` repite únicamente los detalles luminosos y las muestras; configuración ETF `suffix.emissive=_e`.
- Reglas: `items.1=netherite_<pieza>` MÁS `nbt.1.equipment.<ranura>.id=minecraft:netherite_<pieza>`; fallback `models.2=1`.
  El filtro NBT evita que una pieza sostenida en la mano active adornos sobre armadura de otro material.
- PNG y GIF se renderizan leyendo los `.jem` emitidos. El GIF tiene 64 frames de 250 ms (16 s), paleta compartida y
  bucle completo. La noche es simulada: ETF da brillo completo, no luz sobre bloques ni bloom.
- `validate.py` conserva la comprobación de muestras fuera de las UV vanilla y valida recursivamente IDs, cajas,
  UV, destinos/expresiones, ranuras NBT, bases vacías, nombres actuales y máscaras emisivas. `test_celestial.py`
  comprueba pivotes, hueco bajo la aureola, tobillos, ciclo, bases y ubicación correcta de animaciones.
- Verificación: 7 pruebas pasan; dos builds completas con `0 errors, 0 warnings` (incluido glslangValidator),
  emulación de los 27 menús correcta y MD5 iguales para los cuatro ZIP y el GIF. PNG y fotogramas del GIF revisados.
  Aurora Pack: `e166cba18c94f0b0f807db392412cd13`; Aurora EMF: `cff1769c38a1b70fad157976538c08fb`.
  En el ZIP principal solo cambian las dos texturas humanoides de netherita; se añaden los dos `_e.png` y la
  configuración ETF. Todos los demás archivos previos son idénticos byte a byte. Las dos texturas dejan transparentes
  el 99,43 % y el 98,47 % de los texels de las cajas vanilla, respectivamente.

#### Fuentes verificadas para esta implementación
- EMF, commit `622a0cba8c2e3eeef896b5a9dbcb8d94600f3cd7`:
  [EMFManager: nombres de piezas](https://github.com/Traben-0/Entity_Model_Features/blob/622a0cba8c2e3eeef896b5a9dbcb8d94600f3cd7/src/main/java/traben/entity_model_features/EMFManager.java),
  [EMFPartData: submodelos e inversión](https://github.com/Traben-0/Entity_Model_Features/blob/622a0cba8c2e3eeef896b5a9dbcb8d94600f3cd7/src/main/java/traben/entity_model_features/models/jem_objects/EMFPartData.java),
  [EMFJemData: bloques de animación](https://github.com/Traben-0/Entity_Model_Features/blob/622a0cba8c2e3eeef896b5a9dbcb8d94600f3cd7/src/main/java/traben/entity_model_features/models/jem_objects/EMFJemData.java),
  [variables y funciones CEM](https://github.com/Traben-0/Entity_Model_Features/blob/622a0cba8c2e3eeef896b5a9dbcb8d94600f3cd7/.github/emf_animation.txt).
- ETF, commit `ba6dfecca69672b1b5e91ad5d4c8ae1a5c8476d2`:
  [configuración emisiva](https://github.com/Traben-0/Entity_Texture_Features/blob/ba6dfecca69672b1b5e91ad5d4c8ae1a5c8476d2/.github/README-assets/emissive.properties),
  [ItemProperty incluye manos](https://github.com/Traben-0/Entity_Texture_Features/blob/ba6dfecca69672b1b5e91ad5d4c8ae1a5c8476d2/src/main/java/traben/entity_texture_features/features/property_reading/properties/etf_properties/ItemProperty.java),
  [NBTProperty](https://github.com/Traben-0/Entity_Texture_Features/blob/ba6dfecca69672b1b5e91ad5d4c8ae1a5c8476d2/src/main/java/traben/entity_texture_features/features/property_reading/properties/optifine_properties/NBTProperty.java).
  `MixinRenderLayer` intercepta armorCutoutNoCull; `MixinModelPart` y la ruta de submit de 26.2+ mantienen emisivos.
  `ETFTexture` integra Animatica/MoreMcmeta, pero no se requiere ninguno: se animan geometría y colores estáticos.
- [Mojang 1.21.5: equipment también para armadura de jugadores](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-5).

## Estado / pendiente
- El 3D anterior funciona según la prueba del usuario. Pendiente probar este rediseño celestial dentro del juego.
  Sustituir Aurora Pack.zip y Aurora EMF.zip; desactivar Aurora EMF PRUEBA y duplicados. Probar cada pieza y equipos
  mixtos, netherita sostenida con hierro/diamante puestos, modelo slim, movimiento/agacharse, mirar arriba/abajo,
  emisivos en oscuridad y aspecto 2D con EMF desactivado. Mantener activa la actualización de variantes en EMF.
- Ideas pendientes ofrecidas: ajustar intensidad/velocidad de las animaciones.
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

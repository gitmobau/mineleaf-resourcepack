# Prompt para Codex: netherita "celestial" (aureolas en vez de armadura)

Pega el bloque entero en Codex con el repositorio abierto.

```text
Eres mi ayudante para el resource pack "Aurora" de Minecraft Java 26.3. Háblame en español.

CONTEXTO
- Repo gitmobau/mineleaf-resourcepack, carpeta aurora/ (no toques nada fuera). Parte de la última versión de la rama
  claude/kind-goodall-uskil5 y trabaja en una rama nueva: codex/aurora-aureola.
- Lee primero aurora/README.md, aurora/HANDOFF.md y aurora/PROMPT_CODEX.md (reglas del proyecto).
- Referencia vanilla: python3 aurora/scripts/fetch_ref.py ~/ref63
  Build completa: python3 aurora/scripts/build.py --ref ~/ref63 (genera, valida y crea aurora/dist/*.zip).
- La armadura 3D de netherita YA FUNCIONA en mi juego con Entity Model Features (EMF) + Entity Texture Features (ETF)
  en Fabric 26.3. Está en aurora/scripts/emf.py (pack "Aurora EMF") y las texturas en aurora/scripts/gear.py.
  En 26.x la armadura es un modelo por pieza: player_helmet, player_chestplate, player_leggings, player_boots
  (+ player_slim_* y los genéricos helmet/chestplate/leggings/boots de respaldo). NO uses player_outer_armor.
- Hubo dos packs en prueba: "Aurora EMF" (variantes: helmet.properties + helmet2.jem, sin helmet.jem) y
  "Aurora EMF PRUEBA" (los .jem como modelo base, siempre activos, sin .properties). No está confirmado cuál de los
  dos es el que funciona. Para no depender de eso: añade un .jem base "vacío" (las mismas partes con "attach": true
  y sin cajas) para que la variante 1 sea igual a vanilla y la 2 la de Aurora, con la regla "solo con la pieza de
  netherita puesta". Las demás armaduras (diamante, hierro...) no deben cambiar.

TAREA: rediseñar la netherita para que NO parezca una armadura
Quiero algo muy sencillo, elegante y "celestial": que parezca que el personaje lleva luz, no metal.
  1. Cabeza (casco): una AUREOLA flotando encima de la cabeza (anillo fino, separado de la cabeza, ligeramente
     inclinado), que gire despacio y suba y baje un poco. Alternativa si la aureola no queda bien: una corona fina
     de luz con 3-5 puntas pequeñas.
  2. Pecho (pechera): casi nada. Como mucho una pequeña estrella/gema flotando delante del pecho que late, o unas
     motas de luz orbitando alrededor del torso. Los brazos sin hombreras.
  3. Pantalones (grebas): un anillo de luz flotando alrededor de la cintura (tipo anillo de Saturno), fino y que gire.
  4. Botas: aros finos de luz en los tobillos, o unas alitas de luz muy pequeñas a los lados de los talones.
  5. La textura 2D (lo que se ve sin mods y lo que tapa al jugador): casi transparente. Que se vea la skin del
     jugador y solo queden detalles mínimos (líneas finas iridiscentes, una banda en la cintura, puños y tobillos),
     de forma que sin EMF siga siendo reconocible pero ligera. Los iconos de los objetos pueden quedarse como están o
     adaptarse a la idea (aureola/estrella), tú decides lo que quede mejor.
  Estética del pack: pastel iridiscente (cian, lavanda, rosa, melocotón, menta) con brillos blancos.

CÓMO HACERLO (investiga y confirma cada punto en el código/documentación de EMF y ETF antes de usarlo)
- Geometría: los anillos se construyen con cajas finas formando un polígono (8-16 lados) dentro de un submodelo
  propio, hijo de la parte vanilla (head, body, left_leg/right_leg). Coloca las cajas con la fórmula del exportador de
  EMF que ya usa emf.py (translate = (px, py-24, -pz), coordinates = (-mx-sx-px, -my-sy-(py-24), mz+pz, sx, sy, sz),
  invertAxis "xy"). Pivotes vanilla: cabeza/cuerpo (0,0,0), brazos (±5,2,0), piernas (±1.9,12,0).
- Movimiento: usa las animaciones de EMF en el .jem (formato OptiFine CEM: "animations": [{"parte.ry": "...",
  "parte.ty": "..."}], variables como age/time, funciones sin/cos). Giro lento (una vuelta cada varios segundos) y
  flotación suave. Que no se mueva con los brazos ni la cabeza de forma rara: la aureola puede ir en la cabeza,
  el anillo de cintura en el cuerpo.
- Brillo: comprueba si ETF admite texturas emisivas para la armadura (sufijo _e.png, p. ej.
  entity/equipment/humanoid/netherite_e.png) en 26.3. Si sí, haz que las aureolas brillen en la oscuridad.
- Textura animada: las texturas de armadura no admiten .mcmeta en vanilla. Investiga si ETF/EMF tienen alguna forma
  (si no, se puede simular con varias copias del anillo con distintos colores y animaciones "visible" que se
  alternan, o cambiando los colores con la rotación). Elige lo más simple que funcione.
- Muestras de color: emf.py usa EMF_SWATCHES de gear.py, pintadas en texels que ninguna caja vanilla usa;
  validate.py lo comprueba. Si haces la textura 2D casi transparente puedes reorganizar esas muestras, pero mantén
  la comprobación en validate.py (y amplíala para animaciones y submodelos si hace falta).
- Vista previa: emf.py tiene un renderizador propio (previews/emf_netherite.png). Amplíalo para dibujar los
  submodelos y las animaciones y genera también un GIF corto (previews/emf_netherite.gif) con la aureola girando.
- Si de verdad hiciera falta otro mod, dímelo antes y explícame por qué, pero intenta hacerlo solo con EMF + ETF.

NO TOQUES
- Los logros (ventana de progresos, toast, sprites): se quedan vanilla.
- La armadura de diamante, las herramientas, los menús de Aurora HUD XL ni los shaders.
- No vuelvas a poner la capa en la netherita.

ANTES DE TERMINAR
- validate.py debe dar "0 errors".
- Compila dos veces y comprueba que los md5 de aurora/dist/*.zip son iguales.
- Revisa la vista previa y el GIF, y actualiza README.md y HANDOFF.md (en español).
- Commit en español, push a codex/aurora-aureola y dime qué zips tengo que volver a copiar
  (seguramente Aurora Pack.zip y Aurora EMF.zip) y qué tengo que comprobar en el juego.
```

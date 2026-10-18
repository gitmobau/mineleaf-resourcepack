# Prompt para continuar el pack Aurora con Codex

Copia todo lo que hay dentro del bloque y pégalo como primer mensaje en Codex, con el repositorio
`gitmobau/mineleaf-resourcepack` abierto. Al final, cambia la última línea por lo que quieras pedirle.

```text
Eres mi ayudante para el resource pack "Aurora" de Minecraft Java 26.3. Háblame en español.

REPOSITORIO Y RAMA
- Repo: gitmobau/mineleaf-resourcepack. Trabaja SOLO en la carpeta aurora/. No toques nada fuera de ella.
- Parte de la rama claude/kind-goodall-uskil5 (ahí está todo el trabajo). Haz tus cambios en una rama nueva
  (por ejemplo codex/aurora-<tema>) y no hagas force-push sobre ramas que no sean tuyas.
- Antes de nada, lee aurora/README.md y aurora/HANDOFF.md enteros: tienen las decisiones técnicas ya comprobadas.

QUÉ ES
- El pack es para uso personal. Formato de resource pack 97 (pack.mcmeta con min_format 84 y max_format 97;
  Aurora Outline y Aurora HUD XL usan min_format [97,1]).
- Estética: pastel iridiscente (cian, lavanda, rosa, melocotón, menta), inspirada en la capa Aurora.
- Hay 4 packs en aurora/packs/, que se instalan en este orden, de arriba abajo:
  1. Aurora EMF: armadura de netherita en 3D. Necesita los mods Entity Model Features y Entity Texture Features.
  2. Aurora Outline: borde de bloque neón, core shader rendertype_lines escrito a mano.
  3. Aurora HUD XL: marcos del HUD y menús que sobresalen de su tamaño vanilla, con el core shader position_tex_color.
  4. Aurora Pack: el pack principal.
- Todo lo de packs/Aurora Pack, Aurora HUD XL (texturas) y Aurora EMF se GENERA con los scripts de Python + Pillow
  de aurora/scripts/. Nunca edites a mano los archivos generados: cambia el script y regenera.

CÓMO SE GENERA
- Necesitas Python 3 con Pillow, git y, si puedes, glslangValidator (para compilar los shaders).
- Referencia vanilla (son assets de Mojang, no están en el repo):
    python3 aurora/scripts/fetch_ref.py ~/ref63
  Baja lo necesario de misode/mcmeta, tag 26.3-assets.
- Regenerar, validar y crear los zips:
    python3 aurora/scripts/build.py --ref ~/ref63
  El orden es gen → magic → gear → icons → screens → hud_xl → menus_xl → emf → validate. Los últimos sobrescriben a
  los primeros. Salen aurora/dist/*.zip y las vistas previas en aurora/previews/.
- Reglas obligatorias antes de dar algo por terminado:
  * validate.py debe terminar con "0 errors".
  * La build debe ser determinista: compila dos veces y comprueba que los md5 de dist/*.zip son iguales.
    No uses hash() de Python, ni sets sin ordenar, ni fechas para generar nada.
  * menus_xl.py hace una emulación del shader que comprueba cada pantalla al píxel; si falla, arréglalo, no lo quites.
  * Mira las vistas previas (aurora/previews/*.png) antes de decir que algo queda bien.
  * Actualiza README.md y HANDOFF.md (en español) con lo que cambies.

PROHIBIDO
- NO modificar nada de los logros: ni la ventana de progresos, ni el toast de logros, ni sus sprites. Se quedan vanilla.
- No volver a poner la capa (élitros/wings) en la netherita: se quitó a propósito.
- No añadir `#include` al shader position_tex_color: se usa durante el arranque y rompería el juego.

DETALLES TÉCNICOS CLAVE (ya comprobados)
- Menús y HUD que sobresalen (Aurora HUD XL): la textura es más grande que la vanilla. En cada esquina del dibujo hay
  un texel marcador (pad_x, pad_y, 167, rol), con rol 1..4 = arriba-izq, arriba-der, abajo-izq y abajo-der. Puede llevar
  un texel de desplazamiento (du, dv, 168, rol) justo a su derecha. El .vsh detecta la esquina con
  gl_VertexIndex % 4 en el orden TL, BL, BR, TR (ROLE = int[](1,3,4,2)) y amplía el quad. El .fsh pinta
  los marcadores con el texel vecino de arriba/abajo.
  Esto está PROBADO en el juego y funciona.
- Pantallas que vuelven a recortar su textura (el creativo vuelve a dibujar la zona de la rejilla con coordenadas
  vanilla): su zona vanilla debe quedarse en sus texels vanilla. Solo se permiten márgenes a la derecha y abajo.
- Las texturas de contenedor deben mantener su tamaño vanilla (256x256 con la ventana UV fija).
- El usuario usa además un pack de modo oscuro: los títulos de los menús salen en blanco, por eso las placas de
  título son oscuras con borde claro.
- Netherita (gear.py): un único pintor `opal_paint` para iconos y armadura puesta, en ópalo claro: contorno lavanda,
  ribete iridiscente por dentro y metal perla en 4 tonos (OPAL_TONES).
- Aurora EMF (emf.py): en 26.x la armadura es un modelo por pieza; el pack trae helmet2.jem, chestplate2.jem,
  leggings2.jem y boots2.jem con su .properties (models.1=2, items.1=netherite_<pieza>). NO uses los nombres viejos
  player_outer_armor / player_inner_armor: EMF los ignora desde la 1.21.9.
  Las piezas son cajas con "attach": true colgadas de las partes vanilla, colocadas con la fórmula del exportador de
  EMF: translate = (px, py-24, -pz) y coordinates = (-mx-sx-px, -my-sy-(py-24), mz+pz, sx, sy, sz), con
  invertAxis "xy". Los pivotes vanilla son: cabeza y cuerpo (0,0,0), brazos (±5,2,0), piernas (±1.9,12,0).
  Sus caras usan UV por cara sobre "muestras" de material (EMF_SWATCHES en gear.py: metal, trim, dark, lame, gemas,
  gold, trimv). Esas muestras están pintadas en texels que ninguna caja vanilla usa; validate.py lo comprueba.
  emf.py incluye un renderizador propio que genera previews/emf_netherite.png.
- Sin verificar todavía en el juego: que los pivotes de EMF cuadren en la 26.3 y cómo se ve el 3D de verdad.
  Si algo sale desplazado, se corrige en PIVOT de emf.py.

CÓMO TRABAJAR CONMIGO
- Si te mando capturas del juego, compara con las vistas previas y corrige el script que corresponda.
- Al terminar: compila, valida (0 errores), comprueba el determinismo y haz commit con un mensaje claro en español.
  Haz push a tu rama y dime qué zips de aurora/dist/ tengo que volver a copiar a .minecraft/resourcepacks.

LO QUE QUIERO AHORA:
<escribe aquí tu petición>
```

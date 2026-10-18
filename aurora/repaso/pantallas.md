# Repaso: pantallas sin contenedor y menús base (`screens.py`, `magic.py`)

Objetivo: lo mismo de antes (pastel iridiscente), pero más calmado y legible. Comparativas antes/después en
`previews/repaso/pantallas/` (`widgets_tooltips_toasts.png`, `carteles.png`, `menus_base.png`, `hud_libro.png`),
con texto dibujado con la fuente vanilla y en los colores reales del juego (comprobados en el código de la 26.3).

## `screens.py`
- **Botones y widgets planos**: se quita el ruido de piedra vanilla (cada nivel de luminancia se ajusta al más
  frecuente de su alrededor) y cada nivel tiene un solo color. Sigue dependiendo solo de la luminancia, así que el
  nine-slice no cambia.
  - Normal: cuerpo lavanda violeta (98,82,164) → texto blanco con contraste ~6:1.
  - Resaltado: ya no es magenta chillón; cuerpo algo más claro (124,98,188) con borde perla rosado (como el borde
    blanco vanilla) → ~5:1.
  - Desactivado: gris violeta oscuro, texto 0xA0A0A0 ~5:1.
  - Flechas del libro con su propia rampa (lavanda / rosa al pasar el ratón) para que se vean sobre el papel.
- **Tooltips**: fondo ciruela oscuro plano (alpha vanilla 240). Antes llevaba un degradado vertical y, como el centro
  del nine-slice se repite, en tooltips altos salía una franja. Borde aurora más nítido (alpha 150).
- **Fondos de menú**: sin la cuadrícula de puntitos (estrellas) que se repetía en cada baldosa; velo violeta liso.
  Separadores: una línea lavanda suave en vez del arcoíris que se repetía cada 32 px.
- **Carteles (13 maderas, normales y colgantes)**: todas las tablas con la misma saturación pastel y claras
  (luminosidad 0.68 en maderas oscuras → 0.80 en roble pálido), conservando el tono y las vetas de cada madera.
  El texto negro por defecto y los tintes oscurecidos se leen en todas (antes roble oscuro, carmesí o mangle
  quedaban oscuros). Fuera los dos destellos blancos. Las cadenas de los colgantes se detectan solo si son grises
  (antes se comían la madera distorsionada, que es azulada).
- **Libro**: papel perla menos blanco, costura rosa suave, esquinas doradas más pequeñas; quitado el amuleto con
  estrella colgante. Se mantiene la cinta.
- **Toasts**: el de recetas sin destellos y con borde más suave. **Barras de jefe**: brillo más suave y más lento.

## `magic.py` (menús de Aurora Pack cuando HUD XL está apagado + sprites animados)
- Menús: panel perla liso (sin rayas diagonales), borde iridiscente suavizado, solo las 4 gemas de las esquinas
  (fuera las de los lados), casillas sin brillo diagonal, 5 destellos pequeños como máximo. Un solo gato: el
  dormido del inventario (fuera los de crafteo, hornos, cofre y shulker).
- **Bug arreglado**: el contorno negro vanilla se tomaba como la "ventana de noche" del jugador, así que había
  estrellas sueltas y una luna amarilla repartidas por todos los paneles. Ahora solo cuenta el negro de dentro del
  marco: el inventario tiene su cielo con aurora y luna, y los demás menús quedan limpios.
- Casilla resaltada: brillo perla solo dentro de los 16×16 del objeto y un aro iridiscente fino en el borde de la
  propia casilla. Antes el aro y el relleno invadían 2–3 px de las casillas vecinas (tapando sus objetos).
- Animaciones más tranquilas: hotbar (más perla, 6 destellos, frametime 5), selección (pulso suave), XP (brillo
  suave), fuego del horno (parpadeo leve), flecha del horno (degradado fijo con un destello que se desliza), botón
  del libro de recetas resaltado (sin destellos, más lento), casilla resaltada (frametime 4).
- No se ha cambiado ninguna función pública (`cyc`, `mix`, `C`, `build_container`, `find_slots`, `anim_meta`,
  `save`, `TITLE`, `inv_label`, `CAT_*`, `is_rgb`...). `build_container` acepta los mismos parámetros.

## Comprobado
- `build.py`: validador 0 errores (2 avisos: falta glslangValidator en esta máquina). Dos builds seguidas dan los
  mismos bytes en Aurora Pack y Aurora HUD XL.

## Riesgos / para mirar en el juego
- Los botones de altura distinta a 20 px siguen bien (color plano, sin degradado).
- El texto con tinta luminosa blanca/cian en el editor de carteles se lee peor sobre tablas claras (igual que en
  vanilla con abedul o roble pálido); se ha priorizado el texto oscuro, que es el normal.
- Con Aurora HUD XL activo, hotbar, selección, mano secundaria, fondos de barras de jefe y los 25 menús los pone
  HUD XL; de este repaso se ven ahí: widgets, tooltips, carteles, libro, toasts, casilla resaltada, fuego/flecha de
  hornos, XP y botón del libro de recetas.
- El botón del libro de recetas sigue siendo la cara de gato (identidad); si se prefiere que se entienda su
  función, se podría volver a un libro.

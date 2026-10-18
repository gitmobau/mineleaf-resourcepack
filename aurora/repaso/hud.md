# Repaso del HUD (icons.py + hud_xl.py)

Objetivo: un HUD tranquilo y legible (está siempre en pantalla), con la misma identidad pastel Aurora.
Comparativas: `previews/repaso/hud/corazones_antes_despues.png`, `hud_xl_antes_despues.png`, `hud_detalle_antes_despues.png`.

## Corazones y estrellas (`icons.py`, Aurora Pack)
- **Se acabó el arcoíris girando**: antes cada corazón recorría la paleta entera cada 1,6 s. Ahora cada estado es un
  degradado suave de dos tonos (arriba-izquierda más claro), reflejo perla en el píxel de brillo vanilla, borde inferior
  más profundo. Una familia de color por estado:
  normal rosa → lavanda · veneno lima-menta · wither gris ceniza-violeta · congelado azul hielo · absorción oro-melocotón ·
  montura perla-lavanda.
- **Hardcore** (el que usa el usuario): mismas tonalidades, las marcas hardcore vanilla en ciruela profundo (grabadas,
  no negras) y una costura perla entre ellas. Se distingue a simple vista del corazón normal sin chillar.
- **Wither legible**: antes el corazón marchito era casi del mismo color que el contenedor vacío (no se sabía cuánta vida
  quedaba). Ahora es gris ceniza con brillo claro, distinto del hueco vacío.
- **Contenedor vacío**: interior ciruela algo más claro (64,48,100) para que los huecos se lean de noche; contorno oscuro
  para fondos claros. Parpadeo: contorno casi blanco, como vanilla.
- **Medios corazones/estrellas**: misma lectura que vanilla (el corazón conserva la mitad izquierda, la estrella la derecha).
- **Animación**: 20 frames × 4 ticks = 4 s; solo los 2 primeros llevan un destello perla corto en el lóbulo izquierdo
  (y en el centro de la estrella). El resto son iguales y `optimize.py` los junta: casi estático.
- **Estrellas de comida**: oro-melocotón fijo (antes ciclaban rosa/lavanda/oro), punta perla; hambre en verde lima apagado.

## Aurora HUD XL (`hud_xl.py`)
- **Hotbar**: metal perla-lavanda con un tinte aurora muy lavado que deriva despacio (40 frames × 5 ticks = 10 s, antes
  arcoíris saturado cada 3,6 s). Quitados: la línea de brillo bajo la XP, el brillo que recorría el marco y las 8 gemas
  que sobresalían hacia la barra de XP. En cada separador queda un remache perla de 1 px.
- **Alas**: de 3 cristales arcoíris + estrellas a 2 cristales finos perla, metidos en el hueco de 7 px entre la mano
  secundaria y la hotbar: ya no tapan la casilla de la mano secundaria ni llegan a la columna de los corazones.
  Un solo destello lento en la punta una vez por ciclo.
- **Selección**: marco con iridiscencia pastel (más color que la hotbar, para que destaque sobre el perla), halo de 2 px
  que "respira" muy poco (4 s). Quitados la corona (en supervivencia la tapa la barra de XP), las puntas laterales, las
  esquinas y las 3 chispas que daban vueltas.
- **Mano secundaria**: una sola aguja fina en el lado exterior (antes aguja + esquirla + 2 estrellas).
- **Barras de jefe**: sin cambios de diseño (ya eran discretas); sus esquirlas usan el `crystal()` nuevo, algo más suave.
- Márgenes de los sprites (marcadores del shader) sin cambiar: mismo tamaño de textura, cero riesgo para el shader.

## Para el coordinador
- `menus_xl.py`/`menu_themes.py` importan de `hud_xl.py` `cyc, mix, C, OUT, WHITE, MARK, TX, PREVIEWS, AURORA, over,
  put, star`: no he tocado ninguno (mismo comportamiento). `crystal`, `halo` y `frame_recolor` sí cambian, pero solo los usa `hud_xl.py`.
- El README (líneas de `icons.py` y `hud_xl.py`) habla de "corona" y "aguja": si se actualiza, decir "corazones en
  degradado pastel con un destello sincronizado" y "hotbar perla con alas de cristal finas, selección iridiscente con halo".
- `magic.py` (de otro agente) sigue generando la hotbar/selección de Aurora Pack sin XL; no la he tocado.
- Build: 0 errores; dos builds seguidas dan los mismos MD5 en los 6 zips.
- A mirar en el juego: contraste de la selección con shaders (Complementary) y que el destello de los corazones no
  moleste; si molesta, basta con `GLINT = {}` en `icons.py` para dejarlos totalmente estáticos.

# Repaso: menús temáticos de Aurora HUD XL

Scripts: `scripts/menus_xl.py` y `scripts/menu_themes.py`. Cada menú conserva su tema; solo se ha calmado y
afinado. Las posiciones siguen exactas al píxel (la emulación del shader de `menus_xl.py` pasa en las 27 pantallas)
y la build es determinista. Comparaciones antes/después en `previews/repaso/menus/` (con objetos vanilla en las
casillas, como los verá con Faithful).

## Lo más importante: que los objetos se lean en las casillas
- Antes las casillas de los temas oscuros eran casi negras (carbón, netherita o tinta desaparecían) y las de las
  nubes casi blancas (papel, hueso, nieve o azúcar se perdían, y la rejilla apenas se veía).
- Ahora el interior de todas las casillas es un tono medio, como el gris 139 vanilla: lavanda en las nubes,
  violeta en el observatorio, ciruela en el horno, acero en la mesa de crafteo... Se leen bien los objetos
  claros y los oscuros.
- El brillito diagonal de cada casilla es más suave (0,25 → 0,12).

## Menos ruido
- Nuevo `motifs` por tema (antes siempre 10 adornos sueltos) y más separados entre sí. Sin adornos sueltos en
  mesa de crafteo, cartografía, telar y aldeano (se acabaron las "x" rojas y los rombos verdes por todo el fondo).
- Inventario: de ~300 puntitos blancos en el fondo a unos 30 estrellas tenues; fuera la fila de estrellitas
  de los bordes; aurora del fondo más suave. Se quedan las lunas y la rosa de los vientos.
- Mesa de crafteo: una sola cuadrícula de plano (cada 16 px), sin los círculos ni los tornillos del borde;
  4 engranajes de esquina (antes 5).
- Horno: en vez de una fila de llamas por todo el borde, una corona de 7 llamas en el centro bajo la aureola.
  Fuera las lenguas de fuego de los lados (dos tachuelas doradas cierran las esquinas de abajo). Flecha y
  llama vacías en ciruela suave en vez de casi negro.
- Alto horno: sin las grietas diagonales que cruzaban las casillas; 2 rejillas por lado (antes 4); casillas
  con borde cian menos chillón.
- Crafteador: unas pocas pistas de redstone en vez de una rejilla entera; sin antorchas en las esquinas;
  un pistón por lado.
- Telar: tejido fino y pocos hilos en vez del damero con líneas cada 16 px; banderines más espaciados;
  un carrete por lado.
- Baliza: sin las rayas arcoíris diagonales; un brillo suave en el centro, como el haz.
- Cartografía: sin la cuerda punteada de los lados; las rutas del mapa más suaves.

## Coherencia
- El ahumador ya es parte de la familia de nubes (misma rampa de colores, casillas y flechas lavanda); conserva
  su cielo, sus nubes de fondo y su emblema: una voluta de humo y una luna (antes 12 bocanadas).

## Legibilidad de textos
- Creativo: el juego escribe el nombre de la pestaña en gris oscuro (0x404040) arriba a la izquierda y sobre
  el violeta oscuro no se leía. Ahora el fondo es lavanda claro y la caja de búsqueda y la barra de
  desplazamiento quedan en violeta medio, porque la búsqueda se escribe en blanco (nuevo `grey_as_slot = False`).
- Revisado en el código de la 26.3: títulos y "Inventario" en 0x404040 (vaciados por `screens.py`, salvo
  caballo, nautilus, aldeano y pestañas del creativo, todos ya sobre fondo claro; un contenedor renombrado sí
  mostraría su nombre, y en alto horno o crafteador se leería poco), coste
  del yunque con su propia franja oscura, textos de la baliza en claro sobre su panel oscuro (sin cambios).

## Riesgos / por mirar en el juego
- Las casillas más oscuras en los temas de nubes cambian un poco el aire "todo blanco" que tenían; si el
  usuario lo prefiere más claro, basta subir el `WHITE` del `slot` de `Cloudy`.
- El creativo pasa de oscuro a claro: debería encajar mejor con las pestañas grises de Faithful, pero hay que verlo.

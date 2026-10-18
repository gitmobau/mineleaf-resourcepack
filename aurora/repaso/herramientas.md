# Repaso: herramientas, aura, brillo, armaduras e interfaz base (`gear.py`, `gen.py`)

Objetivo: lo mismo que había, pero más tranquilo y limpio. Comparativas en `previews/repaso/herramientas/`.

## Herramientas (`gear.py`)
- **Brillo mucho más tranquilo**: antes la franja de luz cruzaba la herramienta cada 1,6 s (casi siempre parpadeando)
  y había 3 destellos al azar (uno caía en el pomo de la espada en el primer fotograma). Ahora: una sola franja suave
  (50 % de blanco como máximo, el contorno apenas se ilumina) cada **7 s**, y un único destello suave a mitad de ciclo.
  Cada herramienta empieza en un momento distinto, así que la barra no "parpadea" toda a la vez.
  (El `.mcmeta` usa una lista `frames`: el fotograma quieto se queda 100+ ticks.)
- **Netherita más limpia**: el ruido del tramado vanilla se reduce a 4 tonos planos de ciruela-lavanda, con un
  contorno oscuro continuo alrededor de la cabeza y reflejos perla iridiscentes donde vanilla tiene el filo claro.
  Todas las herramientas de netherita quedan coherentes entre sí (antes el hacha salía clara y el pico oscuro) y se
  siguen distinguiendo de un vistazo del diamante (cristal claro). El mango es un poco más claro para leerse en fondos
  oscuros. Diamante: sin cambios de color.
- **Aura normal (encantado)**: de un anillo arcoíris intenso de ~3,6 px a un **halo suave pastel de ~2 px** que se
  desvanece, con dos chispitas suaves; animación interpolada y más lenta (fluye en vez de parpadear). Sin anillo nítido,
  para que se distinga de los niveles raro (anillo dorado) y legendario de `grimorio.py`. Que no se vea en la mano lo
  hace ahora `grimorio.py` (select por `display_context`); aquí no se ha tocado la estructura de `items/*.json`
  ni `aura_model()`.
- **Brillo de encantamiento (glint)**: tonos pastel con ~85 % de la luz del vanilla (antes ~130 % y con vetas blancas).
  Arreglo: faltaba su `.mcmeta` con `"blur": true`, así que salía pixelado; ahora va suave como en vanilla.
  Encaja mejor con el mod Enchantment Outlines.

## Armaduras
- Iconos de netherita: el ribete iridiscente se desplaza más despacio (12 fotogramas × 6 ticks, interpolado) y solo
  2 puntos brillan, más suaves. Iconos de diamante: mismo brillo tranquilo que las herramientas.
- Armadura puesta 2D (humanoide, bebé, caballo, nautilus): sin cambios (le gusta al usuario y Celestial la cubre).

## `gen.py`
- **Mira**: cruz fina del tamaño vanilla (9 px) con punto central y 1 px de hueco, puntas con un toque de cian /
  lavanda / rosa / melocotón. Sin los 4 puntos diagonales (hacían un "tablero" en el centro). Se tuvo en cuenta que el
  juego la pinta con mezcla INVERT: casi blanca = mismo contraste que vanilla en cualquier fondo.
- **pack.png**: cielo nocturno con dos cintas de aurora, estrellas y el pico de diamante Aurora con un brillo suave
  (antes un degradado turbio). `emf.py`/`celestial.py`/Extras copian este icono, por eso cambian también sus pack.png.
- Limpieza: se quitó el código muerto (barra, selección, mano secundaria, progreso de XP, inventario, resaltado de
  casillas y herramientas), que `magic.py`, `gear.py` y HUD XL sobrescribían siempre. El resto (indicadores de ataque,
  fondo de la barra de XP, `slot.png`, `pack.mcmeta`) sale idéntico byte a byte.

## Comprobado
- `build.py`: validador con 0 errores; dos builds seguidas dan un Aurora Pack idéntico (determinista).
- Sin probar en el juego. Mirar: que la franja de brillo y el destello se vean sutiles en mano y en la barra, el halo
  del aura en el inventario con luz baja, y la mira sobre cielo, hierba y cuevas.

## Nota para otros
- `grimorio.py` (niveles raro/legendario) llama a `gear.recolor_tool`; la netherita ahora devuelve los colores nuevos,
  pero su silueta (alpha) y la máscara `head` no cambian, así que sus auras siguen encajando.

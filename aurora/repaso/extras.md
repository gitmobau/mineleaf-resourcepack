# Repaso: Aurora Extras (`grimorio.py`, `hardcore.py`)

Comparaciones antes/después en `previews/repaso/extras/` (`auras.png`, `huevo.png`, `libro_y_particulas.png`).

## Auras por rareza
- **Solo como icono**: el `items/*.json` final es un `select` por `display_context`. En `gui`, `fixed` (marcos) y
  `on_shelf` (estanterías) va el árbol de auras. En el resto (primera y tercera persona, suelo, cabeza) va el modelo
  sin aura. El plano de 24×24 ya no tapa la pantalla al llevar la espada en la mano. El brillo de encantamiento sigue
  igual. Afecta también al aura normal de `gear.py` (la envuelvo yo).
- **Dorada (Reparación)**: un aro dorado de 1 px separado 1 px del objeto, con un relleno muy tenue. Lo recorre un
  reflejo lento y lleva 2 destellos que aparecen y se apagan. Así no choca con el contorno del mod Enchantment Outlines,
  que va pegado al borde.
- **Legendaria**: el mismo aro fino, pero en arcoíris pastel que fluye despacio alrededor del objeto. Lleva un halo
  exterior suave y 3 destellos con forma de estrellita de 4 puntas.
- Más lentas: 32 frames × 3 ticks (4,8 s por vuelta) y un pulso de solo ±10 % (antes era del ±28 %).
- Predicados: Filo/Castigo/Perdición y Eficiencia pasan de `levels: 5` a `{"min": 5}`, igual que Irrompibilidad.
- Compatibilidad con `gear.py`: busco el `condition has_component enchantments` en cualquier parte del árbol y
  sustituyo la referencia `item/aurora/aura_<item>` en su `on_true`. Si `gear.py` deja de usar ese nombre, el script
  falla con un `assert` (no se genera un pack roto en silencio). Los modelos de los tiers son míos (misma geometría
  -4..20 que el aura normal).
- **Nota para quien toque `gear.py`**: para que los tres niveles se distingan, el aura normal debería seguir siendo un
  halo suave, sin aro nítido. Si pasa a ser un aro arcoíris fino, se confundiría con la legendaria.

## Huevo del dragón
- Fuera las dos venas saturadas en zigzag, que en el juego se veían como rayas. Ahora es un cielo nocturno con
  degradado (violeta arriba, índigo abajo), una nebulosa muy tenue y una cortina de aurora suave: menta abajo,
  cian y lavanda en medio, rosa arriba, con pliegues verticales que se desplazan despacio. Lleva 5 estrellas
  tenues y cada una centellea una vez por vuelta.
- 32 frames × 4 ticks interpolados (6,4 s). `light_emission` baja de 10 a 8.

## Libro de la mesa y partículas
- Libro: cuero ciruela que conserva el grano vanilla, con un brillo iridiscente muy leve. Esquinas en oro pastel y
  páginas perla que conservan las líneas de texto en lavanda. Antes tenía un degradado azul-rosa plástico y las
  páginas eran planas.
- Letras mágicas: pasteles muy claros (paleta `P` + 20 % de blanco), porque el juego las oscurece al azar.
  Golpe encantado en lavanda claro y golpe crítico en melocotón claro, con el centro casi blanco.

## Limpieza
- Quitado el código muerto que nadie importa: `menus()`, `button()`, `level_icon()` y `sprites()` de `grimorio.py`,
  y `hearts()`, `hunger_armor()` y `recolor_icon()` de `hardcore.py` (también `import magic`).

## Qué mirar en el juego
- Aura dorada y legendaria en la hotbar, el inventario y un marco. Que **no** salga aura en primera ni en tercera
  persona, ni con el objeto tirado en el suelo.
- La lanza (spear) en la mano debe seguir con su modelo `_in_hand`.
- Huevo de noche, con y sin shaders (Iris).
- El zip de Extras pasa de unos 560 KB a unos 745 KB, porque las auras tienen el doble de frames.

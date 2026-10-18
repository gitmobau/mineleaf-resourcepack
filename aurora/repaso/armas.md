# Repaso: Armas Aurora (`scripts/extras.py`)

Objetivo: menos ruido y menos colores compitiendo, sin perder la paleta pastel iridiscente.
Comparaciones (vanilla / antes / ahora, en casilla clara y oscura, a 4x, 1x y 2x):
`previews/repaso/armas/arcos.png`, `magia.png`, `utilidad.png`, `escudo.png`.

## Qué cambia
- **Libro encantado fuera**: Aurora ya no sobrescribe `item/enchanted_book`; se ve el de *Enchanted Books: Re-covered*.
- **Rampas compartidas de 5 tonos** con el mismo contorno violeta que las herramientas de diamante/netherita
  (`OUT` de `gear.py`): madera lavanda, hilo celeste, metal perla (los tonos ópalo de la netherita), oro pastel,
  rosa y menta. Se acabaron el arcoíris por píxel (maza, perla, escudo) y el lavado a blanco (vara y polvo de
  blaze, manzana, pincel, cuerda...).
- **Arco y ballesta**: madera lavanda en 4 tonos (la culata de la ballesta más oscura que los brazos, ya no es
  un damero blanco); la cuerda es celeste suave en vez de blanca, se ve sobre fondo oscuro pero no compite con
  la madera. El pintor solo mira el color vanilla, así que los 4 + 6 estados siguen coherentes.
- **Flechas**: normal con punta y plumas celestes; espectral en oro pastel (como en vanilla); con poción igual que antes.
- **Maza**: cabeza de metal perla y mango violeta, sin manchas de colores.
- **Tótem, manzana dorada, flecha espectral, vara/polvo de blaze y catalejo**: el mismo oro pastel
  (sombra ciruela → miel → crema); ojos del tótem y hoja en menta.
- **Pintor genérico**: el tono sale del brillo percibido (no del valor HSV), y las sombras conservan la
  saturación en vez de mezclarse con violeta (que daba barro). Perla de ender y ojo vuelven a ser verde-azulados
  (se reconocen al instante); los rojos (cohete, tijeras) usan el rosa de la ballesta cargada.
- **Escudo**: tablas de madera lavanda y borde de metal perla; la zona del estandarte queda casi blanca.

## Riesgos / notas
- Se reutiliza `gear.OPAL_TONES` con un valor de respaldo si el otro agente lo renombra.
- La perla de ender y el fragmento de eco quedan algo oscuros sobre casilla oscura (igual que en vanilla).
- No probado dentro del juego; validador: 0 errores.

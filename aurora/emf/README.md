# Aurora Glow (antes "Aurora EMF")

Add-on opcional que hace que brillen en la oscuridad los ribetes de la túnica de netherita, el borde de la capa y,
de forma más suave, la armadura de diamante. Usa los mapas emisivos `_e` del mod
**Entity Texture Features (ETF)** para la 26.3. Sin ETF no hace nada.

Instalación: ponlo **encima** de Aurora Pack en la lista de packs (ETF solo usa un `_e` de un pack igual o superior al de la
textura base).

Sin verificar en el juego: es probable que las piezas encantadas sin trim no brillen, porque la 26.3 las dibuja con
un render type de glint que ETF no intercepta.

## Túnica 3D (descartada)
La primera versión traía modelos `.jem` de EMF: falda con vuelo, mangas acampanadas y capucha con punta. Quedaba
tosca y se retiró. El generador sigue en `scripts/emf.py` detrás de `GEOMETRY = False`, con las notas técnicas
verificadas (nombres de modelo `<portador>_<pieza>.jem` en `assets/minecraft/optifine/cem/` y el truco de
`.properties` con `nbt.1.equipment.<slot>.id` para activarlo solo con netherita). Un modelo que quede bien hay que
hacerlo a mano en Blockbench.

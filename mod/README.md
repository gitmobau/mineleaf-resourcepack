# Aurora Guía — mod de Fabric para Minecraft Java 26.3

Ayudas **solo de cliente y solo de lectura**: miran el juego y te enseñan información. No cambian costes,
objetos ni reglas, así que no alteran ninguna mecánica vanilla.

| Qué | Dónde | Detalle |
|---|---|---|
| **Yunque inteligente** | Panel a la derecha del yunque (con el fondo de los tooltips del pack) | Aviso si **al revés** sale más barato (mismo resultado, contando la durabilidad), penalización con la que queda el resultado y el **orden más barato** para ponerle los libros útiles que llevas en el inventario (hasta 8) y el que tengas en el yunque. Deja fuera los libros que no aportan, los que no caben por debajo de 40 y, entre alternativas (Filo / Castigo), la de uso general o **la que hayas puesto en el yunque**. Dice cuántos niveles te faltan. |
| **Lo que le falta** | Tooltip | Penalización de yunque (solo si ya ha pasado por uno). En objetos encantados: "✦ Encantamientos completos" o "Mayús: le faltan N"; con **Mayús**, la lista (también en objetos sin encantar). Los que se excluyen entre sí salen como alternativas ("A / B"); sin maldiciones ni Espinas. |

Capturas hechas dentro del juego real con `runClientGameTest`: [`previews/`](previews/).

No dibuja nada en la pantalla normal de juego: solo el panel del yunque (y solo con algo en la casilla izquierda)
y unas líneas en los tooltips.

## Instalar
1. Fabric Loader 0.19.5 o superior para la 26.3 y **Fabric API** 0.162.0+26.3.
2. Copia `dist/aurora-guia-1.2.1.jar` en `.minecraft/mods`.

## Compilar
Necesita JDK 25.
```bash
./gradlew build             # jar en build/libs/
./gradlew test              # tests de la lógica del yunque (mismos casos que encantamientos/yunque.py)
xvfb-run -a -s "-screen 0 1280x720x24 +extension GLX +render -noreset" ./gradlew runClientGameTest
```
El último arranca el juego de verdad (con renderizado por software en un servidor sin pantalla), crea un mundo
hardcore, activa `aurora/packs/Aurora Pack` y saca capturas de todo en
`build/run/clientGameTest/screenshots/`.

## Cómo está hecho
- `anvil/AnvilMath.java`: copia exacta de `AnvilMenu.createResult` de la 26.3 (comprobada contra el código
  descompilado) para encantar, más los +2 de durabilidad al juntar dos iguales; el renombrado y la reparación
  con material no hacen falta (el panel lee la penalización del resultado real). El planificador es programación
  dinámica exacta sobre subconjuntos que elige el subconjunto de libros más completo y luego el más barato.
  No depende de Minecraft, por eso tiene tests de JUnit.
- El plan se calcula en un hilo de fondo con una copia congelada de las reglas, así que nunca da tirones.
- `anvil/McAnvil.java`: traduce `ItemStack` y el registro de encantamientos sincronizado al modelo de arriba.
- `anvil/AnvilOverlay.java`, `tooltip/GuiaTooltip.java`: lo que se dibuja.

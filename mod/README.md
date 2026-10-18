# Aurora Guía — mod de Fabric para Minecraft Java 26.3

Ayudas **solo de cliente y solo de lectura**: miran el juego y te enseñan información. No cambian costes,
objetos ni reglas, así que no alteran ninguna mecánica vanilla.

| Qué | Dónde | Detalle |
|---|---|---|
| **Yunque inteligente** | Panel a la derecha del yunque | Coste de lo que tienes puesto, aviso si al revés sale más barato, penalización con la que queda el objeto y el **orden más barato** para ponerle todos los libros útiles que llevas en el inventario (hasta 8). Nunca propone un paso de 40 o más. |
| **Lo que le falta** | Tooltip de cualquier objeto con durabilidad o libro encantado | Usos de yunque y penalización. Con **Mayús**: encantamientos que le faltan o que no están al máximo. Los que se excluyen entre sí salen como alternativas ("A / B"). |

Capturas hechas dentro del juego real con `runClientGameTest`: [`previews/`](previews/).

No dibuja nada en la pantalla normal de juego: solo el panel del yunque y unas líneas en los tooltips.

## Instalar
1. Fabric Loader 0.19.5 o superior para la 26.3 y **Fabric API** 0.162.0+26.3.
2. Copia `dist/aurora-guia-1.1.0.jar` en `.minecraft/mods`.

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
  descompilado) sin durabilidad ni renombrado, y el planificador por programación dinámica sobre subconjuntos.
  No depende de Minecraft, por eso tiene tests de JUnit.
- `anvil/McAnvil.java`: traduce `ItemStack` y el registro de encantamientos sincronizado al modelo de arriba.
- `anvil/AnvilOverlay.java`, `tooltip/GuiaTooltip.java`: lo que se dibuja.

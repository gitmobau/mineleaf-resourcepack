# Repaso: Aurora Guía 1.2.0 (mod de Fabric)

Objetivo: más útil, más bonito y más limpio, sin tocar ninguna mecánica (sigue siendo solo de cliente y solo de
lectura; no envía nada al servidor).

## Panel del yunque
- **Aspecto**: usa el mismo fondo y marco que los tooltips (`tooltip/background` y `tooltip/frame`), así que con
  Aurora Pack sale morado con el borde lavanda del pack y sin él parece un tooltip vanilla. Se ajusta al ancho
  del texto, con una línea fina separando "lo que tienes puesto" del plan.
- **Sitio**: a la derecha del yunque, dejando 16 px libres para los adornos de Aurora HUD XL (el yunque XL
  sobresale 14 px por cada lado). Si no hay sitio, se pega más y, como último recurso, se encoge. Arriba a la
  altura del yunque, sin salirse de la pantalla.
- **Pantalla limpia**: no aparece con la casilla izquierda vacía ni con objetos que no se pueden encantar
  (renombrar una etiqueta, por ejemplo).
- **Fuera la línea "= N niv."**: el juego ya enseña el coste debajo; repetirlo solo ocupaba sitio.
- **"¡Ponlos al revés!"** solo cuando al revés el resultado es *el mismo* (antes podía recomendarlo aunque
  cambiara qué encantamiento se queda: Filo/Castigo) y contando los +2 de durabilidad (solo se cobran si el de la
  izquierda está dañado). Solo con dos objetos iguales con durabilidad o dos libros, como el juego.
- **Penalización después**: se lee del resultado real del yunque, así que es exacta también al reparar con
  material o al renombrar.
- **Plan**: líneas de texto con el coste alineado a la derecha: `1. Afilado V + Botín III   3`,
  `2. Espada de diamante + (1)   14`... Los pasos anteriores van como `(1)`.
  - Elige **qué libros usar**, no solo en qué orden: deja fuera los que no aportan (un tercer Filo IV), los que no
    caben por debajo de 40 y, entre alternativas que se excluyen, la de uso general (Filo antes que Castigo,
    Protección antes que las otras) **o la que hayas puesto en la casilla derecha**: así decides tú.
  - Los que se quedan fuera y aportarían algo salen en "Sin usar: ...".
  - Libros con varios encantamientos: ya no se descartan si uno no le sirve (el yunque lo ignora gratis).
  - Libros con maldición que se aplicaría: nunca se proponen.
  - Si el objeto de la izquierda es un libro o un montón de más de 1, no hay plan (el juego cobraría 40).
  - "Te faltan N niveles" si no te llega la experiencia (en hardcore importa).
- **Rendimiento**: el panel solo se recalcula cuando cambia algo (comparando los objetos, sin crear cadenas
  cada frame) y el plan se calcula en un hilo de fondo con una copia congelada de las reglas, así que 8 libros
  no dan tirones; mientras tanto pone "Calculando…" (dura una fracción de segundo).

## Tooltip
- La penalización de yunque **solo** sale si el objeto ya ha pasado por un yunque ("Penalización de yunque:
  7 (3 usos)"), en gris, dorado o rojo según lo grave. Antes ponía "Yunque: sin usar" en todo lo que tenía
  durabilidad.
- "✦ Encantamientos completos" y "Mayús: le faltan N" solo en objetos ya encantados; con Mayús la lista sale en
  cualquier objeto encantable (también sin encantar). Nada en objetos que no admiten encantamientos.
- Se calcula una vez por objeto y se recuerda mientras sigues encima (antes se recalculaba cada frame).

## Lógica (`AnvilMath`) y tests
- Revisado contra `AnvilMenu.createResult` descompilado de la 26.3: igual en niveles, incompatibles (+1 y no se
  aplica), "se cobra el nivel final aunque no suba", máximo de nivel, libro + libro y objeto sobre libro (nada).
- Nuevo: `durabilityFee` (+2 de durabilidad), `gain`/`candidates` (qué libros considerar), `value` (lo completo
  que queda), `freeze` (reglas en tablas para el hilo de fondo), elección del mejor subconjunto en `optimize`
  y poda de estados dominados (misma combinación con más penalización y más coste).
- 11 tests nuevos de JUnit (20 en total): durabilidad, libro + libro, objeto sobre libro, nivel por encima del
  máximo, tercer libro inútil, alternativas (y la del yunque manda), libros que no caben por debajo de 40,
  maldiciones, orden de candidatos, nada que mejorar, 8 libros y reglas congeladas.

## Capturas
`mod/previews/`: `yunque_plan.png` (escala 2), `yunque_plan_escala3.png` (escala 3, poco sitio: el texto se
parte con sangría francesa bajo el número del paso), `yunque_al_reves.png` y `tooltip_le_falta.png`, hechas con
`runClientGameTest`. Se quitan `diario.png` y `hud_diario_huevo.png`, que enseñaban el diario ya eliminado.

## Lo que no cambia
Nada en la pantalla normal de juego (sin HUD), ningún coste ni objeto, ningún paquete al servidor.

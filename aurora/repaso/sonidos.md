# Repaso: sonidos (`scripts/sonidos.py`)

Objetivo: sonidos más bonitos, suaves y elegantes, sin clics, sin estridencias y con un volumen parecido al de los
vanilla a los que sustituyen. Siguen siendo 4 eventos (`replace: true`, con subtítulos) en `sounds/aurora/*.ogg`,
mono 44,1 kHz Vorbis, y la build sigue siendo determinista (dos builds seguidas dan los mismos bytes, zips incluidos).

## Qué estaba mal (medido, no a oído)
- **Volumen**: las tres de encantar sonaban unos **12 dB más fuertes** que las vanilla (máx. momentáneo −11 frente a
  −23,5 LUFS). El orbe, unos 2,5 dB más fuerte y sonando cada dos por tres.
- **Clics**: cada campanilla se cortaba de golpe al terminar su buffer (orbe a 0,35 s, encantar a ~1,4 s). Se ven como
  puntos verticales en el espectrograma (`previews/repaso/sonidos/antes.png`) y el detector de clics los marca
  (+36 dB en el orbe). El yunque empezaba con un chasquido de ruido blanco a plena escala.
- **Brillo áspero**: `enchant3` tenía el 43 % de su energía en 2–5 kHz (la zona más molesta para el oído); los
  destellos llegaban a 9–10 kHz (al subirles el tono el juego llega al límite y aparece aliasing).
- **Colas largas y sucias**: subir de nivel duraba 2,8 s; la reverb era ruido blanco plano (cola brillante, "siseo").

## Qué se ha cambiado
- **Motor común**: parciales con ataque en coseno, decaimiento propio por parcial (los agudos se apagan antes, como
  en un objeto golpeado de verdad) y fundido a cero siempre; `mix()` dimensiona el buffer para que nada se corte;
  "gemelo" desafinado unos cents para el batido lento de una campana o una barra de metal.
- **Sala sintética oscura**: respuesta al impulso en la que los agudos mueren antes que los graves, entrada suave
  tras el predelay y sin graves retumbantes. Colas cortas (0,3–1,1 s) porque el juego, Enhanced Audio o Sound
  Physics ya ponen su propia sala.
- **Mastering**: paso alto a 90 Hz, paso bajo a 9,5 kHz (nada por encima de 11 kHz en la síntesis), normalización
  por sonoridad K-ponderada (ITU-R BS.1770, máximo momentáneo de 400 ms) con techo de −1 dBFS, cola recortada
  a −52 dB y fundida.
- **Encantar (3 variantes)**: un soplo de aire (homenaje al "whoosh" vanilla) y un arpegio ascendente de
  vibráfono/celesta que florece en su última nota, con trémolo suave. Las tres son de la misma familia
  (Do mayor): Cmaj9, Am9, Fmaj9. Registro medio (Do5–Re6), sin agudos punzantes.
- **Yunque (ahora 2 variantes)**: tres golpes como el vanilla (tin-tin-tiin), pero sobre una barra de acero
  "dulce": modos inarmónicos reales de barra libre (×2,756, ×5,404, ×8,933) que se apagan rápido, un toque de
  cuerpo grave y un roce de contacto filtrado en vez del chasquido. Se quita el `volume: 0.5` y se ajusta el
  nivel en el propio archivo.
- **Subir de nivel**: Sol-Do-Mi rápido que aterriza en un acorde de Do mayor de cristal con un pequeño destello
  ascendente. 1,7 s en vez de 2,8 s.
- **Orbe (ahora 3 variantes)**: gota de cristal casi pura (Mi6, Sol6, Re6) con ataque de 3 ms, un leve
  deslizamiento de tono al principio y 0,4 s en total. El juego ya le cambia el tono (×0,55–1,25) y lo pone a
  volumen 0,1; tiene que ser corto, redondo y discreto para no cansar.

## Medidas (máx. momentáneo K-ponderado ≈ LUFS; mismo volumen de `sounds.json`)
| Evento | Vanilla | Antes | Ahora | Duración antes → ahora | 2–5 kHz antes → ahora |
|---|---|---|---|---|---|
| Encantar | −23,5 | −11,0 | **−23,5** | 2,3–2,4 s → 1,8 s | 6–43 % → <1 % |
| Yunque (efectivo, con volumen) | −16,4 | −20,9 | **−17,5** | 1,3 s → 1,3–1,4 s | 4 % → 2–4 % (ataque más metálico: 1–2 kHz 13–24 %) |
| Subir de nivel | −13,6 | −12,0 | **−14,5** | 2,8 s → 1,7 s | 7 % → 1,5 % |
| Orbe | −18,0 | −15,6 | **−20,0** | 0,45 s → 0,4 s | 11–17 % → <1 % |

Picos: todos ≤ −3 dBFS (antes −1,3 a −1,6). Clics por corte: 0 (antes en todos los de campanilla). Lo que aún marca
el detector de transitorios son los inicios de nota y los golpes del yunque, que son intencionados.

Imágenes: `previews/repaso/sonidos/antes.png` y `despues.png` (forma de onda + espectrograma 0–11 kHz).
`previews/preview_sonidos.png` lo regenera la build con el mismo formato.

## Riesgos / notas
- No se ha podido escuchar: todo se ha decidido por diseño y medidas. Si en el juego el encantamiento se queda
  corto de volumen, basta con subir `TARGET['enchant']` 2–3 dB.
- Los archivos cambian de nombre (`anvil_use` → `anvil_use1/2`, nuevo `orb3`); `sounds.json` ya apunta a ellos y
  `build.py` copia `sounds/aurora/*` a Aurora Extras sin cambios.

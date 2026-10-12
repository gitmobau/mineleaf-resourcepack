# Encantamientos y yunques — Minecraft Java 26.3

Referencia para MINELEAF. Los números de encantamientos, tags y comercios salen de los datos vanilla de la
26.3 ([misode/mcmeta](https://github.com/misode/mcmeta), tags `26.3-data` y `26.3-summary`). Lo que no
está en datos (fórmulas del yunque y de la mesa) es la lógica del código de `AnvilMenu` y
`EnchantmentHelper`, que no ha cambiado de forma desde la 1.21.

`yunque.py` calcula el orden de combinación más barato para un objeto y una lista de libros
(ver [Calculadora](#calculadora)).

## 1. Los 43 encantamientos

Desde la 1.21 los encantamientos son datos (`data/minecraft/enchantment/*.json`), así que un datapack del
servidor puede cambiar cualquier número de esta tabla.

- **Mult. yunque** = `anvil_cost`. Si viene de un **libro** se usa `max(1, anvil_cost / 2)`.
- **Peso** = probabilidad relativa en la mesa, el botín y los aldeanos (10 común, 5, 2, 1 muy raro).
- **Coste mesa** = rango de "nivel modificado" de la mesa en el que sale el nivel I (`base`) y cuánto sube
  por nivel extra.
- **T** = tesoro: no sale en la mesa de encantamientos.

| Encantamiento | Máx | Peso | Mult. objeto / libro | Coste mesa nivel I (+ por nivel) | Objetos | Excluye a |
|---|---|---|---|---|---|---|
| Protección | IV | 10 | 1 / 1 | 1–12 (+11) | armadura | protecciones |
| Protección contra el fuego | IV | 5 | 2 / 1 | 10–18 (+8) | armadura | protecciones |
| Protección contra explosiones | IV | 2 | 4 / 2 | 5–13 (+8) | armadura | protecciones |
| Protección contra proyectiles | IV | 5 | 2 / 1 | 3–9 (+6) | armadura | protecciones |
| Espinas | III | 1 | 8 / 4 | 10–60 (+20) | armadura (en mesa solo peto) | — |
| Respiración | III | 2 | 4 / 2 | 10–40 (+10) | casco | — |
| Afinidad acuática | I | 2 | 4 / 2 | 1–41 | casco | — |
| Caída de pluma | IV | 5 | 2 / 1 | 5–11 (+6) | botas | — |
| Agilidad acuática | III | 2 | 4 / 2 | 10–25 (+10) | botas | Paso helado |
| Paso helado (T) | II | 2 | 4 / 2 | 10–25 (+10) | botas | Agilidad acuática |
| Velocidad de alma (T) | III | 1 | 8 / 4 | 10–25 (+10) | botas | — |
| Sigilo rápido (T) | III | 1 | 8 / 4 | 25–75 (+25) | grebas | — |
| Filo | V | 10 | 1 / 1 | 1–21 (+11) | espada, lanza, hacha (en mesa sin hacha) | daño |
| Castigo | V | 5 | 2 / 1 | 5–25 (+8) | espada, lanza, hacha, maza (mesa: espada/lanza) | daño |
| Perdición de los artrópodos | V | 5 | 2 / 1 | 5–25 (+8) | igual que Castigo | daño |
| Empuje | II | 5 | 2 / 1 | 5–55 (+20) | espada, lanza | — |
| Aspecto ígneo | II | 2 | 4 / 2 | 10–60 (+20) | espada, lanza, maza (mesa: espada/lanza) | — |
| Botín | III | 2 | 4 / 2 | 15–65 (+9) | espada, lanza | — |
| Filo arrasador | III | 2 | 4 / 2 | 5–20 (+9) | espada | — |
| Embestida (`lunge`) | III | 5 | 2 / 1 | 5–25 (+8) | lanza | — |
| Eficiencia | V | 10 | 1 / 1 | 1–51 (+10) | hachas, picos, palas, azadas, tijeras | — |
| Toque de seda | I | 1 | 8 / 4 | 15–65 | hachas, picos, palas, azadas | Fortuna |
| Fortuna | III | 2 | 4 / 2 | 15–65 (+9) | hachas, picos, palas, azadas | Toque de seda |
| Irrompibilidad | III | 5 | 2 / 1 | 5–55 (+8) | todo lo que tiene durabilidad | — |
| Reparación (T) | I | 2 | 4 / 2 | 25–75 (+25) | todo lo que tiene durabilidad | Infinidad |
| Poder | V | 10 | 1 / 1 | 1–16 (+10) | arco | — |
| Retroceso (`punch`) | II | 2 | 4 / 2 | 12–37 (+20) | arco | — |
| Fuego (`flame`) | I | 2 | 4 / 2 | 20–50 | arco | — |
| Infinidad | I | 1 | 8 / 4 | 20–50 | arco | Reparación |
| Multidisparo | I | 2 | 4 / 2 | 20–50 | ballesta | Perforación |
| Perforación | IV | 10 | 1 / 1 | 1–50 (+10) | ballesta | Multidisparo |
| Carga rápida | III | 5 | 2 / 1 | 12–50 (+20) | ballesta | — |
| Empalamiento | V | 2 | 4 / 2 | 1–21 (+8) | tridente | daño |
| Lealtad | III | 5 | 2 / 1 | 12–50 (+7) | tridente | Propulsión acuática |
| Canalización | I | 1 | 8 / 4 | 25–50 | tridente | Propulsión acuática |
| Propulsión acuática (`riptide`) | III | 2 | 4 / 2 | 17–50 (+7) | tridente | Lealtad, Canalización |
| Densidad | V | 5 | 2 / 1 | 5–25 (+8) | maza | daño |
| Brecha | IV | 2 | 4 / 2 | 15–65 (+9) | maza | daño |
| Carga de viento (T) | III | 2 | 4 / 2 | 15–65 (+9) | maza | — |
| Suerte marina | III | 2 | 4 / 2 | 15–65 (+9) | caña de pescar | — |
| Atracción (`lure`) | III | 2 | 4 / 2 | 15–65 (+9) | caña de pescar | — |
| Maldición de ligamiento (T) | I | 1 | 8 / 4 | 25–50 | armadura, élitros, cabezas, calabaza | — |
| Maldición de desaparición (T) | I | 1 | 8 / 4 | 25–50 | durabilidad + brújula, cabezas, calabaza | — |

Grupos exclusivos (`tags/enchantment/exclusive_set`):

- **protecciones**: Protección, Fuego, Explosiones, Proyectiles (solo una).
- **daño**: Filo, Castigo, Perdición, Empalamiento, Densidad, Brecha.
- Fortuna ↔ Toque de seda · Infinidad ↔ Reparación · Multidisparo ↔ Perforación ·
  Paso helado ↔ Agilidad acuática · Propulsión ↔ Lealtad y Canalización (Lealtad + Canalización sí van juntas).

Notas:
- La columna "Objetos" es `supported_items` (yunque). La mesa usa `primary_items` cuando existe; por eso el
  hacha no saca Filo en la mesa, Espinas solo sale en petos y Aspecto ígneo no sale en la maza.
- Élitros y escudo no tienen `enchantable`: no se encantan en la mesa, solo con libros en el yunque.
- Tags útiles: `treasure` (Ligamiento, Desaparición, Sigilo rápido, Velocidad de alma, Paso helado,
  Reparación, Carga de viento), `in_enchanting_table` = `non_treasure`, `tradeable` = `non_treasure` +
  Ligamiento, Desaparición, Paso helado y Reparación. Sigilo rápido, Velocidad de alma y Carga de viento
  **no** se pueden comprar a aldeanos: Sigilo rápido sale de cofres de ciudad antigua, Velocidad de alma de
  bastiones y trueque con piglins, y Carga de viento de las cámaras de prueba (vault ominoso).

## 2. Mesa de encantamientos

**Encantabilidad** (componente `minecraft:enchantable`):

| Valor | Objetos |
|---|---|
| 25 | armadura de oro |
| 22 | herramientas y armas de oro |
| 15 | madera, netherita (todo), cuero, maza |
| 14 | herramientas y armas de hierro |
| 13 | herramientas y armas de cobre |
| 12 | cota de malla |
| 10 | diamante (todo) |
| 9 | armadura de hierro, caparazón de tortuga |
| 8 | armadura de cobre |
| 5 | piedra |
| 1 | libro, arco, ballesta, tridente, caña de pescar |

**Estanterías**: cuentan las que estén a 2 bloques de la mesa (anillo de 5×5, a la altura de la mesa o un
bloque más arriba) con el hueco intermedio vacío (cualquier bloque del tag `replaceable`). Máximo útil: 15.

**Niveles que se ofrecen** (`b` = estanterías, máx. 15):

```
base   = rand(1..8) + floor(b/2) + rand(0..b)
arriba = max(base/3, 1)    medio = base*2/3 + 1    abajo = max(base, b*2)
```

Con 15 estanterías el botón de abajo siempre es 30. Pide 1/2/3 de lapislázuli y **quita 1/2/3 niveles**
(aunque exija tener 30).

**Qué encantamientos salen** con el nivel `L` del botón y la encantabilidad `E`:

1. `L' = L + 1 + rand(0..E/4) + rand(0..E/4)`
2. `L' = round(L' × (1 + (rand + rand − 1) × 0.15))`, mínimo 1.
3. De los encantamientos de `in_enchanting_table` que valen como primarios para el objeto, se toma para cada
   uno el **nivel más alto** cuyo rango de coste contiene `L'`. Se elige uno al azar por peso.
4. Mientras `rand(0..50) ≤ L'`: se quitan los incompatibles con el último, se añade otro por peso y `L'` se
   divide entre 2.

Consecuencias prácticas:
- Más encantabilidad = más encantamientos extra y niveles más altos (oro en lo alto, diamante en medio).
- Con L=30 en diamante (E=10), `L'` va de 26 a 40: salen Protección IV (34–45), Filo IV (34–54) y
  Eficiencia IV (31–81), pero **nunca** Filo V (desde 45) ni Eficiencia V (desde 41). En netherita llega a 43
  y en oro a 47, así que Filo V solo puede salir en oro. Los máximos se completan con yunque.
- La semilla de encantamiento del jugador solo cambia al encantar. Las tres opciones se pueden "rerolear"
  encantando cualquier cosa barata (un libro en el botón de arriba).
- La pista que enseña la mesa es uno de los encantamientos que saldrán, no todos.

## 3. Yunque

Entrada izquierda = objeto que se queda. Derecha = sacrificio: mismo objeto, libro encantado o material
de reparación.

### Coste total en niveles

```
coste = penalización(izq) + penalización(der) + reparación + encantamientos + renombrar
```

| Parte | Cálculo |
|---|---|
| Reparación con material | 1 nivel por unidad usada. Cada unidad repara el 25 % de la durabilidad máxima. |
| Reparación combinando dos iguales | 2 niveles. Durabilidad = la de los dos + 12 % del máximo. |
| Encantamiento del sacrificio | `mult × nivel_final` por cada uno que se aplique (mult de libro si viene de libro). |
| Incompatible | +1 nivel por cada choque, y no se aplica. |
| No aplicable al objeto | se ignora, no cuesta nada. |
| Renombrar | 1 nivel. |

Reglas de combinación de niveles: iguales → +1 (sin pasar del máximo); distintos → el mayor. **Se cobra el
nivel final aunque no suba**: poner un libro de Filo IV en una espada con Filo V cuesta 5, no 0.
Los encantamientos que solo tiene el objeto de la izquierda no cuestan nada.

Si la derecha no aporta nada (todo incompatible o no aplicable) no hay resultado.

### Penalización por trabajo previo (`repair_cost`)

Cada uso del yunque pone en el resultado `repair_cost = max(izq, der) × 2 + 1`:

| Usos previos | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| Penalización | 0 | 1 | 3 | 7 | 15 | 31 | 63 |

- Solo renombrar no la aumenta, y si el coste de solo renombrar llega a 40 se queda en 39.
- La cuentan los dos lados: un libro que ya ha pasado por el yunque también suma.
- Con 6 usos (63) en supervivencia ya solo se puede renombrar (que se queda en 39).

### Límites

- **40 o más** = "¡Demasiado caro!" en supervivencia (creativo no tiene límite). El máximo real es 39.
- Coste en niveles, no en puntos: hacerlo con nivel 30+ gasta muchos más puntos de experiencia que con nivel
  bajo. Conviene hacer las combinaciones caras con el nivel justo.
- El yunque tiene un 12 % de probabilidad de deteriorarse en cada uso (yunque → astillado → dañado → roto).

### Orden óptimo

El coste lo dispara la penalización, así que hay que hacer un **árbol equilibrado**, no ir añadiendo libros
de uno en uno:
1. Combinar libros entre sí por parejas (dos libros limpios cuestan poco).
2. Poner los libros caros (mult alto: Espinas, Toque de seda, Infinidad, Canalización...) pronto, cuando la
   penalización aún es baja; dejar los baratos (Filo, Protección, Eficiencia, Poder, Reparación) para el final.
3. La penalización final depende de la profundidad del árbol: objeto + hasta 3 libros → mínimo 3;
   hasta 7 libros → mínimo 7; hasta 15 → mínimo 15. A veces sale más barato aceptar un árbol más profundo
   (la calculadora lo decide).

### Muela (grindstone)

Quita todos los encantamientos menos las maldiciones, devuelve algo de experiencia y **reinicia la
penalización** (a 0, o a 1/3 si quedan una/dos maldiciones). Combinar dos objetos iguales en la muela suma
durabilidad + 5 % y también borra encantamientos.

## 4. Aldeanos bibliotecarios

En la 26.3 los comercios son datos (`villager_trade/librarian/*`, `trade_set/librarian/*`): los niveles 1 a 4
pueden ofrecer libro encantado a cambio de libro + esmeraldas, con un encantamiento aleatorio de `tradeable`
a nivel aleatorio. Precio clásico: `2 + rand(0..5 + nivel×10) + 3×nivel` esmeraldas, el doble si es de
`double_trade_price` (= tesoro), máximo 64. Reparación cuesta de 10 a 38.

## 5. Qué toca el resource pack

Un resource pack no cambia mecánicas (costes, máximos, exclusiones son de datapack o plugin). Lo que sí:
- Brillo: `textures/misc/enchanted_glint_item.png` y `enchanted_glint_armor.png` (Aurora ya los cambia).
- Aura de Aurora: los `items/*.json` usan `has_component minecraft:enchantments` con `ignore_default`. Los
  **libros encantados guardan `stored_enchantments`**, no `enchantments`, así que con esa condición nunca
  tendrían aura. Una pieza con solo una maldición sí la tiene.
- Interfaz: `textures/gui/container/anvil.png`, `enchanting_table.png`, `grindstone.png` y los sprites de
  `textures/gui/sprites/container/anvil/*` y `enchanting_table/*`.
- En Paper/Spigot un plugin puede subir el límite de 40 (`AnvilInventory#setMaximumRepairCost`) o cambiar
  costes; con eso la tabla de arriba deja de valer en ese servidor.

## Calculadora

```bash
# Orden más barato para un objeto limpio y sus libros (nivel 1 si no se indica)
python3 encantamientos/yunque.py sword sharpness:5 looting:3 sweeping_edge:3 fire_aspect:2 unbreaking:3 mending
# Objeto que ya ha pasado 2 veces por el yunque
python3 encantamientos/yunque.py pickaxe efficiency:5 fortune:3 unbreaking:3 mending --trabajo 2
# Un paso concreto (rc = penalización actual)
python3 encantamientos/yunque.py --combinar sword:sharpness:5,rc=7 book:mending
```

Busca de forma exacta (programación dinámica sobre subconjuntos) el orden con menos niveles en total sin
ningún paso de 40 o más, con hasta 10 libros. Tipos de objeto: `sword spear axe pickaxe shovel hoe mace
trident bow crossbow fishing_rod helmet chestplate leggings boots turtle_helmet elytra shield shears ...`
(`python3 yunque.py --help`). No modela durabilidad ni renombrado.

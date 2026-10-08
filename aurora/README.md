# Aurora — resource pack para Minecraft Java 26.3

Tema pastel iridiscente (cian → lavanda → rosa → melocotón → menta) inspirado en la capa Aurora.
Formato de resource pack 97 (`min_format` 84 / `max_format` 97).

| Carpeta | Qué hay |
|---|---|
| `dist/` | **Los zips listos para instalar**: `Aurora Pack.zip`, `Aurora Outline.zip` y `Aurora Glow.zip` (opcional, con el mod ETF) |
| `packs/Aurora Pack/` | Pack principal. Se genera entero con los scripts (no editar a mano) |
| `packs/Aurora Outline/` | Borde de bloque neón (core shader `rendertype_lines`). Escrito a mano |
| `packs/Aurora Glow/` | Add-on opcional para el mod ETF: los ribetes de la túnica de netherita, el borde de la capa y la armadura de diamante brillan en la oscuridad. Ver `emf/README.md` |
| `mod/` | Mod Fabric "Aurora FX" (solo cliente): brillo de aurora animado sobre la armadura de netherita puesta y estela de destellos. Ver `mod/README.md` |
| `scripts/` | Generadores en Python + Pillow, validador y `build.py` |
| `previews/` | Capturas y GIFs para ver el resultado sin abrir el juego |
| `HANDOFF.md` | Contexto técnico completo, decisiones verificadas y pendientes |

## Instalar
1. Copia los zips de `dist/` a `%APPDATA%\.minecraft\resourcepacks`.
2. En el juego, activa (de arriba a abajo): **Aurora Glow** (solo si tienes el mod ETF), **Aurora Outline**, **Aurora Pack**.
3. Mod opcional Aurora FX: descarga el `.jar` del artefacto `aurora-fx` de la última ejecución verde de
   [aurora-mod](https://github.com/gitmobau/mineleaf-resourcepack/actions/workflows/aurora-mod.yml)
   y ponlo en `%APPDATA%\.minecraft\mods` (necesita Fabric Loader y Fabric API para la 26.3).

## Armadura 3D (opcional)
Aurora no trae modelos 3D de armadura: los generados por código quedaban mal. Para armadura 3D se usa un pack ya hecho:
[Glowing 3D Armor](https://modrinth.com/project/WkLr6o3M), que lista soporte para 26.3. Hay que usar su subpack
**solo armadura**, para conservar las herramientas Aurora con su aura. Orden de arriba a abajo: Aurora Outline, Glowing 3D Armor,
Aurora Pack. Con él, quita **Aurora Glow**: sus mapas de brillo son para las texturas de armadura de Aurora.

## Regenerar
```bash
pip install pillow
python3 scripts/build.py --ref ~/ref63
```
`--ref` apunta a una carpeta con las texturas vanilla de la 26.3 (`assets/minecraft/...`).
No están en el repo porque son assets de Mojang. Para conseguirlas:
`python3 scripts/fetch_ref.py ~/ref63` (unos 3 s; baja solo lo necesario del espejo
[misode/mcmeta](https://github.com/misode/mcmeta), tag `26.3-assets`). Es byte a byte igual que la
`ref63/` del zip de traspaso y genera exactamente los mismos zips. También vale el
`versions/26.3/26.3.jar`.

`build.py` borra y regenera `packs/Aurora Pack`, ejecuta `gen.py → magic.py → gear.py → extra.py → menus.py → polish.py → armor.py → emf.py → showcase.py` (en ese
orden, porque los últimos sobrescriben a los primeros), pasa `validate.py` y crea los zips.
La salida es determinista: con la misma entrada salen los mismos bytes.

### Qué hace cada script
- `gen.py`: base v1 (agua, mira, fondo de la barra de XP, indicadores de ataque, `pack.png` y `pack.mcmeta`).
- `magic.py`: "Marco mágico". Menús (inventario, mesa de crafteo, hornos, cofre grande y shulker) y sprites animados (hotbar, selección, casilla resaltada, botón del libro de recetas, fuego y flecha del horno, XP).
- `gear.py`: herramientas animadas, aura de encantamiento, brillo de encantamiento, armaduras de diamante (cristal) y de netherita (túnica galáctica + capa 3D), también puestas en bebés, caballos y nautilus.
- `extra.py`: libro de recetas (cielo nocturno con aurora, pestañas, filtros, flechas), inventario creativo (3 fondos, 28 pestañas, scroll) e iconos del HUD (corazones de todos los tipos, comida, armadura, burbujas), conservando su tono para que se sigan distinguiendo.
- `menus.py`: el resto de menús (yunque, faro, soporte de pociones, mesa de cartografía, crafter, dispensador, mesa de encantamientos, afiladora, tolva, caballo, telar, nautilus, herrería, cortapiedras y aldeano) y todos sus sprites, más los widgets comunes: botones, deslizadores, campos de texto, pestañas, casillas de verificación y tooltips. Los widgets son oscuros para que el texto blanco se siga leyendo.
- `polish.py`: hierro en "piedra lunar" (lavanda plateada) y oro en "oro rosa", con herramientas, armaduras, armadura de caballo y de nautilus (icono y puesta), brillo animado y aura de encantamiento; también tótem y élitros.
- `armor.py`: armadura puesta v2 de los cuatro materiales, diseñada pieza a pieza: cobertura propia, contorno, ribete, junta en el peto, cuello en V, rodilleras, remaches, cresta y gemas. También la capa de netherita.
- `emf.py`: genera el add-on Aurora Glow (mapas de brillo `_e` de ETF). La túnica 3D experimental para EMF sigue en el script detrás de `GEOMETRY = False`: se descartó porque quedaba tosca.
- `showcase.py`: vistas previas de todo en `previews/showcase_*.png`, con la armadura renderizada en 3D sobre un maniquí con la geometría vanilla.
- `palette.py`: interpolación de color en OKLab, compartida por los generadores, para que los degradados pastel queden más suaves.
- `validate.py`: validación estática contra la 26.3. Revisa JSON, tamaños y frames de las animaciones, nine-slice, referencias de modelos y texturas, definiciones de items, capas de equipamiento, compilación de los shaders en las 5 variantes OIT con `glslangValidator` y que las salidas del vsh coincidan con las entradas del fsh.
- `fetch_ref.py`: descarga la referencia vanilla 26.3 desde misode/mcmeta.
- `prev.py`: hoja de previsualización antigua de la v1, se conserva como referencia.

Recursos externos útiles (espejos de assets, esquemas, shaders, EMF/ETF y pixel art): ver `RECURSOS.md`.

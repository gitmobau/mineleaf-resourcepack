# Recursos externos para Aurora

Recopilado el 2026-10-07. Todo comprobado con `git ls-remote` o clon superficial, y la fecha es la del último commit.
Desde las sesiones en la nube se puede acceder a `raw.githubusercontent.com`, `git clone` y PyPI/npm.
No se puede acceder a los servidores de Mojang, `minecraft.wiki`, `lospec.com` ni `codeload.github.com`.

## Referencia vanilla (lo más importante)
- **[misode/mcmeta](https://github.com/misode/mcmeta)**: hay tags por versión, como `26.3-assets`, `26.3-summary`, `26.3-atlas` o `26.3-data`.
  Las ramas sin versión van siempre con la última snapshot, así que hay que fijar el tag.
  - Raw: `https://raw.githubusercontent.com/misode/mcmeta/26.3-assets/assets/minecraft/<ruta>`
  - `26.3-summary`: JSON agregados (`assets/{model,item_definition,equipment,atlas,...}/data.min.json`). Sirven para validar referencias.
  - `26.3-atlas`: atlas montados (`items/atlas.png` + `data.json`), útiles para muestrear la paleta vanilla.
  - Lo usa `scripts/fetch_ref.py`.
- Espejos de respaldo, con una rama por versión: [InventivetalentDev/minecraft-assets](https://github.com/InventivetalentDev/minecraft-assets) (`26.3`)
  y [PixiGeko/Minecraft-default-assets](https://github.com/PixiGeko/Minecraft-default-assets) (`26.3`, `latest`).
- **[misode/technical-changes](https://github.com/misode/technical-changes)**: changelog técnico por snapshot (`26.1/`, `26.2/`, `26.3/`),
  con etiquetas como `shader breaking` y `assets breaking`. Es la fuente fiable para los cambios de formato de la 26.x.
- Texturas vanilla = copyright de Mojang: usarlas como referencia, nunca redistribuirlas tal cual.

## Esquemas y validación
- [SpyglassMC/vanilla-mcdoc](https://github.com/SpyglassMC/vanilla-mcdoc) (MIT): esquemas al día de `item_definition`, `equipment`,
  `model`, `atlas`, `texture_meta`, `shader` y `pack.mcmeta`. No existe un JSON Schema mantenido.
- [SpyglassMC/Spyglass](https://github.com/SpyglassMC/Spyglass) (MIT): validador como extensión de VS Code. No tiene CLI publicada.
  Los generadores web de [misode.github.io](https://misode.github.io) sirven para comprobar JSON a mano.
- [ComunidadAylas/PackSquash](https://github.com/ComunidadAylas/PackSquash) (AGPL-3.0): optimiza y valida el pack.
  El soporte de `min_format`/`max_format` todavía no está en una release, solo en las builds de `main`.
- [mcbeet/beet](https://github.com/mcbeet/beet) (MIT, PyPI `beet`): kit en Python para construir y empaquetar packs. Ya conoce la 26.3.

## Shaders
- La fuente buena para el formato actual son los shaders de `26.3-assets/assets/minecraft/shaders/{core,include}`
  más `technical-changes`.
- [McTsts/Minecraft-Shaders-Wiki](https://github.com/McTsts/Minecraft-Shaders-Wiki): buena para los conceptos, pero desactualizada
  (es de 12-2024, anterior a los bloques de uniforms y a `layout(location)`).
- Ejemplos recientes: [JNNGL/vanilla-shaders](https://github.com/JNNGL/vanilla-shaders) (MIT) y [Godlander/objmc](https://github.com/Godlander/objmc) (MIT).

## Pixel art en Python
- `coloraide` (PyPI): rampas en OKLCH con hue-shift, ideales para los degradados pastel iridiscentes.
- [hbldh/hitherdither](https://github.com/hbldh/hitherdither) (MIT): dithering Bayer/Yliluoma con paleta cerrada, bueno para 16x16.
- [sedthh/pyxelate](https://github.com/sedthh/pyxelate) (MIT) y `pixeloe` (PyPI, Apache-2.0): pixelizado y reducción de paleta.

## Formas 3D con mods (túnica con vuelo)
- [Traben-0/Entity_Model_Features](https://github.com/Traben-0/Entity_Model_Features) y
  [Entity_Texture_Features](https://github.com/Traben-0/Entity_Texture_Features) (LGPL-3.0): ya hay versiones para la 26.3.
- Formato `.jem`/`.jpm`: `OptiFineDoc/doc/cem_model.txt`, `cem_part.txt` y `cem_animation.txt` en
  [sp614x/optifine](https://github.com/sp614x/optifine).
- [Blockbench](https://github.com/JannisX11/blockbench) (formato "OptiFine Entity") y los plugins `cem_template_loader`,
  `emf_animation_addon` y `armor_exploded_view` de [blockbench-plugins](https://github.com/JannisX11/blockbench-plugins).

## Packs de referencia
- Faithful ([Faithful-Java-32x](https://github.com/Faithful-Resource-Pack/Faithful-Java-32x)): sirve para estudiar la estructura,
  pero su licencia no permite copiar texturas. No hay packs MIT con GUI procedural animada que merezca la pena estudiar.

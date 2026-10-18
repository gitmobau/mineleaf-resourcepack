# Prompt para Codex: armas y objetos de combate en estilo Aurora

Pega primero el prompt de `PROMPT_CODEX.md` (contexto general) poniendo como petición lo que hay en el bloque de abajo,
o pega este bloque solo: también funciona por sí mismo.

```text
Eres mi ayudante para el resource pack "Aurora" de Minecraft Java 26.3. Háblame en español.

CONTEXTO
- Repo gitmobau/mineleaf-resourcepack, carpeta aurora/ (no toques nada fuera). Parte de la rama
  claude/kind-goodall-uskil5 y trabaja en una rama nueva: codex/aurora-armas.
- Lee primero aurora/README.md, aurora/HANDOFF.md y aurora/PROMPT_CODEX.md: ahí están las reglas del proyecto.
- Todo se genera con scripts Python + Pillow. Referencia vanilla: python3 aurora/scripts/fetch_ref.py ~/ref63
  Build completa: python3 aurora/scripts/build.py --ref ~/ref63 (genera, valida y crea aurora/dist/*.zip).

TAREA: armas y objetos de combate en estilo Aurora
Crea un script nuevo, aurora/scripts/extras.py, que repinte estos objetos con la estética del pack (pastel
iridiscente: cian, lavanda, rosa, melocotón, menta; contorno violeta oscuro; brillos blancos):
  1. Arco: bow y bow_pulling_0/1/2 (los 4 deben verse coherentes al tensarlo).
  2. Ballesta: crossbow_standby, crossbow_pulling_0/1/2, crossbow_arrow y crossbow_firework.
  3. Maza (mace) y tótem de la inmortalidad (totem_of_undying).
  4. Flechas (arrow, spectral_arrow, tipped_arrow_head si existe) y perla de ender (ender_pearl).
  5. Escudo: la textura de entidad del escudo (textures/entity/shield/, shield_base y shield_base_nopattern o los
     nombres que tenga en la 26.3). Si hace falta, añade esa carpeta a FOLDERS en fetch_ref.py.
Reglas de estilo:
  - Respeta la silueta vanilla de cada objeto (mismo tamaño y mismos píxeles opacos). Solo cambian los colores.
  - Reutiliza las utilidades de aurora/scripts/gear.py (cyc, mix, C, hsv, la paleta P/VIVID, crystal_px) para que
    combine con las herramientas de diamante. Si animas algo, usa .mcmeta con frametime 2-4 y pocos frames.
  - Las partes de madera o cuerda pueden ir en lavanda/perla; las puntas y gemas en iridiscente.

INTEGRACIÓN
- Añade 'extras.py' en la lista de scripts de aurora/scripts/build.py justo después de 'icons.py'.
- Que extras.py guarde una vista previa en aurora/previews/extras.png con todos los objetos ampliados (antes/después).
- Documenta el script en aurora/README.md (sección "Qué hace cada script") y añade una sección corta a HANDOFF.md.

NO TOQUES
- Los logros (ventana de progresos, toast, sprites): se quedan vanilla.
- La netherita, el diamante, gear.py (salvo importar sus funciones), emf.py ni el pack Aurora EMF: los está
  ajustando otra sesión y habría conflictos.
- Los shaders y los menús de Aurora HUD XL.

ANTES DE TERMINAR
- validate.py debe dar "0 errors".
- Compila dos veces y comprueba que los md5 de aurora/dist/*.zip son iguales (build determinista: nada de hash()
  de Python, sets sin ordenar ni aleatoriedad sin semilla fija).
- Mira aurora/previews/extras.png y arregla lo que se vea mal.
- Commit en español, push a codex/aurora-armas y dime qué zip tengo que volver a copiar (será Aurora Pack.zip).
```

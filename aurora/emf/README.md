# Aurora EMF (add-on opcional)

Pack extra para quien juegue con los mods de Fabric **Entity Model Features (EMF)** y **Entity Texture
Features (ETF)**. Se pone **encima de Aurora Pack** y añade:

- **Túnica galáctica en 3D** (armadura de netherita):
  - **Falda con vuelo** (modelo de las grebas): 4 paneles de 1 px que caen desde la cintura con una
    abertura de ~7°. En el jugador se animan con las piernas: el panel delantero sigue a la pierna que va
    delante, el trasero a la que va detrás, y los laterales se adelantan al sentarse o montar. Además se
    compensa la inclinación del cuerpo al agacharse. En los mobs y en el soporte de armadura los paneles van
    pegados a cada pierna y no llevan animaciones (ver "Limitaciones").
  - **Mangas de campana** (modelo del peto): campana y puño anchos que solo crecen hacia fuera, delante y
    detrás, así no se meten en el torso.
  - **Punta de capucha** (modelo del casco): 4 segmentos que se curvan hacia atrás, con anillos de ribete y
    una borla que brilla.
- **Brillo en la oscuridad (emisivo de ETF, sufijo `_e`)**: ribetes aurora, broche de cristal y estrellas de
  la túnica, el bajo de la falda, las mangas y la capucha, los bordes de la capa (`wings/aurora_cloak`) y un
  brillo suave (alfa 110) en los reflejos de la armadura de diamante de cristal.

Todo lo genera `aurora/scripts/emf.py` a partir de las texturas ya generadas de Aurora Pack. Vista previa en
`aurora/previews/preview_emf.png`: renders del modelo quieto, andando, montando, de noche y de los mobs, y
todas las texturas con sus mapas emisivos.

## Requisitos
- Minecraft Java **26.3** con Fabric Loader (y lo que pidan los mods, normalmente Fabric API).
- **Entity Model Features** para 26.3. Código revisado: versión **3.3.11** (`mod_version` en `gradle.properties`,
  con subproyecto `versions/26.3-fabric`). Su `etf_version` es la 7.2.2.
- **Entity Texture Features** para 26.3. Código revisado: versión **7.2.5** (`versions/26.3-fabric`).
- Usa esas versiones o más nuevas. No he podido comprobar en Modrinth qué builds están publicadas porque su
  API está bloqueada desde aquí.
- OptiFine no vale: no tiene modelos de armadura ni de jugador.

## Instalación
1. Copia `Aurora EMF` (carpeta o zip) a `resourcepacks`.
2. Activa, de arriba a abajo: **Aurora Outline**, **Aurora EMF**, **Aurora Pack**. Aurora Outline puede ir
   donde quieras. Lo importante es que **Aurora EMF quede por encima de Aurora Pack**, por dos motivos:
   - el pack sobrescribe `humanoid_leggings/netherite.png` (la de Aurora Pack más la tela de la falda);
   - ETF solo usa un `_e.png` si viene del mismo pack que la textura base o de uno superior
     (`ETFTexture.setupEmissives`).
3. En ETF tienen que estar activadas las texturas emisivas y la armadura (`enableEmissiveTextures` y
   `enableArmorAndTrims`, que vienen activadas por defecto). En EMF, los modelos personalizados (`allowedCEM = ALL`,
   también por defecto).

Sin los mods, el pack no rompe nada: la tela de la falda está en una zona de la textura de las grebas que la
geometría vanilla nunca muestrea. Las mangas y la capucha usan una textura aparte que solo cargan los `.jem`.

## Archivos y nombres (verificados en el código)
```
assets/minecraft/optifine/cem/<portador>_<pieza>.properties   regla: variante 2 si lleva esa pieza de netherita
assets/minecraft/optifine/cem/<portador>_<pieza>2.jem         la geometría de la túnica
assets/minecraft/textures/entity/equipment/humanoid_leggings/netherite.png   (+ tela de la falda en las filas 0-12)
assets/minecraft/textures/entity/equipment/humanoid/aurora_robe_flare.png    mangas y capucha (64x32)
assets/minecraft/textures/entity/equipment/{humanoid,humanoid_leggings}/{netherite,diamond}_e.png
assets/minecraft/textures/entity/equipment/humanoid/aurora_robe_flare_e.png
assets/minecraft/textures/entity/equipment/wings/aurora_cloak_e.png
```
- `<pieza>` es `helmet`, `chestplate` o `leggings`. Las botas no cambian.
- `<portador>`: `player`, `player_slim`, `armor_stand`, `zombie`, `husk`, `drowned`, `skeleton`, `stray`,
  `wither_skeleton`, `bogged`, `parched`, `giant`, `piglin`, `piglin_brute`, `zombified_piglin` y
  `zombie_villager`. Los bebés se quedan con el modelo vanilla.

### De dónde salen esos nombres
1. **Vanilla 26.3** (`ModelLayers.registerArmorSet`): cada portador registra 4 capas,
   `ModelLayerLocation("<portador>", "helmet" | "chestplate" | "leggings" | "boots")`. Están `player`,
   `player_slim`, `armor_stand`, `zombie`, `zombie_baby`, etc. Ya no existen `*_inner_armor` ni `*_outer_armor`.
2. **EMF** (`EMFManager.injectIntoModelRootGetter`): el nombre del archivo es `ruta + "_" + capa` cuando la capa
   no es `main`, así que queda `player_chestplate`. Desde la 1.21.9, si el nombre termina en `_helmet`,
   `_chestplate`, `_leggings` o `_boots`, el mapa de partes pasa a ser `helmet`, `chestplate`, etc., y se añade
   como respaldo `helmet.jem`, `chestplate.jem`, etc. Este pack no usa los respaldos genéricos para no afectar a
   los bebés, que en 26.x tienen otra malla.
3. Ruta: `EMFModel_ID.getDisplayFileName` da `assets/<ns>/optifine/cem/<nombre>.jem`. `EMFDirectoryHandler`
   acepta también `emf/cem/` y las subcarpetas `<nombre>/<nombre>.jem`.
4. Partes (`EMFModelMappings`): `helmet`, `chestplate`, `leggings` y `boots` usan `genericNonPlayerBiped`
   (`head`, `headwear`, `body`, `left_arm`, `right_arm`, `left_leg`, `right_leg`).
5. Qué parte trae cada pieza (`HumanoidModel.ADULT_ARMOR_PARTS_PER_SLOT`): HEAD lleva `head`, CHEST lleva
   `body` y los brazos, LEGS lleva `body` y las piernas (deformación 0,5, piernas 0,4), y FEET lleva las piernas
   (0,9). La textura es de 64x32 y se usa `humanoid` para todo menos las grebas, que usan `humanoid_leggings`
   (`HumanoidArmorLayer`).

### Cómo se limita a la netherita (EMF no sabe de materiales)
Un `.jem` de armadura se aplica a **todas** las armaduras de esa pieza, y la textura la pone vanilla según el
material. EMF no tiene ninguna condición de material. Por eso se usan **variantes de modelo con propiedades de
ETF**:
```
models.1=2
nbt.1.equipment.legs.id=minecraft:netherite_leggings
```
- No hay `.jem` base. EMF pone entonces la variante 1 como vanilla (`EMFModelPartRoot.setVariant1ToVanilla0`).
  Esto solo falla si el usuario activa a mano `enforceOptifineVariationRequiresDefaultModel_v2`, que viene
  desactivado: en ese caso se vería la armadura normal.
- El NBT viene de `NbtPredicate.getEntityTagToCompare(entity)` en el cliente. `LivingEntity` guarda
  `equipment: {head, chest, legs, feet, ...}` y cada objeto lleva su `id`. El servidor sincroniza el equipamiento
  de todas las entidades y jugadores.
- La propiedad `items` de ETF **no** sirve: lee `LivingEntity.lastEquipmentItems` (`MixinEntity`), que en la
  26.3 solo se actualiza en el servidor (`detectEquipmentUpdates`, dentro de `!isClientSide()`). Además no
  distingue la mano de la armadura.
- Si las propiedades y las variantes numeradas están en el mismo pack, ganan las propiedades
  (`ETFVariantSuffixProvider`).
- `nbt` no está fijada al aparecer la entidad, así que se vuelve a evaluar cada cierto tiempo
  (`modelUpdateFrequency` de EMF). Al ponerte o quitarte la pieza, la forma puede tardar un instante en cambiar.

### Formato de los .jem (cómo los escribe `emf.py`)
- Todas las partes usan `invertAxis: "xy"`. `EMFPartData.prepare` invierte X/Y de `translate` y `rotate`, y
  `EMFBoxData.prepare` hace `x = -x - w` e `y = -y - h`.
- Cada entrada de nivel superior lleva `attach: true`, así que se conserva la caja vanilla con la textura de
  Aurora Pack. Su `translate` es `(px, py - 24, -pz)`, con p el pivote vanilla, igual que en los ejemplos
  oficiales de OptiFine (`armor_stand.jem`: cabeza `[0, -23, 0]`). Los submodelos quedan entonces en el espacio
  "Blockbench" y se cuelgan como hijos de la parte vanilla, así que siguen su pose.
- Las animaciones escriben directamente `ModelPart.xRot` (en radianes y en espacio de modelo, sin inversión).
  Leen `left_leg.rx`, `right_leg.rx` y `body.rx`, que ya trae puestos el `setupAnim` vanilla.
- Textura por parte: `"texture": "textures/entity/equipment/humanoid/aurora_robe_flare"` (sin `:` y con `/`,
  así que es relativa a `assets/minecraft/`, y EMF añade `.png`) más `"textureSize": [64, 32]`. Las partes sin
  `texture` usan la textura que pasa vanilla, es decir, la de netherita.

### Emisivos (ETF)
- El sufijo por defecto es `_e`. ETF lo prueba siempre (`alwaysCheckVanillaEmissiveSuffix = true`), aunque otro
  pack defina otro sufijo en `optifine/emissive.properties`.
- En armaduras funciona porque ETF intercepta `RenderTypes.armorCutoutNoCull` (`MixinRenderLayer`). El modo
  DULL, que es el que viene por defecto, dibuja el `_e` con `entityTranslucent` a luz máxima, así que el alfa
  parcial se respeta (por eso el diamante usa alfa 110).
- Las partes con textura propia también pintan su `_e` (`EMFModelPart.renderTextureOverrideWithoutReset` llama
  a `ETFUtils2.renderEmissive`).

## Fuentes
- EMF: <https://github.com/Traben-0/Entity_Model_Features>, rama `master`, commit
  `622a0cba8c2e3eeef896b5a9dbcb8d94600f3cd7` (5-10-2026, "fix KeyframeLoopMethod"). Archivos:
  `EMFManager.java`, `models/EMFModel_ID.java`, `models/EMFModelMappings.java`, `utils/EMFDirectoryHandler.java`,
  `models/jem_objects/{EMFJemData,EMFPartData,EMFBoxData}.java`, `models/parts/{EMFModelPartRoot,EMFModelPart,EMFModelPartCustom}.java`,
  `mixin/mixins/rendering/submits/{Mixin_ModelRenderer,Mixin_HumanoidArmorLayer_AddBaseModelPoseRef}.java`,
  `config/EMFConfig.java`, `CHANGELOG.MD` y `gradle.properties`.
- ETF: <https://github.com/Traben-0/Entity_Texture_Features>, rama `ETF-Main`, commit
  `ba6dfecca69672b1b5e91ad5d4c8ae1a5c8476d2` (4-10-2026). Archivos: `features/ETFManager.java`,
  `features/texture_handlers/ETFTexture.java`, `mixin/mixins/MixinRenderLayer.java`, `utils/ETFUtils2.java`,
  `features/property_reading/properties/optifine_properties/NBTProperty.java`,
  `features/property_reading/properties/etf_properties/ItemProperty.java`,
  `features/property_reading/{PropertiesRandomProvider,TrueRandomProvider}.java`,
  `features/property_reading/properties/RandomProperties.java`, `mixin/mixins/entity/misc/MixinEntity.java`,
  `config/ETFConfig.java` y `ETFApi.java`.
- Vanilla 26.3 descompilado: <https://github.com/mc-dataminning/build-changes>, tag `26.3` (commit
  `213a1038d61f60468efdfd73c34138cd5b2679ce`). Archivos: `client/model/geom/{ModelLayers,LayerDefinitions,ModelPart}.java`,
  `client/model/geom/builders/PartDefinition.java`, `client/model/HumanoidModel.java`,
  `client/model/player/PlayerModel.java`, `client/model/object/armorstand/ArmorStandArmorModel.java`,
  `client/model/monster/zombie/ZombieVillagerModel.java`, `client/model/monster/piglin/AbstractPiglinModel.java`,
  `client/renderer/entity/layers/{HumanoidArmorLayer,EquipmentLayerRenderer,WingsLayer}.java`,
  `client/renderer/entity/player/AvatarRenderer.java`, `client/renderer/rendertype/RenderTypes.java`,
  `world/entity/{LivingEntity,EntityEquipment,EquipmentSlot}.java`, `world/entity/player/Player.java` y
  `advancements/predicates/NbtPredicate.java`. Coincide con la 26.2 de otros repos (p. ej. `Renekovski/26.2-mcp`).
- OptiFine CEM: <https://github.com/sp614x/optifine>, commit `83d482c3882bb3fcacc3c3d2ce6dcb18b39383f2`.
  Archivos: `OptiFineDoc/doc/cem_model.txt`, `cem_part.txt` y `examples/CEM Animation Examples` (convención de
  `translate`).

## Sin verificar (no se puede arrancar el juego aquí)
- **Nada se ha probado dentro del juego.** La geometría y las animaciones solo se han comprobado con el
  renderizador de `emf.py`, que reproduce `ModelPart.Cube`, el UV de caja y `rotationZYX`. Puede que haga falta
  ajustar ángulos y tamaños.
- **Texturas propias en armaduras en 26.3** (mangas y capucha): EMF las soporta, pero su ruta alternativa para
  26.2+ tiene un `TODO probably wrong`. Si falla, las mangas y la capucha podrían salir con otra textura o no
  salir. La falda no depende de esto porque usa la textura de netherita que pasa vanilla.
- **Brillo en piezas encantadas sin trim**: en la 26.3 se pintan con `armorCutoutNoCullGlint`, que ETF no
  intercepta, así que probablemente no brillen. Con trim o sin encantar deberían brillar. Las partes con
  textura propia también se vuelven a pintar en las pasadas del trim y del glint, y eso podría verse raro con
  armadura encantada.
- **Compatibilidad con packs de animación** (Fresh Animations y similares): si un modelo de armadura tiene
  animaciones propias, EMF deja de copiarle la pose del modelo base (`Mixin_ModelRenderer.applyArmorBipedPose`).
  La falda animada del jugador no seguiría una pose personalizada del jugador, aunque sí la pose vanilla. Por eso
  los mobs llevan la versión sin animaciones.
- La propiedad `nbt` en jugadores (local y remotos) depende de que `saveWithoutId` funcione en el cliente. Por
  el código debería, pero no está probado. Coste: ETF guarda en caché el NBT por estado de render.
- EMF añade de forma automática puntos de anclaje de loros a los brazos en los modelos cuyo nombre empieza por
  `player` (`parrotShoulderPositionAnimatesByDefault`). En `player_chestplate2.jem` debería ser inofensivo.
- Pivotes de mobs poco comunes (`giant`, `husk` y `wither_skeleton` usan la malla humanoide escalada en la raíz;
  `zombie_villager` tiene la cabeza 2 px más alta y las piernas a ±2) sacados del código, no vistos en el juego.
- Donde se juntan las medias faldas de los mobs puede haber pequeños solapes o rendijas al andar.
- No he podido ver qué versiones de EMF y ETF para 26.3 hay publicadas en Modrinth.

## Regenerar
```bash
python3 -I aurora/scripts/build.py --ref ~/ref63   # genera Aurora Pack (lo necesita emf.py)
python3 -I aurora/scripts/emf.py                    # genera packs/Aurora EMF y previews/preview_emf.png
```
`emf.py` borra y regenera `packs/Aurora EMF`. Valida el JSON, que existan las texturas referenciadas (en este
pack o en Aurora Pack), los límites de UV, que las partes y los ids de las animaciones existan, que cada
`.properties` tenga su variante y que cada `_e` tenga su base del mismo tamaño. La salida es determinista.

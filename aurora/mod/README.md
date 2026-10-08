# Aurora FX: mod cliente para Fabric (Minecraft Java 26.3)

Complemento del resource pack **Aurora**. Añade los efectos que un resource pack no puede hacer.

1. **Brillo de aurora en la armadura de netherita puesta.** Sobre cada pieza de netherita que lleve
   un jugador o un mob (la "túnica galáctica" del pack) se dibuja una capa translúcida que brilla.
   Sus cintas de aurora se desplazan despacio, laten y cambian de color recorriendo la paleta Aurora
   (cian → lavanda → rosa → melocotón → menta). No sustituye la armadura: la textura del resource
   pack se sigue viendo debajo. Usa el mismo tipo de render que el halo del creeper cargado
   (`energy_swirl`: mezcla aditiva y desplazamiento de UV). Funciona en jugadores, zombis,
   esqueletos, piglins, soportes de armadura y demás mobs humanoides. En los bebés no se dibuja.
2. **Estela de destellos pastel.** Detrás de los jugadores que llevan **el set completo de netherita**
   salen partículas de polvo de colores de la paleta, con algún destello blanco suelto. También salen
   detrás de quien lleva en la mano una herramienta o arma **de diamante o netherita encantada**
   (espada, pico, hacha, pala, azada o lanza). Si el jugador está quieto, la estela es mucho más
   floja. Hay un límite de partículas por jugador y otro global por tick.
3. **Configuración** en `config/aurora_fx.json`, sin librerías extra.

Es **solo cliente**: no hace falta en el servidor y funciona en cualquier servidor, vanilla incluido.
Las partículas y el brillo solo los ves tú. No sustituye al resource pack, lo complementa.
Para el look completo, activa también *Aurora Pack* y *Aurora Outline*.

## Conseguir el .jar

### Opción A: descargarlo de GitHub Actions (sin instalar nada)
1. En GitHub, ve a **Actions → aurora-mod** y abre la ejecución más reciente que esté en verde.
2. Abajo, en **Artifacts**, descarga **aurora-fx**. Es un zip con dentro `aurora_fx-1.0.0.jar`.
3. Descomprímelo.

El workflow (`.github/workflows/aurora-mod.yml`) se ejecuta solo cuando cambia algo de `aurora/mod/`.
También se puede lanzar a mano con *Run workflow*.

### Opción B: compilarlo en tu PC (Windows)
Necesitas un **JDK 25**, por ejemplo Microsoft Build of OpenJDK 25 o Temurin 25. Con un JRE no basta.
```bat
cd aurora\mod
gradlew.bat build
```
El primer build tarda unos minutos porque descarga Gradle 9.7.1, Minecraft 26.3 y Fabric.
El jar sale en `aurora\mod\build\libs\aurora_fx-1.0.0.jar`.
En Linux o macOS es lo mismo con `./gradlew build`.

## Instalar
1. Instala **Fabric Loader 0.19.5 o superior para Minecraft 26.3** con el instalador de
   [fabricmc.net](https://fabricmc.net/use/).
2. Copia en `%APPDATA%\.minecraft\mods\`:
   - **Fabric API para 26.3** (`fabric-api-0.161.0+26.3.jar` o más nueva), que es obligatoria;
   - `aurora_fx-1.0.0.jar`.
3. Arranca el juego con el perfil *fabric-loader-26.3*.

Es compatible con Entity Model Features y Entity Texture Features. El brillo es una capa aparte
y no toca el modelo de la armadura, pero esa combinación no se ha probado.

## Configuración (`config/aurora_fx.json`)
Se crea sola la primera vez que arrancas el juego con el mod. Si la editas con el juego abierto, se
vuelve a leer sola en unos 3 segundos, sin reiniciar.

```json
{
  "armorOverlay": true,
  "overlayOnMobs": true,
  "overlayIntensity": 0.55,
  "overlaySpeed": 1.0,
  "particleTrail": true,
  "trailOnEnchantedTools": true,
  "trailInFirstPerson": false,
  "particleRate": 1.0,
  "maxParticlesPerTick": 8,
  "particleRange": 32.0
}
```

| Opción | Qué hace |
|---|---|
| `armorOverlay` | `false` quita el brillo de la armadura |
| `overlayOnMobs` | `false` deja el brillo solo en jugadores |
| `overlayIntensity` | Intensidad del brillo, de 0 a 1 |
| `overlaySpeed` | Velocidad del desplazamiento y del cambio de color, de 0 a 5. Con 0 se queda quieto |
| `particleTrail` | `false` quita la estela |
| `trailOnEnchantedTools` | `false` deja la estela solo para el set completo de netherita |
| `trailInFirstPerson` | `true` también dibuja tu propia estela cuando juegas en primera persona |
| `particleRate` | Multiplicador de la cantidad de partículas, de 0 a 3 |
| `maxParticlesPerTick` | Tope global de partículas por tick (20 ticks = 1 s), de 1 a 64 |
| `particleRange` | Solo se genera la estela de los jugadores que están a menos de esta distancia (en bloques) |

Los valores fuera de rango se ajustan al límite. Si el JSON tiene un error, el mod avisa en el log
y sigue con la configuración que tenía. Tu archivo no se sobrescribe.

## Cómo está hecho
- `src/client/java/io/github/gitmobau/aurorafx/`
  - `AuroraFxClient`: punto de entrada. Registra la capa de render y el evento de tick.
  - `AuroraArmorLayer`: la capa de brillo. Usa modelos de armadura propios, 0.08 más grandes que los
    de vanilla para que no parpadeen (z-fighting), y copia la pose del modelo del mob.
  - `AuroraTrail`: la estela de partículas.
  - `AuroraConfig`: carga, crea y recarga el JSON (con Gson, que ya viene con Minecraft).
  - `AuroraPalette`: la paleta de `aurora/scripts/gear.py` en Java.
- `src/main/resources/assets/aurora_fx/`: `icon.png` y `textures/entity/aurora_overlay.png`.
  Las genera `tools/gen_textures.py` (`pip install pillow && python3 aurora/mod/tools/gen_textures.py`),
  que es determinista: siempre produce los mismos bytes. La textura del brillo es periódica en
  las dos direcciones para que el desplazamiento no tenga costuras. El fondo es negro porque con
  la mezcla aditiva el negro no se ve.
- No usa mixins. Todo va por la API de Fabric:
  - `LivingEntityRenderLayerRegistrationCallback` añade la capa a los renderers con modelo humanoide.
  - `ModelLayerRegistry.registerArmorModelLayers` registra los modelos de armadura propios.
  - `ArmorRenderer.submitTransformCopyingModel` dibuja la pieza copiando la pose del mob.
  - `ClientTickEvents.END_CLIENT_TICK` genera las partículas.
- Versiones (copiadas de `FabricMC/fabric-example-mod`, rama `26.3`): Minecraft 26.3, Fabric Loader 0.19.5,
  Loom 1.18-SNAPSHOT (plugin `net.fabricmc.fabric-loom`), Fabric API 0.161.0+26.3, Gradle 9.7.1, Java 25.
  En la 26.x el juego no está ofuscado: no hay bloque `mappings` y se usan los nombres oficiales de Mojang.

## Sin verificar
Este mod se escribió en un entorno sin acceso a los servidores de Mojang ni al maven de Fabric, así
que **no se ha compilado ni probado en el juego** desde aquí. La compilación la hace GitHub Actions.
Lo que sí se comprobó y lo que queda pendiente:

- **Comprobado contra código real de la 26.3.** Los nombres de clases y métodos de vanilla se
  comprobaron en el código descompilado de la 26.3 (`mc-dataminning/build-changes`, tag `26.3`):
  `RenderTypes.energySwirl`, `HumanoidRenderState.*Equipment`, `HumanoidModel.createArmorMeshSet`,
  `ArmorModelSet`, `ClientLevel.addParticle`, `DustParticleOptions(int, float)`, `Items.*_SPEAR`, etc.
  Los de la API de Fabric se comprobaron en el código de `FabricMC/fabric`, tag `0.161.0+26.3`, y en
  sus testmods. Además, los fuentes se pasaron por `javac` contra stubs con esas mismas firmas.
  Eso detecta errores de tipos, pero no garantiza que compile contra el jar real.
- **El aspecto en el juego no se ha visto.** Puede que haya que ajustar `overlayIntensity`, la
  velocidad, o la escala de la textura si las cintas se ven demasiado grandes o pequeñas en la armadura.
- **El brillo se ve igual de día que de noche.** El pipeline `energy_swirl` de vanilla es emisivo:
  no usa la luz del sitio.
- **Mobs con modelos raros.** La pose se copia por nombre de pieza (`head`, `body`, `right_arm`...).
  En mobs humanoides con proporciones distintas (piglins, soportes de armadura pequeños...) el brillo
  podría no encajar del todo. Si molesta, `overlayOnMobs: false`.
- **La estela de otros jugadores.** El movimiento de los jugadores remotos se calcula con su posición
  en el tick anterior. Debería funcionar, pero solo se ha razonado sobre el código, no se ha probado
  en multijugador.
- **Compatibilidad con Sodium, Iris o shaders.** Sin probar. El brillo usa un pipeline vanilla, así
  que debería funcionar, pero con shaders de Iris la mezcla aditiva puede verse distinta.

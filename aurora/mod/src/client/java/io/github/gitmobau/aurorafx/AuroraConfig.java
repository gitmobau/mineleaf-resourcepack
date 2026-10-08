package io.github.gitmobau.aurorafx;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;
import com.google.gson.JsonParseException;

import net.fabricmc.loader.api.FabricLoader;

/**
 * Configuración en {@code config/aurora_fx.json}. Sin librerías extra: Gson ya viene con Minecraft.
 *
 * <p>Si el archivo no existe se crea con los valores por defecto. Si se edita con el juego abierto,
 * se vuelve a leer solo (se comprueba la fecha de modificación cada pocos segundos).
 */
public final class AuroraConfig {
	// ---- brillo de aurora sobre la armadura de netherita puesta ----
	/** Activa el brillo animado sobre la armadura de netherita (la "túnica galáctica"). */
	public boolean armorOverlay = true;
	/** También en mobs (zombis, esqueletos, piglins, soportes de armadura...), no solo en jugadores. */
	public boolean overlayOnMobs = true;
	/** Brilla en la oscuridad (luz máxima) en vez de usar la luz del sitio. */
	public boolean overlayGlow = true;
	/** Intensidad del brillo, 0..1. */
	public float overlayIntensity = 0.55F;
	/** Velocidad de desplazamiento y cambio de color, 0..5 (1 = normal). */
	public float overlaySpeed = 1.0F;

	// ---- estela de destellos ----
	/** Activa la estela de destellos pastel. */
	public boolean particleTrail = true;
	/** También al llevar en la mano una herramienta/arma de diamante o netherita encantada. */
	public boolean trailOnEnchantedTools = true;
	/** Dibujar también la estela del propio jugador en primera persona. */
	public boolean trailInFirstPerson = false;
	/** Multiplicador de la cantidad de partículas, 0..3. */
	public float particleRate = 1.0F;
	/** Tope global de partículas por tick (20 ticks = 1 s), 1..64. */
	public int maxParticlesPerTick = 8;
	/** Distancia máxima a la cámara (bloques) para generar la estela, 4..128. */
	public double particleRange = 32.0;

	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static final Path PATH = FabricLoader.getInstance().getConfigDir().resolve(AuroraFxClient.MOD_ID + ".json");

	private static volatile AuroraConfig current = new AuroraConfig();
	private static long lastModified = Long.MIN_VALUE;

	public static AuroraConfig get() {
		return current;
	}

	/** Carga el archivo, o lo crea con los valores por defecto si no existe. */
	public static synchronized void load() {
		if (!Files.exists(PATH)) {
			current = new AuroraConfig();
			save(current);
		} else {
			try (Reader reader = Files.newBufferedReader(PATH, StandardCharsets.UTF_8)) {
				AuroraConfig cfg = GSON.fromJson(reader, AuroraConfig.class);
				current = cfg == null ? new AuroraConfig() : cfg.clamp();
			} catch (IOException | JsonParseException e) {
				// No se sobrescribe el archivo del usuario: se avisa y se siguen usando los valores anteriores.
				AuroraFxClient.LOGGER.warn("[Aurora FX] No se pudo leer {}: {}", PATH, e.getMessage());
			}
		}

		lastModified = modifiedTime();
	}

	/** Vuelve a cargar si el archivo cambió desde la última lectura. */
	public static void reloadIfChanged() {
		long mod = modifiedTime();

		if (mod != lastModified) {
			load();
			AuroraFxClient.LOGGER.info("[Aurora FX] Configuración recargada");
		}
	}

	private static void save(AuroraConfig cfg) {
		try {
			Files.createDirectories(PATH.getParent());

			try (Writer writer = Files.newBufferedWriter(PATH, StandardCharsets.UTF_8)) {
				GSON.toJson(cfg, writer);
			}
		} catch (IOException e) {
			AuroraFxClient.LOGGER.warn("[Aurora FX] No se pudo escribir {}: {}", PATH, e.getMessage());
		}
	}

	private static long modifiedTime() {
		try {
			return Files.exists(PATH) ? Files.getLastModifiedTime(PATH).toMillis() : Long.MIN_VALUE;
		} catch (IOException e) {
			return Long.MIN_VALUE;
		}
	}

	private AuroraConfig clamp() {
		overlayIntensity = clamp(overlayIntensity, 0.0F, 1.0F);
		overlaySpeed = clamp(overlaySpeed, 0.0F, 5.0F);
		particleRate = clamp(particleRate, 0.0F, 3.0F);
		maxParticlesPerTick = Math.max(1, Math.min(64, maxParticlesPerTick));
		particleRange = Math.max(4.0, Math.min(128.0, particleRange));
		return this;
	}

	private static float clamp(float v, float lo, float hi) {
		return Float.isNaN(v) ? lo : Math.max(lo, Math.min(hi, v));
	}
}

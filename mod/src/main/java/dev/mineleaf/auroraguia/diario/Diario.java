package dev.mineleaf.auroraguia.diario;

import java.io.IOException;
import java.io.Reader;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import net.fabricmc.loader.api.FabricLoader;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ServerData;

/** Hardcore diary: personal goals per world, saved in config/aurora_guia/diario.json. */
public final class Diario {
	public static final class Goal {
		public String text = "";
		public boolean done;

		public Goal() {
		}

		public Goal(String text) {
			this.text = text;
		}
	}

	public static final class Data {
		public boolean visible = true;
		public Map<String, List<Goal>> worlds = new LinkedHashMap<>();
	}

	private static final Gson GSON = new GsonBuilder().setPrettyPrinting().create();
	private static Data data;

	private Diario() {
	}

	private static Path file() {
		return FabricLoader.getInstance().getConfigDir().resolve("aurora_guia").resolve("diario.json");
	}

	public static Data data() {
		if (data == null) {
			data = new Data();
			Path f = file();
			if (Files.exists(f)) {
				try (Reader r = Files.newBufferedReader(f, StandardCharsets.UTF_8)) {
					Data d = GSON.fromJson(r, Data.class);
					if (d != null) {
						data = d;
					}
				} catch (IOException | RuntimeException e) {
					// a broken file must not crash the game: start with an empty diary
				}
			}
		}
		return data;
	}

	public static void save() {
		Path f = file();
		try {
			Files.createDirectories(f.getParent());
			try (Writer w = Files.newBufferedWriter(f, StandardCharsets.UTF_8)) {
				GSON.toJson(data(), w);
			}
		} catch (IOException e) {
			// nothing else to do on the client; the diary keeps working in memory
		}
	}

	/** Singleplayer worlds by name, servers by address. */
	public static String worldKey() {
		Minecraft mc = Minecraft.getInstance();
		if (mc.getSingleplayerServer() != null) {
			return "sp:" + mc.getSingleplayerServer().getWorldData().getLevelName();
		}
		ServerData sd = mc.getCurrentServer();
		return sd != null ? "mp:" + sd.ip : "otro";
	}

	public static List<Goal> goals() {
		return data().worlds.computeIfAbsent(worldKey(), k -> new ArrayList<>());
	}
}

package dev.mineleaf.auroraguia.diario;

import java.util.ArrayList;
import java.util.List;

import net.minecraft.advancements.AdvancementHolder;
import net.minecraft.advancements.AdvancementProgress;
import net.minecraft.client.DeltaTracker;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;

/** Small panel in the top-left corner: day, boss/progress milestones and the open personal goals. */
public final class DiarioHud {
	static final String[][] MILESTONES = {
		{"end/kill_dragon", "aurora_guia.diario.dragon"},
		{"nether/summon_wither", "aurora_guia.diario.wither"},
		{"end/elytra", "aurora_guia.diario.elytra"},
		{"nether/netherite_armor", "aurora_guia.diario.netherite"},
		{"adventure/totem_of_undying", "aurora_guia.diario.totem"},
	};
	private static final int BG = 0xB0201436, EDGE = 0xFFB48CFF, TITLE = 0xFFFFE08C, TEXT = 0xFFFFFFFF,
		DONE = 0xFF8CFFB4, TODO = 0xFFC8B8F0;
	private static final int MAX_GOALS = 5;

	private DiarioHud() {
	}

	public static boolean milestoneDone(Minecraft mc, String path) {
		if (mc.getConnection() == null) {
			return false;
		}
		for (var e : mc.getConnection().getAdvancements().progress().entrySet()) {
			AdvancementHolder h = e.getKey();
			AdvancementProgress p = e.getValue();
			if (h.id().equals(Identifier.withDefaultNamespace(path))) {
				return p.isDone();
			}
		}
		return false;
	}

	public static void extract(GuiGraphicsExtractor g, DeltaTracker delta) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null || mc.level == null || !Diario.data().visible || mc.gui.screen() != null
			|| mc.getDebugOverlay().showDebugScreen()) {
			return;
		}
		Font font = mc.font;
		List<Object[]> lines = new ArrayList<>();   // {Component, color}
		long day = mc.level.getOverworldClockTime() / 24000L + 1;
		lines.add(new Object[] {Component.translatable("aurora_guia.diario.day", day), TITLE});
		List<Object[]> milestoneLines = new ArrayList<>();
		for (String[] m : MILESTONES) {
			boolean done = milestoneDone(mc, m[0]);
			milestoneLines.add(new Object[] {Component.literal(done ? "✔ " : "· ").append(Component.translatable(m[1])), done ? DONE : TODO});
		}
		lines.addAll(milestoneLines);
		List<Diario.Goal> goals = Diario.goals();
		long open = goals.stream().filter(gl -> !gl.done).count();
		if (!goals.isEmpty()) {
			lines.add(new Object[] {Component.translatable("aurora_guia.diario.goals", goals.size() - open, goals.size()), TITLE});
			goals.stream().filter(gl -> !gl.done).limit(MAX_GOALS)
				.forEach(gl -> lines.add(new Object[] {Component.literal("☐ " + gl.text), TEXT}));
		}
		int w = 0;
		for (Object[] l : lines) {
			w = Math.max(w, font.width((Component) l[0]));
		}
		w = Math.min(w + 10, 180);
		int h = lines.size() * 10 + 6;
		int x = 4, y = 4;
		g.fill(x, y, x + w, y + h, BG);
		g.outline(x, y, w, h, EDGE);
		int yy = y + 4;
		for (Object[] l : lines) {
			g.text(font, font.substrByWidth((Component) l[0], w - 8).getString(), x + 5, yy, (int) l[1], true);
			yy += 10;
		}
	}
}

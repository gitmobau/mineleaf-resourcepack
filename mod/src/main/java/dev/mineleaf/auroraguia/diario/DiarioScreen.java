package dev.mineleaf.auroraguia.diario;

import java.util.List;

import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.EditBox;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Edit the personal goals of the current world: add, tick, remove, and show/hide the HUD panel. */
public final class DiarioScreen extends Screen {
	private static final int ROWS = 8;
	private EditBox input;
	private int page;

	public DiarioScreen() {
		super(Component.translatable("aurora_guia.diario.title"));
	}

	@Override
	protected void init() {
		int cx = this.width / 2;
		int top = 40;
		this.input = new EditBox(this.font, cx - 150, top, 240, 20, Component.translatable("aurora_guia.diario.new"));
		this.input.setMaxLength(60);
		this.input.setHint(Component.translatable("aurora_guia.diario.new"));
		this.addRenderableWidget(this.input);
		this.addRenderableWidget(Button.builder(Component.translatable("aurora_guia.diario.add"), b -> add()).bounds(cx + 94, top, 56, 20).build());
		List<Diario.Goal> goals = Diario.goals();
		int pages = Math.max(1, (goals.size() + ROWS - 1) / ROWS);
		this.page = Math.min(this.page, pages - 1);
		for (int i = 0; i < ROWS; i++) {
			int idx = this.page * ROWS + i;
			if (idx >= goals.size()) {
				break;
			}
			Diario.Goal goal = goals.get(idx);
			int y = top + 28 + i * 22;
			this.addRenderableWidget(Button.builder(Component.literal((goal.done ? "✔ " : "☐ ") + goal.text), b -> {
				goal.done = !goal.done;
				Diario.save();
				rebuildWidgets();
			}).bounds(cx - 150, y, 270, 20).build());
			this.addRenderableWidget(Button.builder(Component.literal("✕"), b -> {
				goals.remove(goal);
				Diario.save();
				rebuildWidgets();
			}).bounds(cx + 126, y, 24, 20).build());
		}
		int by = top + 28 + ROWS * 22 + 6;
		if (pages > 1) {
			this.addRenderableWidget(Button.builder(Component.literal("<"), b -> { this.page = (this.page + pages - 1) % pages; rebuildWidgets(); })
				.bounds(cx - 150, by, 20, 20).build());
			this.addRenderableWidget(Button.builder(Component.literal(">"), b -> { this.page = (this.page + 1) % pages; rebuildWidgets(); })
				.bounds(cx - 126, by, 20, 20).build());
		}
		this.addRenderableWidget(Button.builder(Component.translatable(Diario.data().visible ? "aurora_guia.diario.hide" : "aurora_guia.diario.show"), b -> {
			Diario.data().visible = !Diario.data().visible;
			Diario.save();
			rebuildWidgets();
		}).bounds(cx - 100, by, 120, 20).build());
		this.addRenderableWidget(Button.builder(Component.translatable("gui.done"), b -> this.onClose()).bounds(cx + 30, by, 120, 20).build());
		this.setInitialFocus(this.input);
	}

	private void add() {
		String t = this.input.getValue().strip();
		if (!t.isEmpty()) {
			Diario.goals().add(new Diario.Goal(t));
			Diario.save();
			this.input.setValue("");
			rebuildWidgets();
		}
	}

	@Override
	public void extractRenderState(GuiGraphicsExtractor g, int mouseX, int mouseY, float a) {
		super.extractRenderState(g, mouseX, mouseY, a);
		g.centeredText(this.font, this.title, this.width / 2, 20, 0xFFFFE08C);
	}

	@Override
	public boolean isPauseScreen() {
		return true;
	}
}

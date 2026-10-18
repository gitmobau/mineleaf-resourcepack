package dev.mineleaf.auroraguia.anvil;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;

import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AnvilScreen;
import net.minecraft.client.gui.screens.inventory.tooltip.TooltipRenderUtil;
import net.minecraft.client.player.LocalPlayer;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.util.FormattedCharSequence;
import net.minecraft.util.Util;
import net.minecraft.world.inventory.AnvilMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;

/**
 * "Yunque inteligente": a side panel on the anvil screen. For the pair on the anvil it says whether the other
 * way round is cheaper and what penalty the result keeps; below, the cheapest order to put the useful
 * enchanted books of the inventory on the item. It only reads and draws; it never moves items or changes costs.
 * The panel uses the tooltip background, so it takes the look of the resource pack.
 */
public final class AnvilOverlay {
	private static final int ANVIL_W = 176, ANVIL_H = 166;
	/** Aurora HUD XL draws the anvil 14 px wider on each side: keep clear of its ornaments when there is room. */
	private static final int GAP = 16, GAP_TIGHT = 4, EDGE = 4;
	private static final int MIN_W = 100, MAX_W = 200, PAD = 5, LINE = 10, SECTION = 5;
	private static final int MAX_BOOKS = 8;
	private static final int TEXT = 0xFFFFFFFF, DIM = 0xFFBFB2E0, TITLE = 0xFFFFE08C, GOOD = 0xFF9CF5C0,
		WARN = 0xFFFFB0C8, ITEM = 0xFF9CE0FF, RULE = 0x50C8A0FF;

	/**
	 * One paragraph: an optional prefix ("1.") with the text wrapped beside it (hanging indent), and an optional
	 * number aligned right on the first line.
	 */
	private record Row(FormattedCharSequence prefix, int indent, List<FormattedCharSequence> lines, FormattedCharSequence right,
		int rightWidth, boolean section) {
	}

	private record Layout(List<Row> rows, int width, int height) {
	}

	// cache: the panel is only rebuilt when something it depends on changes
	private static final List<ItemStack> seen = new ArrayList<>();
	private static final List<ItemStack> now = new ArrayList<>();
	private static int seenCost = -1, seenXp = -1, seenWidth = -1;
	private static Layout layout;

	/** The plan is worked out on a background thread (8 books can take tens of ms); the panel shows it when ready. */
	private record PlanInput(Object item, AnvilMath.Piece target, List<AnvilMath.Piece> books, int preferred) {
	}

	private static PlanInput planInput;
	private static CompletableFuture<AnvilMath.Plan> planFuture;
	private static boolean waiting;

	private AnvilOverlay() {
	}

	public static void register() {
		ScreenEvents.AFTER_INIT.register((client, screen, w, h) -> {
			if (screen instanceof AnvilScreen anvil) {
				ScreenEvents.afterExtract(screen).register((s, g, mx, my, a) -> draw(anvil, g));
			}
		});
	}

	private static void draw(AnvilScreen screen, GuiGraphicsExtractor g) {
		Minecraft mc = Minecraft.getInstance();
		LocalPlayer player = mc.player;
		if (player == null || mc.level == null) {
			return;
		}
		AnvilMenu menu = screen.getMenu();
		ItemStack left = menu.getSlot(AnvilMenu.INPUT_SLOT).getItem();
		if (left.isEmpty()) {
			return;                                            // nothing to say: keep the screen clean
		}
		now.clear();
		now.add(left);
		now.add(menu.getSlot(AnvilMenu.ADDITIONAL_SLOT).getItem());
		now.add(menu.getSlot(AnvilMenu.RESULT_SLOT).getItem());
		for (ItemStack s : player.getInventory().getNonEquipmentItems()) {
			if (McAnvil.isBook(s)) {
				now.add(s);
			}
		}
		int room = screen.width - (screen.width + ANVIL_W) / 2 - EDGE;
		int gap = room - GAP >= MIN_W + 2 * PAD ? GAP : GAP_TIGHT;
		int width = Math.max(MIN_W, Math.min(MAX_W, room - gap - 2 * PAD));
		int xp = player.hasInfiniteMaterials() ? Integer.MAX_VALUE : player.experienceLevel;
		if (changed(menu.getCost(), xp, width) || waiting && planFuture.isDone()) {
			layout = layout(mc.font, build(mc, menu, xp), width);
		}
		if (layout != null) {
			render(screen, g, mc.font, layout, (screen.width + ANVIL_W) / 2 + gap, room - gap);
		}
	}

	private static boolean changed(int cost, int xp, int width) {
		boolean same = cost == seenCost && xp == seenXp && width == seenWidth && now.size() == seen.size();
		for (int i = 0; same && i < now.size(); i++) {
			same = ItemStack.matches(now.get(i), seen.get(i));
		}
		if (!same) {
			seen.clear();
			now.forEach(s -> seen.add(s.copy()));
			seenCost = cost;
			seenXp = xp;
			seenWidth = width;
		}
		return !same;
	}

	// ------------------------------------------------------------------ content

	private record Text(Component prefix, Component text, Component right, boolean section) {
		Text(Component text, Component right, boolean section) {
			this(null, text, right, section);
		}
	}

	private static List<Text> build(Minecraft mc, AnvilMenu menu, int xp) {
		List<Text> out = new ArrayList<>();
		waiting = false;
		ItemStack left = menu.getSlot(AnvilMenu.INPUT_SLOT).getItem();
		ItemStack right = menu.getSlot(AnvilMenu.ADDITIONAL_SLOT).getItem();
		ItemStack result = menu.getSlot(AnvilMenu.RESULT_SLOT).getItem();
		Map<String, Holder<Enchantment>> reg = McAnvil.registry(mc.level.registryAccess());
		AnvilMath.Piece target = McAnvil.piece(left);
		AnvilMath.Rules rules = McAnvil.rules(left, reg);

		// --- the pair that is on the anvil now
		if (!right.isEmpty()) {
			swap(left, right, target, rules, reg).ifPresent(out::add);
			if (!result.isEmpty()) {
				int rc = McAnvil.repairCost(result);
				out.add(new Text(color(Component.translatable("aurora_guia.anvil.after", penalty(rc)), DIM), null, false));
			}
		}

		// --- cheapest order with the books of the inventory (and the one on the anvil)
		if (McAnvil.isBook(left) || left.getCount() > 1) {
			return out;                                        // merging books / a stack: nothing to plan
		}
		List<ItemStack> pool = new ArrayList<>();
		int preferred = -1;
		if (McAnvil.isBook(right)) {
			preferred = 0;
			pool.add(right);
		}
		for (ItemStack s : mc.player.getInventory().getNonEquipmentItems()) {
			if (McAnvil.isBook(s)) {
				pool.add(s);
			}
		}
		List<AnvilMath.Piece> pieces = pool.stream().map(McAnvil::piece).toList();
		List<Integer> idx = AnvilMath.candidates(target, pieces, rules, preferred, MAX_BOOKS);
		boolean anyGain = idx.stream().anyMatch(i -> AnvilMath.gain(target, pieces.get(i), rules) > 0);
		if (!anyGain) {
			if (out.isEmpty() && !McAnvil.improvable(left, reg).isEmpty()) {
				out.add(new Text(color(Component.translatable("aurora_guia.anvil.no_books"), DIM), null, false));
			}
			return out;
		}
		List<ItemStack> chosen = idx.stream().map(pool::get).toList();
		PlanInput input = new PlanInput(left.getItem(), target, idx.stream().map(pieces::get).toList(), idx.indexOf(preferred));
		if (!input.equals(planInput)) {
			java.util.Set<String> ids = new java.util.HashSet<>(target.enchantments().keySet());
			input.books().forEach(b -> ids.addAll(b.enchantments().keySet()));
			AnvilMath.Rules frozen = AnvilMath.freeze(rules, ids);
			planInput = input;
			planFuture = CompletableFuture.supplyAsync(() -> AnvilMath.optimize(input.target(), input.books(), frozen,
				input.preferred()), Util.backgroundExecutor());
		}
		waiting = !planFuture.isDone();
		if (waiting) {
			out.add(new Text(color(Component.translatable("aurora_guia.anvil.thinking"), DIM), null, !out.isEmpty()));
			return out;
		}
		AnvilMath.Plan plan = planFuture.isCompletedExceptionally() ? null : planFuture.join();
		if (plan == null) {
			out.add(new Text(color(Component.translatable("aurora_guia.anvil.impossible"), WARN), null, !out.isEmpty()));
			return out;
		}
		List<AnvilMath.Step> steps = plan.steps();
		int books = Integer.bitCount(plan.used()) - 1;
		out.add(new Text(color(Component.translatable("aurora_guia.anvil.plan"), TITLE),
			color(Component.translatable(books == 1 ? "aurora_guia.anvil.books_one" : "aurora_guia.anvil.books", books), DIM),
			!out.isEmpty()));
		List<AnvilMath.Node> done = new ArrayList<>();
		for (AnvilMath.Step s : steps) {
			done.add(s);
			MutableComponent line = Component.empty().append(ref(s.left(), left, done, reg))
				.append(color(Component.literal(" + "), DIM)).append(ref(s.right(), left, done, reg));
			out.add(new Text(color(Component.literal(done.size() + "."), DIM), line,
				color(Component.literal(String.valueOf(s.cost())), TEXT), false));
		}
		out.add(new Text(color(Component.translatable("aurora_guia.anvil.total"), GOOD),
			color(Component.translatable("aurora_guia.anvil.levels", plan.total()), GOOD), false));
		if (xp < plan.total()) {
			out.add(new Text(color(Component.translatable("aurora_guia.anvil.short", plan.total() - xp), WARN), null, false));
		}
		out.add(new Text(color(Component.translatable("aurora_guia.anvil.final", penalty(plan.root().piece().repairCost())), DIM),
			null, false));
		// books that would add something but were left out (an alternative to one in the plan, or too expensive)
		MutableComponent unused = Component.empty();
		for (int i = 0; i < chosen.size(); i++) {
			if (!plan.uses(i) && AnvilMath.gain(target, pieces.get(idx.get(i)), rules) > 0) {
				if (!unused.getSiblings().isEmpty()) {
					unused.append(", ");
				}
				unused.append(bookName(McAnvil.piece(chosen.get(i)), reg));
			}
		}
		if (!unused.getSiblings().isEmpty()) {
			out.add(new Text(color(Component.translatable("aurora_guia.anvil.unused", unused), DIM), null, false));
		}
		return out;
	}

	/** "Swap them" when the other way round gives the same result for fewer levels. */
	private static java.util.Optional<Text> swap(ItemStack left, ItemStack right, AnvilMath.Piece target, AnvilMath.Rules rules,
		Map<String, Holder<Enchantment>> reg) {
		boolean books = McAnvil.isBook(left) && McAnvil.isBook(right);
		boolean items = !McAnvil.isBook(left) && ItemStack.isSameItem(left, right) && left.isDamageableItem();
		if (!books && !items || left.getCount() > 1 || right.getCount() > 1) {
			return java.util.Optional.empty();
		}
		AnvilMath.Piece other = McAnvil.piece(right);
		AnvilMath.Result cur = AnvilMath.combine(target, other, rules);
		AnvilMath.Result rev = AnvilMath.combine(other, target, McAnvil.rules(right, reg));
		if (cur == null || rev == null || !cur.piece().enchantments().equals(rev.piece().enchantments())) {
			return java.util.Optional.empty();
		}
		int curCost = cur.cost(), revCost = rev.cost();
		if (items) {
			curCost += AnvilMath.durabilityFee(left.getMaxDamage(), left.getDamageValue(), right.getDamageValue());
			revCost += AnvilMath.durabilityFee(right.getMaxDamage(), right.getDamageValue(), left.getDamageValue());
		}
		if (revCost >= curCost || revCost >= AnvilMath.TOO_EXPENSIVE) {
			return java.util.Optional.empty();
		}
		return java.util.Optional.of(new Text(color(Component.translatable("aurora_guia.anvil.swap", revCost, curCost - revCost), WARN),
			null, false));
	}

	/** Leaves by name (books: their enchantments; the item: its name); earlier steps by number. */
	private static Component ref(AnvilMath.Node n, ItemStack target, List<AnvilMath.Node> done, Map<String, Holder<Enchantment>> reg) {
		if (n instanceof AnvilMath.Leaf l) {
			return l.index() == 0 ? color(target.getHoverName().copy(), ITEM) : bookName(l.piece(), reg);
		}
		return color(Component.literal("(" + (done.indexOf(n) + 1) + ")"), DIM);
	}

	private static Component bookName(AnvilMath.Piece p, Map<String, Holder<Enchantment>> reg) {
		MutableComponent c = Component.empty();
		for (Map.Entry<String, Integer> e : p.enchantments().entrySet()) {
			Holder<Enchantment> h = reg.get(e.getKey());
			if (h != null) {
				if (!c.getSiblings().isEmpty()) {
					c.append(", ");
				}
				c.append(McAnvil.name(h, e.getValue()));
			}
		}
		return color(c, TEXT);
	}

	private static Component penalty(int repairCost) {
		int uses = AnvilMath.uses(repairCost);
		return Component.translatable(uses == 1 ? "aurora_guia.penalty_one" : "aurora_guia.penalty", repairCost, uses);
	}

	private static MutableComponent color(MutableComponent c, int rgb) {
		return Component.empty().withColor(rgb & 0xFFFFFF).append(c);
	}

	// ------------------------------------------------------------------ drawing

	private static Layout layout(Font font, List<Text> texts, int width) {
		if (texts.isEmpty()) {
			return null;
		}
		List<Row> rows = new ArrayList<>();
		int h = 0, used = 0;
		for (Text t : texts) {
			FormattedCharSequence right = t.right() == null ? null : t.right().getVisualOrderText();
			int rw = right == null ? 0 : font.width(right) + 4;
			FormattedCharSequence prefix = t.prefix() == null ? null : t.prefix().getVisualOrderText();
			int indent = prefix == null ? 0 : font.width("00.") + 3;
			List<FormattedCharSequence> lines = font.split(t.text(), width - rw - indent);
			boolean section = t.section() && !rows.isEmpty();
			rows.add(new Row(prefix, indent, lines, right, rw, section));
			h += lines.size() * LINE + (section ? SECTION : 0);
			for (FormattedCharSequence line : lines) {
				used = Math.max(used, indent + font.width(line) + rw);
			}
		}
		return new Layout(rows, Math.min(width, used), h - 1);      // as narrow as the text allows
	}

	/** To the right of the anvil, from {@code x0}; shrunk only when it does not fit in {@code room}. */
	private static void render(AnvilScreen screen, GuiGraphicsExtractor g, Font font, Layout l, int x0, int room) {
		int boxW = l.width() + 2 * PAD, boxH = l.height() + 2 * PAD;
		float scale = Math.min(1f, Math.min((float) room / boxW, (float) (screen.height - 2 * EDGE) / boxH));
		scale = Math.max(0.5f, scale);
		int anvilTop = (screen.height - ANVIL_H) / 2;
		int y0 = Math.max(EDGE, Math.min(anvilTop, screen.height - EDGE - Math.round(boxH * scale)));
		g.pose().pushMatrix();
		g.pose().translate(x0, y0);
		g.pose().scale(scale, scale);
		// the tooltip sprites leave 3 px of padding around the content they are given
		TooltipRenderUtil.extractTooltipBackground(g, 3, 3, boxW - 6, boxH - 6, null);
		int y = PAD;
		for (Row r : l.rows()) {
			if (r.section()) {
				g.horizontalLine(PAD, PAD + l.width() - 1, y + 1, RULE);  // thin rule in the gap above the section
				y += SECTION;
			}
			if (r.right() != null) {
				g.text(font, r.right(), PAD + l.width() - r.rightWidth() + 4, y, TEXT, true);
			}
			if (r.prefix() != null) {
				g.text(font, r.prefix(), PAD, y, TEXT, true);
			}
			for (FormattedCharSequence line : r.lines()) {
				g.text(font, line, PAD + r.indent(), y, TEXT, true);
				y += LINE;
			}
		}
		g.pose().popMatrix();
	}
}

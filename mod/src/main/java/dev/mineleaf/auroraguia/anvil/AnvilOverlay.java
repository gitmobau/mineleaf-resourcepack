package dev.mineleaf.auroraguia.anvil;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;

import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.inventory.AnvilScreen;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.world.inventory.AnvilMenu;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;

/**
 * "Yunque inteligente": a side panel on the anvil screen with the cost of the current pair, the cost the
 * other way round, and the cheapest order to put every useful enchanted book of the inventory on the item.
 * It only reads and draws; it never moves items or changes costs.
 */
public final class AnvilOverlay {
	private static final int W = 176, H = 166, PANEL_W = 156;
	private static final int MAX_BOOKS = 8;
	private static final int BG = 0xE0201436, EDGE = 0xFFB48CFF, TEXT = 0xFFFFFFFF, DIM = 0xFFC8B8F0,
		GOOD = 0xFF8CFFB4, WARN = 0xFFFFB0C8, GOLD = 0xFFFFE08C;

	private static String cacheKey = "";
	private static Panel cached;

	private AnvilOverlay() {
	}

	public static void register() {
		ScreenEvents.AFTER_INIT.register((client, screen, w, h) -> {
			if (screen instanceof AnvilScreen anvil) {
				ScreenEvents.afterExtract(screen).register((s, g, mx, my, a) -> draw(anvil, g));
			}
		});
	}

	/** parts: item icons or short strings drawn before {@code text}. */
	private record Line(List<Object> parts, Component text, int color) {
		boolean icons() {
			return parts.stream().anyMatch(p -> p instanceof ItemStack);
		}
	}

	private record Panel(List<Line> lines) {
	}

	private static void draw(AnvilScreen screen, GuiGraphicsExtractor g) {
		Minecraft mc = Minecraft.getInstance();
		if (mc.player == null || mc.level == null) {
			return;
		}
		AnvilMenu menu = screen.getMenu();
		ItemStack left = menu.getSlot(AnvilMenu.INPUT_SLOT).getItem();
		ItemStack right = menu.getSlot(AnvilMenu.ADDITIONAL_SLOT).getItem();
		List<ItemStack> books = new ArrayList<>();
		for (ItemStack s : mc.player.getInventory().getNonEquipmentItems()) {
			if (McAnvil.isBook(s)) {
				books.add(s);
			}
		}
		String key = describe(left) + "|" + describe(right) + "|" + menu.getCost() + "|"
			+ books.stream().map(AnvilOverlay::describe).sorted().toList();
		if (!key.equals(cacheKey)) {
			cacheKey = key;
			cached = build(mc, menu, left, right, books);
		}
		render(screen, g, mc.font, cached);
	}

	private static String describe(ItemStack s) {
		return s.isEmpty() ? "-" : s.getItem() + "x" + s.getCount() + McAnvil.piece(s).key() + s.getDamageValue();
	}

	private static Panel build(Minecraft mc, AnvilMenu menu, ItemStack left, ItemStack right, List<ItemStack> books) {
		List<Line> out = new ArrayList<>();
		out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.title"), GOLD));
		if (left.isEmpty()) {
			out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.put_left"), DIM));
			return new Panel(out);
		}
		Map<String, Holder<Enchantment>> reg = McAnvil.registry(mc.level.registryAccess());
		AnvilMath.Piece target = McAnvil.piece(left);
		AnvilMath.Rules rules = McAnvil.rules(left, reg);

		// --- the pair that is on the anvil now
		if (!right.isEmpty()) {
			int now = menu.getCost();
			boolean swappable = McAnvil.isBook(left) == McAnvil.isBook(right) && ItemStack.isSameItem(left, right);
			if (now > 0) {
				out.add(new Line(List.of(left, "+", right), Component.translatable("aurora_guia.anvil.now", now),
					now >= AnvilMath.TOO_EXPENSIVE ? WARN : TEXT));
			}
			if (swappable) {
				AnvilMath.Result rev = AnvilMath.combine(McAnvil.piece(right), target, McAnvil.rules(right, reg));
				AnvilMath.Result cur = AnvilMath.combine(target, McAnvil.piece(right), rules);
				if (rev != null && cur != null && rev.cost() < cur.cost()) {
					out.add(new Line(List.of(right, "+", left), Component.translatable("aurora_guia.anvil.swap", rev.cost()), WARN));
					out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.swap_hint", cur.cost() - rev.cost()), WARN));
				}
			}
			AnvilMath.Result cur = AnvilMath.combine(target, McAnvil.piece(right), rules);
			if (cur != null) {
				int rc = cur.piece().repairCost();
				out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.after", rc, AnvilMath.uses(rc)), DIM));
			}
		}

		// --- cheapest plan with the useful books of the inventory (+ the right slot if it holds a book)
		List<ItemStack> pool = new ArrayList<>(books);
		if (McAnvil.isBook(right)) {
			pool.add(right);
		}
		List<ItemStack> chosen = choose(target, pool, rules);
		if (chosen.isEmpty()) {
			out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.no_books"), DIM));
			return new Panel(out);
		}
		List<AnvilMath.Piece> pieces = chosen.stream().map(McAnvil::piece).toList();
		AnvilMath.Plan plan = AnvilMath.optimize(target, pieces, rules);
		out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.plan", chosen.size()), GOLD));
		if (plan == null) {
			out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.impossible"), WARN));
			return new Panel(out);
		}
		List<ItemStack> leaves = new ArrayList<>();
		leaves.add(left);
		leaves.addAll(chosen);
		Map<AnvilMath.Node, Integer> stepNo = new HashMap<>();
		int i = 1;
		for (AnvilMath.Step s : plan.steps()) {
			stepNo.put(s, i);
			List<Object> parts = new ArrayList<>();
			parts.add(i + ".");
			parts.add(ref(s.left(), stepNo, leaves));
			parts.add("+");
			parts.add(ref(s.right(), stepNo, leaves));
			out.add(new Line(parts, Component.translatable("aurora_guia.anvil.step", s.cost()), TEXT));
			if (s.left() instanceof AnvilMath.Leaf || s.right() instanceof AnvilMath.Leaf) {
				// the books all look alike: say which ones they are
				out.add(new Line(List.of(), Component.literal("   ").append(name(s.left(), stepNo, leaves, reg))
					.append(" + ").append(name(s.right(), stepNo, leaves, reg)), DIM));
			}
			i++;
		}
		out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.total", plan.total(), plan.maxStep()), GOOD));
		int rc = plan.root().piece().repairCost();
		out.add(new Line(List.of(), Component.translatable("aurora_guia.anvil.after", rc, AnvilMath.uses(rc)), DIM));
		return new Panel(out);
	}

	private static Component name(AnvilMath.Node n, Map<AnvilMath.Node, Integer> stepNo, List<ItemStack> leaves,
		Map<String, Holder<Enchantment>> reg) {
		if (!(n instanceof AnvilMath.Leaf l)) {
			return Component.literal("(" + stepNo.get(n) + ")");
		}
		ItemStack s = leaves.get(l.index());
		if (!McAnvil.isBook(s)) {
			return s.getHoverName();
		}
		net.minecraft.network.chat.MutableComponent c = Component.empty();
		boolean first = true;
		for (Map.Entry<String, Integer> e : l.piece().enchantments().entrySet()) {
			Holder<Enchantment> h = reg.get(e.getKey());
			if (h == null) {
				continue;
			}
			if (!first) {
				c.append(", ");
			}
			c.append(Component.empty().append(Enchantment.getFullname(h, e.getValue())).withColor(DIM));
			first = false;
		}
		return c;
	}

	/** Leaves are drawn as icons; earlier steps are referred to by number. */
	private static Object ref(AnvilMath.Node n, Map<AnvilMath.Node, Integer> stepNo, List<ItemStack> leaves) {
		if (n instanceof AnvilMath.Leaf l) {
			return leaves.get(l.index());
		}
		return "(" + stepNo.get(n) + ")";
	}

	/**
	 * Books that add something to the target, most valuable first, dropping any that clash with what is
	 * already kept (the anvil would charge for the clash and apply nothing).
	 */
	static List<ItemStack> choose(AnvilMath.Piece target, List<ItemStack> pool, AnvilMath.Rules rules) {
		record Cand(ItemStack stack, Map<String, Integer> useful, int value) {
		}
		List<Cand> cands = new ArrayList<>();
		for (ItemStack s : pool) {
			AnvilMath.Piece p = McAnvil.piece(s);
			Map<String, Integer> useful = new HashMap<>();
			int value = 0;
			for (Map.Entry<String, Integer> e : p.enchantments().entrySet()) {
				String id = e.getKey();
				int have = target.enchantments().getOrDefault(id, 0);
				boolean raises = e.getValue() > have || e.getValue() == have && have < rules.maxLevel(id);
				boolean clash = target.enchantments().keySet().stream().anyMatch(o -> !o.equals(id) && !rules.areCompatible(id, o));
				if (rules.canEnchant(id) && raises && !clash) {
					useful.put(id, e.getValue());
					value += rules.anvilCost(id) * e.getValue();
				}
			}
			if (!useful.isEmpty() && useful.size() == p.enchantments().size()) {
				cands.add(new Cand(s, useful, value));
			}
		}
		cands.sort(Comparator.comparingInt(Cand::value).reversed());
		List<ItemStack> kept = new ArrayList<>();
		Set<String> have = new HashSet<>(target.enchantments().keySet());
		for (Cand c : cands) {
			if (kept.size() >= MAX_BOOKS) {
				break;
			}
			boolean ok = c.useful().keySet().stream().allMatch(id -> have.stream().allMatch(o -> o.equals(id) || rules.areCompatible(id, o)));
			if (ok) {
				kept.add(c.stack());
				have.addAll(c.useful().keySet());
			}
		}
		return kept;
	}

	private static int height(Font font, Line l) {
		if (l.icons()) {
			return 18;
		}
		return l.parts().isEmpty() ? font.split(l.text(), PANEL_W - 10).size() * 10 + 2 : 12;
	}

	private static void render(AnvilScreen screen, GuiGraphicsExtractor g, Font font, Panel panel) {
		if (panel == null) {
			return;
		}
		int left = (screen.width - W) / 2, top = (screen.height - H) / 2;
		int h = 8;
		for (Line l : panel.lines()) {
			h += height(font, l);
		}
		// to the right of the anvil; shrink to fit the free space instead of covering the anvil
		int room = screen.width - (left + W) - 6;
		float scale = Math.min(1f, Math.min((float) room / PANEL_W, (float) (screen.height - 4) / h));
		int x0 = left + W + 4;
		if (scale < 0.5f) {               // no room at all: left side, same rule
			room = left - 6;
			scale = Math.max(0.5f, Math.min(1f, (float) room / PANEL_W));
			x0 = Math.max(2, left - 4 - Math.round(PANEL_W * scale));
		}
		int y0 = Math.max(2, Math.min(top, screen.height - 2 - Math.round(h * scale)));
		g.pose().pushMatrix();
		g.pose().translate(x0, y0);
		g.pose().scale(scale, scale);
		int x = 0;
		g.fill(x, 0, x + PANEL_W, h, BG);
		g.outline(x, 0, PANEL_W, h, EDGE);
		int y = 5;
		for (Line l : panel.lines()) {
			int tx = x + 5;
			if (!l.parts().isEmpty()) {
				int ty = l.icons() ? y + 4 : y;
				for (Object p : l.parts()) {
					if (p instanceof ItemStack s) {
						g.item(s, tx, y);
						tx += 17;
					} else {
						g.text(font, p.toString(), tx, ty, DIM, true);
						tx += font.width(p.toString()) + 3;
					}
				}
				g.text(font, l.text(), tx + 2, ty, l.color(), true);
			} else {
				int yy = y;
				for (var seq : font.split(l.text(), PANEL_W - 10)) {
					g.text(font, seq, tx, yy, l.color(), true);
					yy += 10;
				}
			}
			y += height(font, l);
		}
		g.pose().popMatrix();
	}
}

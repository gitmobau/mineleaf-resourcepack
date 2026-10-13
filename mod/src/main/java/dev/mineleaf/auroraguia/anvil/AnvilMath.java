package dev.mineleaf.auroraguia.anvil;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Pure model of the 26.3 anvil enchanting cost (AnvilMenu.createResult), without durability or renaming.
 * Kept free of Minecraft classes so it can be unit tested.
 */
public final class AnvilMath {
	public static final int TOO_EXPENSIVE = 40;

	private AnvilMath() {
	}

	/** What the anvil needs to know about the enchantments and the target item. */
	public interface Rules {
		int maxLevel(String enchantment);

		int anvilCost(String enchantment);

		/** Enchantment.canEnchant for the target item (supported_items). */
		boolean canEnchant(String enchantment);

		/** Enchantment.areCompatible: false for the same enchantment, like the game. */
		boolean areCompatible(String a, String b);
	}

	/** An item on the anvil: the target item kind or an enchanted book. */
	public record Piece(boolean book, Map<String, Integer> enchantments, int repairCost) {
		public Piece {
			enchantments = Map.copyOf(enchantments);
		}

		String key() {
			return (book ? "B" : "I") + new TreeMap<>(enchantments) + "/" + repairCost;
		}
	}

	public record Result(Piece piece, int cost) {
	}

	public static int increasedRepairCost(int repairCost) {
		return (int) Math.min(repairCost * 2L + 1L, Integer.MAX_VALUE);
	}

	/** Number of anvil uses that produce this repair cost (0, 1, 3, 7 ... -> 0, 1, 2, 3 ...). */
	public static int uses(int repairCost) {
		int n = 0;
		for (long c = 0; c < repairCost; c = c * 2 + 1) {
			n++;
		}
		return n;
	}

	/** left + right on the anvil, or null when the anvil gives no result. Same item kind is assumed for non-books. */
	public static Result combine(Piece left, Piece right, Rules rules) {
		Map<String, Integer> result = new LinkedHashMap<>(left.enchantments());
		int price = 0;
		boolean anyCompatible = false;
		boolean anyIncompatible = false;
		if (!right.book() && left.book()) {
			return null;
		}
		for (Map.Entry<String, Integer> e : right.enchantments().entrySet()) {
			String ench = e.getKey();
			int current = result.getOrDefault(ench, 0);
			int level = e.getValue();
			level = current == level ? level + 1 : Math.max(level, current);
			boolean compatible = left.book() || rules.canEnchant(ench);
			for (String other : result.keySet()) {
				if (!other.equals(ench) && !rules.areCompatible(ench, other)) {
					compatible = false;
					price++;
				}
			}
			if (!compatible) {
				anyIncompatible = true;
			} else {
				anyCompatible = true;
				level = Math.min(level, rules.maxLevel(ench));
				result.put(ench, level);
				int fee = rules.anvilCost(ench);
				if (right.book()) {
					fee = Math.max(1, fee / 2);
				}
				price += fee * level;
			}
		}
		if (anyIncompatible && !anyCompatible || price <= 0) {
			return null;
		}
		int cost = (int) Math.min((long) left.repairCost() + right.repairCost() + price, Integer.MAX_VALUE);
		int repairCost = increasedRepairCost(Math.max(left.repairCost(), right.repairCost()));
		return new Result(new Piece(left.book(), result, repairCost), cost);
	}

	// ------------------------------------------------------------------ planner

	/** One anvil step of a plan. Leaves are indexes into the planner input (0 = target). */
	public sealed interface Node permits Leaf, Step {
		Piece piece();
	}

	public record Leaf(int index, Piece piece) implements Node {
	}

	public record Step(Node left, Node right, int cost, Piece piece) implements Node {
	}

	public record Plan(Node root, int total, int maxStep) {
		/** Steps in the order they must be done (left subtree first). */
		public List<Step> steps() {
			List<Step> out = new ArrayList<>();
			collect(root, out);
			return out;
		}

		private static void collect(Node n, List<Step> out) {
			if (n instanceof Step s) {
				collect(s.left(), out);
				collect(s.right(), out);
				out.add(s);
			}
		}
	}

	private static int power(State s) {
		return s.node().piece().enchantments().values().stream().mapToInt(Integer::intValue).sum();
	}

	private record State(Node node, int total, int maxStep) {
		boolean better(State o) {
			return total < o.total || total == o.total && maxStep < o.maxStep;
		}
	}

	/**
	 * Cheapest order to put every piece of {@code others} onto {@code target}, never paying 40 or more in a
	 * step. Exact dynamic programming over subsets, like encantamientos/yunque.py. Returns null when no order
	 * works. Keep {@code others} small (the cost grows as 3^n).
	 */
	public static Plan optimize(Piece target, List<Piece> others, Rules rules) {
		List<Piece> items = new ArrayList<>();
		items.add(target);
		items.addAll(others);
		int n = items.size();
		Map<Integer, Map<String, State>> best = new HashMap<>();
		for (int i = 0; i < n; i++) {
			Map<String, State> m = new HashMap<>();
			m.put(items.get(i).key(), new State(new Leaf(i, items.get(i)), 0, 0));
			best.put(1 << i, m);
		}
		int full = (1 << n) - 1;
		List<Integer> masks = new ArrayList<>();
		for (int m = 1; m <= full; m++) {
			masks.add(m);
		}
		masks.sort((a, b) -> Integer.bitCount(a) - Integer.bitCount(b));
		for (int mask : masks) {
			if (best.containsKey(mask)) {
				continue;
			}
			Map<String, State> states = new HashMap<>();
			for (int a = (mask - 1) & mask; a > 0; a = (a - 1) & mask) {
				int b = mask ^ a;
				if ((b & 1) != 0) {
					continue;          // the target is never the sacrifice
				}
				Map<String, State> sa = best.get(a);
				Map<String, State> sb = best.get(b);
				if (sa == null || sb == null) {
					continue;
				}
				for (State la : sa.values()) {
					for (State lb : sb.values()) {
						Result r = combine(la.node().piece(), lb.node().piece(), rules);
						if (r == null || r.cost() >= TOO_EXPENSIVE) {
							continue;
						}
						State cand = new State(new Step(la.node(), lb.node(), r.cost(), r.piece()),
							la.total() + lb.total() + r.cost(), Math.max(r.cost(), Math.max(la.maxStep(), lb.maxStep())));
						String k = r.piece().key();
						State old = states.get(k);
						if (old == null || cand.better(old)) {
							states.put(k, cand);
						}
					}
				}
			}
			if (!states.isEmpty()) {
				best.put(mask, states);
			}
		}
		Map<String, State> fin = best.get(full);
		if (fin == null) {
			return null;
		}
		// orders can end with different levels (III + III + IV): keep the strongest result, then the cheapest
		State win = null;
		for (State s : fin.values()) {
			if (win == null || power(s) > power(win) || power(s) == power(win) && s.better(win)) {
				win = s;
			}
		}
		return win == null ? null : new Plan(win.node(), win.total(), win.maxStep());
	}
}

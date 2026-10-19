package dev.mineleaf.auroraguia.anvil;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Pure model of the 26.3 anvil cost (AnvilMenu.createResult) for enchanting, plus the durability fee of
 * combining two equal items. Renaming and repairing with material are not modelled (the panel reads those
 * from the real menu). Kept free of Minecraft classes so it can be unit tested.
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

		/** Curses (and anything else the player does not want, like Thorns) never count as an improvement. */
		default boolean isCurse(String enchantment) {
			return false;
		}
	}

	/**
	 * A copy of {@code rules} for the given enchantments as plain tables: cheap to ask and safe to use from
	 * another thread (the planner runs off the render thread).
	 */
	public static Rules freeze(Rules rules, java.util.Collection<String> ids) {
		Map<String, int[]> info = new HashMap<>();             // max level, anvil cost, can enchant, curse
		Map<String, java.util.Set<String>> clashes = new HashMap<>();
		for (String a : ids) {
			info.put(a, new int[] {rules.maxLevel(a), rules.anvilCost(a), rules.canEnchant(a) ? 1 : 0, rules.isCurse(a) ? 1 : 0});
			for (String b : ids) {
				if (!rules.areCompatible(a, b)) {
					clashes.computeIfAbsent(a, k -> new java.util.HashSet<>()).add(b);
				}
			}
		}
		int[] unknown = {1, 1, 0, 0};
		return new Rules() {
			@Override
			public int maxLevel(String e) {
				return info.getOrDefault(e, unknown)[0];
			}

			@Override
			public int anvilCost(String e) {
				return info.getOrDefault(e, unknown)[1];
			}

			@Override
			public boolean canEnchant(String e) {
				return info.getOrDefault(e, unknown)[2] == 1;
			}

			@Override
			public boolean areCompatible(String a, String b) {
				return info.containsKey(a) && info.containsKey(b) && !clashes.getOrDefault(a, java.util.Set.of()).contains(b);
			}

			@Override
			public boolean isCurse(String e) {
				return info.getOrDefault(e, unknown)[3] == 1;
			}
		};
	}

	/** An item on the anvil: the target item kind or an enchanted book. */
	public record Piece(boolean book, Map<String, Integer> enchantments, int repairCost) {
		public Piece {
			enchantments = Map.copyOf(enchantments);
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

	/**
	 * Extra levels for the durability when two equal damageable items are combined: 2 when the left one gets
	 * repaired, 0 when it is already at full durability (or the sacrifice is too worn to help).
	 */
	public static int durabilityFee(int maxDamage, int leftDamage, int rightDamage) {
		long remaining = (long) (maxDamage - leftDamage) + (maxDamage - rightDamage) + maxDamage * 12L / 100;
		long resultDamage = Math.max(0, maxDamage - remaining);
		return resultDamage < leftDamage ? 2 : 0;
	}

	/** left + right on the anvil, or null when the anvil gives no result. Same item kind is assumed for non-books. */
	public static Result combine(Piece left, Piece right, Rules rules) {
		if (!right.book() && left.book()) {
			return null;
		}
		Map<String, Integer> result = new LinkedHashMap<>(left.enchantments());
		int price = 0;
		boolean anyCompatible = false;
		boolean anyIncompatible = false;
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

	/**
	 * How complete a piece is: every enchantment that is not a curse adds level / max level, so Mending
	 * (1/1) is worth as much as Sharpness V (5/5) and Sharpness V is worth more than Sharpness IV.
	 */
	public static double value(Piece piece, Rules rules) {
		double v = 0;
		for (Map.Entry<String, Integer> e : piece.enchantments().entrySet()) {
			if (!rules.isCurse(e.getKey())) {
				int max = Math.max(1, rules.maxLevel(e.getKey()));
				v += (double) Math.min(e.getValue(), max) / max;
			}
		}
		return v;
	}

	/**
	 * What {@code book} alone adds to {@code target} (same scale as {@link #value}), or -1 when it is not worth
	 * considering: it would put a curse on it, or none of its enchantments can still be raised on it.
	 * 0 means "might help combined with another book" (two Sharpness III books make IV).
	 */
	public static double gain(Piece target, Piece book, Rules rules) {
		double gain = 0;
		boolean raisable = false;
		for (Map.Entry<String, Integer> e : book.enchantments().entrySet()) {
			String id = e.getKey();
			if (!rules.canEnchant(id) || target.enchantments().keySet().stream()
				.anyMatch(o -> !o.equals(id) && !rules.areCompatible(id, o))) {
				continue;                                      // the anvil skips it (or charges 1 for the clash)
			}
			if (rules.isCurse(id)) {
				return -1;
			}
			int max = Math.max(1, rules.maxLevel(id));
			int have = target.enchantments().getOrDefault(id, 0);
			if (have < max) {
				raisable = true;
				int lvl = e.getValue();
				int after = Math.min(max, lvl == have ? lvl + 1 : Math.max(lvl, have));
				gain += (double) (after - have) / max;
			}
		}
		return raisable ? gain : -1;
	}

	/**
	 * Indexes of the books worth giving to {@link #optimize}: the preferred one first, then the ones that add
	 * the most. At most {@code limit}.
	 */
	public static List<Integer> candidates(Piece target, List<Piece> books, Rules rules, int preferred, int limit) {
		List<Integer> out = new ArrayList<>();
		Map<Integer, Double> gains = new HashMap<>();
		for (int i = 0; i < books.size(); i++) {
			double g = gain(target, books.get(i), rules);
			if (g >= 0) {
				out.add(i);
				gains.put(i, i == preferred ? Double.MAX_VALUE : g);
			}
		}
		out.sort((a, b) -> Double.compare(gains.get(b), gains.get(a)));
		return out.size() > limit ? List.copyOf(out.subList(0, limit)) : out;
	}

	/**
	 * Last tie-break between alternatives that cost the same: the general-purpose enchantment has the lower
	 * anvil cost (Sharpness 1 vs Smite 2, Protection 1 vs Blast Protection 2, Mending 2 vs Infinity 8).
	 */
	private static int weight(Piece piece, Rules rules) {
		int w = 0;
		for (String e : piece.enchantments().keySet()) {
			w += rules.anvilCost(e);
		}
		return w;
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

	/** {@code used}: bit i set when input i is part of the plan (bit 0 = target, bit i = others[i - 1]). */
	public record Plan(Node root, int total, int maxStep, int used) {
		/** Steps in the order they must be done (left subtree first). */
		public List<Step> steps() {
			List<Step> out = new ArrayList<>();
			collect(root, out);
			return out;
		}

		/** Whether others[i] is used. */
		public boolean uses(int other) {
			return (used >> (other + 1) & 1) != 0;
		}

		private static void collect(Node n, List<Step> out) {
			if (n instanceof Step s) {
				collect(s.left(), out);
				collect(s.right(), out);
				out.add(s);
			}
		}
	}

	private record State(Node node, int total, int maxStep) {
		/** Later steps only depend on the piece, so a lower or equal penalty and a cheaper past always win. */
		boolean dominates(State o) {
			return node.piece().repairCost() <= o.node.piece().repairCost() && !o.cheaper(this);
		}

		boolean cheaper(State o) {
			return total < o.total || total == o.total && maxStep < o.maxStep;
		}
	}

	public static Plan optimize(Piece target, List<Piece> others, Rules rules) {
		return optimize(target, others, rules, -1);
	}

	/**
	 * Best way to put {@code others} onto {@code target}, never paying 40 or more in a step. Exact dynamic
	 * programming over subsets, like encantamientos/yunque.py, but a piece is left out when it adds nothing
	 * or when it does not fit under 40. Picks, in this order: the most complete result ({@link #value}), the
	 * one that uses {@code others[preferred]} (the book the player put on the anvil: it decides between
	 * alternatives like Sharpness / Smite), the lowest total, the lowest most expensive step, then the
	 * general-purpose alternative ({@link #weight}).
	 * Returns null when no order under 40 improves the target. Keep {@code others} small (the cost grows as 3^n).
	 */
	public static Plan optimize(Piece target, List<Piece> others, Rules rules, int preferred) {
		List<Piece> items = new ArrayList<>();
		items.add(target);
		items.addAll(others);
		int n = items.size();
		List<List<State>> best = new ArrayList<>(1 << n);
		for (int m = 0; m < 1 << n; m++) {
			best.add(null);
		}
		for (int i = 0; i < n; i++) {
			best.set(1 << i, List.of(new State(new Leaf(i, items.get(i)), 0, 0)));
		}
		int full = (1 << n) - 1;
		// any order where every subset comes before its supersets works: increasing numbers do
		for (int mask = 1; mask <= full; mask++) {
			if (Integer.bitCount(mask) < 2) {
				continue;
			}
			// per resulting set of enchantments, the orders that no other order beats in both penalty and total
			Map<Map<String, Integer>, List<State>> states = new HashMap<>();
			for (int a = (mask - 1) & mask; a > 0; a = (a - 1) & mask) {
				int b = mask ^ a;
				if ((b & 1) != 0) {
					continue;          // the target is never the sacrifice
				}
				List<State> sa = best.get(a);
				List<State> sb = best.get(b);
				if (sa == null || sb == null) {
					continue;
				}
				for (State la : sa) {
					for (State lb : sb) {
						Result r = combine(la.node().piece(), lb.node().piece(), rules);
						if (r == null || r.cost() >= TOO_EXPENSIVE) {
							continue;
						}
						State cand = new State(new Step(la.node(), lb.node(), r.cost(), r.piece()),
							la.total() + lb.total() + r.cost(), Math.max(r.cost(), Math.max(la.maxStep(), lb.maxStep())));
						List<State> same = states.computeIfAbsent(r.piece().enchantments(), k -> new ArrayList<>());
						if (same.stream().noneMatch(o -> o.dominates(cand))) {
							same.removeIf(cand::dominates);
							same.add(cand);
						}
					}
				}
			}
			if (!states.isEmpty()) {
				best.set(mask, states.values().stream().flatMap(List::stream).toList());
			}
		}
		int prefBit = preferred < 0 ? 0 : 1 << (preferred + 1);
		State win = null;
		int winMask = 0;
		double winValue = 0;
		for (int mask = 3; mask <= full; mask += 2) {          // odd masks: the ones with the target
			List<State> states = best.get(mask);
			if (states == null) {
				continue;
			}
			for (State s : states) {
				double v = value(s.node().piece(), rules);
				int cmp = win == null ? 1 : Double.compare(Math.round(v * 1e6), Math.round(winValue * 1e6));
				if (cmp == 0) {
					boolean p = (mask & prefBit) != 0, wp = (winMask & prefBit) != 0;
					cmp = p != wp ? (p ? 1 : -1) : s.cheaper(win) ? 1 : win.cheaper(s) ? -1
						: Integer.compare(weight(win.node().piece(), rules), weight(s.node().piece(), rules));
				}
				if (cmp > 0) {
					win = s;
					winMask = mask;
					winValue = v;
				}
			}
		}
		if (win == null || Math.round(winValue * 1e6) <= Math.round(value(target, rules) * 1e6)) {
			return null;                                      // nothing that fits under 40 improves the target
		}
		return new Plan(win.node(), win.total(), win.maxStep(), winMask);
	}
}

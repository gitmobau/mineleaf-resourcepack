package dev.mineleaf.auroraguia.anvil;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;

import java.util.List;
import java.util.Map;
import java.util.Set;

import org.junit.jupiter.api.Test;

/** Values checked by hand against the 26.3 data and the decompiled AnvilMenu (see encantamientos/README.md). */
class AnvilMathTest {
	// id -> max level, anvil cost (26.3 data)
	static final Map<String, int[]> DATA = Map.ofEntries(
		Map.entry("sharpness", new int[] {5, 1}), Map.entry("smite", new int[] {5, 2}),
		Map.entry("looting", new int[] {3, 4}), Map.entry("sweeping_edge", new int[] {3, 4}),
		Map.entry("fire_aspect", new int[] {2, 4}), Map.entry("knockback", new int[] {2, 2}),
		Map.entry("unbreaking", new int[] {3, 2}), Map.entry("mending", new int[] {1, 4}),
		Map.entry("protection", new int[] {4, 1}), Map.entry("feather_falling", new int[] {4, 2}),
		Map.entry("depth_strider", new int[] {3, 4}), Map.entry("respiration", new int[] {3, 4}),
		Map.entry("aqua_affinity", new int[] {1, 4}), Map.entry("efficiency", new int[] {5, 1}),
		Map.entry("silk_touch", new int[] {1, 8}), Map.entry("soul_speed", new int[] {3, 8}));
	static final List<Set<String>> EXCLUSIVE = List.of(Set.of("sharpness", "smite"));

	static AnvilMath.Rules rules(Set<String> applicable) {
		return new AnvilMath.Rules() {
			public int maxLevel(String e) { return DATA.get(e)[0]; }
			public int anvilCost(String e) { return DATA.get(e)[1]; }
			public boolean canEnchant(String e) { return applicable.contains(e); }
			public boolean areCompatible(String a, String b) {
				if (a.equals(b)) return false;
				return EXCLUSIVE.stream().noneMatch(s -> s.contains(a) && s.contains(b));
			}
		};
	}

	static final AnvilMath.Rules SWORD = rules(Set.of("sharpness", "smite", "looting", "sweeping_edge", "fire_aspect", "knockback", "unbreaking", "mending"));
	static final AnvilMath.Rules BOOTS = rules(Set.of("protection", "feather_falling", "depth_strider", "unbreaking", "mending", "soul_speed"));
	static final AnvilMath.Rules HELMET = rules(Set.of("protection", "respiration", "aqua_affinity", "unbreaking", "mending"));
	static final AnvilMath.Rules PICK = rules(Set.of("efficiency", "silk_touch", "unbreaking", "mending"));

	static AnvilMath.Piece item(int rc, Object... kv) { return piece(false, rc, kv); }
	static AnvilMath.Piece book(Object... kv) { return piece(true, 0, kv); }
	static AnvilMath.Piece piece(boolean book, int rc, Object... kv) {
		java.util.Map<String, Integer> m = new java.util.LinkedHashMap<>();
		for (int i = 0; i < kv.length; i += 2) m.put((String) kv[i], (Integer) kv[i + 1]);
		return new AnvilMath.Piece(book, m, rc);
	}

	@Test
	void bootsMergeCosts23() {
		var r = AnvilMath.combine(item(1, "protection", 3, "feather_falling", 4, "depth_strider", 2, "unbreaking", 3, "mending", 1),
			item(0, "protection", 3, "depth_strider", 3, "unbreaking", 3), BOOTS);
		assertEquals(23, r.cost());
		assertEquals(4, r.piece().enchantments().get("protection"));
		assertEquals(3, r.piece().repairCost());
	}

	@Test
	void soulSpeedBookAfterwardsCosts15() {
		var boots = item(3, "protection", 4, "feather_falling", 4, "depth_strider", 3, "unbreaking", 3, "mending", 1);
		assertEquals(15, AnvilMath.combine(boots, book("soul_speed", 3), BOOTS).cost());
	}

	@Test
	void helmetGoodOneLeft() {
		var full = item(0, "protection", 3, "respiration", 3, "aqua_affinity", 1, "unbreaking", 3);
		var prot = item(0, "protection", 4);
		assertEquals(4, AnvilMath.combine(full, prot, HELMET).cost());
		assertEquals(26, AnvilMath.combine(prot, full, HELMET).cost());
	}

	@Test
	void pickaxeOrderMatters() {
		var good = item(0, "efficiency", 4, "unbreaking", 3, "silk_touch", 1);
		var eff = item(0, "efficiency", 4);
		assertEquals(5, AnvilMath.combine(good, eff, PICK).cost());
		assertEquals(19, AnvilMath.combine(eff, good, PICK).cost());
	}

	@Test
	void incompatibleCountsOneAndIsSkipped() {
		var r = AnvilMath.combine(item(0, "sharpness", 5), book("smite", 5, "looting", 3), SWORD);
		assertEquals(7, r.cost());
		assertNull(r.piece().enchantments().get("smite"));
	}

	@Test
	void chargesFinalLevelEvenWhenNotRaised() {
		assertEquals(5, AnvilMath.combine(item(0, "sharpness", 5), book("sharpness", 4), SWORD).cost());
	}

	@Test
	void tooExpensiveIsReported() {
		assertEquals(40, AnvilMath.combine(item(31, "sharpness", 5), piece(true, 7, "mending", 1), SWORD).cost());
	}

	@Test
	void swordPlanMatchesPythonCalculator() {
		var plan = AnvilMath.optimize(item(0), List.of(book("sharpness", 5), book("looting", 3), book("mending", 1),
			book("unbreaking", 3), book("sweeping_edge", 3), book("fire_aspect", 2), book("knockback", 2)), SWORD);
		assertNotNull(plan);
		assertEquals(49, plan.total());
		assertEquals(14, plan.maxStep());
	}

	@Test
	void usesFromRepairCost() {
		assertEquals(0, AnvilMath.uses(0));
		assertEquals(1, AnvilMath.uses(1));
		assertEquals(2, AnvilMath.uses(3));
		assertEquals(5, AnvilMath.uses(31));
	}
}

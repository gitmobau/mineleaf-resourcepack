package dev.mineleaf.auroraguia.anvil;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.junit.jupiter.api.Assertions.assertFalse;

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
		Map.entry("silk_touch", new int[] {1, 8}), Map.entry("soul_speed", new int[] {3, 8}),
		Map.entry("vanishing_curse", new int[] {1, 8}));
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
			public boolean isCurse(String e) { return e.endsWith("_curse"); }
		};
	}

	static final AnvilMath.Rules SWORD = rules(Set.of("sharpness", "smite", "looting", "sweeping_edge", "fire_aspect", "knockback", "unbreaking", "mending", "vanishing_curse"));
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

	// ------------------------------------------------------------------ edge cases

	@Test
	void durabilityFeeOnlyWhenTheLeftOneGetsRepaired() {
		assertEquals(0, AnvilMath.durabilityFee(1561, 0, 800));       // left already at full durability
		assertEquals(2, AnvilMath.durabilityFee(1561, 800, 0));
		assertEquals(2, AnvilMath.durabilityFee(1561, 10, 1560));    // even a worn sacrifice adds 12 %
	}

	@Test
	void bookOnBookAlwaysApplies() {
		var r = AnvilMath.combine(book("silk_touch", 1), book("looting", 3), PICK);
		assertNotNull(r);
		assertEquals(6, r.cost());                                   // looting book fee 2 x 3
		assertEquals(1, r.piece().repairCost());
	}

	@Test
	void itemOnBookOrNothingUsefulGivesNoResult() {
		assertNull(AnvilMath.combine(book("sharpness", 1), item(0, "sharpness", 1), SWORD));
		assertNull(AnvilMath.combine(item(0, "efficiency", 1), book("sharpness", 5), PICK));
		assertNull(AnvilMath.combine(item(0, "sharpness", 5), book("smite", 5), SWORD));
	}

	@Test
	void levelAboveMaxIsClamped() {
		var r = AnvilMath.combine(item(0), book("sharpness", 7), SWORD);
		assertEquals(5, r.piece().enchantments().get("sharpness"));
		assertEquals(5, r.cost());
	}

	@Test
	void uselessThirdBookIsLeftOut() {
		var plan = AnvilMath.optimize(item(0), List.of(book("sharpness", 4), book("sharpness", 4), book("sharpness", 4)), SWORD);
		assertEquals(5, plan.root().piece().enchantments().get("sharpness"));
		assertEquals(2, plan.steps().size());
		assertEquals(2, Integer.bitCount(plan.used()) - 1);
	}

	@Test
	void alternativesPreferCheaperUnlessOneIsOnTheAnvil() {
		var books = List.of(book("smite", 5), book("sharpness", 5));
		var plan = AnvilMath.optimize(item(0), books, SWORD);
		assertTrue(plan.uses(1));
		assertFalse(plan.uses(0));
		var pinned = AnvilMath.optimize(item(0), books, SWORD, 0);
		assertTrue(pinned.uses(0));
		assertEquals(5, pinned.root().piece().enchantments().get("smite"));
	}

	@Test
	void booksThatDoNotFitUnder40AreDropped() {
		// penalty 31 on the sword: looting (37) or fire aspect (35) fit, both together never do
		var plan = AnvilMath.optimize(item(31, "sharpness", 5), List.of(book("looting", 3), book("fire_aspect", 2)), SWORD);
		assertNotNull(plan);
		assertFalse(plan.uses(0));
		assertTrue(plan.uses(1));
		assertEquals(35, plan.total());
		assertNull(AnvilMath.optimize(item(63, "sharpness", 5), List.of(book("mending", 1)), SWORD));
	}

	@Test
	void gainIgnoresWhatCannotHelp() {
		assertEquals(-1, AnvilMath.gain(item(0), book("vanishing_curse", 1, "mending", 1), SWORD));
		assertEquals(-1, AnvilMath.gain(item(0), book("efficiency", 5), SWORD));
		assertEquals(-1, AnvilMath.gain(item(0, "sharpness", 5), book("sharpness", 5), SWORD));
		assertEquals(-1, AnvilMath.gain(item(0, "sharpness", 1), book("smite", 5), SWORD));
		assertEquals(0, AnvilMath.gain(item(0, "sharpness", 4), book("sharpness", 3), SWORD));
		assertEquals(0.2, AnvilMath.gain(item(0, "sharpness", 4), book("sharpness", 4), SWORD), 1e-9);
		assertEquals(1, AnvilMath.gain(item(0), book("mending", 1, "efficiency", 5), SWORD), 1e-9);
	}

	@Test
	void candidatesPutTheAnvilBookFirstAndRespectTheLimit() {
		var books = List.of(book("knockback", 1), book("mending", 1), book("efficiency", 5), book("looting", 3));
		assertEquals(List.of(1, 3, 0), AnvilMath.candidates(item(0), books, SWORD, -1, 8));
		assertEquals(List.of(0, 1), AnvilMath.candidates(item(0), books, SWORD, 0, 2));
	}

	@Test
	void nothingToImproveGivesNoPlan() {
		assertNull(AnvilMath.optimize(item(0, "sharpness", 5), List.of(book("sharpness", 3)), SWORD));
	}

	@Test
	void eightBooksAndFrozenRulesGiveTheSamePlan() {
		var books = List.of(book("sharpness", 4), book("sharpness", 4), book("looting", 3), book("mending", 1),
			book("unbreaking", 3), book("sweeping_edge", 3), book("fire_aspect", 2), book("knockback", 2));
		var plan = AnvilMath.optimize(item(0), books, SWORD);
		assertEquals(5, plan.root().piece().enchantments().get("sharpness"));
		assertEquals(511, plan.used());                          // target + all 8 books
		var frozen = AnvilMath.freeze(SWORD, DATA.keySet());
		var again = AnvilMath.optimize(item(0), books, frozen);
		assertEquals(plan.total(), again.total());
		assertEquals(plan.root().piece(), again.root().piece());
		assertFalse(frozen.areCompatible("sharpness", "smite"));
		assertFalse(frozen.areCompatible("mending", "mending"));
		assertTrue(frozen.isCurse("vanishing_curse"));
	}
}

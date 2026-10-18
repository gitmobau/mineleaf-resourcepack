package dev.mineleaf.auroraguia.anvil;

import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import it.unimi.dsi.fastutil.objects.Object2IntMap;

import net.minecraft.core.Holder;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.CommonComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.tags.EnchantmentTags;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.ItemEnchantments;

/** Builds {@link AnvilMath} inputs from real item stacks and the synced enchantment registry. */
public final class McAnvil {
	private McAnvil() {
	}

	private static RegistryAccess lastAccess;
	private static Map<String, Holder<Enchantment>> lastRegistry = Map.of();

	/**
	 * id -> enchantment, sorted by id and cached per registry access (tooltips ask for it every frame).
	 * Empty when there is no world or the registry is missing.
	 */
	public static synchronized Map<String, Holder<Enchantment>> registry(RegistryAccess access) {
		if (access == null) {
			return Map.of();
		}
		if (access != lastAccess) {
			Map<String, Holder<Enchantment>> out = new LinkedHashMap<>();
			access.lookup(Registries.ENCHANTMENT).ifPresent(r -> r.listElements()
				.sorted(Comparator.comparing(Holder::getRegisteredName))
				.forEach(h -> out.put(h.getRegisteredName(), h)));
			lastAccess = access;
			lastRegistry = java.util.Collections.unmodifiableMap(out);
		}
		return lastRegistry;
	}

	public static boolean isBook(ItemStack stack) {
		return stack.is(Items.ENCHANTED_BOOK);
	}

	public static AnvilMath.Piece piece(ItemStack stack) {
		Map<String, Integer> ench = new LinkedHashMap<>();
		ItemEnchantments e = EnchantmentHelper.getEnchantmentsForCrafting(stack);
		for (Object2IntMap.Entry<Holder<Enchantment>> entry : e.entrySet()) {
			ench.put(entry.getKey().getRegisteredName(), entry.getIntValue());
		}
		return new AnvilMath.Piece(isBook(stack), ench, repairCost(stack));
	}

	public static int repairCost(ItemStack stack) {
		return stack.getOrDefault(DataComponents.REPAIR_COST, 0);
	}

	/** "Sharpness V" without the grey colour of the vanilla tooltip, so the caller can colour it. */
	public static MutableComponent name(Holder<Enchantment> h, int level) {
		MutableComponent c = Component.empty().append(h.value().description());
		if (level != 1 || h.value().getMaxLevel() != 1) {
			c.append(CommonComponents.SPACE).append(Component.translatable("enchantment.level." + level));
		}
		return c;
	}

	/** Enchantments (no curses) that {@code stack} could still get or raise, ignoring ones that clash with what it has. */
	public static List<Holder<Enchantment>> improvable(ItemStack stack, Map<String, Holder<Enchantment>> reg) {
		ItemEnchantments have = EnchantmentHelper.getEnchantmentsForCrafting(stack);
		return reg.values().stream()
			.filter(h -> !h.is(EnchantmentTags.CURSE) && h.value().canEnchant(stack))
			.filter(h -> {
				int lvl = have.getLevel(h);
				return lvl > 0 ? lvl < h.value().getMaxLevel() : have.keySet().stream().allMatch(o -> Enchantment.areCompatible(h, o));
			})
			.toList();
	}

	/** Rules for putting things onto {@code target}. */
	public static AnvilMath.Rules rules(ItemStack target, Map<String, Holder<Enchantment>> reg) {
		return new AnvilMath.Rules() {
			@Override
			public int maxLevel(String e) {
				Holder<Enchantment> h = reg.get(e);
				return h == null ? 1 : h.value().getMaxLevel();
			}

			@Override
			public int anvilCost(String e) {
				Holder<Enchantment> h = reg.get(e);
				return h == null ? 1 : h.value().getAnvilCost();
			}

			@Override
			public boolean canEnchant(String e) {
				Holder<Enchantment> h = reg.get(e);
				return h != null && h.value().canEnchant(target);
			}

			@Override
			public boolean areCompatible(String a, String b) {
				Holder<Enchantment> ha = reg.get(a);
				Holder<Enchantment> hb = reg.get(b);
				return ha != null && hb != null && Enchantment.areCompatible(ha, hb);
			}

			@Override
			public boolean isCurse(String e) {
				Holder<Enchantment> h = reg.get(e);
				return h != null && h.is(EnchantmentTags.CURSE);
			}
		};
	}
}

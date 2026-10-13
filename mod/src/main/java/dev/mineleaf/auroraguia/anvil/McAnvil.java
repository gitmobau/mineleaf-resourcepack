package dev.mineleaf.auroraguia.anvil;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

import it.unimi.dsi.fastutil.objects.Object2IntMap;

import net.minecraft.core.Holder;
import net.minecraft.core.RegistryAccess;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
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

	/** id -> enchantment, cached per registry access (tooltips ask for it every frame). */
	public static synchronized Map<String, Holder<Enchantment>> registry(RegistryAccess access) {
		if (access != lastAccess) {
			Map<String, Holder<Enchantment>> out = new HashMap<>();
			access.lookupOrThrow(Registries.ENCHANTMENT).listElements().forEach(h -> out.put(h.getRegisteredName(), h));
			lastAccess = access;
			lastRegistry = Map.copyOf(out);
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
		return new AnvilMath.Piece(isBook(stack), ench, stack.getOrDefault(DataComponents.REPAIR_COST, 0));
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
		};
	}
}

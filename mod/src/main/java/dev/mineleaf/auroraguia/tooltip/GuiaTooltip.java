package dev.mineleaf.auroraguia.tooltip;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;

import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.tags.EnchantmentTags;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.ItemEnchantments;

import dev.mineleaf.auroraguia.anvil.AnvilMath;
import dev.mineleaf.auroraguia.anvil.McAnvil;

/**
 * Extra tooltip lines for anything that can be enchanted: anvil uses / prior work penalty, and (holding
 * Shift) the enchantments the item is still missing. Read-only.
 */
public final class GuiaTooltip {
	private GuiaTooltip() {
	}

	public static void register() {
		ItemTooltipCallback.EVENT.register((stack, context, flag, lines) -> {
			Minecraft mc = Minecraft.getInstance();
			if (mc.level == null || stack.isEmpty() || !relevant(stack)) {
				return;
			}
			int rc = stack.getOrDefault(DataComponents.REPAIR_COST, 0);
			int uses = AnvilMath.uses(rc);
			if (rc == 0) {
				lines.add(Component.translatable("aurora_guia.tooltip.anvil_new").withStyle(ChatFormatting.DARK_AQUA));
			} else {
				ChatFormatting c = rc >= 31 ? ChatFormatting.RED : rc >= 15 ? ChatFormatting.GOLD : ChatFormatting.DARK_AQUA;
				lines.add(Component.translatable("aurora_guia.tooltip.anvil_used", uses, rc).withStyle(c));
			}
			if (McAnvil.isBook(stack)) {
				return;
			}
			List<Component> missing = missing(stack, McAnvil.registry(mc.level.registryAccess()));
			if (missing.isEmpty()) {
				lines.add(Component.translatable("aurora_guia.tooltip.complete").withStyle(ChatFormatting.LIGHT_PURPLE));
			} else if (mc.hasShiftDown()) {
				lines.add(Component.translatable("aurora_guia.tooltip.missing").withStyle(ChatFormatting.LIGHT_PURPLE));
				for (Component m : missing) {
					lines.add(Component.literal("  ").append(m));
				}
			} else {
				lines.add(Component.translatable("aurora_guia.tooltip.shift", missing.size()).withStyle(ChatFormatting.DARK_GRAY));
			}
		});
	}

	private static boolean relevant(ItemStack stack) {
		return McAnvil.isBook(stack) || stack.isDamageableItem();
	}

	/**
	 * Enchantments the item supports that it does not have at max level. Curses are left out. Enchantments
	 * that clash with one it already has are left out; the ones that clash with each other are shown as
	 * alternatives ("A / B").
	 */
	static List<Component> missing(ItemStack stack, Map<String, Holder<Enchantment>> reg) {
		ItemEnchantments have = EnchantmentHelper.getEnchantmentsForCrafting(stack);
		List<Holder<Enchantment>> upgrades = new ArrayList<>();
		List<Holder<Enchantment>> absent = new ArrayList<>();
		reg.values().stream()
			.filter(h -> !h.is(EnchantmentTags.CURSE) && h.value().canEnchant(stack))
			.sorted(Comparator.comparing(Holder::getRegisteredName))
			.forEach(h -> {
				int lvl = have.getLevel(h);
				if (lvl > 0) {
					if (lvl < h.value().getMaxLevel()) {
						upgrades.add(h);
					}
				} else if (have.keySet().stream().allMatch(o -> Enchantment.areCompatible(h, o))) {
					absent.add(h);
				}
			});
		List<Component> out = new ArrayList<>();
		for (Holder<Enchantment> h : upgrades) {
			out.add(Component.translatable("aurora_guia.tooltip.upgrade",
				Enchantment.getFullname(h, have.getLevel(h)), Component.translatable("enchantment.level." + h.value().getMaxLevel()))
				.withStyle(ChatFormatting.GRAY));
		}
		// group absent enchantments that exclude each other: A / B
		List<List<Holder<Enchantment>>> groups = new ArrayList<>();
		for (Holder<Enchantment> h : absent) {
			List<Holder<Enchantment>> g = groups.stream()
				.filter(gr -> gr.stream().anyMatch(o -> !Enchantment.areCompatible(h, o)))
				.findFirst().orElse(null);
			if (g == null) {
				groups.add(g = new ArrayList<>());
			}
			g.add(h);
		}
		for (List<Holder<Enchantment>> g : groups) {
			MutableComponent line = Component.empty();
			for (int i = 0; i < g.size(); i++) {
				if (i > 0) {
					line.append(Component.literal(" / ").withStyle(ChatFormatting.DARK_GRAY));
				}
				Holder<Enchantment> h = g.get(i);
				line.append(Enchantment.getFullname(h, h.value().getMaxLevel()));
			}
			out.add(line);
		}
		return out;
	}
}

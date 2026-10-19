package dev.mineleaf.auroraguia.tooltip;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

import net.fabricmc.fabric.api.client.item.v1.ItemTooltipCallback;

import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.EnchantmentHelper;
import net.minecraft.world.item.enchantment.ItemEnchantments;

import dev.mineleaf.auroraguia.anvil.AnvilMath;
import dev.mineleaf.auroraguia.anvil.McAnvil;

/**
 * Extra tooltip lines, only where they say something: the anvil penalty of items that have been on the anvil,
 * and for enchanted items what they are still missing (the list with Shift). Read-only.
 */
public final class GuiaTooltip {
	private GuiaTooltip() {
	}

	/** What an item could still get: an empty list when it is complete, null when it cannot be enchanted. */
	private record Missing(List<Component> lines) {
	}

	// the hovered stack is asked for its tooltip every frame: remember the last answer
	private static ItemStack lastStack = ItemStack.EMPTY;
	private static Map<String, Holder<Enchantment>> lastReg;
	private static Missing lastMissing;

	public static void register() {
		ItemTooltipCallback.EVENT.register((stack, context, flag, lines) -> {
			Minecraft mc = Minecraft.getInstance();
			if (mc.level == null || stack.isEmpty()) {
				return;
			}
			int rc = McAnvil.repairCost(stack);
			if (rc > 0) {
				ChatFormatting c = rc >= 31 ? ChatFormatting.RED : rc >= 15 ? ChatFormatting.GOLD : ChatFormatting.GRAY;
				int uses = AnvilMath.uses(rc);
				lines.add(Component.translatable("aurora_guia.tooltip.penalty",
					Component.translatable(uses == 1 ? "aurora_guia.penalty_one" : "aurora_guia.penalty", rc, uses)).withStyle(c));
			}
			if (McAnvil.isBook(stack)) {
				return;
			}
			Missing missing = missing(stack, McAnvil.registry(mc.level.registryAccess()));
			if (missing == null) {
				return;                                        // not enchantable: nothing to say
			}
			boolean enchanted = !EnchantmentHelper.getEnchantmentsForCrafting(stack).isEmpty();
			if (missing.lines().isEmpty()) {
				if (enchanted) {
					lines.add(Component.translatable("aurora_guia.tooltip.complete").withStyle(ChatFormatting.LIGHT_PURPLE));
				}
			} else if (mc.hasShiftDown()) {
				lines.add(Component.translatable("aurora_guia.tooltip.missing").withStyle(ChatFormatting.LIGHT_PURPLE));
				for (Component m : missing.lines()) {
					lines.add(Component.literal("  ").append(m));
				}
			} else if (enchanted) {
				lines.add(Component.translatable("aurora_guia.tooltip.shift", missing.lines().size()).withStyle(ChatFormatting.DARK_GRAY));
			}
		});
	}

	private static synchronized Missing missing(ItemStack stack, Map<String, Holder<Enchantment>> reg) {
		if (reg != lastReg || !ItemStack.matches(stack, lastStack)) {
			lastStack = stack.copy();
			lastReg = reg;
			lastMissing = compute(stack, reg);
		}
		return lastMissing;
	}

	/**
	 * Enchantments the item supports that it does not have at max level. Curses and Thorns are left out. Enchantments
	 * that clash with one it already has are left out; the ones that clash with each other are shown as
	 * alternatives ("A / B").
	 */
	private static Missing compute(ItemStack stack, Map<String, Holder<Enchantment>> reg) {
		if (reg.values().stream().noneMatch(h -> !McAnvil.unwanted(h) && h.value().canEnchant(stack))) {
			return null;
		}
		ItemEnchantments have = EnchantmentHelper.getEnchantmentsForCrafting(stack);
		List<Component> out = new ArrayList<>();
		List<List<Holder<Enchantment>>> groups = new ArrayList<>();
		for (Holder<Enchantment> h : McAnvil.improvable(stack, reg)) {
			int lvl = have.getLevel(h);
			if (lvl > 0) {                                     // raise: "Sharpness IV → V"
				out.add(Component.translatable("aurora_guia.tooltip.upgrade", McAnvil.name(h, lvl),
					Component.translatable("enchantment.level." + h.value().getMaxLevel())).withStyle(ChatFormatting.GRAY));
				continue;
			}
			// absent: group the ones that exclude each other
			List<Holder<Enchantment>> g = groups.stream()
				.filter(gr -> gr.stream().anyMatch(o -> !Enchantment.areCompatible(h, o)))
				.findFirst().orElse(null);
			if (g == null) {
				groups.add(g = new ArrayList<>());
			}
			g.add(h);
		}
		for (List<Holder<Enchantment>> g : groups) {
			MutableComponent line = Component.empty().withStyle(ChatFormatting.GRAY);
			for (int i = 0; i < g.size(); i++) {
				if (i > 0) {
					line.append(Component.literal(" / ").withStyle(ChatFormatting.DARK_GRAY));
				}
				line.append(McAnvil.name(g.get(i), g.get(i).value().getMaxLevel()));
			}
			out.add(line);
		}
		return new Missing(List.copyOf(out));
	}
}

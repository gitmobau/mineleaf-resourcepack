package dev.mineleaf.auroraguia;

import com.mojang.blaze3d.platform.InputConstants;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;

import net.minecraft.client.KeyMapping;
import net.minecraft.resources.Identifier;

import dev.mineleaf.auroraguia.anvil.AnvilOverlay;
import dev.mineleaf.auroraguia.diario.Diario;
import dev.mineleaf.auroraguia.diario.DiarioHud;
import dev.mineleaf.auroraguia.diario.DiarioScreen;
import dev.mineleaf.auroraguia.tooltip.GuiaTooltip;

/**
 * Aurora Guía: client-only helpers that read the game and draw information. Nothing here changes how the
 * game plays: no costs, items or rules are modified.
 */
public final class AuroraGuia implements ClientModInitializer {
	public static final String MOD_ID = "aurora_guia";
	private static final KeyMapping.Category CATEGORY = KeyMapping.Category.register(Identifier.fromNamespaceAndPath(MOD_ID, "main"));

	@Override
	public void onInitializeClient() {
		KeyMapping toggle = KeyMappingHelper.registerKeyMapping(
			new KeyMapping("key.aurora_guia.toggle_diario", InputConstants.KEY_J, CATEGORY));
		KeyMapping open = KeyMappingHelper.registerKeyMapping(
			new KeyMapping("key.aurora_guia.open_diario", InputConstants.KEY_K, CATEGORY));
		ClientTickEvents.END_CLIENT_TICK.register(mc -> {
			while (toggle.consumeClick()) {
				Diario.data().visible = !Diario.data().visible;
				Diario.save();
			}
			while (open.consumeClick()) {
				if (mc.gui.screen() == null) {
					mc.gui.setScreen(new DiarioScreen());
				}
			}
		});
		HudElementRegistry.addLast(Identifier.fromNamespaceAndPath(MOD_ID, "diario"), DiarioHud::extract);
		GuiaTooltip.register();
		AnvilOverlay.register();
	}
}

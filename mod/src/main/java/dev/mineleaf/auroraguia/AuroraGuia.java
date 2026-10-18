package dev.mineleaf.auroraguia;

import net.fabricmc.api.ClientModInitializer;

import dev.mineleaf.auroraguia.anvil.AnvilOverlay;
import dev.mineleaf.auroraguia.tooltip.GuiaTooltip;

/**
 * Aurora Guía: client-only helpers that read the game and draw information. Nothing here changes how the
 * game plays: no costs, items or rules are modified. Nothing is drawn on the normal game screen; only the
 * anvil gets a side panel and tooltips get a few extra lines.
 */
public final class AuroraGuia implements ClientModInitializer {
	public static final String MOD_ID = "aurora_guia";

	@Override
	public void onInitializeClient() {
		GuiaTooltip.register();
		AnvilOverlay.register();
	}
}

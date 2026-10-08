package io.github.gitmobau.aurorafx;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.LivingEntityRenderer;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.resources.Identifier;

import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.LivingEntityRenderLayerRegistrationCallback;

public class AuroraFxClient implements ClientModInitializer {
	public static final String MOD_ID = "aurora_fx";
	public static final Logger LOGGER = LoggerFactory.getLogger(MOD_ID);

	@Override
	@SuppressWarnings("unchecked")
	public void onInitializeClient() {
		AuroraConfig.load();

		// 1) Brillo de aurora sobre la armadura de netherita puesta.
		AuroraArmorLayer.registerModelLayers();
		LivingEntityRenderLayerRegistrationCallback.EVENT.register((entityType, entityRenderer, registrationHelper, context) -> {
			// Cualquier renderer cuyo modelo sea humanoide (jugadores, zombis, esqueletos, piglins, soportes de armadura...).
			if (entityRenderer.getModel() instanceof HumanoidModel<?>) {
				registrationHelper.register(createArmorLayer(entityRenderer, context));
			}
		});

		// 2) Estela de destellos (y recarga del config si se edita con el juego abierto).
		ClientTickEvents.END_CLIENT_TICK.register(AuroraTrail::tick);

		LOGGER.info("[Aurora FX] listo");
	}

	/**
	 * El callback da el renderer con comodines; si su modelo es un {@link HumanoidModel}, su estado es un
	 * HumanoidRenderState (lo exige la firma de HumanoidModel), así que el cast sin comprobar es seguro.
	 */
	@SuppressWarnings({"unchecked", "rawtypes"})
	private static RenderLayer createArmorLayer(LivingEntityRenderer<?, ?, ?> renderer, EntityRendererProvider.Context context) {
		return new AuroraArmorLayer((RenderLayerParent) renderer, context);
	}

	public static Identifier id(String path) {
		return Identifier.fromNamespaceAndPath(MOD_ID, path);
	}
}

package io.github.gitmobau.aurorafx;

import com.mojang.blaze3d.vertex.PoseStack;

import net.minecraft.client.model.HumanoidModel;
import net.minecraft.client.model.geom.ModelLayerLocation;
import net.minecraft.client.model.geom.builders.CubeDeformation;
import net.minecraft.client.model.geom.builders.LayerDefinition;
import net.minecraft.client.renderer.OrderedSubmitNodeCollector;
import net.minecraft.client.renderer.SubmitNodeCollector;
import net.minecraft.client.renderer.entity.ArmorModelSet;
import net.minecraft.client.renderer.entity.EntityRendererProvider;
import net.minecraft.client.renderer.entity.RenderLayerParent;
import net.minecraft.client.renderer.entity.layers.RenderLayer;
import net.minecraft.client.renderer.entity.state.AvatarRenderState;
import net.minecraft.client.renderer.entity.state.HumanoidRenderState;
import net.minecraft.client.renderer.rendertype.RenderType;
import net.minecraft.client.renderer.rendertype.RenderTypes;
import net.minecraft.client.renderer.texture.OverlayTexture;
import net.minecraft.resources.Identifier;
import net.minecraft.util.LightCoordsUtil;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

import net.fabricmc.fabric.api.client.rendering.v1.ArmorRenderer;
import net.fabricmc.fabric.api.client.rendering.v1.ModelLayerRegistry;

/**
 * Brillo de aurora animado sobre cada pieza de netherita puesta.
 *
 * <p>No sustituye el render de la armadura (la túnica galáctica del resource pack se sigue viendo
 * debajo): dibuja encima una copia un poco más grande de la pieza con el mismo tipo de render que la
 * carga del creeper cargado ({@link RenderTypes#energySwirl}: mezcla aditiva + desplazamiento de UV).
 * La textura se desplaza con el tiempo y el color recorre la paleta Aurora.
 *
 * <p>La pose se copia del modelo del propio mob con {@link ArmorRenderer#submitTransformCopyingModel}
 * (Fabric API), así funciona con jugadores, zombis, esqueletos, piglins, soportes de armadura, etc.
 */
public class AuroraArmorLayer<S extends HumanoidRenderState, M extends HumanoidModel<S>> extends RenderLayer<S, M> {
	public static final Identifier TEXTURE = AuroraFxClient.id("textures/entity/aurora_overlay.png");

	/** Capas de modelo propias: como las de la armadura vanilla pero 0.08 más grandes, para no pelearse en Z con ella. */
	public static final ArmorModelSet<ModelLayerLocation> MODEL_LAYERS = new ArmorModelSet<>("helmet", "chestplate", "leggings", "boots")
			.map(name -> new ModelLayerLocation(AuroraFxClient.id("armor_overlay"), name));

	/** Vanilla usa 0.5 (piernas) y 1.0 (resto); ver LayerDefinitions.INNER/OUTER_ARMOR_DEFORMATION. */
	private static final float INNER_GROW = 0.5F + 0.08F;
	private static final float OUTER_GROW = 1.0F + 0.08F;

	private final ArmorModelSet<HumanoidModel<HumanoidRenderState>> models;

	public AuroraArmorLayer(RenderLayerParent<S, M> parent, EntityRendererProvider.Context context) {
		super(parent);
		this.models = MODEL_LAYERS.map(location -> new HumanoidModel<HumanoidRenderState>(context.bakeLayer(location)));
	}

	/** Se llama una vez en la inicialización del cliente, antes de que se creen los renderers. */
	public static void registerModelLayers() {
		ModelLayerRegistry.registerArmorModelLayers(MODEL_LAYERS, () -> HumanoidModel
				.createArmorMeshSet(new CubeDeformation(INNER_GROW), new CubeDeformation(OUTER_GROW))
				.map(mesh -> LayerDefinition.create(mesh, 64, 32)));
	}

	@Override
	public void submit(PoseStack poseStack, SubmitNodeCollector submitNodeCollector, int lightCoords, S state, float yRot, float xRot) {
		AuroraConfig cfg = AuroraConfig.get();

		if (!cfg.armorOverlay || cfg.overlayIntensity <= 0.0F) {
			return;
		}

		// Los bebés usan otra geometría de armadura (humanoid_baby); no se intenta encajar el brillo en ellos.
		if (state.isBaby) {
			return;
		}

		if (!cfg.overlayOnMobs && !(state instanceof AvatarRenderState)) {
			return;
		}

		boolean head = isNetherite(state.headEquipment, Items.NETHERITE_HELMET);
		boolean chest = isNetherite(state.chestEquipment, Items.NETHERITE_CHESTPLATE);
		boolean legs = isNetherite(state.legsEquipment, Items.NETHERITE_LEGGINGS);
		boolean feet = isNetherite(state.feetEquipment, Items.NETHERITE_BOOTS);

		if (!head && !chest && !legs && !feet) {
			return;
		}

		float t = state.ageInTicks * cfg.overlaySpeed;
		// Desplazamiento lento en diagonal (la textura es periódica, se repite sin costuras).
		float u = (t * 0.0030F) % 1.0F;
		float v = (t * 0.0080F) % 1.0F;
		// Pulso suave + ciclo de color por la paleta (un ciclo completo cada ~25 s a velocidad 1).
		float pulse = 0.72F + 0.28F * (float) Math.sin(t * 0.07F);
		int color = AuroraPalette.argbScaled(AuroraPalette.cyc(t * 0.002F, AuroraPalette.VIVID), cfg.overlayIntensity * pulse);
		int light = cfg.overlayGlow ? LightCoordsUtil.FULL_BRIGHT : lightCoords;

		// Igual que EnergySwirlLayer: un RenderType nuevo por frame con el desplazamiento de UV.
		RenderType renderType = RenderTypes.energySwirl(TEXTURE, u, v);
		OrderedSubmitNodeCollector collector = submitNodeCollector.order(1);

		if (chest) {
			submitPiece(models.chest(), state, collector, poseStack, renderType, light, color);
		}

		if (legs) {
			submitPiece(models.legs(), state, collector, poseStack, renderType, light, color);
		}

		if (feet) {
			submitPiece(models.feet(), state, collector, poseStack, renderType, light, color);
		}

		if (head) {
			submitPiece(models.head(), state, collector, poseStack, renderType, light, color);
		}
	}

	private void submitPiece(HumanoidModel<HumanoidRenderState> piece, S state, OrderedSubmitNodeCollector collector, PoseStack poseStack,
			RenderType renderType, int light, int color) {
		ArmorRenderer.submitTransformCopyingModel(
				this.getParentModel(), state,
				piece, state,
				false,
				collector, poseStack, renderType,
				light, OverlayTexture.NO_OVERLAY, color, null, state.outlineColor);
	}

	private static boolean isNetherite(ItemStack stack, Item item) {
		return !stack.isEmpty() && stack.getItem() == item;
	}
}

package io.github.gitmobau.aurorafx;

import java.util.Set;

import net.minecraft.client.Minecraft;
import net.minecraft.client.multiplayer.ClientLevel;
import net.minecraft.client.player.AbstractClientPlayer;
import net.minecraft.core.particles.DustParticleOptions;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.util.RandomSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;

/**
 * Estela de destellos pastel detrás de los jugadores que llevan el set completo de netherita
 * (o, si está activado, una herramienta/arma de diamante o netherita encantada en la mano).
 *
 * <p>Solo cliente: las partículas se añaden al mundo local con {@link ClientLevel#addParticle},
 * no se envía nada al servidor. Limitado por jugador y con un tope global por tick.
 */
public final class AuroraTrail {
	private static final Set<Item> TOOLS = Set.of(
			Items.DIAMOND_SWORD, Items.DIAMOND_PICKAXE, Items.DIAMOND_AXE, Items.DIAMOND_SHOVEL, Items.DIAMOND_HOE, Items.DIAMOND_SPEAR,
			Items.NETHERITE_SWORD, Items.NETHERITE_PICKAXE, Items.NETHERITE_AXE, Items.NETHERITE_SHOVEL, Items.NETHERITE_HOE, Items.NETHERITE_SPEAR
	);

	private static int tickCounter = 0;

	private AuroraTrail() {
	}

	/** Se llama al final de cada tick del cliente. */
	public static void tick(Minecraft client) {
		if (++tickCounter % 60 == 0) {
			AuroraConfig.reloadIfChanged();
		}

		AuroraConfig cfg = AuroraConfig.get();
		ClientLevel level = client.level;

		if (!cfg.particleTrail || cfg.particleRate <= 0.0F || level == null || client.isPaused()) {
			return;
		}

		Entity camera = client.getCameraEntity();

		if (camera == null) {
			return;
		}

		boolean firstPerson = client.options.getCameraType().isFirstPerson();
		double rangeSq = cfg.particleRange * cfg.particleRange;
		int budget = cfg.maxParticlesPerTick;
		RandomSource random = level.getRandom();
		long time = level.getGameTime();

		for (AbstractClientPlayer player : level.players()) {
			if (budget <= 0) {
				break;
			}

			if (player.isSpectator() || player.isInvisible()) {
				continue;
			}

			if (player == camera && firstPerson && !cfg.trailInFirstPerson) {
				continue;
			}

			if (player.distanceToSqr(camera) > rangeSq) {
				continue;
			}

			boolean fullSet = hasFullNetherite(player);
			boolean tool = !fullSet && cfg.trailOnEnchantedTools && (isEnchantedTool(player.getMainHandItem()) || isEnchantedTool(player.getOffhandItem()));

			if (!fullSet && !tool) {
				continue;
			}

			// Movimiento desde el tick anterior (sirve también para jugadores remotos, que no tienen deltaMovement fiable).
			double dx = player.getX() - player.xo;
			double dy = player.getY() - player.yo;
			double dz = player.getZ() - player.zo;
			double speedSq = dx * dx + dy * dy + dz * dz;
			boolean moving = speedSq > 0.0025; // > 0.05 bloques/tick

			// Probabilidad por tick: en movimiento ~1 partícula cada 2 ticks con el set completo;
			// quieto, solo algún destello suelto. Con herramienta, la mitad.
			float chance = (moving ? 0.55F : 0.06F) * (fullSet ? 1.0F : 0.5F) * cfg.particleRate;
			int count = (int) chance + (random.nextFloat() < (chance - (int) chance) ? 1 : 0);

			for (int i = 0; i < count && budget > 0; i++, budget--) {
				spawn(level, player, random, time, dx, dz, moving);
			}
		}
	}

	private static void spawn(ClientLevel level, AbstractClientPlayer player, RandomSource random, long time, double dx, double dz, boolean moving) {
		// Un poco por detrás del jugador (en sentido contrario al movimiento) y a la altura de cintura/espalda.
		double backX = moving ? -dx * 2.0 : 0.0;
		double backZ = moving ? -dz * 2.0 : 0.0;
		double x = player.getX() + backX + (random.nextDouble() - 0.5) * 0.6;
		double y = player.getY() + 0.25 + random.nextDouble() * player.getBbHeight() * 0.7;
		double z = player.getZ() + backZ + (random.nextDouble() - 0.5) * 0.6;

		if (random.nextInt(9) == 0) {
			// Destello blanco ocasional que flota hacia arriba muy despacio.
			level.addParticle(ParticleTypes.END_ROD, x, y, z,
					(random.nextDouble() - 0.5) * 0.01, 0.012, (random.nextDouble() - 0.5) * 0.01);
		} else {
			// Polvo de color: cada partícula toma un color de la paleta pastel según el tiempo y un desfase aleatorio.
			int rgb = AuroraPalette.cyc(time * 0.01F + random.nextFloat() * 0.3F, AuroraPalette.P);
			float scale = 0.55F + random.nextFloat() * 0.35F;
			level.addParticle(new DustParticleOptions(rgb, scale), x, y, z, 0.0, 0.01, 0.0);
		}
	}

	private static boolean hasFullNetherite(AbstractClientPlayer player) {
		return is(player.getItemBySlot(EquipmentSlot.HEAD), Items.NETHERITE_HELMET)
				&& is(player.getItemBySlot(EquipmentSlot.CHEST), Items.NETHERITE_CHESTPLATE)
				&& is(player.getItemBySlot(EquipmentSlot.LEGS), Items.NETHERITE_LEGGINGS)
				&& is(player.getItemBySlot(EquipmentSlot.FEET), Items.NETHERITE_BOOTS);
	}

	private static boolean isEnchantedTool(ItemStack stack) {
		return !stack.isEmpty() && TOOLS.contains(stack.getItem()) && stack.isEnchanted();
	}

	private static boolean is(ItemStack stack, Item item) {
		return !stack.isEmpty() && stack.getItem() == item;
	}
}

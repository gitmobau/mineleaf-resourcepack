package dev.mineleaf.auroraguia.gametest;

import static dev.mineleaf.auroraguia.gametest.AuroraGuiaClientTest.item;
import static dev.mineleaf.auroraguia.gametest.AuroraGuiaClientTest.player;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import net.minecraft.client.CameraType;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.MenuProvider;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.decoration.ArmorStand;
import net.minecraft.world.entity.decoration.ItemFrame;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.CraftingMenu;
import net.minecraft.world.inventory.ShulkerBoxMenu;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.entity.FurnaceBlockEntity;

/** A tour of everything the Aurora packs change, for the user to see before installing. */
public class AuroraShowcaseTest implements FabricClientGameTest {
	private static BlockPos base;

	@Override
	public void runTest(ClientGameTestContext ctx) {
		ctx.getInput().resizeWindow(1280, 720);
		AuroraGuiaClientTest.enableAuroraPack(ctx);
		try (TestSingleplayerContext sp = ctx.worldBuilder()
			.adjustSettings(s -> s.setGameMode(WorldCreationUiState.SelectedGameMode.HARDCORE))
			.create()) {
			sp.getConnection().waitForChunksRender();
			base = sp.getServer().computeOnServer(s -> player(s).blockPosition());
			sp.getServer().runCommand("time set 1000");
			sp.getServer().runCommand("weather clear");
			sp.getServer().runOnServer(AuroraShowcaseTest::build);
			ctx.waitTicks(10);

			// --- water from above, flowing water and underwater
			tp(sp, 0, 4, 0, 0, 40);
			shot(ctx, sp, "10_agua");
			tp(sp, 0, -2, 7, 0, 0);
			shot(ctx, sp, "11_bajo_el_agua");

			// --- tools with the three auras in item frames + neon block outline
			tp(sp, 0, 0, -2, 180, 8);
			shot(ctx, sp, "12_herramientas_auras_y_borde");

			// --- armour stands: diamond crystal and netherite galactic robe with its cloak
			tp(sp, 10, 0, 0, -90, 5);
			shot(ctx, sp, "13_armaduras");

			// --- first person with the legendary sword, then third person with the cloak
			sp.getServer().runOnServer(s -> {
				ServerPlayer p = player(s);
				p.getInventory().setItem(0, legendSword(s));
				p.getInventory().setSelectedSlot(0);
				for (var slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
					p.setItemSlot(slot, new ItemStack(netherite(slot)));
				}
			});
			tp(sp, 0, 4, 0, 0, 30);
			shot(ctx, sp, "14_primera_persona_espada_legendaria");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_BACK));
			shot(ctx, sp, "15_tercera_persona_capa");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.THIRD_PERSON_FRONT));
			shot(ctx, sp, "16_tercera_persona_tunica");
			ctx.runOnClient(mc -> mc.options.setCameraType(CameraType.FIRST_PERSON));

			// --- menus
			sp.getServer().runOnServer(s -> {
				ServerPlayer p = player(s);
				p.getInventory().setItem(9, new ItemStack(Items.DIAMOND, 32));
				p.getInventory().setItem(10, new ItemStack(Items.GOLDEN_CARROT, 64));
				p.getInventory().setItem(11, new ItemStack(Items.ENDER_PEARL, 5));
				p.getInventory().setItem(12, item(s, Items.DIAMOND_PICKAXE, 1, Enchantments.EFFICIENCY, 5, Enchantments.MENDING, 1));
				p.getInventory().setItem(1, new ItemStack(Items.TORCH, 40));
			});
			ctx.setScreen(() -> new InventoryScreen(ctx.computeOnClient(mc -> mc.player)));
			menuShot(ctx, "20_inventario");
			ctx.setScreen(() -> null);
			open(ctx, sp, new SimpleMenuProvider((id, inv, p) -> new CraftingMenu(id, inv), Component.translatable("container.crafting")), "21_mesa_de_crafteo");
			open(ctx, sp, null, "22_horno");
			open(ctx, sp, new SimpleMenuProvider((id, inv, p) -> ChestMenu.sixRows(id, inv), Component.translatable("container.chestDouble")), "23_cofre_grande");
			open(ctx, sp, new SimpleMenuProvider((id, inv, p) -> new ShulkerBoxMenu(id, inv), Component.translatable("container.shulkerBox")), "24_caja_de_shulker");

			// --- night: glowing dragon egg
			sp.getServer().runCommand("time set 18000");
			tp(sp, -10, 0, 0, 90, 10);
			shot(ctx, sp, "25_huevo_de_noche");
		}
	}

	private static Item netherite(EquipmentSlot slot) {
		return switch (slot) {
			case HEAD -> Items.NETHERITE_HELMET;
			case CHEST -> Items.NETHERITE_CHESTPLATE;
			case LEGS -> Items.NETHERITE_LEGGINGS;
			default -> Items.NETHERITE_BOOTS;
		};
	}

	private static Item diamond(EquipmentSlot slot) {
		return switch (slot) {
			case HEAD -> Items.DIAMOND_HELMET;
			case CHEST -> Items.DIAMOND_CHESTPLATE;
			case LEGS -> Items.DIAMOND_LEGGINGS;
			default -> Items.DIAMOND_BOOTS;
		};
	}

	private static ItemStack legendSword(MinecraftServer s) {
		return item(s, Items.DIAMOND_SWORD, 7, Enchantments.SHARPNESS, 5, Enchantments.UNBREAKING, 3, Enchantments.MENDING, 1, Enchantments.LOOTING, 3);
	}

	/** Builds every scene around the spawn point. */
	private static void build(MinecraftServer s) {
		ServerPlayer p = player(s);
		ServerLevel level = (ServerLevel) p.level();
		int x = base.getX(), y = base.getY(), z = base.getZ();
		// pool south of spawn, with a source block on the grass to get flowing water
		for (int dx = -4; dx <= 4; dx++) {
			for (int dz = 4; dz <= 10; dz++) {
				for (int dy = -3; dy <= -1; dy++) {
					level.setBlockAndUpdate(new BlockPos(x + dx, y + dy, z + dz), Blocks.WATER.defaultBlockState());
				}
				level.setBlockAndUpdate(new BlockPos(x + dx, y - 4, z + dz), Blocks.SAND.defaultBlockState());
			}
		}
		level.setBlockAndUpdate(new BlockPos(x + 6, y, z + 7), Blocks.WATER.defaultBlockState());
		level.setBlockAndUpdate(new BlockPos(x - 6, y + 1, z + 6), Blocks.STONE.defaultBlockState());
		level.setBlockAndUpdate(new BlockPos(x - 6, y + 2, z + 6), Blocks.WATER.defaultBlockState());
		// wall with item frames north of spawn: diamond sword / netherite pickaxe x normal, rare, legendary
		for (int dx = -4; dx <= 4; dx++) {
			for (int dy = 0; dy <= 3; dy++) {
				level.setBlockAndUpdate(new BlockPos(x + dx, y + dy, z - 6), Blocks.QUARTZ_BLOCK.defaultBlockState());
			}
		}
		ItemStack[] row1 = {
			item(s, Items.DIAMOND_SWORD, 0, Enchantments.SHARPNESS, 3),
			item(s, Items.DIAMOND_SWORD, 0, Enchantments.SHARPNESS, 3, Enchantments.MENDING, 1),
			legendSword(s)};
		ItemStack[] row2 = {
			item(s, Items.NETHERITE_PICKAXE, 0, Enchantments.EFFICIENCY, 3),
			item(s, Items.NETHERITE_PICKAXE, 0, Enchantments.EFFICIENCY, 3, Enchantments.MENDING, 1),
			item(s, Items.NETHERITE_PICKAXE, 3, Enchantments.EFFICIENCY, 5, Enchantments.UNBREAKING, 3, Enchantments.MENDING, 1, Enchantments.FORTUNE, 3)};
		for (int i = 0; i < 3; i++) {
			frame(level, new BlockPos(x - 2 + 2 * i, y + 2, z - 5), row1[i]);
			frame(level, new BlockPos(x - 2 + 2 * i, y + 1, z - 5), row2[i]);
		}
		// armour stands east of spawn, facing the player that stands at x+10
		stand(level, x + 14, y, z - 2, 90, true);
		stand(level, x + 14, y, z, 90, false);
		stand(level, x + 14, y, z + 2, -90, false);    // seen from behind: the cloak
		// dragon egg west of spawn
		level.setBlockAndUpdate(new BlockPos(x - 13, y, z), Blocks.DRAGON_EGG.defaultBlockState());
		// a lit furnace to open later
		BlockPos f = new BlockPos(x + 1, y, z - 3);
		level.setBlockAndUpdate(f, Blocks.FURNACE.defaultBlockState());
		if (level.getBlockEntity(f) instanceof FurnaceBlockEntity fe) {
			fe.setItem(0, new ItemStack(Items.RAW_IRON, 16));
			fe.setItem(1, new ItemStack(Items.COAL, 16));
		}
	}

	private static void frame(ServerLevel level, BlockPos pos, ItemStack stack) {
		ItemFrame fr = new ItemFrame(level, pos, Direction.SOUTH);
		fr.setItem(stack, false);
		level.addFreshEntity(fr);
	}

	private static void stand(ServerLevel level, int x, int y, int z, float yaw, boolean diamond) {
		ArmorStand a = new ArmorStand(level, x + 0.5, y, z + 0.5);
		a.setYRot(yaw);
		a.setYBodyRot(yaw);
		a.setYHeadRot(yaw);
		a.setShowArms(true);
		for (var slot : new EquipmentSlot[] {EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET}) {
			a.setItemSlot(slot, new ItemStack(diamond ? diamond(slot) : netherite(slot)));
		}
		level.addFreshEntity(a);
	}

	private static void tp(TestSingleplayerContext sp, int dx, int dy, int dz, float yaw, float pitch) {
		sp.getServer().runCommand("tp @a %.1f %d %.1f %.1f %.1f".formatted(base.getX() + dx + 0.5, base.getY() + dy, base.getZ() + dz + 0.5, yaw, pitch)
			.replace(',', '.'));
	}

	private static void shot(ClientGameTestContext ctx, TestSingleplayerContext sp, String name) {
		sp.getConnection().waitForChunksRender();
		ctx.waitTicks(20);
		ctx.takeScreenshot(name);
	}

	private static void menuShot(ClientGameTestContext ctx, String name) {
		ctx.waitFor(mc -> mc.gui.screen() instanceof AbstractContainerScreen<?>);
		ctx.waitTicks(10);
		ctx.getInput().setCursorPos(10, 10);
		ctx.takeScreenshot(name);
	}

	private static void open(ClientGameTestContext ctx, TestSingleplayerContext sp, MenuProvider provider, String name) {
		sp.getServer().runOnServer(s -> {
			ServerPlayer p = player(s);
			p.closeContainer();
			if (provider != null) {
				p.openMenu(provider);
			} else if (p.level().getBlockEntity(new BlockPos(base.getX() + 1, base.getY(), base.getZ() - 3)) instanceof FurnaceBlockEntity fe) {
				p.openMenu(fe);
			}
		});
		menuShot(ctx, name);
		sp.getServer().runOnServer(s -> player(s).closeContainer());
		ctx.waitTicks(2);
	}
}

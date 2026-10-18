package dev.mineleaf.auroraguia.gametest;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

import net.fabricmc.fabric.api.client.gametest.v1.FabricClientGameTest;
import net.fabricmc.fabric.api.client.gametest.v1.context.ClientGameTestContext;
import net.fabricmc.fabric.api.client.gametest.v1.context.TestSingleplayerContext;

import net.minecraft.client.gui.screens.inventory.AnvilScreen;
import net.minecraft.client.gui.screens.inventory.EnchantmentScreen;
import net.minecraft.client.gui.screens.inventory.GrindstoneScreen;
import net.minecraft.client.gui.screens.inventory.InventoryScreen;
import net.minecraft.client.gui.screens.worldselection.WorldCreationUiState;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.inventory.AnvilMenu;
import net.minecraft.world.inventory.ContainerLevelAccess;
import net.minecraft.world.inventory.EnchantmentMenu;
import net.minecraft.world.inventory.GrindstoneMenu;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantment;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.item.enchantment.ItemEnchantments;


/** Screenshots of every feature in a hardcore world with the Aurora pack enabled. */
public class AuroraGuiaClientTest implements FabricClientGameTest {
	@Override
	public void runTest(ClientGameTestContext ctx) {
		ctx.getInput().resizeWindow(1280, 720);
		enableAuroraPack(ctx);
		try (TestSingleplayerContext sp = ctx.worldBuilder()
			.adjustSettings(s -> s.setGameMode(WorldCreationUiState.SelectedGameMode.HARDCORE))
			.create()) {
			sp.getConnection().waitForChunksRender();
			sp.getServer().runCommand("time set 18000");
			sp.getServer().runCommand("advancement grant @a only minecraft:end/elytra");

			// --- HUD: hardcore hearts and the glowing dragon egg in front of the player
			BlockPos egg = sp.getServer().computeOnServer(s -> s.getPlayerList().getPlayers().get(0).blockPosition().relative(
				s.getPlayerList().getPlayers().get(0).getDirection(), 2));
			sp.getServer().runCommand("setblock %d %d %d minecraft:dragon_egg".formatted(egg.getX(), egg.getY(), egg.getZ()));
			ctx.getInput().lookAt(egg);
			sp.getConnection().waitForChunksRender();
			ctx.waitTicks(20);
			ctx.takeScreenshot("01_hud_hardcore_huevo");

			// --- anvil with books in the inventory: cheapest plan
			sp.getServer().runOnServer(s -> {
				ServerPlayer p = player(s);
				p.getInventory().clearContent();
				p.getInventory().setItem(9, book(s, Enchantments.SHARPNESS, 5));
				p.getInventory().setItem(10, book(s, Enchantments.LOOTING, 3));
				p.getInventory().setItem(11, book(s, Enchantments.MENDING, 1));
				p.getInventory().setItem(12, book(s, Enchantments.UNBREAKING, 3));
				p.getInventory().setItem(13, book(s, Enchantments.SWEEPING_EDGE, 3));
				p.getInventory().setItem(14, book(s, Enchantments.FIRE_ASPECT, 2));
				p.getInventory().setItem(15, book(s, Enchantments.KNOCKBACK, 2));
				p.getInventory().setItem(16, book(s, Enchantments.SMITE, 5));      // alternative to Sharpness: left out
				p.giveExperienceLevels(30);
				openAnvil(p, new ItemStack(Items.DIAMOND_SWORD), ItemStack.EMPTY);
			});
			ctx.waitForScreen(AnvilScreen.class);
			ctx.waitTicks(20);
			ctx.takeScreenshot("02_yunque_plan_espada");
			// the same at GUI scale 3 (less room at the side of the anvil)
			ctx.runOnClient(mc -> {
				mc.options.guiScale().set(3);
				mc.resizeGui();
			});
			ctx.waitTicks(10);
			ctx.takeScreenshot("02b_yunque_plan_escala3");
			ctx.runOnClient(mc -> {
				mc.options.guiScale().set(2);
				mc.resizeGui();
			});

			// --- anvil with the pickaxes the wrong way round
			sp.getServer().runOnServer(s -> {
				ServerPlayer p = player(s);
				p.closeContainer();
				p.getInventory().clearContent();
				openAnvil(p, item(s, Items.DIAMOND_PICKAXE, 0, Enchantments.EFFICIENCY, 4),
					item(s, Items.DIAMOND_PICKAXE, 0, Enchantments.EFFICIENCY, 4, Enchantments.UNBREAKING, 3, Enchantments.SILK_TOUCH, 1));
			});
			ctx.waitTicks(10);
			ctx.takeScreenshot("03_yunque_picos_al_reves");

			// --- tooltip with Shift: what the boots are missing
			sp.getServer().runOnServer(s -> {
				ServerPlayer p = player(s);
				p.closeContainer();
				ItemStack boots = item(s, Items.DIAMOND_BOOTS, 1, Enchantments.PROTECTION, 3, Enchantments.FEATHER_FALLING, 4,
					Enchantments.DEPTH_STRIDER, 2, Enchantments.UNBREAKING, 3, Enchantments.MENDING, 1);
				p.getInventory().setItem(0, boots);
			});
			ctx.waitTicks(5);
			ctx.setScreen(() -> new InventoryScreen(ctx.computeOnClient(mc -> mc.player)));
			ctx.waitForScreen(InventoryScreen.class);
			hoverHotbarSlot0(ctx);
			ctx.getInput().holdShift();
			ctx.waitTicks(5);
			ctx.takeScreenshot("04_tooltip_botas_mayus");
			ctx.getInput().releaseShift();
			ctx.setScreen(() -> null);

			// --- enchanting table with 15 bookshelves
			sp.getServer().runOnServer(s -> {
				ServerPlayer p = player(s);
				BlockPos t = p.blockPosition().offset(0, 0, -6);
				var level = p.level();
				level.setBlockAndUpdate(t, net.minecraft.world.level.block.Blocks.ENCHANTING_TABLE.defaultBlockState());
				for (int dx = -2; dx <= 2; dx++) {
					for (int dz = -2; dz <= 2; dz++) {
						if (Math.abs(dx) == 2 || Math.abs(dz) == 2) {
							level.setBlockAndUpdate(t.offset(dx, 0, dz), net.minecraft.world.level.block.Blocks.BOOKSHELF.defaultBlockState());
						}
					}
				}
				p.getInventory().setItem(1, new ItemStack(Items.LAPIS_LAZULI, 3));
				p.giveExperienceLevels(30);
				p.openMenu(new SimpleMenuProvider((id, inv, pl) -> new EnchantmentMenu(id, inv, ContainerLevelAccess.create(level, t)),
					Component.translatable("container.enchant")));
				p.containerMenu.getSlot(0).set(new ItemStack(Items.DIAMOND_SWORD));
				p.containerMenu.getSlot(1).set(new ItemStack(Items.LAPIS_LAZULI, 3));
			});
			ctx.waitForScreen(EnchantmentScreen.class);
			ctx.waitTicks(10);
			ctx.takeScreenshot("05_mesa_encantamientos");

			// --- grindstone
			sp.getServer().runOnServer(s -> {
				ServerPlayer p = player(s);
				p.closeContainer();
				p.openMenu(new SimpleMenuProvider((id, inv, pl) -> new GrindstoneMenu(id, inv), Component.translatable("container.grindstone_title")));
				p.containerMenu.getSlot(0).set(item(s, Items.DIAMOND_SWORD, 3, Enchantments.SMITE, 3, Enchantments.SWEEPING_EDGE, 3));
			});
			ctx.waitForScreen(GrindstoneScreen.class);
			ctx.waitTicks(5);
			ctx.takeScreenshot("06_muela");

		}
	}

	static ServerPlayer player(MinecraftServer s) {
		return s.getPlayerList().getPlayers().get(0);
	}

	private static void openAnvil(ServerPlayer p, ItemStack left, ItemStack right) {
		p.openMenu(new SimpleMenuProvider((id, inv, pl) -> new AnvilMenu(id, inv), Component.translatable("container.repair")));
		p.containerMenu.getSlot(AnvilMenu.INPUT_SLOT).set(left);
		p.containerMenu.getSlot(AnvilMenu.ADDITIONAL_SLOT).set(right);
	}

	static Holder<Enchantment> ench(MinecraftServer s, ResourceKey<Enchantment> key) {
		return s.registryAccess().lookupOrThrow(Registries.ENCHANTMENT).getOrThrow(key);
	}

	static ItemStack book(MinecraftServer s, ResourceKey<Enchantment> key, int level) {
		ItemStack b = new ItemStack(Items.ENCHANTED_BOOK);
		ItemEnchantments.Mutable m = new ItemEnchantments.Mutable(ItemEnchantments.EMPTY);
		m.set(ench(s, key), level);
		b.set(DataComponents.STORED_ENCHANTMENTS, m.toImmutable());
		return b;
	}

	/** item, repair cost, then enchantment/level pairs */
	static ItemStack item(MinecraftServer s, Item item, int repairCost, Object... kv) {
		ItemStack st = new ItemStack(item);
		ItemEnchantments.Mutable m = new ItemEnchantments.Mutable(ItemEnchantments.EMPTY);
		for (int i = 0; i < kv.length; i += 2) {
			@SuppressWarnings("unchecked")
			ResourceKey<Enchantment> k = (ResourceKey<Enchantment>) kv[i];
			m.set(ench(s, k), (Integer) kv[i + 1]);
		}
		st.set(DataComponents.ENCHANTMENTS, m.toImmutable());
		st.set(DataComponents.REPAIR_COST, repairCost);
		return st;
	}

	private static void hoverHotbarSlot0(ClientGameTestContext ctx) {
		double[] pos = ctx.computeOnClient(mc -> {
			var w = mc.getWindow();
			int left = (w.getGuiScaledWidth() - 176) / 2, top = (w.getGuiScaledHeight() - 166) / 2;
			return new double[] {(left + 8 + 8) * w.getGuiScale(), (top + 142 + 8) * w.getGuiScale()};
		});
		ctx.getInput().setCursorPos(pos[0], pos[1]);
	}

	/** Copies the packs named in -Daurora.order (bottom to top) from -Daurora.packs into resourcepacks and enables them. */
	static void enableAuroraPack(ClientGameTestContext ctx) {
		String src = System.getProperty("aurora.packs");
		if (src == null) {
			return;
		}
		ctx.runOnClient(mc -> {
			List<String> sel = new ArrayList<>(mc.getResourcePackRepository().getSelectedIds());
			for (String name : System.getProperty("aurora.order", "Aurora Pack,Aurora Outline").split(",")) {
				try {
					copy(Path.of(src, name), mc.getResourcePackDirectory().resolve(name));
				} catch (IOException e) {
					throw new java.io.UncheckedIOException(e);
				}
				if (!sel.contains("file/" + name)) {
					sel.add("file/" + name);
				}
			}
			mc.getResourcePackRepository().reload();
			mc.getResourcePackRepository().setSelected(sel);
			mc.options.languageCode = "es_es";
			mc.getLanguageManager().setSelected("es_es");
			mc.options.guiScale().set(2);
			mc.resizeGui();
			mc.options.updateResourcePacks(mc.getResourcePackRepository());
		});
		ctx.waitTicks(40);
		ctx.waitFor(mc -> mc.gui.overlay() == null, 20 * 120);
	}

	private static void copy(Path from, Path to) throws IOException {
		try (Stream<Path> walk = Files.walk(from)) {
			for (Path p : (Iterable<Path>) walk::iterator) {
				Path t = to.resolve(from.relativize(p).toString());
				if (Files.isDirectory(p)) {
					Files.createDirectories(t);
				} else {
					Files.copy(p, t, java.nio.file.StandardCopyOption.REPLACE_EXISTING);
				}
			}
		}
	}
}

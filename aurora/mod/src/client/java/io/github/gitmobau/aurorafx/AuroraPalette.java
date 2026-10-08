package io.github.gitmobau.aurorafx;

/**
 * Paleta Aurora, la misma que {@code aurora/scripts/gear.py} ({@code P}, {@code VIVID} y {@code cyc()}).
 */
public final class AuroraPalette {
	/** Pastel: cian, azul, lavanda, lila, rosa, salmón, melocotón, amarillo, lima, menta. */
	public static final int[] P = {
			0x7BE1F9, 0x9BD2F8, 0xBBB9F8, 0xDCB5F0, 0xF8B0EA,
			0xF8BCC7, 0xF8C9AD, 0xF8E19C, 0xD1F891, 0xAAF5D7
	};
	/** Versión saturada de la paleta (se usa para el brillo de la armadura). */
	public static final int[] VIVID = {
			0x50DCFF, 0x78AFFF, 0xAA8CFF, 0xDC82FF, 0xFF7DDC,
			0xFF96AF, 0xFFBE87, 0xFFE478, 0xAFF887, 0x6EF5CD
	};

	private AuroraPalette() {
	}

	/** Interpola cíclicamente la paleta; {@code t} se toma módulo 1. Devuelve 0xRRGGBB. */
	public static int cyc(float t, int[] pal) {
		float f = (t - (float) Math.floor(t)) * pal.length;
		int i = ((int) f) % pal.length;
		float k = f - (int) f;
		int a = pal[i];
		int b = pal[(i + 1) % pal.length];
		int r = lerp((a >> 16) & 0xFF, (b >> 16) & 0xFF, k);
		int g = lerp((a >> 8) & 0xFF, (b >> 8) & 0xFF, k);
		int bl = lerp(a & 0xFF, b & 0xFF, k);
		return (r << 16) | (g << 8) | bl;
	}

	/**
	 * Color ARGB opaco con el RGB multiplicado por {@code brightness} (0..1).
	 * Para la mezcla aditiva el brillo es lo que manda, no el alfa.
	 */
	public static int argbScaled(int rgb, float brightness) {
		float s = Math.max(0.0F, Math.min(1.0F, brightness));
		int r = Math.round(((rgb >> 16) & 0xFF) * s);
		int g = Math.round(((rgb >> 8) & 0xFF) * s);
		int b = Math.round((rgb & 0xFF) * s);
		return 0xFF000000 | (r << 16) | (g << 8) | b;
	}

	private static int lerp(int a, int b, float k) {
		return Math.round(a + (b - a) * k);
	}
}

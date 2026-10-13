import type { CSSProperties } from 'react';

/**
 * Inline-style fallback for edit mode (SchemaRenderer), which renders LLM
 * schemas with the host app's Tailwind build. Tailwind only generates classes
 * it finds in our source, so two kinds of colour class would render bare:
 *
 * - arbitrary values: bg-[#0f172a], text-[#fbbf24], border-[#334155],
 *   from-/via-/to-[#667eea]
 * - gradient stops: from-/via-/to-{hue}-{shade}. These are deliberately not
 *   safelisted in index.css (~157 KB of CSS). Their colours come from the
 *   --color-* theme variables that the bg/text/border safelist already emits.
 *
 * - opacity colours: bg-blue-500/50, text-white/80, border-[#0f172a]/40,
 *   from-rose-500/30 (the safelist has no opacity variants), drawn with
 *   color-mix() over the same colour.
 *
 * Only unprefixed classes are handled: variants like hover:/md: can't be
 * expressed inline and are left to Tailwind.
 */

const HEX = /^#(?:[0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})$/i;

// Must match the hues safelisted in src/index.css; only those have a
// --color-* variable guaranteed to exist in the build.
const PALETTE_HUES = new Set([
  'slate', 'gray', 'zinc', 'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald',
  'teal', 'cyan', 'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose',
]);
const PALETTE_SHADES = new Set(['50', '100', '200', '300', '400', '500', '600', '700', '800', '900']);
const KEYWORD_COLORS: Record<string, string> = {
  white: 'var(--color-white)',
  black: 'var(--color-black)',
  transparent: 'transparent',
};

const DIRECTIONS: Record<string, string> = {
  t: 'to top', tr: 'to top right', r: 'to right', br: 'to bottom right',
  b: 'to bottom', bl: 'to bottom left', l: 'to left', tl: 'to top left',
};

/** `[#abc]` -> `#abc`; anything else -> null. */
function arbitraryHex(value: string): string | null {
  const m = value.match(/^\[(#[0-9a-fA-F]+)\]$/);
  return m && HEX.test(m[1]) ? m[1] : null;
}

/** "<colour>/<0-100>" -> color-mix() of that colour; null if not an opacity colour. */
function withOpacity(value: string): string | null {
  const m = value.match(/^(.+)\/(\d{1,3})$/);
  if (!m || Number(m[2]) > 100) return null;
  const base = stopColor(m[1]);
  if (!base || base === 'transparent') return null;
  return `color-mix(in oklab, ${base} ${Number(m[2])}%, transparent)`;
}

/** A gradient-stop colour: [#hex], palette hue-shade, white/black/transparent, or any of those /opacity. */
function stopColor(value: string): string | null {
  if (value.includes('/')) return withOpacity(value);
  const hex = arbitraryHex(value);
  if (hex) return hex;
  if (value in KEYWORD_COLORS) return KEYWORD_COLORS[value];
  const m = value.match(/^([a-z]+)-(\d+)$/);
  if (m && PALETTE_HUES.has(m[1]) && PALETTE_SHADES.has(m[2])) return `var(--color-${m[1]}-${m[2]})`;
  return null;
}

export function classStyle(className: string | undefined, explicit?: unknown): CSSProperties | undefined {
  const style: CSSProperties = {};
  let direction: string | undefined;
  const stops: { from?: string; via?: string; to?: string } = {};

  for (const raw of (className ?? '').split(/\s+/)) {
    if (!raw) continue;
    // Important modifier, either side (v3 "!bg-x", v4 "bg-x!").
    const token = raw.replace(/^!/, '').replace(/!$/, '');
    // Variant-prefixed (hover:, md:, dark:, [&>*]:) — not expressible inline.
    if (/^[^[]*:/.test(token) || token.startsWith('[')) continue;

    const dir = token.match(/^bg-(?:gradient|linear)-to-(t|tr|r|br|b|bl|l|tl)$/);
    if (dir) {
      direction = DIRECTIONS[dir[1]];
      continue;
    }

    const m = token.match(/^(bg|text|border|from|via|to)-(.+)$/);
    if (!m) continue;
    const [, utility, value] = m;

    if (utility === 'from' || utility === 'via' || utility === 'to') {
      const color = stopColor(value);
      if (color) stops[utility] = color;
      continue;
    }

    // Arbitrary hex, or an opacity colour (palette classes without opacity
    // are safelisted and need no inline style).
    const hex = arbitraryHex(value) ?? withOpacity(value);
    if (!hex) continue;
    if (utility === 'bg') style.backgroundColor = hex;
    else if (utility === 'text') style.color = hex;
    else style.borderColor = hex;
  }

  if (direction && (stops.from || stops.via || stops.to)) {
    // Tailwind's defaults: a missing from/to stop is transparent.
    const colors = [stops.from ?? 'transparent', ...(stops.via ? [stops.via] : []), stops.to ?? 'transparent'];
    style.backgroundImage = `linear-gradient(${direction}, ${colors.join(', ')})`;
  }

  // Explicit style props from the schema always win.
  const merged = {
    ...style,
    ...(explicit && typeof explicit === 'object' && !Array.isArray(explicit) ? (explicit as CSSProperties) : {}),
  };
  return Object.keys(merged).length > 0 ? merged : undefined;
}

/**
 * Default classes for the in-app renderer (edit mode), added without ever
 * overriding what the schema asked for.
 *
 * Tailwind orders conflicting utilities by their position in the stylesheet,
 * not by their order in the class attribute, so `${className} text-gray-500`
 * can silently beat the schema's own `text-blue-200`. withDefaults() drops a
 * default whenever the schema already sets the same property, instead of
 * relying on order. Nothing the schema wrote is touched.
 */

const BRACKETS = /\[[^\]]*\]/g;
const BG_NON_COLOUR = /^bg-(?:clip|origin|blend|repeat|no-repeat|cover|contain|auto|center|top|bottom|left|right|fixed|local|scroll|none|\[(?:length|position|size|percentage):)/;
const TEXT_SIZE = /^text-(?:xs|sm|base|lg|xl|[2-9]xl|\[\d[^\]]*(?:px|rem|em|%|vw|vh)\])$/;
const TEXT_COLOUR = /^text-(?:white|black|transparent|current|inherit|[a-z]+-\d{2,3}(?:\/\d+)?|\[(?:#|rgb|hsl|oklch|color:)[^\]]*\](?:\/\d+)?)$/;
const BORDER_COLOUR = /^border-(?:white|black|transparent|current|[a-z]+-\d{2,3}(?:\/\d+)?|\[(?:#|rgb|hsl|oklch|color:)[^\]]*\](?:\/\d+)?)$/;

/** Base-state utilities only: no `hover:`/`md:`/`[&>*]:` variant; `!` stripped. */
function utilities(className: string): string[] {
  return className
    .split(/\s+/)
    .filter((t) => t && !t.startsWith('[') && !t.replace(BRACKETS, '').includes(':'))
    .map((t) => t.replace(/^!/, '').replace(/!$/, ''));
}

/** The property a utility sets, for the properties our defaults can clash on. */
function propertyOf(utility: string): string | null {
  if (utility.startsWith('bg-') && !BG_NON_COLOUR.test(utility)) return 'background';
  if (TEXT_SIZE.test(utility)) return 'text-size';
  if (TEXT_COLOUR.test(utility)) return 'text-color';
  if (BORDER_COLOUR.test(utility)) return 'border-color';
  if (utility === 'rounded' || utility.startsWith('rounded-')) return 'rounded';
  if (utility === 'shadow' || /^shadow-(?:sm|md|lg|xl|2xl|inner|none)$/.test(utility)) return 'shadow';
  const m = utility.match(/^(p|px|py|pt|pb|pl|pr)-/);
  if (m) return `padding-${m[1]}`;
  if (/^font-(?:thin|extralight|light|normal|medium|semibold|bold|extrabold|black)$/.test(utility)) return 'font-weight';
  return null;
}

/** A base-state background colour or gradient (not bg-clip-text, not hover:bg-x). */
export function hasBackground(className: string): boolean {
  return utilities(className).some((u) => propertyOf(u) === 'background');
}

/**
 * `className` followed by those `defaults` whose property it doesn't already
 * set. Variant defaults (hover:shadow-lg) are kept unless the schema has the
 * same variant class, which they can't conflict with otherwise.
 */
export function withDefaults(className: string, defaults: string): string {
  const taken = new Set(utilities(className).map(propertyOf).filter((p): p is string => p !== null));
  const own = new Set(className.split(/\s+/));
  const kept = defaults
    .split(/\s+/)
    .filter((d) => d && !own.has(d) && !taken.has(propertyOf(d) ?? '\0'));
  return [className, ...kept].join(' ').trim();
}

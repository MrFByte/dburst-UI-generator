/**
 * URL allowlist for user/LLM-supplied href and src values rendered in the app
 * (mirrors backend/generation/codegen.py safe_url). Allows http(s), mailto,
 * tel, #anchors and relative paths (/x, ./x, ../x). Everything else
 * (javascript:, data:, vbscript:, file:, //host, bare words) is rejected.
 * Schemas already stored in the database pass through here too.
 */

const SAFE_SCHEMES = new Set(['http', 'https', 'mailto', 'tel']);

/** Returns the (leading-whitespace-trimmed) URL if safe, otherwise null. */
export function safeUrl(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  // eslint-disable-next-line no-control-regex
  const url = value.replace(/^[\u0000- ]+/, '');
  if (!url) return null;

  // Browsers drop tab/CR/LF anywhere in a URL ("java\tscript:"), so the
  // scheme check runs on that form.
  const probe = url.replace(/[\t\r\n]/g, '').toLowerCase();
  if (probe.startsWith('#')) return url;
  if (probe.startsWith('/')) {
    // "//host" and "/\host" are protocol-relative to browsers.
    return probe[1] === '/' || probe[1] === '\\' ? null : url;
  }
  if (probe.startsWith('./') || probe.startsWith('../')) return url;

  const scheme = probe.match(/^([a-z][a-z0-9+.-]*):/);
  return scheme && SAFE_SCHEMES.has(scheme[1]) ? url : null;
}

export function safeHref(value: unknown): string {
  return safeUrl(value) ?? '#';
}

/** Only _blank and _self; _blank always gets rel="noopener noreferrer". */
export function safeLinkTarget(target: unknown): { target?: '_blank' | '_self'; rel?: string } {
  if (target === '_blank') return { target, rel: 'noopener noreferrer' };
  if (target === '_self') return { target };
  return {};
}

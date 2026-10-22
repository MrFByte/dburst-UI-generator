/**
 * User-facing error wording, by the backend's stable error `code` and by HTTP
 * status. The backend already sends a friendly `error` for its own codes;
 * these are the fallbacks for when it can't (proxy pages, network failures,
 * legacy bodies) and the source of truth for client-side codes.
 */

export const GENERIC_ERROR = "Something went wrong. Please try again.";

export const MESSAGES_BY_CODE: Record<string, string> = {
  // Client-side (no usable server response)
  network_error: "Can't reach the server. Check your internet connection.",
  timeout: "This is taking longer than expected. Please check your connection and try again.",
  csrf_failed: "Your session security check failed. Please refresh the page and try again.",

  // Auth & access
  not_authenticated: "Your session has expired. Please sign in again.",
  permission_denied: "You don't have permission to do that.",
  not_found: "We couldn't find what you were looking for.",
  validation_error: "Please check the highlighted fields and try again.",
  bad_request: "That request couldn't be processed. Please check your input and try again.",
  method_not_allowed: "This action isn't supported.",
  throttled: "You're doing that too often. Please wait a moment and try again.",
  server_error: "Something went wrong on our side. Please try again.",
  service_unavailable: "This service is temporarily unavailable. Please try again in a moment.",

  // AI generation
  llm_bad_request: "The AI model couldn't process this request. Try rephrasing your prompt, shortening it, or choosing a different model.",
  llm_rate_limited: "The model is busy right now. Please wait a moment and try again, or pick another model.",
  llm_unavailable: "This model is temporarily unavailable. Please try again shortly or choose a different model.",
  llm_quota: "This model is temporarily unavailable. Please choose a different model.",
  llm_timeout: "The model took too long to respond. Try again, or use a faster model or a simpler prompt.",
  llm_content_blocked: "The AI couldn't generate this because of its content policy. Try a different description.",
  llm_invalid_response: "The AI returned an incomplete design. Please try again.",
  llm_error: "The AI model ran into a problem. Please try again, or choose a different model.",

  // Editing, OTP, OAuth
  invalid_schema: "This change couldn't be applied because it would break the page structure.",
  nothing_to_undo: "There's nothing to undo.",
  otp_invalid: "Invalid or expired code. Please try again.",
  otp_rate_limited: "Too many code requests. Please try again later.",
  email_unavailable: "We couldn't send the email right now. Please try again.",
  oauth_failed: "Sign-in failed. Please try again.",
  oauth_unavailable: "We couldn't reach the sign-in provider. Please try again.",
};

export const MESSAGES_BY_STATUS: Record<number, string> = {
  400: MESSAGES_BY_CODE.bad_request,
  401: MESSAGES_BY_CODE.not_authenticated,
  403: MESSAGES_BY_CODE.permission_denied,
  404: MESSAGES_BY_CODE.not_found,
  408: MESSAGES_BY_CODE.timeout,
  413: "That's too large to send. Please shorten it and try again.",
  422: "That couldn't be processed. Please adjust it and try again.",
  429: "Too many requests. Please wait a moment and try again.",
  500: MESSAGES_BY_CODE.server_error,
  502: "Our server is having trouble right now. Please try again in a moment.",
  503: MESSAGES_BY_CODE.service_unavailable,
  504: "The server took too long to respond. Please try again.",
};

/** Codes for which a "try again" makes sense (offer Retry). */
export const RETRYABLE_CODES = new Set([
  "network_error", "timeout", "server_error", "service_unavailable",
  "llm_unavailable", "llm_timeout", "llm_invalid_response", "llm_error", "llm_rate_limited", "throttled",
]);

const MAX_MESSAGE_LENGTH = 300;

/**
 * True for text that must never be shown to a user: JSON/HTML blobs, stack
 * traces, provider payloads, HTTP status jargon, or anything very long.
 */
export function isUnsafeMessage(text: unknown): boolean {
  if (typeof text !== "string") return true;
  const t = text.trim();
  if (!t || t.length > MAX_MESSAGE_LENGTH) return true;
  if (/^[[{<]/.test(t)) return true;                                          // JSON / HTML
  if (/<\/?[a-z!][^>]*>/i.test(t)) return true;                               // embedded tags
  if (/"(error|message|status|code)"\s*:/.test(t) || /\{\s*"/.test(t)) return true; // JSON fragments
  if (/\bat [\w$.<>]+ \(|Traceback|\.(py|tsx?|jsx?):\d+|Exception:|Error\s*\(\d{3}\)/.test(t)) return true; // traces
  if (/^(Request failed with status code|Network Error$|timeout of \d+ms exceeded)/i.test(t)) return true; // axios jargon
  if (/\b[A-Z]+_[A-Z_]+\b/.test(t) && /INVALID|EXHAUSTED|DENIED|UNAVAILABLE|EXCEEDED|PRECONDITION/.test(t)) return true; // provider status names
  return false;
}

/** Best message for a code/status, never jargon. */
export function defaultMessage(code?: string, status?: number): string {
  return (code && MESSAGES_BY_CODE[code]) || (status && MESSAGES_BY_STATUS[status]) ||
    (status && status >= 500 ? MESSAGES_BY_CODE.server_error : GENERIC_ERROR);
}

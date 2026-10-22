import axios from "axios";
import type { AxiosError } from "axios";
import { MESSAGES_BY_CODE, MESSAGES_BY_STATUS, defaultMessage, isUnsafeMessage } from "./errorMessages";

/**
 * The one shape every failure is turned into. `message` is always safe to show
 * to a user; raw bodies, stack traces and provider payloads never end up here.
 */
export interface ApiError {
  isApiError: true;
  message: string;
  /** Stable machine code (backend `code`, or network_error / timeout / aborted). */
  code: string;
  status?: number;
  /** Per-field messages for forms, e.g. { avatar_url: ["Enter a valid URL."] }. */
  details?: Record<string, string[]>;
  /** Seconds to wait before retrying (429). */
  retryAfter?: number;
  /** Backend request id, shown with 5xx errors for support. */
  requestId?: string;
}

export function isApiError(value: unknown): value is ApiError {
  return typeof value === "object" && value !== null && (value as ApiError).isApiError === true;
}

type Body = Record<string, unknown>;

function header(error: AxiosError, name: string): string | undefined {
  const headers = error.response?.headers as Record<string, unknown> | undefined;
  const value = headers?.[name] ?? headers?.[name.toLowerCase()];
  return typeof value === "string" ? value : undefined;
}

function toSeconds(value: unknown): number | undefined {
  const n = typeof value === "string" ? Number(value) : value;
  return typeof n === "number" && Number.isFinite(n) && n > 0 ? Math.ceil(n) : undefined;
}

/** A DRF field-error dict: every value is a list of strings (or nested dicts). */
function asFieldErrors(value: unknown): Record<string, string[]> | undefined {
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  const out: Record<string, string[]> = {};
  for (const [field, messages] of Object.entries(value as Body)) {
    const list = (Array.isArray(messages) ? messages : [messages])
      .flat(3)
      .filter((m): m is string => typeof m === "string" && !isUnsafeMessage(m));
    if (list.length) out[field] = list;
  }
  return Object.keys(out).length ? out : undefined;
}

function humanizeField(field: string, message: string): string {
  if (field === "non_field_errors" || !message.startsWith("This field")) return message;
  const name = field.replace(/_/g, " ");
  return name.charAt(0).toUpperCase() + name.slice(1) + message.slice("This field".length);
}

function fromResponse(error: AxiosError): ApiError {
  const status = error.response!.status;
  const raw = error.response!.data;
  const body: Body | undefined = raw && typeof raw === "object" && !Array.isArray(raw) ? (raw as Body) : undefined;

  let code = typeof body?.code === "string" ? body.code : "";
  let details = asFieldErrors(body?.details);
  let message: string | undefined;

  // The contract / legacy keys, if their text is safe to show.
  for (const key of ["error", "message", "detail"]) {
    const value = body?.[key];
    if (typeof value === "string" && !isUnsafeMessage(value)) {
      message = value;
      break;
    }
  }

  // Legacy DRF field-error body: {"email": ["Enter a valid email address."]}
  if (!message && !code && body && !("error" in body) && !("detail" in body)) {
    const fields = asFieldErrors(body);
    if (fields) {
      details = fields;
      code = "validation_error";
      const pairs = Object.entries(fields).flatMap(([f, ms]) => ms.map((m) => humanizeField(f, m)));
      message = pairs.length === 1 ? pairs[0] : MESSAGES_BY_CODE.validation_error;
    }
  }

  const legacyDetail = typeof body?.detail === "string" ? body.detail : "";
  if (status === 403 && (code === "csrf_failed" || legacyDetail.startsWith("CSRF Failed"))) {
    code = "csrf_failed";
    message = MESSAGES_BY_CODE.csrf_failed;
  }

  if (!code) {
    code = status === 401 ? "not_authenticated" : status === 403 ? "permission_denied" : status === 404 ? "not_found"
      : status === 429 ? "throttled" : status >= 500 ? "server_error" : "bad_request";
  }
  // 401 without a contract message: the generic session-expired wording.
  if (status === 401 && !body?.code) message = MESSAGES_BY_CODE.not_authenticated;

  const retryAfter = toSeconds(body?.retry_after) ?? toSeconds(header(error, "Retry-After"));
  if (status === 429 && retryAfter && !message) {
    message = `Too many requests. Please wait ${retryAfter} seconds and try again.`;
  }

  const requestId = (typeof body?.request_id === "string" && body.request_id) || header(error, "X-Request-ID");

  // No server-provided code: the status says more than our inferred code.
  const fallbackMessage = body?.code ? defaultMessage(code, status) : (MESSAGES_BY_STATUS[status] ?? defaultMessage(code, status));

  return {
    isApiError: true,
    message: message ?? fallbackMessage,
    code,
    status,
    details,
    retryAfter,
    requestId: requestId || undefined,
  };
}

/** Turn anything thrown by an API call (or our own code) into an ApiError. */
export function normalizeError(err: unknown): ApiError {
  if (isApiError(err)) return err;

  if (axios.isCancel(err) || (axios.isAxiosError(err) && err.code === "ERR_CANCELED") ||
      (err instanceof DOMException && err.name === "AbortError")) {
    return { isApiError: true, code: "aborted", message: "" };
  }

  if (axios.isAxiosError(err)) {
    if (err.response) return fromResponse(err);
    if (err.code === "ECONNABORTED" || err.code === "ETIMEDOUT") {
      return { isApiError: true, code: "timeout", message: MESSAGES_BY_CODE.timeout };
    }
    // No response at all: offline, DNS, CORS-blocked, server down.
    return { isApiError: true, code: "network_error", message: MESSAGES_BY_CODE.network_error };
  }

  // A plain Error from our own code: its text is for developers, not users.
  console.error("Unexpected error:", err);
  return { isApiError: true, code: "client_error", message: "" };
}

/** A safe message for `err`, or `fallback` (the call site's own wording). */
export function getErrorMessage(err: unknown, fallback?: string): string {
  const e = normalizeError(err);
  if (e.code === "aborted") return "";
  return e.message || fallback || defaultMessage(e.code, e.status);
}

/** Wraps an API call so callers only ever see a normalized ApiError. */
export async function apiHandler<T>(apiCall: () => Promise<T>): Promise<T> {
  try {
    return await apiCall();
  } catch (err) {
    const error = normalizeError(err);
    if (error.code !== "aborted") {
      // Diagnostics only (code/status/request id); never shown to users.
      console.warn("API error:", { code: error.code, status: error.status, requestId: error.requestId });
    }
    throw error;
  }
}

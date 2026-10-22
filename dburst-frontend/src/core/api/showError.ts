import { toast } from "@/shared/hooks/useToast";
import { RETRYABLE_CODES } from "./errorMessages";
import { normalizeError } from "./apiHandler";
import type { ApiError } from "./apiHandler";

interface ShowErrorOptions {
  /** Wording when the error carries no usable message ("Failed to load projects"). */
  fallback?: string;
  /** Offer a Retry button (only for errors where retrying can help). */
  onRetry?: () => void;
}

/** Short reference shown with server errors so support can find the log line. */
export function errorReference(error: ApiError): string | undefined {
  if (!error.requestId || !error.status || error.status < 500) return undefined;
  return `Reference: ${error.requestId.slice(0, 8)}`;
}

/**
 * Show any error as a friendly toast. Returns the normalized error so callers
 * can react to its code (e.g. start a rate-limit countdown). Aborted requests
 * are silent.
 */
export function showError(err: unknown, { fallback, onRetry }: ShowErrorOptions = {}): ApiError {
  const error = normalizeError(err);
  if (error.code === "aborted") return error;

  const message = error.message || fallback || "Something went wrong. Please try again.";
  toast.error(message, {
    description: errorReference(error),
    action: onRetry && RETRYABLE_CODES.has(error.code) ? { label: "Retry", onClick: onRetry } : undefined,
  });
  return error;
}

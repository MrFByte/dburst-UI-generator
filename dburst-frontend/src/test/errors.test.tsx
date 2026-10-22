import { describe, it, expect, vi, afterEach } from "vitest";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import axios, { AxiosError, AxiosHeaders, CanceledError } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";

import { getErrorMessage, normalizeError } from "@/core/api/apiHandler";
import { isUnsafeMessage, MESSAGES_BY_CODE } from "@/core/api/errorMessages";
import { showError } from "@/core/api/showError";
import api from "@/core/api/axiosConfig";
import { Toaster } from "@/shared/ui/Toaster";
import ErrorBoundary from "@/shared/components/ErrorBoundary";

const GEMINI_BLOB =
  'Gemini API Error (400): { "error": { "code": 400, "message": "Request contains an invalid argument.", "status": "INVALID_ARGUMENT" } }';

function httpError(status: number, data: unknown, headers: Record<string, string> = {}): AxiosError {
  const config = { headers: new AxiosHeaders() } as InternalAxiosRequestConfig;
  const response = { status, statusText: "x", data, headers, config } as AxiosResponse;
  return new AxiosError(`Request failed with status code ${status}`, "ERR_BAD_RESPONSE", config, {}, response);
}

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("normalizeError", () => {
  it("never shows the raw Gemini blob (legacy backend body)", () => {
    const e = normalizeError(httpError(400, { error: GEMINI_BLOB }));
    expect(e.message).not.toMatch(/INVALID_ARGUMENT|Gemini API Error|\{/);
    expect(e.message).toBe(MESSAGES_BY_CODE.bad_request);
    expect(e.status).toBe(400);
  });

  it("uses the contract's friendly message, code and request id", () => {
    const e = normalizeError(httpError(502, {
      error: MESSAGES_BY_CODE.llm_bad_request, code: "llm_bad_request", request_id: "abcd1234-ef",
    }));
    expect(e).toMatchObject({ message: MESSAGES_BY_CODE.llm_bad_request, code: "llm_bad_request", status: 502, requestId: "abcd1234-ef" });
  });

  it("falls back to the code's message when the contract text is unsafe", () => {
    const e = normalizeError(httpError(502, { error: '{"error": {"status": "INVALID_ARGUMENT"}}', code: "llm_bad_request" }));
    expect(e.message).toBe(MESSAGES_BY_CODE.llm_bad_request);
  });

  it("keeps per-field details from the contract", () => {
    const e = normalizeError(httpError(400, {
      error: "Please check the highlighted fields and try again.", code: "validation_error",
      details: { name: ["Name cannot be blank."], avatar_url: ["Enter a valid http(s) URL."] },
    }));
    expect(e.code).toBe("validation_error");
    expect(e.details).toEqual({ name: ["Name cannot be blank."], avatar_url: ["Enter a valid http(s) URL."] });
  });

  it("flattens a legacy DRF field-error dict", () => {
    const one = normalizeError(httpError(400, { email: ["Enter a valid email address."] }));
    expect(one).toMatchObject({ code: "validation_error", message: "Enter a valid email address." });
    expect(one.details).toEqual({ email: ["Enter a valid email address."] });

    const generic = normalizeError(httpError(400, { prompt: ["This field may not be blank."] }));
    expect(generic.message).toBe("Prompt may not be blank.");

    const many = normalizeError(httpError(400, { email: ["Bad."], code: ["Too short."] }));
    expect(many.message).toBe(MESSAGES_BY_CODE.validation_error);
  });

  it("reads 429 Retry-After from the body or the header", () => {
    const body = normalizeError(httpError(429, { error: "Please wait 12 seconds.", code: "llm_rate_limited", retry_after: 12 }));
    expect(body).toMatchObject({ retryAfter: 12, code: "llm_rate_limited", message: "Please wait 12 seconds." });

    const headerOnly = normalizeError(httpError(429, "<html>Too Many Requests</html>", { "retry-after": "7" }));
    expect(headerOnly.retryAfter).toBe(7);
    expect(headerOnly.message).toBe("Too many requests. Please wait 7 seconds and try again.");
  });

  it.each([
    [502, "<html><head><title>502 Bad Gateway</title></head><body><center>nginx</center></body></html>"],
    [504, "<!DOCTYPE html><html><body>ngrok gateway timeout</body></html>"],
    [500, "Traceback (most recent call last):\n  File \"views.py\", line 1"],
  ])("never shows an HTML/trace body for %s", (status, body) => {
    const e = normalizeError(httpError(status, body));
    expect(e.message).not.toMatch(/<|html|Traceback|nginx|ngrok/i);
    expect(e.code).toBe("server_error");
  });

  it("maps network errors, timeouts and aborts", () => {
    const config = { headers: new AxiosHeaders() } as InternalAxiosRequestConfig;
    expect(normalizeError(new AxiosError("Network Error", "ERR_NETWORK", config, {}))).toMatchObject({
      code: "network_error", message: "Can't reach the server. Check your internet connection.",
    });
    expect(normalizeError(new AxiosError("timeout of 60000ms exceeded", "ECONNABORTED", config, {})).code).toBe("timeout");
    expect(normalizeError(new CanceledError())).toMatchObject({ code: "aborted", message: "" });
    expect(normalizeError(new DOMException("aborted", "AbortError")).code).toBe("aborted");
  });

  it("401 without a contract body says the session expired", () => {
    const e = normalizeError(httpError(401, { detail: "Authentication credentials were not provided." }));
    expect(e).toMatchObject({ code: "not_authenticated", message: "Your session has expired. Please sign in again." });
  });

  it("recognises CSRF failures (contract code and legacy detail)", () => {
    expect(normalizeError(httpError(403, { error: "x", code: "csrf_failed" })).message).toBe(MESSAGES_BY_CODE.csrf_failed);
    const legacy = normalizeError(httpError(403, { detail: "CSRF Failed: CSRF token missing." }));
    expect(legacy).toMatchObject({ code: "csrf_failed", message: MESSAGES_BY_CODE.csrf_failed });
  });

  it("413 and unknown 4xx get readable defaults", () => {
    expect(normalizeError(httpError(413, "<html>Request Entity Too Large</html>")).message).toBe(
      "That's too large to send. Please shorten it and try again."
    );
  });

  it("does not expose messages from our own thrown Errors", () => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    expect(getErrorMessage(new TypeError("Cannot read properties of undefined (reading 'map')"), "Failed to load")).toBe("Failed to load");
  });

  it("is idempotent", () => {
    const e = normalizeError(httpError(404, { error: "Project not found.", code: "not_found" }));
    expect(normalizeError(e)).toBe(e);
  });
});

describe("isUnsafeMessage", () => {
  it.each([
    GEMINI_BLOB,
    '{"error": "x"}',
    "<html>oops</html>",
    "Request failed with status code 500",
    "Network Error",
    "Error at Object.<anonymous> (app.js:10:5)",
    "RESOURCE_EXHAUSTED: quota",
    "x".repeat(400),
    "",
  ])("rejects %j", (text) => expect(isUnsafeMessage(text)).toBe(true));

  it.each([
    "Project not found.",
    "The model is busy right now. Please wait 12 seconds and try again, or pick another model.",
    "Invalid or expired OTP.",
  ])("accepts %j", (text) => expect(isUnsafeMessage(text)).toBe(false));
});

describe("showError", () => {
  function renderToaster() {
    return render(<Toaster />);
  }

  it.each([
    httpError(400, { error: GEMINI_BLOB }),
    httpError(502, "<html><body>502 Bad Gateway</body></html>"),
    httpError(500, { error: "Failed to apply patch", details: "Traceback ... psycopg2.OperationalError" }),
    new Error('{"status": "INVALID_ARGUMENT"}'),
  ])("never renders JSON/HTML/trace text (%#)", async (err) => {
    vi.spyOn(console, "error").mockImplementation(() => {});
    renderToaster();
    await act(async () => { showError(err, { fallback: "Failed to generate UI" }); });
    const text = screen.getByRole("alert").textContent ?? "";
    expect(text).not.toMatch(/[{}<>]|INVALID_ARGUMENT|Traceback|psycopg2|html/i);
    expect(text.length).toBeGreaterThan(10);
  });

  it("shows a reference for 5xx errors with a request id", async () => {
    renderToaster();
    await act(async () => {
      showError(httpError(500, { error: "Something went wrong on our side. Please try again.", code: "server_error", request_id: "abcd1234-5678-90" }));
    });
    expect(screen.getByRole("alert").textContent).toContain("Reference: abcd1234");
  });

  it("offers Retry for retryable errors and calls it", async () => {
    const onRetry = vi.fn();
    renderToaster();
    await act(async () => {
      showError(httpError(503, { error: "This model is temporarily unavailable.", code: "llm_unavailable" }), { onRetry });
    });
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it("no Retry for errors retrying can't fix", async () => {
    renderToaster();
    await act(async () => {
      showError(httpError(422, { error: "Blocked by content policy.", code: "llm_content_blocked" }), { onRetry: vi.fn() });
    });
    expect(screen.queryByRole("button", { name: "Retry" })).toBeNull();
  });

  it("is silent for aborted requests", async () => {
    renderToaster();
    await act(async () => { showError(new CanceledError()); });
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

describe("axios CSRF auto-retry with the error contract", () => {
  it("refreshes the CSRF cookie and retries once on code=csrf_failed", async () => {
    const original = api.defaults.adapter;
    document.cookie = "csrftoken=old; path=/";
    vi.spyOn(axios, "get").mockImplementation(async () => {
      document.cookie = "csrftoken=fresh; path=/";
      return { data: {} };
    });
    const sent: string[] = [];
    api.defaults.adapter = async (config) => {
      sent.push(String(config.headers.get("X-CSRFToken")));
      const status = sent.length === 1 ? 403 : 200;
      const data = status === 403 ? { error: "x", code: "csrf_failed" } : { ok: true };
      const response = { data, status, statusText: "", headers: {}, config } as AxiosResponse;
      if (status === 403) throw new AxiosError("403", "ERR_BAD_REQUEST", config, null, response);
      return response;
    };
    try {
      const res = await api.post("projects/create-project/", { title: "x" });
      expect(res.data).toEqual({ ok: true });
      expect(sent).toEqual(["old", "fresh"]);
    } finally {
      api.defaults.adapter = original;
    }
  });
});

describe("ErrorBoundary", () => {
  function Boom(): never {
    throw new Error("render exploded");
  }

  it("renders the friendly fallback and logs the real error", () => {
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>
    );
    expect(screen.getByRole("heading", { name: "Something went wrong" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Reload" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Go to dashboard" })).toBeTruthy();
    expect(document.body.textContent).not.toContain("render exploded");
    expect(log.mock.calls.some((c) => c.some((a) => a instanceof Error && a.message === "render exploded"))).toBe(true);
  });

  it("renders children when nothing throws", () => {
    render(<ErrorBoundary><p>fine</p></ErrorBoundary>);
    expect(screen.getByText("fine")).toBeTruthy();
  });
});

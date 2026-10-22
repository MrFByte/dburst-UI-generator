import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";

import { store } from "@/core/redux/store";
import { setCredentials } from "@/core/redux/authSlice";
import Dashboard from "@/features/dashboard/pages/Dashboard";
import { Toaster } from "@/shared/ui/Toaster";
import { generateUI, getAvailableModels, getRecentProjects } from "@/features/dashboard/api/dashboardApi";
import type { ApiError } from "@/core/api/apiHandler";

vi.mock("@/features/dashboard/api/dashboardApi", () => ({
  generateUI: vi.fn(),
  getAvailableModels: vi.fn(),
  getRecentProjects: vi.fn(),
  createProject: vi.fn(),
}));

const RATE_LIMITED: ApiError = {
  isApiError: true,
  code: "llm_rate_limited",
  status: 429,
  retryAfter: 12,
  message: "The model is busy right now. Please wait 12 seconds and try again, or pick another model.",
};

function renderDashboard() {
  return render(
    <Provider store={store}>
      <MemoryRouter>
        <Dashboard />
        <Toaster />
      </MemoryRouter>
    </Provider>
  );
}

beforeEach(() => {
  store.dispatch(setCredentials({ user: { id: "u1", email: "a@b.co", name: "A", role: "user" } }));
  vi.mocked(getRecentProjects).mockResolvedValue([]);
  vi.mocked(getAvailableModels).mockResolvedValue({ models: [{ id: "groq:x", label: "X" }], default: "groq:x" });
});

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("Dashboard generate errors", () => {
  it("keeps the prompt, shows the friendly message and counts down after a rate limit", async () => {
    vi.mocked(generateUI).mockRejectedValue(RATE_LIMITED);
    renderDashboard();
    const prompt = await screen.findByPlaceholderText(/^e\.g\., /);
    fireEvent.change(prompt, { target: { value: "A bakery website with a menu" } });

    await act(async () => fireEvent.click(screen.getByRole("button", { name: /Build Now/ })));

    expect((await screen.findByRole("alert")).textContent).toContain("Please wait 12 seconds");
    expect((prompt as HTMLTextAreaElement).value).toBe("A bakery website with a menu");
    const button = screen.getByRole("button", { name: /Try again in 12s/ }) as HTMLButtonElement;
    expect(button.disabled).toBe(true);
    expect(screen.queryByText("Generating...")).toBeNull();

    // Retry from the toast is offered for rate limits.
    expect(screen.getByRole("button", { name: "Retry" })).toBeTruthy();
  });

  it("a load failure doesn't crash the page or leave an unhandled rejection", async () => {
    vi.mocked(getRecentProjects).mockRejectedValue({ isApiError: true, code: "network_error", message: "Can't reach the server. Check your internet connection." });
    const unhandled = vi.fn();
    window.addEventListener("unhandledrejection", unhandled);
    renderDashboard();
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("Can't reach the server"));
    expect(screen.getByRole("button", { name: /Build Now/ })).toBeTruthy();
    window.removeEventListener("unhandledrejection", unhandled);
    expect(unhandled).not.toHaveBeenCalled();
  });
});

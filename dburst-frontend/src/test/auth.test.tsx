import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { AxiosError } from "axios";
import type { AxiosResponse, InternalAxiosRequestConfig } from "axios";

import authReducer from "@/core/redux/authSlice";
import type { AuthState } from "@/core/redux/authSlice";
import { store } from "@/core/redux/store";
import { setCredentials } from "@/core/redux/authSlice";
import ProtectedRoute from "@/core/routes/ProtectedRoute";
import PublicRoute from "@/core/routes/PublicRoutes";
import { safeRedirect } from "@/core/auth/safeRedirect";
import api from "@/core/api/axiosConfig";

const USER = { id: "u1", email: "a@b.c", name: "A", role: "user" };

type TestAuth = Pick<AuthState, "user" | "status"> & Partial<AuthState>;

function makeStore(auth: TestAuth) {
  return configureStore({
    reducer: { auth: authReducer },
    preloadedState: { auth: { logoutPending: false, ...auth } },
  });
}

function ShowLocation() {
  const location = useLocation();
  return <div data-testid="location">{location.pathname + location.search}</div>;
}

function renderRoutes(auth: TestAuth, initialPath: string) {
  return render(
    <Provider store={makeStore(auth)}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard/*" element={<div>secret dashboard</div>} />
          </Route>
          <Route element={<PublicRoute />}>
            <Route path="/login" element={<ShowLocation />} />
          </Route>
          <Route path="*" element={<ShowLocation />} />
        </Routes>
      </MemoryRouter>
    </Provider>
  );
}

describe("safeRedirect", () => {
  it.each([
    ["/dashboard/all-projects", "/dashboard/all-projects"],
    ["/dashboard/ui-generator/?projectId=1", "/dashboard/ui-generator/?projectId=1"],
  ])("keeps internal path %s", (input, expected) => {
    expect(safeRedirect(input)).toBe(expected);
  });

  it.each([
    null,
    "",
    "https://evil.com",
    "//evil.com",
    "/\\evil.com",
    "javascript:alert(1)",
    "/\tevil",
    "dashboard",
    "/login",
    "/auth/google/callback",
  ])("rejects %s", (input) => {
    expect(safeRedirect(input)).toBe("/dashboard");
  });
});

describe("ProtectedRoute", () => {
  it("redirects logged-out users to /login with next", () => {
    renderRoutes({ user: null, status: "unauthenticated" }, "/dashboard/all-projects?page=2");
    expect(screen.queryByText("secret dashboard")).toBeNull();
    expect(screen.getByTestId("location").textContent).toBe(
      `/login?next=${encodeURIComponent("/dashboard/all-projects?page=2")}`
    );
  });

  it("shows nothing protected while the session check is pending", () => {
    renderRoutes({ user: null, status: "loading" }, "/dashboard");
    expect(screen.queryByText("secret dashboard")).toBeNull();
    expect(screen.queryByTestId("location")).toBeNull();
  });

  it("renders protected content for an authenticated user", () => {
    renderRoutes({ user: USER, status: "authenticated" }, "/dashboard");
    expect(screen.getByText("secret dashboard")).toBeTruthy();
  });
});

describe("PublicRoute", () => {
  it("sends authenticated users from /login to the dashboard", () => {
    renderRoutes({ user: USER, status: "authenticated" }, "/login");
    expect(screen.getByText("secret dashboard")).toBeTruthy();
  });

  it("ignores an external next target", () => {
    renderRoutes({ user: USER, status: "authenticated" }, "/login?next=%2F%2Fevil.com");
    expect(screen.getByText("secret dashboard")).toBeTruthy();
  });

  it("shows the login page to logged-out users", () => {
    renderRoutes({ user: null, status: "unauthenticated" }, "/login");
    expect(screen.getByTestId("location").textContent).toBe("/login");
  });
});

// ---------------------------------------------------------------------------
// axios: CSRF header + single-flight refresh
// ---------------------------------------------------------------------------

type Handler = (config: InternalAxiosRequestConfig) => { status: number; data?: unknown };

function respond(config: InternalAxiosRequestConfig, status: number, data: unknown = {}) {
  const response = { data, status, statusText: String(status), headers: {}, config } as AxiosResponse;
  if (status >= 400) {
    return Promise.reject(new AxiosError(`HTTP ${status}`, "ERR_BAD_REQUEST", config, null, response));
  }
  return Promise.resolve(response);
}

describe("api interceptors", () => {
  const originalAdapter = api.defaults.adapter;
  let calls: InternalAxiosRequestConfig[];

  function useHandler(handler: Handler) {
    api.defaults.adapter = async (config) => {
      calls.push(config);
      // let parallel requests interleave like real network calls
      await new Promise((r) => setTimeout(r, 5));
      const { status, data } = handler(config);
      return respond(config, status, data);
    };
  }

  const refreshCalls = () => calls.filter((c) => c.url === "users/auth/refresh/").length;

  beforeEach(() => {
    calls = [];
    document.cookie = "csrftoken=test-csrf-token; path=/";
    store.dispatch(setCredentials({ user: USER }));
  });

  afterEach(() => {
    api.defaults.adapter = originalAdapter;
    vi.restoreAllMocks();
  });

  it("adds X-CSRFToken on unsafe methods only", async () => {
    useHandler(() => ({ status: 200 }));
    await api.get("projects/recent-projects/");
    await api.post("projects/create-project/", { title: "x" });

    expect(calls[0].headers.get("X-CSRFToken")).toBeUndefined();
    expect(calls[1].headers.get("X-CSRFToken")).toBe("test-csrf-token");
  });

  it("queues parallel 401s behind a single refresh", async () => {
    let refreshed = false;
    useHandler((config) => {
      if (config.url === "users/auth/refresh/") {
        refreshed = true;
        return { status: 200 };
      }
      return refreshed ? { status: 200, data: { ok: config.url } } : { status: 401 };
    });

    const results = await Promise.all([
      api.get("a/"),
      api.get("b/"),
      api.get("c/"),
    ]);

    expect(refreshCalls()).toBe(1);
    expect(results.map((r) => r.data.ok)).toEqual(["a/", "b/", "c/"]);
    expect(store.getState().auth.status).toBe("authenticated");
  });

  it("clears the session when refresh fails, without retrying refresh", async () => {
    useHandler(() => ({ status: 401 }));

    await expect(api.get("projects/recent-projects/")).rejects.toBeInstanceOf(AxiosError);

    expect(refreshCalls()).toBe(1);
    expect(store.getState().auth.status).toBe("unauthenticated");
    expect(store.getState().auth.user).toBeNull();
  });

  it("gives up after one retry if the refreshed request still 401s", async () => {
    useHandler((config) => (config.url === "users/auth/refresh/" ? { status: 200 } : { status: 401 }));

    await expect(api.get("x/")).rejects.toBeInstanceOf(AxiosError);

    expect(refreshCalls()).toBe(1);
    expect(calls.filter((c) => c.url === "x/").length).toBe(2);
    expect(store.getState().auth.status).toBe("unauthenticated");
  });

  it("never stores auth data in web storage", async () => {
    useHandler(() => ({ status: 200 }));
    await api.get("users/profile/");
    expect(Object.keys(localStorage)).toEqual([]);
    expect(Object.keys(sessionStorage)).toEqual([]);
  });
});

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Provider, useSelector } from "react-redux";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import { store } from "@/core/redux/store";
import type { RootState } from "@/core/redux/store";
import { setCredentials, setLogoutPending } from "@/core/redux/authSlice";
import LogoutOverlay from "@/core/auth/LogoutOverlay";
import ProtectedRoute from "@/core/routes/ProtectedRoute";
import ProfileModal from "@/features/dashboard/components/ProfileModal";
import UserProfile from "@/features/dashboard/components/UserProfile";
import { useLogout } from "@/features/index/api/logoutApi";
import { logoutUser, updateProfile } from "@/features/index/api/indexApi";
import { validateAvatarUrl, validateName } from "@/features/dashboard/lib/profileValidation";
import Avatar from "@/shared/components/Avatar";
import { toast } from "@/shared/hooks/useToast";

vi.mock("@/features/index/api/indexApi", () => ({
  logoutUser: vi.fn(),
  updateProfile: vi.fn(),
}));

const USER = { id: "u1", email: "ada@example.com", name: "Ada", avatar_url: undefined, role: "user" };

beforeEach(() => {
  store.dispatch(setLogoutPending(false));
  store.dispatch(setCredentials({ user: { ...USER } }));
  vi.mocked(logoutUser).mockReset();
  vi.mocked(updateProfile).mockReset();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// Validation (mirrors the backend serializer)
// ---------------------------------------------------------------------------

describe("profile validation", () => {
  it("requires a non-blank name within 120 chars, no < >", () => {
    expect(validateName("Ada")).toBeNull();
    expect(validateName("   ")).toMatch(/required/);
    expect(validateName("\u0007\n")).toMatch(/required/);
    expect(validateName("a".repeat(121))).toMatch(/120/);
    expect(validateName("a".repeat(120))).toBeNull();
    expect(validateName("<b>x</b>")).toMatch(/</);
  });

  it.each(["", "  ", "https://cdn.example.com/a.png", "http://example.com/a.png?x=1"])(
    "accepts %j",
    (url) => expect(validateAvatarUrl(url)).toBeNull()
  );

  it.each([
    "javascript:alert(1)",
    "data:image/png;base64,AAAA",
    "file:///etc/passwd",
    "ftp://example.com/a.png",
    "/relative.png",
    "example.com/a.png",
    "https://user:pass@example.com/a.png",
    "http://localhost/a.png",
    "http://127.0.0.1/a.png",
    "http://192.168.0.1/a.png",
    "http://[::1]/a.png",
    "https://example.com/a b.png",
    "https://example.com/" + "a".repeat(2048),
  ])("rejects %s", (url) => expect(validateAvatarUrl(url)).not.toBeNull());
});

// ---------------------------------------------------------------------------
// ProfileModal
// ---------------------------------------------------------------------------

function renderModal(onClose = vi.fn()) {
  render(
    <Provider store={store}>
      <ProfileModal isOpen onClose={onClose} />
    </Provider>
  );
  return {
    onClose,
    name: screen.getByLabelText("Name") as HTMLInputElement,
    url: screen.getByLabelText("Avatar image URL") as HTMLInputElement,
    save: screen.getByRole("button", { name: "Save" }) as HTMLButtonElement,
  };
}

describe("ProfileModal", () => {
  it("shows read-only email, focuses name, and disables Save until something changes", () => {
    const { name, save } = renderModal();
    expect(screen.getByRole("dialog")).toBeTruthy();
    expect((screen.getByLabelText("Email") as HTMLInputElement).readOnly).toBe(true);
    expect((screen.getByLabelText("Email") as HTMLInputElement).value).toBe(USER.email);
    expect(document.activeElement).toBe(name);
    expect(save.disabled).toBe(true);

    fireEvent.change(name, { target: { value: "Ada Lovelace" } });
    expect(save.disabled).toBe(false);
  });

  it("blocks a non-http(s) avatar URL with an inline error", () => {
    const { url, save } = renderModal();
    fireEvent.change(url, { target: { value: "javascript:alert(1)" } });
    expect(screen.getByText("URL must start with http:// or https://.")).toBeTruthy();
    expect(url.getAttribute("aria-invalid")).toBe("true");
    expect(save.disabled).toBe(true);
  });

  it("requires a name", () => {
    const { name, save } = renderModal();
    fireEvent.change(name, { target: { value: "   " } });
    expect(screen.getByText("Name is required.")).toBeTruthy();
    expect(save.disabled).toBe(true);
  });

  it("submits only changed fields, updates the store, toasts and closes", async () => {
    const updated = { ...USER, name: "Ada Lovelace", avatar_url: "https://cdn.example.com/ada.png" };
    let resolve!: (v: unknown) => void;
    vi.mocked(updateProfile).mockReturnValue(new Promise((r) => (resolve = r)));
    const success = vi.spyOn(toast, "success");

    const { name, url, save, onClose } = renderModal();
    fireEvent.change(name, { target: { value: "  Ada Lovelace " } });
    fireEvent.change(url, { target: { value: "https://cdn.example.com/ada.png" } });
    fireEvent.click(save);

    // Saving state: button disabled with a spinner label.
    expect(screen.getByRole("button", { name: /Saving/ })).toHaveProperty("disabled", true);
    expect(updateProfile).toHaveBeenCalledWith({
      name: "Ada Lovelace",
      avatar_url: "https://cdn.example.com/ada.png",
    });

    await act(async () => resolve({ user: updated }));

    expect(store.getState().auth.user).toEqual(updated);
    expect(success).toHaveBeenCalledWith("Profile updated");
    expect(onClose).toHaveBeenCalled();
  });

  it("sends null to clear the avatar", async () => {
    store.dispatch(setCredentials({ user: { ...USER, avatar_url: "https://cdn.example.com/a.png" } }));
    vi.mocked(updateProfile).mockResolvedValue({ user: USER });
    const { url, save } = renderModal();
    fireEvent.change(url, { target: { value: "" } });
    await act(async () => fireEvent.click(save));
    expect(updateProfile).toHaveBeenCalledWith({ avatar_url: null });
  });

  it("shows backend field errors inline and stays open", async () => {
    vi.mocked(updateProfile).mockRejectedValue({
      message: "Bad Request",
      status: 400,
      details: { avatar_url: ["URL must point to a public host."] },
    });
    const { url, save, onClose } = renderModal();
    fireEvent.change(url, { target: { value: "https://internal.example.com/a.png" } });
    await act(async () => fireEvent.click(save));

    expect(screen.getByText("URL must point to a public host.")).toBeTruthy();
    expect(onClose).not.toHaveBeenCalled();
    expect(store.getState().auth.user?.avatar_url).toBeUndefined();
  });

  it("closes on Escape and on backdrop click, not on dialog click", () => {
    const { onClose } = renderModal();
    const dialog = screen.getByRole("dialog");
    fireEvent.click(dialog);
    expect(onClose).not.toHaveBeenCalled();
    fireEvent.keyDown(dialog, { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
    fireEvent.click(dialog.parentElement!);
    expect(onClose).toHaveBeenCalledTimes(2);
  });

  it("traps Tab focus inside the dialog", () => {
    renderModal();
    const dialog = screen.getByRole("dialog");
    const close = screen.getByRole("button", { name: "Close profile" });
    const cancel = screen.getByRole("button", { name: "Cancel" });
    // Save is disabled, so Cancel is the last focusable element.
    cancel.focus();
    fireEvent.keyDown(dialog, { key: "Tab" });
    expect(document.activeElement).toBe(close);
    fireEvent.keyDown(dialog, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(cancel);
  });
});

describe("ProfileModal portal + error gating", () => {
  it("renders into document.body, outside a filtered header", () => {
    render(
      <Provider store={store}>
        <header data-testid="hdr" className="backdrop-blur-md">
          <ProfileModal isOpen onClose={() => {}} />
        </header>
      </Provider>
    );
    const backdrop = screen.getByRole("dialog").parentElement!;
    expect(screen.getByTestId("hdr").contains(backdrop)).toBe(false);
    expect(backdrop.parentElement).toBe(document.body);
    expect(document.body.style.overflow).toBe("hidden");
  });

  it("restores scroll and focus on close", () => {
    const opener = document.createElement("button");
    document.body.appendChild(opener);
    opener.focus();
    const { unmount } = render(
      <Provider store={store}>
        <ProfileModal isOpen onClose={() => {}} />
      </Provider>
    );
    expect(document.activeElement).toBe(screen.getByLabelText("Name"));
    unmount();
    expect(document.body.style.overflow).toBe("");
    expect(document.activeElement).toBe(opener);
    opener.remove();
  });

  it("prefills the email local part for users without a name, with no error and Save enabled", () => {
    store.dispatch(setCredentials({ user: { ...USER, name: "" } }));
    const { name, save } = renderModal();
    expect(name.value).toBe("ada");
    expect(screen.queryByText("Name is required.")).toBeNull();
    expect(save.disabled).toBe(false);
  });

  it("hides the required error until the field is touched", () => {
    store.dispatch(setCredentials({ user: { ...USER, name: "", email: "@example.com" } }));
    const { name, save } = renderModal();
    expect(name.value).toBe("");
    expect(screen.queryByText("Name is required.")).toBeNull();
    expect(save.disabled).toBe(true);
    fireEvent.blur(name);
    expect(screen.getByText("Name is required.")).toBeTruthy();
  });

  it("shows errors after a submit attempt (Enter) without calling the API", () => {
    store.dispatch(setCredentials({ user: { ...USER, name: "", email: "@example.com" } }));
    const { name } = renderModal();
    fireEvent.submit(name.closest("form")!);
    expect(screen.getByText("Name is required.")).toBeTruthy();
    expect(updateProfile).not.toHaveBeenCalled();
  });

  it("hides the URL error until the URL field is touched", () => {
    store.dispatch(setCredentials({ user: { ...USER, avatar_url: "javascript:x" } }));
    const { url } = renderModal();
    expect(screen.queryByText("URL must start with http:// or https://.")).toBeNull();
    fireEvent.blur(url);
    expect(screen.getByText("URL must start with http:// or https://.")).toBeTruthy();
  });
});

describe("display name fallback", () => {
  it("UserProfile shows the email local part and its initial when name is empty", () => {
    render(
      <Provider store={store}>
        <MemoryRouter>
          <UserProfile user={{ ...USER, name: "", email: "grace.hopper@example.com" }} />
        </MemoryRouter>
      </Provider>
    );
    const trigger = screen.getByRole("button", { name: "Account menu for grace.hopper" });
    expect(trigger.textContent).toContain("grace.hopper");
    expect(trigger.textContent?.startsWith("G")).toBe(true);
  });
});

describe("Avatar", () => {
  it("uses no-referrer + lazy and falls back to the initial on error", () => {
    const { container } = render(<Avatar src="https://cdn.example.com/broken.png" name="ada" />);
    const img = container.querySelector("img")!;
    expect(img.getAttribute("referrerpolicy")).toBe("no-referrer");
    expect(img.getAttribute("loading")).toBe("lazy");
    fireEvent.error(img);
    expect(container.querySelector("img")).toBeNull();
    expect(container.textContent).toBe("A");
  });
});

// ---------------------------------------------------------------------------
// Logout overlay
// ---------------------------------------------------------------------------

function SecondLogoutButton() {
  const { logout, isLoggingOut } = useLogout();
  return (
    <button onClick={logout} disabled={isLoggingOut}>
      Mobile logout
    </button>
  );
}

function DashboardStub() {
  const user = useSelector((s: RootState) => s.auth.user);
  return (
    <>
      <UserProfile user={user} onOpenProfile={() => {}} />
      <SecondLogoutButton />
    </>
  );
}

function renderApp() {
  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={["/dashboard"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<DashboardStub />} />
          </Route>
          <Route path="/" element={<div>home page</div>} />
          <Route path="/login" element={<div>login page</div>} />
        </Routes>
        <LogoutOverlay />
      </MemoryRouter>
    </Provider>
  );
}

function clickDropdownLogout() {
  fireEvent.click(screen.getByRole("button", { name: /Account menu/ }));
  fireEvent.click(screen.getByRole("menuitem", { name: "Logout" }));
}

describe("logout overlay", () => {
  it("blocks the screen and disables every logout button until we land on /", async () => {
    let resolve!: (v: unknown) => void;
    vi.mocked(logoutUser).mockReturnValue(new Promise((r) => (resolve = r)));

    renderApp();
    clickDropdownLogout();

    const overlay = screen.getByRole("status");
    expect(overlay.getAttribute("aria-live")).toBe("polite");
    expect(overlay.textContent).toContain("Logging out...");
    expect((screen.getByRole("button", { name: "Mobile logout" }) as HTMLButtonElement).disabled).toBe(true);

    // Reopen the dropdown: its Logout item is disabled too.
    fireEvent.click(screen.getByRole("button", { name: /Account menu/ }));
    const item = screen.getByRole("menuitem", { name: /Logging out/ }) as HTMLButtonElement;
    expect(item.disabled).toBe(true);

    // A second click (bypassing the disabled attribute) still doesn't double-fire.
    fireEvent.click(screen.getByRole("button", { name: "Mobile logout" }));
    expect(logoutUser).toHaveBeenCalledTimes(1);

    await act(async () => resolve({ message: "Logout successful" }));

    await waitFor(() => expect(screen.getByText("home page")).toBeTruthy());
    expect(screen.queryByRole("status")).toBeNull();
    expect(screen.queryByText("login page")).toBeNull();
    expect(store.getState().auth.status).toBe("unauthenticated");
    expect(store.getState().auth.logoutPending).toBe(false);
  });

  it("still logs out client-side when the request fails", async () => {
    vi.mocked(logoutUser).mockRejectedValue({ message: "Network Error" });
    const error = vi.spyOn(toast, "error");
    vi.spyOn(console, "error").mockImplementation(() => {});

    renderApp();
    fireEvent.click(screen.getByRole("button", { name: /Account menu/ }));
    await act(async () => fireEvent.click(screen.getByRole("menuitem", { name: "Logout" })));

    await waitFor(() => expect(screen.getByText("home page")).toBeTruthy());
    expect(error).toHaveBeenCalled();
    expect(store.getState().auth.user).toBeNull();
    expect(screen.queryByRole("status")).toBeNull();
  });
});

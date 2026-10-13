import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { store } from "@/core/redux/store";
import { setCredentials } from "@/core/redux/authSlice";
import UIGenerator from "@/features/dashboard/pages/UIGenerator";
import { getProjectDetail, generateUI, refineUI } from "@/features/dashboard/api/dashboardApi";
import { patchApi } from "@/features/dashboard/api/patchApi";
import { setItem } from "@/shared/utils/storageManager";

// The live preview boots a WebContainer; irrelevant here.
vi.mock("@/core/webcontainer", () => ({ WebContainerPreview: () => <div data-testid="live-preview" /> }));
vi.mock("@/core/webcontainer/webcontainerAuth", () => ({}));
vi.mock("@/features/dashboard/api/dashboardApi", () => ({
  getProjectDetail: vi.fn(),
  generateUI: vi.fn(),
  refineUI: vi.fn(),
  getChatHistory: vi.fn(),
}));
vi.mock("@/features/dashboard/api/patchApi", () => ({
  patchApi: {
    applyPatch: vi.fn(),
    getPatchHistory: vi.fn(),
    getVersion: vi.fn(),
    getSchema: vi.fn(),
    undo: vi.fn(),
    redo: vi.fn(),
    clearCache: vi.fn(),
  },
}));

const SCHEMA = {
  type: "Root",
  children: [
    { type: "Text", props: { tag: "h1", className: "text-4xl" }, content: "Hello world" },
    { type: "Grid", props: { className: "grid grid-cols-3 gap-6" }, children: [] },
  ],
};

const PROJECT_DETAIL = {
  project: { id: "p1", title: "Demo" },
  latest_generation: { id: "g1", schema: SCHEMA, code: "export default function X() {}", token_usage: 12 },
};

function renderAt(path: string) {
  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/dashboard/ui-generator" element={<UIGenerator />} />
        </Routes>
      </MemoryRouter>
    </Provider>
  );
}

const editButton = () => screen.getByRole("button", { name: /^Edit$|^Editing$/ });

beforeEach(() => {
  store.dispatch(setCredentials({ user: { id: "u1", email: "a@b.co", name: "A", role: "user" } }));
  vi.mocked(getProjectDetail).mockReset().mockResolvedValue(PROJECT_DETAIL);
  vi.mocked(patchApi.applyPatch).mockReset();
  vi.mocked(patchApi.getPatchHistory).mockReset().mockResolvedValue({ generation_id: "g1", total_patches: 0, limit: 20, offset: 0, patches: [] } as never);
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("UIGenerator edit controls", () => {
  it("shows enabled edit controls when the project has a generation id", async () => {
    renderAt("/dashboard/ui-generator?projectId=p1");
    await waitFor(() => expect(editButton()).toBeTruthy());
    expect(getProjectDetail).toHaveBeenCalledWith("p1");
    expect((editButton() as HTMLButtonElement).disabled).toBe(false);
    // Rendered into the tab row's portal target.
    expect(document.getElementById("edit-controls-container")!.contains(editButton())).toBe(true);
  });

  it("keeps the tab row below the fixed header at every breakpoint (regression)", () => {
    // The 64px fixed header is cleared by pt-16; a responsive padding
    // shorthand (sm:p-3) would override it from 640px up and hide the row.
    const source = readFileSync(resolve(__dirname, "../features/dashboard/pages/UIGenerator.tsx"), "utf8");
    const layout = source.match(/className="(flex flex-1 overflow-hidden[^"]*)"/)![1].split(/\s+/);
    expect(layout).toContain("pt-16");
    expect(layout.filter((c) => /^(sm|md|lg|xl|2xl):(p|py|pt)-/.test(c))).toEqual([]);
  });

  it("shows controls disabled with a reason when there is no generation id", async () => {
    setItem("lastGeneratedProject", { schema: SCHEMA, code: "x", meta: { usage: { total_tokens: 0 } } });
    renderAt("/dashboard/ui-generator");
    const controls = await screen.findByTestId("edit-controls");
    expect(controls.getAttribute("title")).toMatch(/Editing is unavailable/);
    const edit = editButton() as HTMLButtonElement;
    expect(edit.disabled).toBe(true);
    expect(edit.title).toMatch(/Editing is unavailable/);
    expect((screen.getByRole("button", { name: /Saved/ }) as HTMLButtonElement).disabled).toBe(true);
    expect(screen.getByTestId("live-preview")).toBeTruthy();
  });

  it("resolves a missing generation id from the cached project", async () => {
    setItem("lastGeneratedProject", { project_id: "p1", schema: SCHEMA, code: "x", meta: { usage: { total_tokens: 0 } } });
    renderAt("/dashboard/ui-generator");
    await waitFor(() => expect((editButton() as HTMLButtonElement).disabled).toBe(false));
    expect(getProjectDetail).toHaveBeenCalledWith("p1");
  });

  it("toggling Edit renders the schema in the editable renderer", async () => {
    renderAt("/dashboard/ui-generator?projectId=p1");
    await waitFor(() => expect(editButton()).toBeTruthy());
    expect(screen.getByTestId("live-preview")).toBeTruthy();

    fireEvent.click(editButton());

    const canvas = await screen.findByTestId("edit-canvas");
    expect(screen.queryByTestId("live-preview")).toBeNull();
    expect(canvas.querySelector("main")).toBeTruthy();
    expect(canvas.querySelector('[role="textbox"][data-path="/children/0/content"]')).toBeTruthy();
    expect(editButton().getAttribute("aria-pressed")).toBe("true");
  });

  it("an inline text edit saves through the patch API only (no LLM calls)", async () => {
    vi.mocked(patchApi.applyPatch).mockResolvedValue({
      success: true, generation_id: "g1", patch_id: "pt1", patch_count: 1, snapshot_created: false,
      schema: { ...SCHEMA, children: [{ ...SCHEMA.children[0], content: "Hello edited" }, SCHEMA.children[1]] },
      code: "edited code",
    } as never);
    renderAt("/dashboard/ui-generator?projectId=p1");
    await waitFor(() => expect(editButton()).toBeTruthy());
    fireEvent.click(editButton());

    const text = (await screen.findByTestId("edit-canvas")).querySelector('[role="textbox"]') as HTMLElement;
    fireEvent.click(text);
    text.textContent = "Hello edited";
    fireEvent.input(text);
    fireEvent.blur(text);

    const save = await screen.findByRole("button", { name: /Save \*/ });
    await act(async () => fireEvent.click(save));

    expect(patchApi.applyPatch).toHaveBeenCalledTimes(1);
    const [generationId, patch] = vi.mocked(patchApi.applyPatch).mock.calls[0];
    expect(generationId).toBe("g1");
    expect(patch).toEqual([{ op: "replace", path: "/children/0/content", value: "Hello edited" }]);
    expect(generateUI).not.toHaveBeenCalled();
    expect(refineUI).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.getByRole("button", { name: /Saved/ })).toBeTruthy());
  });

  it("undo restores the previous text before saving", async () => {
    renderAt("/dashboard/ui-generator?projectId=p1");
    await waitFor(() => expect(editButton()).toBeTruthy());
    fireEvent.click(editButton());
    const text = (await screen.findByTestId("edit-canvas")).querySelector('[role="textbox"]') as HTMLElement;
    fireEvent.click(text);
    text.textContent = "Changed";
    fireEvent.blur(text);
    await screen.findByRole("button", { name: /Save \*/ });

    fireEvent.click(screen.getByTitle("Undo (Ctrl+Z)"));
    await waitFor(() => expect(screen.getByRole("button", { name: /Saved/ })).toBeTruthy());
    expect(patchApi.applyPatch).not.toHaveBeenCalled();
  });
});

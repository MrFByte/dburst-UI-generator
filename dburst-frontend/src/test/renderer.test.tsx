import { describe, it, expect, vi, afterEach } from "vitest";
import { cleanup, render, waitFor } from "@testing-library/react";
import { SchemaRenderer } from "@/features/dashboard/lib/renderer";
import type { SchemaNode } from "@/features/dashboard/types/renderType";
import { classStyle } from "@/features/dashboard/lib/classStyle";
import { safeHref, safeLinkTarget, safeUrl } from "@/shared/utils/safeUrl";

afterEach(cleanup);

// ---------------------------------------------------------------------------
// classStyle: inline fallback for classes the host Tailwind build can't emit
// ---------------------------------------------------------------------------

describe("classStyle", () => {
  it("maps arbitrary hex bg/text/border", () => {
    expect(classStyle("p-4 bg-[#0f172a] text-[#FBBF24] border border-[#334155cc]")).toEqual({
      backgroundColor: "#0f172a",
      color: "#FBBF24",
      borderColor: "#334155cc",
    });
  });

  it("builds a hex gradient with direction", () => {
    expect(classStyle("bg-gradient-to-r from-[#667eea] to-[#764ba2]")).toEqual({
      backgroundImage: "linear-gradient(to right, #667eea, #764ba2)",
    });
  });

  it("supports bg-linear-to-*, via, palette and keyword stops", () => {
    expect(classStyle("bg-linear-to-br from-blue-500 via-white to-[#fff]")).toEqual({
      backgroundImage: "linear-gradient(to bottom right, var(--color-blue-500), var(--color-white), #fff)",
    });
  });

  it("defaults missing stops to transparent", () => {
    expect(classStyle("bg-gradient-to-t from-rose-200")!.backgroundImage).toBe(
      "linear-gradient(to top, var(--color-rose-200), transparent)"
    );
  });

  it("keeps a background colour alongside a gradient", () => {
    expect(classStyle("bg-[#111] bg-gradient-to-b from-[#222] to-[#333]")).toEqual({
      backgroundColor: "#111",
      backgroundImage: "linear-gradient(to bottom, #222, #333)",
    });
  });

  it.each([
    "",
    "p-4 text-lg font-bold",
    "from-blue-500 to-purple-500",            // stops without a direction: no gradient
    "bg-gradient-to-r",                        // direction without stops
    "hover:bg-[#fff] md:text-[#000]",          // variants can't be inline
    "[&>*]:bg-[#fff]",
    "bg-[#ggg] text-[#12] bg-[url(x)] text-[12px] border-[3px]",
    "from-neutral-500 bg-gradient-to-r",       // hue not safelisted: no var guaranteed
    "from-blue-550 bg-gradient-to-r",
  ])("ignores %j", (cls) => {
    expect(classStyle(cls)).toBeUndefined();
  });

  it("handles the important modifier on either side", () => {
    expect(classStyle("!bg-[#abc] text-[#def]!")).toEqual({ backgroundColor: "#abc", color: "#def" });
  });

  it("never overrides explicit style props", () => {
    expect(classStyle("bg-[#000] text-[#111]", { color: "red", padding: 4 })).toEqual({
      backgroundColor: "#000",
      color: "red",
      padding: 4,
    });
    expect(classStyle("", "not-an-object")).toBeUndefined();
  });
});

// ---------------------------------------------------------------------------
// safeUrl
// ---------------------------------------------------------------------------

describe("safeUrl", () => {
  it.each([
    "https://example.com/a?b=1#c", "http://example.com", "HTTPS://EXAMPLE.COM", "mailto:a@b.co",
    "tel:+123", "#section", "/pricing", "./a.png", "../up.png",
  ])("allows %s", (url) => expect(safeUrl(url)).toBe(url));

  it.each([
    "javascript:alert(1)", "JavaScript:alert(1)", " javascript:alert(1)", "\u0000javascript:alert(1)",
    "java\tscript:alert(1)", "java\nscript:alert(1)", "\tjava\rscript:x", "data:text/html,<script>",
    "data:image/png;base64,AAAA", "vbscript:msgbox", "file:///etc/passwd", "//evil.com", "/\\evil.com",
    "evil.com", "about:blank", "", "   ", null, undefined, 42, {},
  ])("rejects %j", (url) => expect(safeUrl(url)).toBeNull());

  it("strips leading whitespace/control characters from allowed URLs", () => {
    expect(safeUrl("  \n https://a.com")).toBe("https://a.com");
  });

  it("safeHref falls back to #", () => {
    expect(safeHref("javascript:alert(1)")).toBe("#");
    expect(safeHref("/ok")).toBe("/ok");
  });

  it("safeLinkTarget allows only _blank/_self and forces noopener on _blank", () => {
    expect(safeLinkTarget("_blank")).toEqual({ target: "_blank", rel: "noopener noreferrer" });
    expect(safeLinkTarget("_self")).toEqual({ target: "_self" });
    expect(safeLinkTarget("_top")).toEqual({});
    expect(safeLinkTarget("evilframe")).toEqual({});
    expect(safeLinkTarget(undefined)).toEqual({});
  });
});

// ---------------------------------------------------------------------------
// SchemaRenderer integration
// ---------------------------------------------------------------------------

function renderSchema(schema: unknown, editMode = false) {
  return render(<SchemaRenderer schema={schema as SchemaNode} editMode={editMode} onTextEdit={() => {}} />);
}

describe("SchemaRenderer", () => {
  it("neutralises dangerous href/src and normalises target/rel", () => {
    const { container } = renderSchema({
      type: "Root",
      children: [
        { type: "Link", props: { href: "javascript:alert(1)", target: "_blank", rel: "opener" }, content: "a" },
        { type: "Link", props: { href: "https://ok.example", target: "_top" }, content: "b" },
        { type: "Image", props: { src: "data:image/svg+xml,<svg onload=alert(1)>", alt: "pic" } },
        { type: "Image", props: { src: "https://cdn.example.com/a.png", alt: "ok" } },
      ],
    });
    const [bad, good] = Array.from(container.querySelectorAll("a"));
    expect(bad.getAttribute("href")).toBe("#");
    expect(bad.getAttribute("target")).toBe("_blank");
    expect(bad.getAttribute("rel")).toBe("noopener noreferrer");
    expect(good.getAttribute("href")).toBe("https://ok.example");
    expect(good.hasAttribute("target")).toBe(false);

    const [badImg, goodImg] = Array.from(container.querySelectorAll("img"));
    expect(badImg.getAttribute("src")).toBe("https://placehold.co/800x600?text=pic");
    expect(goodImg.getAttribute("src")).toBe("https://cdn.example.com/a.png");
  });

  it("applies the inline colour fallback, including to editable text in edit mode", () => {
    const { container } = renderSchema({
      type: "Root",
      props: { className: "bg-[#0f172a]" },
      children: [
        { type: "Card", props: { className: "rounded-xl bg-gradient-to-br from-[#667eea] to-purple-600" }, children: [] },
        { type: "Text", props: { className: "text-[#fbbf24]", style: { fontWeight: 700 } }, content: "Hello" },
      ],
    }, true);
    const main = container.querySelector("main")!;
    expect(main.style.backgroundColor).toBe("rgb(15, 23, 42)");
    const card = main.querySelector("div.rounded-xl") as HTMLElement;
    expect(card.style.backgroundImage).toBe("linear-gradient(to bottom right, #667eea, var(--color-purple-600))");
    const text = container.querySelector('[role="textbox"]') as HTMLElement;
    expect(text.style.color).toBe("rgb(251, 191, 36)");
    expect(text.style.fontWeight).toBe("700");
  });

  it.each([
    [{ type: "Icon" }],
    [{ type: "Icon", props: { name: "DefinitelyNotARealIcon" } }],
    [{ type: "Icon", props: { name: 42 } }],
    [{ type: "Icon", props: { name: { evil: true } } }],
    [{ type: "Icon", props: { name: "../../etc" } }],
    [{ type: "Icon", content: "Mail" }],
  ])("Icon never throws for %j", async (node) => {
    const error = vi.spyOn(console, "error").mockImplementation(() => {});
    expect(() => renderSchema({ type: "Root", children: [node] })).not.toThrow();
    // Let DynamicIcon's async lookup settle; it must not surface an error.
    await waitFor(() => expect(document.querySelector("main")).toBeTruthy());
    expect(error.mock.calls.filter((c) => String(c[0]).includes("The above error occurred"))).toEqual([]);
    error.mockRestore();
  });

  it("does not crash on a non-string className", () => {
    expect(() => renderSchema({ type: "Card", props: { className: 42 } })).not.toThrow();
  });
});

describe("classStyle opacity colours", () => {
  it("maps palette, keyword and hex colours with /opacity to color-mix", () => {
    expect(classStyle("bg-blue-500/50 text-white/80 border-[#0f172a]/40")).toEqual({
      backgroundColor: "color-mix(in oklab, var(--color-blue-500) 50%, transparent)",
      color: "color-mix(in oklab, var(--color-white) 80%, transparent)",
      borderColor: "color-mix(in oklab, #0f172a 40%, transparent)",
    });
  });

  it("supports opacity on gradient stops", () => {
    expect(classStyle("bg-gradient-to-r from-rose-500/30 to-[#000]/0")!.backgroundImage).toBe(
      "linear-gradient(to right, color-mix(in oklab, var(--color-rose-500) 30%, transparent), color-mix(in oklab, #000 0%, transparent))"
    );
  });

  it.each(["bg-blue-500/150", "text-sm/6", "bg-neutral-500/50", "w-1/2", "bg-transparent/50", "bg-blue-500"])(
    "ignores %s", (cls) => expect(classStyle(cls)).toBeUndefined()
  );
});

describe("SchemaRenderer defaults match codegen", () => {
  it("Hero without a background gets the saturated gradient with white text", () => {
    const { container } = renderSchema({ type: "Hero", children: [] });
    const cls = container.firstElementChild!.className;
    expect(cls).toContain("from-indigo-500 via-purple-500 to-pink-500 text-white");
    expect(cls).not.toMatch(/from-blue-50|via-white/);
  });

  it("Hero with its own background keeps it and gains rounded/shadow/padding", () => {
    const { container } = renderSchema({ type: "Hero", props: { className: "bg-[#0369a1]" }, children: [] });
    expect(container.firstElementChild!.className).toBe("bg-[#0369a1] rounded-2xl shadow-lg p-12");
  });

  it("Root and Card no longer rewrite bg-white into a pale gradient", () => {
    const { container } = renderSchema({ type: "Root", props: { className: "bg-white" }, children: [
      { type: "Card", props: { className: "bg-white p-4" }, children: [] },
      { type: "Card", children: [] },
    ] });
    const html = container.innerHTML;
    expect(html).not.toMatch(/from-gray-50|from-white|via-white/);
    expect(container.querySelector("main")!.className).toContain("bg-white");
  });

  it("Timeline and TimelineItem use the coloured defaults", () => {
    const { container } = renderSchema({ type: "Timeline", children: [{ type: "TimelineItem", children: [] }] });
    const html = container.innerHTML;
    expect(html).toContain("border-indigo-400");
    expect(html).toContain("bg-indigo-50 border-l-4 border-pink-500");
    expect(html).toContain("bg-pink-500 rounded-full");
    expect(html).not.toMatch(/border-blue-200|from-white/);
  });
});

describe("edit-mode text layout", () => {
  it("block text (p/h1) is block-level in edit mode, spans stay inline", () => {
    const { container } = renderSchema({ type: "Root", children: [
      { type: "Text", props: { tag: "h1" }, content: "Title" },
      { type: "Text", content: "Body" },
      { type: "Text", props: { tag: "span" }, content: "inline" },
    ] }, true);
    const wrappers = Array.from(container.querySelectorAll('[role="textbox"]')).map((t) => t.parentElement!.className);
    expect(wrappers[0]).toContain("block");
    expect(wrappers[0]).not.toContain("inline-block");
    expect(wrappers[1]).not.toContain("inline-block");
    expect(wrappers[2]).toContain("inline-block");
  });
});

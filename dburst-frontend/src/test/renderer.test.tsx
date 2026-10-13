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

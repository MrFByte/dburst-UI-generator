import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render } from "@testing-library/react";
import { hasBackground, withDefaults } from "@/features/dashboard/lib/classDefaults";
import { SchemaRenderer } from "@/features/dashboard/lib/renderer";
import type { SchemaNode } from "@/features/dashboard/types/renderType";

afterEach(cleanup);

describe("hasBackground", () => {
  it("sees base-state colours and gradients", () => {
    for (const c of ["bg-red-500", "bg-[#0f172a]", "bg-gradient-to-br", "bg-linear-to-r", "bg-white/10", "p-4 !bg-black", "bg-slate-900!"]) {
      expect(hasBackground(c), c).toBe(true);
    }
  });

  it("ignores variants and non-colour bg-* utilities", () => {
    for (const c of ["", "p-4", "hover:bg-red-500", "dark:bg-slate-900", "md:bg-[#fff]", "[&>*]:bg-red-500", "bg-clip-text", "bg-cover bg-center", "bg-no-repeat"]) {
      expect(hasBackground(c), c).toBe(false);
    }
  });
});

describe("withDefaults", () => {
  it("never removes or edits what the schema wrote", () => {
    const own = "bg-[#fff7ed] text-[#be123c] rounded-2xl hover:bg-rose-100 p-8";
    expect(withDefaults(own, "bg-white text-gray-500 rounded-xl p-6 shadow-md").startsWith(own)).toBe(true);
  });

  it("drops a default that sets a property the schema already sets", () => {
    expect(withDefaults("text-blue-200", "text-sm text-gray-500")).toBe("text-blue-200 text-sm");
    expect(withDefaults("bg-[#0f172a]", "bg-white shadow-md")).toBe("bg-[#0f172a] shadow-md");
    expect(withDefaults("rounded-lg p-8 text-lg", "rounded-full p-6 text-xs")).toBe("rounded-lg p-8 text-lg");
    expect(withDefaults("border-[#334155]", "border-t border-gray-200")).toBe("border-[#334155] border-t");
  });

  it("keeps defaults for properties the schema leaves alone", () => {
    expect(withDefaults("mt-4", "text-sm text-gray-500")).toBe("mt-4 text-sm text-gray-500");
    expect(withDefaults("", "bg-white")).toBe("bg-white");
  });

  it("a variant on the schema does not suppress the base default", () => {
    expect(withDefaults("hover:bg-red-500", "bg-white")).toBe("hover:bg-red-500 bg-white");
  });
});

describe("renderer defaults do not fight the schema", () => {
  const classOf = (node: SchemaNode) => {
    const { container } = render(<SchemaRenderer schema={node} />);
    return (container.firstElementChild as HTMLElement).className;
  };

  it("CardDescription keeps the schema's text colour and size, adds neither default", () => {
    const cls = classOf({ type: "CardDescription", props: { className: "text-blue-200 text-lg" }, content: "x" } as SchemaNode);
    expect(cls).toContain("text-blue-200");
    expect(cls).not.toContain("text-gray-500");
    expect(cls).not.toContain("text-sm");
  });

  it("a Card whose only background is a hover variant still gets the white surface", () => {
    expect(classOf({ type: "Card", props: { className: "hover:bg-rose-100" }, children: [] } as SchemaNode)).toContain("bg-white");
  });

  it("a Card with a gradient or colour keeps it and gets no white", () => {
    for (const c of ["bg-[#fff7ed]", "bg-gradient-to-br from-[#667eea] to-[#764ba2]", "bg-rose-600"]) {
      const cls = classOf({ type: "Card", props: { className: c }, children: [] } as SchemaNode);
      expect(cls).toContain(c);
      expect(cls).not.toContain("bg-white");
    }
  });

  it("a Hero with only a hover background still gets the saturated default", () => {
    expect(classOf({ type: "Hero", props: { className: "hover:bg-rose-100" }, children: [] } as SchemaNode)).toContain("from-indigo-500");
  });

  it("Badge keeps the schema's radius and padding", () => {
    const cls = classOf({ type: "Badge", props: { className: "rounded-lg px-4 bg-[#fbbf24]" }, content: "x" } as SchemaNode);
    expect(cls).toContain("rounded-lg");
    expect(cls).not.toContain("rounded-full");
    expect(cls).not.toContain("px-2.5");
  });
});

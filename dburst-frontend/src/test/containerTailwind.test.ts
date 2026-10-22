// @vitest-environment node
import { describe, it, expect } from "vitest";
import { compile } from "@tailwindcss/node"; // transitive dep of @tailwindcss/vite, the plugin the container uses
import { buildReactViteProject } from "@/core/webcontainer/fileSystemUtils";

/**
 * The preview runs in a WebContainer: Vite + Tailwind v4 with the files from
 * buildReactViteProject. This compiles that project's own CSS with the same
 * Tailwind, to prove colours the model asks for come out, and that the stub
 * components' default classes can never override them.
 */

type Tree = Record<string, { file?: { contents: string }; directory?: Tree }>;
function readFile(tree: Tree, filePath: string): string {
  let current: Tree[string] | undefined = { directory: tree };
  for (const part of filePath.split("/")) current = current?.directory?.[part];
  if (!current?.file) throw new Error(`missing ${filePath}`);
  return current.file.contents;
}

const tree = buildReactViteProject("export default function A() { return null }") as Tree;
const indexCss = readFile(tree, "src/index.css");
const uiStubs = readFile(tree, "src/components/ui.tsx");

async function build(candidates: string[]): Promise<string> {
  const compiler = await compile(indexCss, { base: process.cwd(), onDependency() {} });
  return compiler.build(candidates);
}
const escapeSelector = (c: string) => c.replace(/([^a-zA-Z0-9_-])/g, "\\$1");
const layerOf = (css: string, selector: string) => {
  const at = css.indexOf(selector);
  expect(at, selector).toBeGreaterThan(-1);
  return [...css.slice(0, at).matchAll(/@layer (\w+) \{/g)].pop()?.[1];
};

describe("container Tailwind output", () => {
  const COLOUR_CLASSES = [
    "bg-gradient-to-br", "bg-gradient-to-r", "bg-linear-to-br", "from-indigo-500", "via-purple-500", "to-pink-500",
    "bg-[#0f172a]", "from-[#667eea]", "via-[#764ba2]", "to-[#ec4899]", "text-[#fbbf24]", "border-[#334155]", "ring-[#fbbf24]",
    "border-[#fbbf24]/40", "bg-blue-500/50", "text-white/80", "bg-[#0f172a]/90", "text-[#cbd5e1]/80",
    "hover:bg-[#1d4ed8]", "md:bg-rose-600", "dark:bg-[#020617]", "group-hover:bg-rose-100", "bg-white/10", "-mt-4",
    "[&>*]:p-2", "!bg-black", "bg-black!", "text-transparent", "bg-clip-text", "shadow-indigo-500/50", "bg-slate-950",
  ];

  it.each(COLOUR_CLASSES)("generates %s", async (cls) => {
    const base = await build([]);
    expect(await build([cls]), cls).not.toBe(base);
  });

  it("does NOT generate the removed v3 opacity helpers (so the prompt must not ask for them)", async () => {
    const base = await build([]);
    for (const cls of ["bg-opacity-50", "text-opacity-80", "border-opacity-50"]) {
      expect(await build([cls]), cls).toBe(base);
    }
  });

  it("emits gradient stops for from-[#hex] with the real colour", async () => {
    const css = await build(["bg-gradient-to-br", "from-[#667eea]", "to-[#ec4899]"]);
    expect(css).toMatch(/--tw-gradient-from:\s*#667eea/);
    expect(css).toMatch(/--tw-gradient-to:\s*#ec4899/);
  });
});

describe("stub components never override the schema's classes", () => {
  it("puts every stub default in the components layer and the schema's utilities after it", async () => {
    const css = await build(["ui-card", "ui-button", "ui-input", "ui-badge", "bg-[#fff7ed]", "bg-slate-900", "rounded-2xl", "text-lg", "border-[#334155]", "shadow-lg"]);
    for (const stub of ["ui-card", "ui-button", "ui-input", "ui-badge"]) expect(layerOf(css, `.${stub} {`), stub).toBe("components");
    for (const cls of ["bg-[#fff7ed]", "bg-slate-900", "rounded-2xl", "text-lg", "border-[#334155]", "shadow-lg"]) {
      expect(layerOf(css, `.${escapeSelector(cls)}`), cls).toBe("utilities");
    }
    // Layer precedence is fixed by this declaration (not by where the blocks sit in the file).
    expect(css).toMatch(/@layer theme, base, components, utilities;/);
  });

  it("no stub component hard-codes colour classes in its className string", () => {
    // Defaults come from the ui-* classes; a literal `bg-white ` in the JSX would be a utility again.
    const jsxClassNames = [...uiStubs.matchAll(/className=\{?[`'"]([^`'"]*)[`'"]/g)].map((m) => m[1]);
    for (const cls of jsxClassNames) {
      const colourful = cls.split(/\s+/).filter((t) => /^(bg|text|border)-(?!transparent)[a-z]+-\d{2,3}$|^bg-white$/.test(t));
      // The Progress bar fill and Switch thumb are internal elements, not user-styled.
      expect(colourful.filter((t) => !["bg-blue-600", "bg-white"].includes(t)), cls).toEqual([]);
    }
  });

  it("exports every component the code generator imports from @/components/ui", () => {
    // Mirrors ReactCodeGenerator.COMPONENT_IMPORTS (backend/generation/codegen.py).
    for (const name of ["Button", "Input", "Label", "Select", "Badge", "Card", "CardHeader", "CardContent", "CardFooter",
      "CardTitle", "CardDescription", "Separator", "Table", "TableHeader", "TableBody", "TableRow", "TableCell", "TableHead"]) {
      expect(uiStubs, name).toMatch(new RegExp(`export function ${name}\\(`));
    }
  });
});

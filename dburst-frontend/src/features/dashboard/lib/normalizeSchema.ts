export function normalizeSchema(node) {
  if (!node) return node;

  // Ensure text contrast
  if (node.type === "Text" && !node.class?.includes("text-")) {
    node.class = (node.class || "") + " text-gray-900";
  }

  // Ensure cards have column layout
  if (node.type === "Card" && !node.class.includes("flex")) {
    node.class += " flex flex-col gap-3";
  }

  // Fix white-on-white issues
  if (node.class?.includes("bg-white") && !node.class.includes("text-gray")) {
    node.class += " text-gray-900";
  }

  // Recurse children
  if (node.children) {
    node.children = node.children.map(normalizeSchema);
  }

  return node;
}

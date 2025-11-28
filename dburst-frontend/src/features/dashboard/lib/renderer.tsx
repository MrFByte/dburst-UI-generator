import React from "react";

type Node = {
  type: string;
  class?: string;
  props?: any;
  content?: string;
  children?: Node[];
};

export function RenderNode(node: Node) {
  if (!node) return null;

  const { type, class: className, props, children, content } = node;

  switch (type) {
    case "Container":
      return (
        <div className={className}>
          {children?.map((child, i) => (
            <RenderNode key={i} {...child} />
          ))}
        </div>
      );

    case "Text":
      return <p className={className}>{content}</p>;

    case "Button":
      return <button className={className}>{content}</button>;

    case "Input":
      return (
        <input
          className={className}
          placeholder={props?.placeholder || ""}
        />
      );

    case "Card":
      return (
        <div className={className}>
          {children?.map((child, i) => (
            <RenderNode key={i} {...child} />
          ))}
        </div>
      );

    case "Grid":
      return (
        <div className={`grid grid-cols-${props?.cols || 2} ${className || ""}`}>
          {children?.map((child, i) => (
            <RenderNode key={i} {...child} />
          ))}
        </div>
      );

    default:
      return <div className="text-red-400">Unknown type: {type}</div>;
  }
}

export function SchemaRenderer({ schema }: { schema: Node }) {
  return <RenderNode {...schema} />;
}

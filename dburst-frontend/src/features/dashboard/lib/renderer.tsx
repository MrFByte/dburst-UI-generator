import React from 'react';
import type { SchemaNode } from '../types/renderType';


export function SchemaRenderer({ schema }: { schema: SchemaNode }) {
  if (!schema) return null;
  return <RenderNode node={schema} />;
}

function RenderNode({ node }: { node: SchemaNode }): React.ReactNode | null {
  if (!node) return null;

  const { type, props = {}, children = [], content = '', src } = node;
  const className = props.className || '';

  switch (type) {
    case 'Root':
      return (
        <div className={className}>
          {children.map((child, i) => (
            <RenderNode key={i} node={child} />
          ))}
        </div>
      );

    case 'Section':
      return (
        <section className={className}>
          {children.map((child, i) => (
            <RenderNode key={i} node={child} />
          ))}
        </section>
      );

    case 'Grid':
      return (
        <div className={className}>
          {children.map((child, i) => (
            <RenderNode key={i} node={child} />
          ))}
        </div>
      );

    case 'Card':
      return (
        <div className={className}>
          {children.map((child, i) => (
            <RenderNode key={i} node={child} />
          ))}
        </div>
      );

    case 'Flex':
      return (
        <div className={className}>
          {children.map((child, i) => (
            <RenderNode key={i} node={child} />
          ))}
        </div>
      );

    case 'Container':
      return (
        <div className={className}>
          {children.map((child, i) => (
            <RenderNode key={i} node={child} />
          ))}
        </div>
      );

    case 'Text':
      return <p className={className}>{content}</p>;

    case 'Button':
      return (
        <button
          className={className}
          onClick={props.onClick}
          type={props.type || 'button'}
        >
          {children.length > 0
            ? children.map((child, i) => <RenderNode key={i} node={child} />)
            : content}
        </button>
      );

    case 'Input':
      return (
        <input
          className={className}
          type={props.type || 'text'}
          placeholder={props.placeholder}
          defaultValue={props.defaultValue}
          disabled={props.disabled}
        />
      );

    case 'Textarea':
      return (
        <textarea
          className={className}
          placeholder={props.placeholder}
          defaultValue={props.defaultValue}
          disabled={props.disabled}
          rows={props.rows || 4}
        />
      );

    case 'Image':
      return (
        <img
          className={className}
          src={src || props.src || 'https://cdn.pixabay.com/photo/2017/11/10/04/47/image-2935360_1280.png'}
          alt={props.alt || 'Image'}
          loading={props.loading || 'lazy'}
        />
      );

    case 'Badge':
      return <span className={className}>{content}</span>;

    case 'Icon':
      return <span className={className}>{content}</span>;

    case 'Separator':
      return <hr className={className} />;

    case 'Skeleton':
      return <div className={`${className} animate-pulse`} />;

    default:
      return (
        <div className={className}>
          {children.length > 0
            ? children.map((child, i) => <RenderNode key={i} node={child} />)
            : content || `Unknown type: ${type}`}
        </div>
      );
  }
}
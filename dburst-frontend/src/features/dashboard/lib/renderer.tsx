import React from 'react';
import type { SchemaNode } from '../types/renderType';

// Type guard to ensure we only pass SchemaNode objects to RenderNode
function isSchemaNode(child: SchemaNode | string): child is SchemaNode {
  return typeof child !== 'string';
}

export function SchemaRenderer({ schema }: { schema: SchemaNode }) {
  if (!schema) return null;
  return <RenderNode node={schema} />;
}

function RenderNode({ node }: { node: SchemaNode }): React.ReactNode | null {
  if (!node) return null;

  const { type, props = {}, children = [], content = '', src } = node;
  const className = props.className || '';
  const tag = props.tag || '';

  // Function to render children, filtering out strings for container elements
  const renderChildren = () => (
    children
      .filter(isSchemaNode) 
      .map((child, i) => (
        <RenderNode key={i} node={child} />
      ))
  );

  // Function to render content/children for text-holding elements
  const renderTextContent = () => (
    children.length > 0
      ? children.map((child, i) => {
          // This handles both SchemaNode (recursive call) and string (direct render)
          return isSchemaNode(child) ? <RenderNode key={i} node={child} /> : child;
        })
      : content
  );

  switch (type) {
    case 'Root':
      return (
        <main className={`${className} h-fit w-full`}>
          {renderChildren()}
        </main>
      );

    case 'Section':
      return (
        <section className={className}>
          {renderChildren()}
        </section>
      );

    case 'Grid':
      return (
        <div className={className}>
          {renderChildren()}
        </div>
      );

    case 'Card':
      return (
        <div className={`${className} bg-white rounded-lg border shadow-sm`}>
          {renderChildren()}
        </div>
      );

    case 'CardHeader':
      return (
        <div className={`${className} flex flex-col space-y-1.5 p-6`}>
          {renderChildren()}
        </div>
      );

    case 'CardTitle':
      return (
        <h3 className={`${className} text-2xl font-semibold leading-none tracking-tight`}>
          {renderTextContent()}
        </h3>
      );

    case 'CardDescription':
      return (
        <p className={`${className} text-sm text-gray-500`}>
          {renderTextContent()}
        </p>
      );

    case 'CardContent':
      return (
        <div className={`${className} p-6 pt-0`}>
          {renderChildren()}
        </div>
      );

    case 'CardFooter':
      return (
        <div className={`${className} flex items-center p-6 pt-0`}>
          {renderChildren()}
        </div>
      );

    case 'Flex':
      // CRITICAL FIX: Ensure Flex always has flex class
      const flexClass = className.includes('flex') ? className : `flex ${className}`;
      return (
        <div className={flexClass}>
          {renderChildren()}
        </div>
      );

    case 'Container':
      return (
        <div className={className}>
          {renderChildren()}
        </div>
      );

    case 'Text': {
      const TextTag: React.ElementType = props.tag || 'p';
      
      return (
        <TextTag className={className}>
          {renderTextContent()}
        </TextTag>
      );
    }

    case 'Button':
      return (
        <button
          className={className}
          onClick={props.onClick}
          // Note: The fix for type safety here is still dependent on SchemaProps definition
          type={props.type as 'button' | 'submit' | 'reset' || 'button'}
          disabled={props.disabled}
        >
          {renderTextContent()}
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
          name={props.name}
          id={props.id}
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
          name={props.name}
          id={props.id}
        />
      );

    case 'Label':
      return (
        <label className={className} htmlFor={props.htmlFor}>
          {renderTextContent()}
        </label>
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
      return (
        <span className={`${className} inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold`}>
          {content}
        </span>
      );

    case 'Icon':
      return <span className={className}>{content}</span>;

    case 'Separator':
      return <hr className={`${className} border-t border-gray-200`} />;

    case 'Skeleton':
      return <div className={`${className} animate-pulse bg-gray-200 rounded`} />;

    case 'Link':
    case 'Link/A':
      return (
        <a
          className={className}
          href={props.href || '#'}
          target={props.target}
          rel={props.rel}
        >
          {renderTextContent()}
        </a>
      );

    case 'List':
      return (
        <ul className={className}>
          {renderChildren()}
        </ul>
      );

    case 'ListItem':
      return (
        <li className={className}>
          {renderTextContent()}
        </li>
      );

    case 'Form':
      return (
        <form className={className} onSubmit={props.onSubmit}>
          {renderChildren()}
        </form>
      );

    // TABLE COMPONENTS (NEW)
    case 'Table':
      return (
        <table className={className}>
          <tbody>
            {renderChildren()}
          </tbody>
        </table>
      );

    case 'TableRow':
      return (
        <tr className={className}>
          {renderChildren()}
        </tr>
      );

    case 'TableCell':
      return (
        <td className={className}>
          {renderTextContent()}
        </td>
      );

    case 'TableHeader':
      return (
        <thead className={className}>
          {renderChildren()}
        </thead>
      );

    case 'TableHead':
      return (
        <th className={className}>
          {renderTextContent()}
        </th>
      );

    // CHART COMPONENTS (PLACEHOLDER)
    case 'LineChart':
    case 'BarChart':
    case 'DonutChart':
    case 'PieChart':
    case 'AreaChart':
      return (
        <div className={`${className} flex items-center justify-center bg-gray-100 rounded-lg border-2 border-dashed border-gray-300`}>
          <div className="text-center p-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <p className="mt-2 text-sm text-gray-500">Chart: {type}</p>
            <p className="text-xs text-gray-400 mt-1">Placeholder</p>
          </div>
        </div>
      );

    // Generic fallback for unknown types
    default:
      console.warn(`Unknown component type: ${type}`);
      return (
        <div className={className}>
          {renderTextContent() || null}
        </div>
      );
  }
}
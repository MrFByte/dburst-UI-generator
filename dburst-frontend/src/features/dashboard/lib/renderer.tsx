import React from 'react';
import type { SchemaNode } from '../types/renderType';
import * as LucideIcons from 'lucide-react';
import { EditableText } from '../components/EditableText';

// Type guard to ensure we only pass SchemaNode objects to RenderNode
function isSchemaNode(child: SchemaNode | string): child is SchemaNode {
  return typeof child !== 'string';
}

interface SchemaRendererProps {
  schema: SchemaNode;
  editMode?: boolean;
  onTextEdit?: (path: string, newContent: string) => void | Promise<void>;
}

export function SchemaRenderer({ schema, editMode = false, onTextEdit }: SchemaRendererProps) {
  if (!schema) return null;
  return <RenderNode node={schema} path="" editMode={editMode} onTextEdit={onTextEdit} />;
}

interface RenderNodeProps {
  node: SchemaNode;
  path?: string;
  editMode?: boolean;
  onTextEdit?: (path: string, newContent: string) => void | Promise<void>;
}

function RenderNode({ node, path = '', editMode = false, onTextEdit }: RenderNodeProps): React.ReactNode | null {
  if (!node) return null;

  const { type, props = {}, children = [], content = '', src } = node;
  const className = props.className || '';

  // Function to render children, filtering out strings for container elements
  const renderChildren = () => (
    children
      .filter(isSchemaNode)
      .map((child, i) => (
        <RenderNode
          key={i}
          node={child}
          path={`${path}/children/${i}`}
          editMode={editMode}
          onTextEdit={onTextEdit}
        />
      ))
  );

  // Function to render content/children for text-holding elements
  const renderTextContent = () => (
    children.length > 0
      ? children.map((child, i) => {
        // This handles both SchemaNode (recursive call) and string (direct render)
        return isSchemaNode(child) ? (
          <RenderNode
            key={i}
            node={child}
            path={`${path}/children/${i}`}
            editMode={editMode}
            onTextEdit={onTextEdit}
          />
        ) : child;
      })
      : content
  );

  switch (type) {
    case 'Root':
      // Add default background if not specified to reduce white overuse
      // Replace any explicit bg-white with gradient
      let rootClass = className;
      if (className.includes('bg-white') && !className.includes('bg-gradient')) {
        rootClass = className.replace('bg-white', 'bg-gradient-to-br from-gray-50 via-white to-slate-50');
      } else if (!className.includes('bg-')) {
        rootClass = `${className} bg-gradient-to-br from-gray-50 via-white to-slate-50`;
      }
      return (
        <main className={`${rootClass} h-fit w-full min-h-screen`}>
          {renderChildren()}
        </main>
      );

    case 'Section':
      // Add default padding and structure if not specified
      const sectionClass = className.includes('py-') || className.includes('px-')
        ? className
        : `${className} py-12 px-4 sm:px-6 lg:px-8`;
      return (
        <section className={sectionClass}>
          {renderChildren()}
        </section>
      );

    case 'Grid':
      // Add default grid styling if not specified
      const gridClass = className.includes('grid')
        ? className
        : `${className} grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6`;
      return (
        <div className={gridClass}>
          {renderChildren()}
        </div>
      );

    case 'Card':
      // Enhanced card styling with better defaults
      // If bg-white is explicitly set, replace it with a subtle gradient
      let cardClass = className;
      if (className.includes('bg-white') && !className.includes('bg-gradient')) {
        // Replace bg-white with a subtle gradient
        cardClass = className.replace('bg-white', 'bg-gradient-to-br from-white to-gray-50');
      } else if (!className.includes('bg-')) {
        // Add default gradient if no background specified
        cardClass = `${className} bg-gradient-to-br from-white to-gray-50`;
      }

      const cardDefaults = cardClass.includes('rounded')
        ? cardClass
        : `${cardClass} rounded-xl border border-gray-200 shadow-md hover:shadow-lg transition-shadow`;
      return (
        <div className={cardDefaults}>
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
      // Add default max-width and centering for containers
      const containerClass = className.includes('max-w-') || className.includes('mx-auto')
        ? className
        : `${className} max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`;
      return (
        <div className={containerClass}>
          {renderChildren()}
        </div>
      );

    case 'Text': {
      const TextTag: React.ElementType = props.tag || 'p';
      const textContent = children.length > 0 ? children.map(c => isSchemaNode(c) ? '' : c).join('') : content;

      if (editMode && onTextEdit) {
        return (
          <EditableText
            content={textContent}
            path={`${path}/content`}
            onEdit={onTextEdit}
            className={className}
          />
        );
      }

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

    case 'Icon': {
      // Dynamic icon rendering from lucide-react
      const iconName = props.name || content || 'Circle';
      const IconComponent = (LucideIcons as any)[iconName] as React.ComponentType<{ className?: string }> | undefined;
      const iconClass = className || 'w-6 h-6 text-gray-600';

      if (IconComponent) {
        return <IconComponent className={iconClass} />;
      }

      // Fallback for unknown icons
      return (
        <span className={`${iconClass} inline-flex items-center justify-center`}>
          ●
        </span>
      );
    }

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

    case 'Div':
      // Add better default styling for Div elements
      const divClass = className || '';
      return (
        <div className={divClass}>
          {renderChildren()}
        </div>
      );

    case 'Hero':
      // Hero section with modern styling
      const heroClass = className.includes('bg-')
        ? className
        : `${className} bg-gradient-to-br from-blue-50 via-white to-purple-50 rounded-2xl shadow-lg p-12`;
      return (
        <div className={heroClass}>
          {renderChildren()}
        </div>
      );

    case 'Timeline':
      // Timeline container with vertical line styling
      const timelineClass = className.includes('bg-')
        ? className
        : `${className} relative pl-8 border-l-2 border-blue-200 space-y-8`;
      return (
        <div className={timelineClass}>
          {renderChildren()}
        </div>
      );

    case 'TimelineItem':
      // Individual timeline item with dot indicator
      return (
        <div className={`${className} relative`}>
          {/* Timeline dot */}
          <div className="absolute -left-[2.1rem] top-0 w-4 h-4 bg-blue-500 rounded-full border-4 border-white shadow-md"></div>
          <div className="bg-gradient-to-br from-white to-gray-50 rounded-lg p-6 shadow-md border border-gray-200">
            {renderChildren()}
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
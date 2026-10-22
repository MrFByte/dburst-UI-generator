import type { FileSystemTree } from '@webcontainer/api';

/**
 * Convert a flat path → content map into a WebContainer FileSystemTree.
 * Handles nested directories by recursively building the tree.
 */
export function buildFileSystemTree(files: Record<string, string>): FileSystemTree {
  const tree: FileSystemTree = {};

  for (const [filePath, content] of Object.entries(files)) {
    const parts = filePath.replace(/^\//, '').split('/');
    let current: FileSystemTree = tree;

    for (let i = 0; i < parts.length - 1; i++) {
      const part = parts[i];
      if (!current[part]) {
        current[part] = { directory: {} };
      }
      current = (current[part] as { directory: FileSystemTree }).directory;
    }

    const fileName = parts[parts.length - 1];
    current[fileName] = { file: { contents: content } };
  }

  return tree;
}

/**
 * Default look of the stub components, as plain CSS classes in Tailwind's
 * `components` layer.
 *
 * Why not put the defaults in each component's className string? Tailwind
 * orders conflicting utilities by their position in the generated stylesheet,
 * not by their order in the class attribute. With `bg-white` in the stub and
 * `bg-[#fff7ed]` from the model, `bg-white` is emitted later and wins, so every
 * Card/Input rendered white no matter what colour the schema asked for (same
 * for border-gray-200, rounded-lg, text-sm, shadow-sm...). Anything in the
 * `components` layer loses to every utility, so the model's classes always win
 * and the defaults only apply where the model said nothing.
 */
export const UI_STUBS_CSS = `
@layer components {
  .ui-card { @apply rounded-lg border bg-white shadow-sm; }
  .ui-card-header { @apply flex flex-col space-y-1.5 p-6; }
  .ui-card-title { @apply text-2xl font-semibold leading-none tracking-tight; }
  .ui-card-description { @apply text-sm text-gray-500; }
  .ui-card-content { @apply p-6 pt-0; }
  .ui-card-footer { @apply flex items-center p-6 pt-0; }
  .ui-button { @apply inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 px-4 py-2; }
  .ui-input { @apply flex h-10 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm ring-offset-white file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50; }
  .ui-textarea { @apply flex min-h-[80px] w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm placeholder:text-gray-500 focus-visible:outline-none focus-visible:ring-2 disabled:cursor-not-allowed disabled:opacity-50; }
  .ui-select { @apply flex h-10 w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm; }
  .ui-label { @apply text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70; }
  .ui-badge { @apply inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors; }
  .ui-avatar { @apply relative flex h-10 w-10 shrink-0 overflow-hidden rounded-full; }
  .ui-avatar-image { @apply aspect-square h-full w-full; }
  .ui-avatar-fallback { @apply flex h-full w-full items-center justify-center rounded-full bg-gray-100; }
  .ui-separator { @apply shrink-0 bg-gray-200; }
  .ui-separator[data-orientation="horizontal"] { @apply h-[1px] w-full; }
  .ui-separator[data-orientation="vertical"] { @apply h-full w-[1px]; }
  .ui-progress { @apply relative h-4 w-full overflow-hidden rounded-full bg-gray-100; }
  .ui-switch { @apply inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent bg-gray-200 transition-colors; }
  .ui-switch[aria-checked="true"] { @apply bg-blue-600; }
  .ui-table-wrap { @apply relative w-full overflow-auto; }
  .ui-table { @apply w-full caption-bottom text-sm; }
  .ui-table-row { @apply border-b transition-colors hover:bg-gray-50; }
  .ui-table-head { @apply h-12 px-4 text-left align-middle font-medium text-gray-500; }
  .ui-table-cell { @apply p-4 align-middle; }
}
`;

/** Stub implementations of DBurst's @/components/ui so AI-generated code runs as-is. */
const UI_STUBS = `
import React from 'react';

const cx = (base, extra) => (extra ? base + ' ' + extra : base);

export function Card({ className = '', children, ...props }) {
  return <div className={cx('ui-card', className)} {...props}>{children}</div>;
}

export function CardHeader({ className = '', children, ...props }) {
  return <div className={cx('ui-card-header', className)} {...props}>{children}</div>;
}

export function CardTitle({ className = '', children, ...props }) {
  return <h3 className={cx('ui-card-title', className)} {...props}>{children}</h3>;
}

export function CardDescription({ className = '', children, ...props }) {
  return <p className={cx('ui-card-description', className)} {...props}>{children}</p>;
}

export function CardContent({ className = '', children, ...props }) {
  return <div className={cx('ui-card-content', className)} {...props}>{children}</div>;
}

export function CardFooter({ className = '', children, ...props }) {
  return <div className={cx('ui-card-footer', className)} {...props}>{children}</div>;
}

export function Button({ className = '', children, variant = 'default', size = 'default', ...props }) {
  return <button className={cx('ui-button', className)} {...props}>{children}</button>;
}

export function Input({ className = '', ...props }) {
  return <input className={cx('ui-input', className)} {...props} />;
}

export function Label({ className = '', children, ...props }) {
  return <label className={cx('ui-label', className)} {...props}>{children}</label>;
}

export function Badge({ className = '', children, variant = 'default', ...props }) {
  return <div className={cx('ui-badge', className)} {...props}>{children}</div>;
}

export function Avatar({ className = '', children, ...props }) {
  return <span className={cx('ui-avatar', className)} {...props}>{children}</span>;
}

export function AvatarImage({ className = '', ...props }) {
  return <img className={cx('ui-avatar-image', className)} {...props} />;
}

export function AvatarFallback({ className = '', children, ...props }) {
  return <span className={cx('ui-avatar-fallback', className)} {...props}>{children}</span>;
}

export function Separator({ className = '', orientation = 'horizontal', ...props }) {
  return <div data-orientation={orientation} className={cx('ui-separator', className)} {...props} />;
}

export function Progress({ className = '', value = 0, ...props }) {
  return (
    <div className={cx('ui-progress', className)} {...props}>
      <div className="h-full bg-blue-600 transition-all" style={{ width: \`\${value}%\` }} />
    </div>
  );
}

export function Switch({ className = '', checked, onChange, ...props }) {
  return (
    <button
      role="switch"
      aria-checked={!!checked}
      onClick={() => onChange?.(!checked)}
      className={cx('ui-switch peer', className)}
      {...props}
    >
      <span className={\`pointer-events-none block h-5 w-5 rounded-full bg-white shadow-lg transform transition-transform \${checked ? 'translate-x-5' : 'translate-x-0'}\`} />
    </button>
  );
}

export function Textarea({ className = '', ...props }) {
  return <textarea className={cx('ui-textarea', className)} {...props} />;
}

export function Select({ className = '', children, ...props }) {
  return <select className={cx('ui-select', className)} {...props}>{children}</select>;
}

export function SelectItem({ value, children }) {
  return <option value={value}>{children}</option>;
}

export function Table({ className = '', children, ...props }) {
  return (
    <div className="ui-table-wrap">
      <table className={cx('ui-table', className)} {...props}>{children}</table>
    </div>
  );
}

export function TableHeader({ className = '', children, ...props }) {
  return <thead className={className} {...props}>{children}</thead>;
}

export function TableBody({ className = '', children, ...props }) {
  return <tbody className={className} {...props}>{children}</tbody>;
}

export function TableRow({ className = '', children, ...props }) {
  return <tr className={cx('ui-table-row', className)} {...props}>{children}</tr>;
}

export function TableHead({ className = '', children, ...props }) {
  return <th className={cx('ui-table-head', className)} {...props}>{children}</th>;
}

export function TableCell({ className = '', children, ...props }) {
  return <td className={cx('ui-table-cell', className)} {...props}>{children}</td>;
}
`;

/**
 * Wrap a single React component code string into a minimal Vite + React project.
 * The `code` string is written to `src/App.tsx`.
 * Provides:
 *  - `@` alias → `./src`
 *  - `@/components/ui` stub with all common DBurst UI primitives
 *  - `lucide-react` as a dependency
 *  - Tailwind CSS v4 (Vite plugin); stub defaults live in the components layer, see UI_STUBS_CSS
 */
export function buildReactViteProject(code: string): FileSystemTree {
  const packageJson = JSON.stringify(
    {
      name: 'dburst-preview',
      private: true,
      version: '0.0.0',
      type: 'module',
      scripts: {
        dev: 'vite --host',
        build: 'vite build',
        preview: 'vite preview',
      },
      dependencies: {
        react: '^18.3.1',
        'react-dom': '^18.3.1',
        'lucide-react': '^0.469.0',
      },
      devDependencies: {
        '@types/react': '^18.3.19',
        '@types/react-dom': '^18.3.5',
        '@vitejs/plugin-react': '^4.3.4',
        tailwindcss: '^4.0.0',
        '@tailwindcss/vite': '^4.0.0',
        vite: '^6.3.5',
      },
    },
    null,
    2
  );

  const viteConfig = `import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: true,
    port: 5173,
  },
});
`;

  const indexHtml = `<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>DBurst Preview</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
`;

  const mainTsx = `import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
`;

  const indexCss = `@import "tailwindcss";
${UI_STUBS_CSS}`;

  const files: Record<string, string> = {
    'package.json': packageJson,
    'vite.config.ts': viteConfig,
    'index.html': indexHtml,
    'src/main.tsx': mainTsx,
    'src/index.css': indexCss,
    'src/App.tsx': code,
    'src/components/ui.tsx': UI_STUBS,
  };

  return buildFileSystemTree(files);
}

import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

/**
 * Catches render crashes anywhere in the route tree and shows a friendly
 * screen instead of a blank page. The real error goes to the console only.
 * Navigation uses full page loads so it works even if the router is the
 * part that crashed.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled render error:', error, info.componentStack);
  }

  render() {
    if (!this.state.hasError) return this.props.children;

    return (
      <div
        role="alert"
        className="min-h-dvh flex items-center justify-center bg-zinc-950 text-zinc-100 px-4 py-10"
      >
        <div className="w-full max-w-md text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-red-500/15">
            <AlertTriangle className="h-7 w-7 text-red-400" aria-hidden="true" />
          </div>
          <h1 className="text-2xl font-semibold">Something went wrong</h1>
          <p className="mt-2 text-sm text-zinc-400">
            This page ran into an unexpected problem. Reloading usually fixes it; your saved work is safe.
          </p>
          <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="min-h-11 px-5 rounded-xl bg-violet-600 hover:bg-violet-700 font-semibold transition-colors"
            >
              Reload
            </button>
            <button
              type="button"
              onClick={() => window.location.assign('/dashboard')}
              className="min-h-11 px-5 rounded-xl border border-zinc-700 hover:bg-zinc-800 font-semibold transition-colors"
            >
              Go to dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }
}

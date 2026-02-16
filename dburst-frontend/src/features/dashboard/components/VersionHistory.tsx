import { formatDistanceToNow } from 'date-fns';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Clock, RotateCcw, Package } from 'lucide-react';
import Loader from '@/shared/components/Loader';
import type { PatchHistoryItem } from '@/types/patch';

interface VersionHistoryProps {
    patches: PatchHistoryItem[];
    totalPatches: number;
    isLoading: boolean;
    onRestore: (versionId: string) => void | Promise<void>;
    onLoadMore?: () => void;
    hasMore?: boolean;
}

/**
 * Version history component with pagination
 * Displays all patches with restore functionality
 */
export function VersionHistory({
    patches,
    totalPatches,
    isLoading,
    onRestore,
    onLoadMore,
    hasMore = false,
}: VersionHistoryProps) {
    if (isLoading && patches.length === 0) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader size="md" text="Loading history..." />
            </div>
        );
    }

    if (patches.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-gray-500">
                <Clock className="h-12 w-12 mb-2 opacity-50" />
                <p className="text-sm">No version history yet</p>
                <p className="text-xs mt-1">Start editing to create versions</p>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Clock className="h-5 w-5" />
                    Version History
                </h3>
                <Badge variant="secondary">{totalPatches} versions</Badge>
            </div>

            <ScrollArea className="h-[500px] pr-4">
                <div className="space-y-3">
                    {patches.map((patch, index) => {
                        const versionNumber = totalPatches - index;
                        const isLatest = index === 0;

                        return (
                            <div
                                key={patch.id}
                                className="group relative p-4 border rounded-lg hover:shadow-md transition-all bg-white"
                            >
                                {/* Version header */}
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        <span className="font-semibold text-gray-900">
                                            Version {versionNumber}
                                        </span>

                                        {isLatest && (
                                            <Badge variant="default" className="text-xs">
                                                Current
                                            </Badge>
                                        )}

                                        {patch.snapshot_created && (
                                            <Badge variant="outline" className="text-xs flex items-center gap-1">
                                                <Package className="h-3 w-3" />
                                                Snapshot
                                            </Badge>
                                        )}
                                    </div>

                                    {!isLatest && (
                                        <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={() => onRestore(patch.id)}
                                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <RotateCcw className="h-3 w-3 mr-1" />
                                            Restore
                                        </Button>
                                    )}
                                </div>

                                {/* Description */}
                                {patch.description && (
                                    <p className="text-sm text-gray-700 mb-2">
                                        {patch.description}
                                    </p>
                                )}

                                {/* Metadata */}
                                <div className="flex items-center gap-4 text-xs text-gray-500">
                                    <span className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        {formatDistanceToNow(new Date(patch.applied_at), {
                                            addSuffix: true,
                                        })}
                                    </span>
                                    <span>{patch.user_email}</span>
                                    <span>{patch.patch_data.length} operation(s)</span>
                                </div>

                                {/* Patch operations preview */}
                                <details className="mt-2">
                                    <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-700">
                                        View changes
                                    </summary>
                                    <div className="mt-2 p-2 bg-gray-50 rounded text-xs font-mono">
                                        <pre className="overflow-x-auto">
                                            {JSON.stringify(patch.patch_data, null, 2)}
                                        </pre>
                                    </div>
                                </details>
                            </div>
                        );
                    })}
                </div>

                {/* Load more button */}
                {hasMore && (
                    <div className="mt-4 text-center">
                        <Button
                            variant="outline"
                            onClick={onLoadMore}
                            disabled={isLoading}
                        >
                            {isLoading ? 'Loading...' : 'Load More'}
                        </Button>
                    </div>
                )}
            </ScrollArea>
        </div>
    );
}

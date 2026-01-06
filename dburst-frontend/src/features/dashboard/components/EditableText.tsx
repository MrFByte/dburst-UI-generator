import React, { useState, useRef, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface EditableTextProps {
    content: string;
    path: string;
    onEdit: (path: string, newContent: string) => void | Promise<void>;
    className?: string;
    placeholder?: string;
    disabled?: boolean;
    debounceMs?: number;
    multiline?: boolean;
}

/**
 * Editable text component with contentEditable
 * Modern React implementation with proper accessibility
 */
export function EditableText({
    content,
    path,
    onEdit,
    className,
    placeholder = 'Click to edit...',
    disabled = false,
    debounceMs = 500,
    multiline = false,
}: EditableTextProps) {
    const [isEditing, setIsEditing] = useState(false);
    const [localContent, setLocalContent] = useState(content);

    const editableRef = useRef<HTMLDivElement>(null);
    const previousContent = useRef(content);

    /**
     * Handle click to enter edit mode
     */
    const handleClick = useCallback(() => {
        if (disabled || isEditing) return;

        setIsEditing(true);

        // Focus after state update
        requestAnimationFrame(() => {
            if (editableRef.current) {
                editableRef.current.focus();

                // Select all text
                const range = document.createRange();
                range.selectNodeContents(editableRef.current);
                const selection = window.getSelection();
                selection?.removeAllRanges();
                selection?.addRange(range);
            }
        });
    }, [disabled, isEditing]);

    /**
     * Handle blur to exit edit mode
     */
    const handleBlur = useCallback(() => {
        setIsEditing(false);

        const newContent = editableRef.current?.textContent || '';
        setLocalContent(newContent);

        // Call onEdit immediately (no debounce, no async)
        if (newContent !== previousContent.current) {
            onEdit(path, newContent);
            previousContent.current = newContent;
        }
    }, [path, onEdit]);

    /**
     * Handle input changes with cursor preservation
     */
    const handleInput = useCallback(
        (e: React.FormEvent<HTMLDivElement>) => {
            const newContent = e.currentTarget.textContent || '';
            setLocalContent(newContent);

            // Don't trigger save on every keystroke, only on blur
        },
        []
    );

    /**
     * Handle keyboard shortcuts
     */
    const handleKeyDown = useCallback(
        (e: React.KeyboardEvent<HTMLDivElement>) => {
            // Enter without shift = save (for single-line)
            if (e.key === 'Enter' && !e.shiftKey && !multiline) {
                e.preventDefault();
                editableRef.current?.blur();
            }

            // Escape = cancel
            if (e.key === 'Escape') {
                e.preventDefault();
                setLocalContent(previousContent.current);
                if (editableRef.current) {
                    editableRef.current.textContent = previousContent.current;
                }
                editableRef.current?.blur();
            }

            // Ctrl/Cmd + Enter = save (for multiline)
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey) && multiline) {
                e.preventDefault();
                editableRef.current?.blur();
            }
        },
        [multiline]
    );

    /**
     * Prevent paste with formatting
     */
    const handlePaste = useCallback((e: React.ClipboardEvent) => {
        e.preventDefault();
        const text = e.clipboardData.getData('text/plain');
        document.execCommand('insertText', false, text);
    }, []);

    const showPlaceholder = !localContent && !isEditing;

    // Don't update content while editing to preserve cursor
    useEffect(() => {
        if (!isEditing && editableRef.current) {
            editableRef.current.textContent = localContent;
        }
    }, [localContent, isEditing]);

    return (
        <div className="relative inline-block group">
            <div
                ref={editableRef}
                contentEditable={isEditing && !disabled}
                suppressContentEditableWarning
                onClick={handleClick}
                onBlur={handleBlur}
                onInput={handleInput}
                onKeyDown={handleKeyDown}
                onPaste={handlePaste}
                role="textbox"
                aria-label="Editable text"
                aria-disabled={disabled}
                data-path={path}
                className={cn(
                    'outline-none transition-all duration-200',
                    className,
                    isEditing && 'ring-2 ring-blue-500 ring-offset-2 rounded px-1',
                    !isEditing && !disabled && 'cursor-pointer hover:bg-blue-50/50 rounded px-1',
                    disabled && 'cursor-not-allowed opacity-50',
                    showPlaceholder && 'text-gray-400 italic'
                )}
            >
                {/* Content is managed by contentEditable, not React */}
            </div>

            {/* Edit indicator */}
            {!disabled && !isEditing && (
                <span className="absolute -right-6 top-0 opacity-0 group-hover:opacity-100 transition-opacity text-xs text-gray-400">
                    ✏️
                </span>
            )}
        </div>
    );
}

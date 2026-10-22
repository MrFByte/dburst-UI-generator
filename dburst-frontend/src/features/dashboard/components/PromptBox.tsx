import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, MessageSquare } from 'lucide-react';
import Loader from '@/shared/components/Loader';
import { getChatHistory, refineUI } from '../api/dashboardApi';
import { showError } from '@/core/api/showError';
import { useCountdown } from '@/hooks/useCountdown';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    created_at: string;
}

interface PromptBoxProps {
    generationId: string;
    onSchemaUpdate: (schema: any, code: string) => void;
}

export function PromptBox({ generationId, onSchemaUpdate }: PromptBoxProps) {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    // After a rate limit, Send counts down instead of failing again.
    const cooldown = useCountdown();

    // Load chat history on mount
    useEffect(() => {
        loadChatHistory();
    }, [generationId]);

    const loadChatHistory = async () => {
        try {
            setIsLoading(true);
            const data = await getChatHistory(generationId);
            setMessages(data.messages || []);
        } catch (error) {
            showError(error, { fallback: "Couldn't load the chat history" });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async (retryText?: string) => {
        const text = retryText ?? inputValue;
        if (!text.trim() || isSending || cooldown.active) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: text,
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        const messageText = text;
        setInputValue('');
        setIsSending(true);

        try {
            const result = await refineUI(generationId, messageText);

            const aiMessage: ChatMessage = {
                role: 'assistant',
                content: result.ai_response,
                created_at: new Date().toISOString()
            };

            setMessages(prev => [...prev, aiMessage]);
            onSchemaUpdate(result.schema, result.code);
        } catch (error) {
            // Take the unsent message back out of the thread and give the
            // text back to the user, so retrying is one click (or Enter).
            setMessages(prev => prev.filter(m => m !== userMessage));
            setInputValue(messageText);
            const apiError = showError(error, {
                fallback: "Couldn't apply that change. Please try again.",
                onRetry: () => { void handleSendMessage(messageText); },
            });
            if (apiError.code === 'llm_rate_limited' || apiError.code === 'throttled') {
                cooldown.start(apiError.retryAfter ?? 30);
            }
        } finally {
            setIsSending(false);
        }
    };

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex flex-col flex-1 min-h-0 h-full bg-slate-900">
            {/* Chat Messages */}
            <div className="flex-1 min-h-0 overflow-auto p-3 sm:p-4 space-y-4">
                {isLoading ? (
                    <div className="flex items-center justify-center h-full">
                        <Loader size="md" text="Loading chat..." />
                    </div>
                ) : messages.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-400">
                        <MessageSquare className="w-12 h-12 mb-3 opacity-50" />
                        <p className="text-sm">No messages yet</p>
                    </div>
                ) : (
                    messages.map((msg, index) => (
                        <div
                            key={index}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[90%] sm:max-w-[85%] min-w-0 p-3 rounded-lg ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-slate-800 text-gray-200 border border-slate-700'
                                    }`}
                            >
                                <p className="text-sm whitespace-pre-wrap break-words">{msg.content}</p>
                                <p className="text-xs opacity-60 mt-1">
                                    {new Date(msg.created_at).toLocaleTimeString()}
                                </p>
                            </div>
                        </div>
                    ))
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-3 sm:p-4 border-t border-slate-700 bg-slate-900">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                        placeholder="Ask for changes to the UI..."
                        disabled={isSending}
                        className="flex-1 min-w-0 bg-slate-800 text-white rounded px-3 py-2.5 md:py-2 text-base md:text-sm border border-slate-700 
                     focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 
                     placeholder-gray-500 disabled:opacity-50"
                    />
                    <button
                        onClick={() => handleSendMessage()}
                        disabled={!inputValue.trim() || isSending || cooldown.active}
                        aria-label={cooldown.active ? `Try again in ${cooldown.secondsLeft} seconds` : 'Send'}
                        className="px-4 py-2 min-w-11 min-h-11 md:min-h-0 justify-center shrink-0 bg-blue-600 hover:bg-blue-700 text-white rounded transition 
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isSending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : cooldown.active ? (
                            <span className="text-xs tabular-nums">{cooldown.secondsLeft}s</span>
                        ) : (
                            <Send className="w-4 h-4" />
                        )}
                    </button>
                </div>
                <p className="text-xs text-gray-500 mt-2">
                    Describe changes you'd like to make to the UI
                </p>
            </div>
        </div>
    );
}

import { useState, useEffect, useRef } from 'react';
import { Send, Loader2, MessageSquare } from 'lucide-react';
import Loader from '@/shared/components/Loader';

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

    // Load chat history on mount
    useEffect(() => {
        loadChatHistory();
    }, [generationId]);

    const loadChatHistory = async () => {
        try {
            setIsLoading(true);
            const response = await fetch(`/api/v1/generation/chat/history/${generationId}/`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json',
                },
            });

            if (!response.ok) {
                throw new Error('Failed to load chat history');
            }

            const data = await response.json();
            setMessages(data.messages || []);
        } catch (error) {
            console.error('Failed to load chat history:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSendMessage = async () => {
        if (!inputValue.trim() || isSending) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: inputValue,
            created_at: new Date().toISOString()
        };

        setMessages(prev => [...prev, userMessage]);
        const messageText = inputValue;
        setInputValue('');
        setIsSending(true);

        try {
            const response = await fetch('/api/v1/generation/chat/refine/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    generation_id: generationId,
                    message: messageText
                })
            });

            if (!response.ok) {
                throw new Error('Failed to refine UI');
            }

            const result = await response.json();

            const aiMessage: ChatMessage = {
                role: 'assistant',
                content: result.ai_response,
                created_at: new Date().toISOString()
            };

            setMessages(prev => [...prev, aiMessage]);
            onSchemaUpdate(result.schema, result.code);
        } catch (error: any) {
            console.error('Failed to refine UI:', error);
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: 'Sorry, I encountered an error processing your request.',
                created_at: new Date().toISOString()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsSending(false);
        }
    };

    // Auto-scroll to bottom when messages change
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex flex-col h-full bg-slate-900">
            {/* Chat Messages */}
            <div className="flex-1 overflow-auto p-4 space-y-4">
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
                                className={`max-w-[85%] p-3 rounded-lg ${msg.role === 'user'
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-slate-800 text-gray-200 border border-slate-700'
                                    }`}
                            >
                                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
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
            <div className="p-4 border-t border-slate-700 bg-slate-900">
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                        placeholder="Ask for changes to the UI..."
                        disabled={isSending}
                        className="flex-1 bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700 
                     focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 
                     placeholder-gray-500 disabled:opacity-50"
                    />
                    <button
                        onClick={handleSendMessage}
                        disabled={!inputValue.trim() || isSending}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition 
                     disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isSending ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
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

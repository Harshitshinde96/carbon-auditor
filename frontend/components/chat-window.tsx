'use client';

import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, User, Bot, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';


interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: any[];
  confidenceScore?: number;
}

interface ChatWindowProps {
  onSendMessage: (message: string) => Promise<{ answer: string; sources?: string[]; confidence_score?: number }>;
}

export function ChatWindow({ onSendMessage }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Hello! I am your AI compliance assistant. Ask me anything about ESG reporting or your uploaded utility bills.',
    }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isTyping) return;

    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await onSendMessage(userMsg.content);
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        confidenceScore: response.confidence_score,
      };
      setMessages(prev => [...prev, aiMsg]);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Error: Failed to fetch response. Please try again.',
        }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <Card className="flex flex-col h-[600px] border-border bg-surface">
      <CardHeader className="border-b border-border pb-4">
        <CardTitle className="text-ink">Compliance Chat</CardTitle>
      </CardHeader>
      
      <CardContent className="flex-1 flex flex-col p-0 overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-ink text-background' : 'bg-surface border border-ink text-ink'}`}>
                {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>
              
              <div className={`flex flex-col max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
                <div className={`px-4 py-2 rounded-2xl ${msg.role === 'user' ? 'bg-ink text-background' : 'bg-background border border-border text-ink'}`}>
                  {msg.role === 'assistant' ? (
                    <div className="prose prose-sm dark:prose-invert max-w-none text-ink">
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                  ) : (
                    msg.content
                  )}
                </div>
                
                {msg.role === 'assistant' && msg.confidenceScore !== undefined && (
                  <div className="mt-2 space-y-1">
                    {msg.confidenceScore < 0.70 && (
                      <div className="flex items-center text-xs font-medium text-ink bg-surface border border-ink px-2 py-1 rounded">
                        <AlertTriangle className="w-3 h-3 mr-1" />
                        Low confidence response
                      </div>
                    )}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="text-xs text-ink-secondary">
                        <span className="font-semibold">Sources:</span>
                        <ul className="list-disc pl-4 mt-1">
                          {msg.sources.map((src: any, i) => (
                            <li key={i}>{src.source_file} ({src.section})</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3">
              <div className="w-8 h-8 rounded-full bg-surface border border-ink flex items-center justify-center shrink-0 text-ink">
                <Bot className="w-5 h-5" />
              </div>
              <div className="px-4 py-3 rounded-2xl bg-background border border-border flex items-center">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 rounded-full bg-ink animate-bounce [animation-delay:-0.3s]"></div>
                  <div className="w-2 h-2 rounded-full bg-ink animate-bounce [animation-delay:-0.15s]"></div>
                  <div className="w-2 h-2 rounded-full bg-ink animate-bounce"></div>
                </div>
                <span className="sr-only">AI is thinking...</span>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        <div className="p-4 bg-background border-t border-border">
          <form onSubmit={handleSubmit} className="flex gap-2 relative">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your data or ESG standards..."
              className="flex-1 bg-surface"
              disabled={isTyping}
            />
            <Button type="submit" disabled={isTyping || !input.trim()}>
              <Send className="w-4 h-4 mr-2" />
              Send
            </Button>
          </form>
        </div>
      </CardContent>
    </Card>
  );
}

'use client';

import { ChatWindow } from '@/components/chat-window';
import { apiClient } from '@/lib/api-client';

export default function ChatPage() {
  const handleSendMessage = async (message: string) => {
    const response = await apiClient('/chat/query', {
      method: 'POST',
      body: JSON.stringify({ query: message }),
    });
    return response.data;
  };

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-ink">Compliance Chat</h1>
        <p className="text-ink-secondary mt-2">
          Ask questions about ESG compliance or query your uploaded carbon data.
        </p>
      </div>
      
      <ChatWindow onSendMessage={handleSendMessage} />
    </div>
  );
}

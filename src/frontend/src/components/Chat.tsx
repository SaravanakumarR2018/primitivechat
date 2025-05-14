'use client';

import 'highlight.js/styles/github.css'; // or another highlight.js theme

import { useOrganization } from '@clerk/nextjs';
import { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';

type Message = {
  sender: 'user' | 'ai';
  text: string;
  id?: string;
};

export default function Chat({
  chatId,
}: {
  chatId: string;
}) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const { organization } = useOrganization();

  // Load messages when chatId changes
  useEffect(() => {
    const loadChat = () => {
      if (!chatId) {
        // New chat - reset everything
        setMessages([]);
        setCurrentChatId(null);
        return;
      }

      // Existing chat - try to load from session storage
      const savedChat = sessionStorage.getItem(chatId);
      if (savedChat) {
        const parsed = JSON.parse(savedChat);
        setMessages(parsed.messages || []);
        setCurrentChatId(parsed.chatId || null);
      } else {
        // New chat instance
        setMessages([]);
        setCurrentChatId(null);
      }
    };

    loadChat();
  }, [chatId]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const startNewChat = async (firstMessage: string) => {
    if (!firstMessage.trim()) {
      return;
    }
    const userMessage: Message = { sender: 'user', text: firstMessage };
    setMessages([userMessage]);
    setInput('');
    setIsTyping(true);

    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await fetch('/api/backend/sendMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: firstMessage,
          stream: true,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error('Failed to start new chat');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const aiMessage = { id: crypto.randomUUID(), sender: 'ai' as const, text: '' };
      let newChatId = '';
      let userId = '';
      const orgId = organization?.id || '';

      setMessages(prev => [...prev, aiMessage]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || trimmedLine === 'data: [DONE]') {
            continue;
          }

          if (trimmedLine.startsWith('data: ')) {
            try {
              const json = JSON.parse(trimmedLine.slice(6));

              // Get IDs from first response
              if (json.chat_id && !newChatId) {
                newChatId = json.chat_id;
                setCurrentChatId(newChatId);
              }
              if (json.user_id && !userId) {
                userId = json.user_id;
              }

              // Update AI message
              const content = json.choices?.[0]?.delta?.content;
              if (content) {
                aiMessage.text += content;
                setMessages(prev => [...prev.slice(0, -1), { ...aiMessage }]);
              }
            } catch (error) {
              console.error('Error parsing stream:', error);
            }
          }
        }
      }

      // Save the new chat
      if (newChatId && orgId && userId) {
        const storageKey = `${newChatId}-${orgId}-${userId}`;
        const chatData = {
          chatId: newChatId,
          messages: [userMessage, aiMessage],
          createdAt: Date.now(),
        };
        sessionStorage.setItem(storageKey, JSON.stringify(chatData));
      }
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('New chat error:', err);
        setMessages(prev => prev.slice(0, -1)); // Remove incomplete AI message
      }
    } finally {
      setIsTyping(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) {
      return;
    }

    // If no current chat, treat as new chat
    if (!currentChatId) {
      return startNewChat(input);
    }

    const userMessage: Message = { sender: 'user', text: input };
    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsTyping(true);
    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await fetch('/api/backend/sendMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          stream: true,
          chat_id: currentChatId,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error('Streaming failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const aiMessage = { id: crypto.randomUUID(), sender: 'ai' as const, text: '' };
      let newChatId = currentChatId;
      let userId = '';
      const orgId = organization?.id || '';

      setMessages(prev => [...prev, aiMessage]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmedLine = line.trim();
          if (!trimmedLine || trimmedLine === 'data: [DONE]') {
            continue;
          }

          if (trimmedLine.startsWith('data: ')) {
            try {
              const json = JSON.parse(trimmedLine.slice(6));

              // Update chat_id if changed
              if (json.chat_id && json.chat_id !== currentChatId) {
                newChatId = json.chat_id;
                setCurrentChatId(newChatId);
              }
              if (json.user_id) {
                userId = json.user_id;
              }

              // Update AI message
              const content = json.choices?.[0]?.delta?.content;
              if (content) {
                aiMessage.text += content;
                setMessages(prev => [...prev.slice(0, -1), { ...aiMessage }]);
              }
            } catch (error) {
              console.error('Error parsing stream:', error);
            }
          }
        }
      }

      // Save updated chat
      if (newChatId && orgId && userId) {
        const storageKey = `${newChatId}-${orgId}-${userId}`;
        const finalMessages = [...newMessages, aiMessage];
        const chatData = {
          chatId: newChatId,
          messages: finalMessages,
          updatedAt: Date.now(),
        };

        // If chat_id changed, clean up old storage
        if (newChatId !== currentChatId) {
          const oldKey = `${currentChatId}-${orgId}-${userId}`;
          sessionStorage.removeItem(oldKey);
        }

        sessionStorage.setItem(storageKey, JSON.stringify(chatData));
      }
    } catch (err) {
      if (err instanceof Error && err.name !== 'AbortError') {
        console.error('Stream error:', err);
        setMessages(prev => prev.slice(0, -1)); // Remove incomplete AI message
      }
    } finally {
      setIsTyping(false);
    }
  };

  const stopStreaming = () => {
    controllerRef.current?.abort();
    setIsTyping(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen flex-col pt-16 sm:pt-12">
      <div className="mx-auto flex w-full max-w-4xl flex-1 flex-col overflow-y-auto">

        {/* Scrollable Message Area */}
        <div className="flex-1 space-y-4 border px-4 pt-4">
          {messages.length === 0 && !isTyping
            ? (
                <div className="text-center text-xl text-gray-400">
                  Start a new chat
                </div>
              )
            : (
                messages.map(msg => (
                  <div
                    key={msg.id || crypto.randomUUID()}
                    className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`prose prose-sm overflow-x-auto whitespace-pre-wrap rounded-2xl p-3 shadow-md ${
                        msg.sender === 'user' ? 'rounded-br-none bg-blue-400 text-white' : 'bg-gray-200 text-gray-800'
                      }`}
                    >
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeHighlight]}
                      >
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  </div>
                ))
              )}

          {isTyping && (
            <div className="flex w-full">
              <span className="size-4 animate-pulse rounded-full bg-black shadow-md" />
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <div className="sticky bottom-0 z-10 border-t border-gray-300 bg-gray-100 px-4 py-3">
          <div className="mx-auto flex max-w-3xl items-center rounded-full border border-gray-300 bg-gray-100 px-4 py-2 shadow-sm">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 bg-transparent text-sm focus:outline-none"
              placeholder="Type a message..."
            />
            <button
              type="button"
              onClick={isTyping ? stopStreaming : sendMessage}
              className="ml-2 rounded-full bg-blue-500 p-2 text-white hover:bg-blue-600"
            >
              {isTyping
                ? (
                    <svg className="size-5" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                      <path d="M6 18L18 6M6 6l12 12" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )
                : (
                    <svg className="size-5" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                      <path d="M5 12h14M12 5l7 7-7 7" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  )}
            </button>
          </div>
        </div>
      </div>
    </div>

  );
}

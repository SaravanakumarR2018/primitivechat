'use client';

import { useOrganization } from '@clerk/nextjs';
import { useEffect, useRef, useState } from 'react';

type Message = {
  sender: 'user' | 'ai';
  text: string;
  id?: string;
};

export default function Chat({
  chatId,
  isSidebarOpen,
}: {
  chatId: string;
  isSidebarOpen: boolean;
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
    <div className="flex h-screen flex-col pb-28 pt-24 sm:pt-12">
      <div className="scrollbar-hide flex flex-1 flex-col items-center space-y-4 overflow-y-auto p-4 md:items-start">
        {messages.length === 0 && !isTyping
          ? (
              <div className="flex size-full items-center justify-center text-center text-xl text-gray-400">
                Start a new chat
              </div>
            )
          : (
              messages.map(msg => (
                <div
                  key={msg.id || crypto.randomUUID()}
                  className={`flex w-full sm:px-24 ${
                    msg.sender === 'user' ? 'justify-end' : 'justify-start'
                  }`}
                >
                  <div
                    className={`relative max-w-[75%] rounded-xl px-4 py-2 shadow-md transition-all duration-300 sm:max-w-[60%] md:max-w-[50%] lg:max-w-[40%] xl:max-w-[35%] ${
                      msg.sender === 'user'
                        ? 'rounded-br-none bg-blue-400 text-white'
                        : 'rounded-bl-none bg-gray-200 text-gray-800'
                    }`}
                  >
                    {msg.text}
                    <span
                      className={`absolute -bottom-1 size-3 rotate-45 ${
                        msg.sender === 'user' ? 'right-2 bg-blue-400' : 'left-2 bg-gray-200'
                      }`}
                    >
                    </span>
                  </div>
                </div>
              ))
            )}

        {isTyping && (
          <div className="flex w-full sm:pl-24">
            <div className="flex space-x-1 rounded-xl bg-gray-200 px-4 py-2 shadow-md">
              <span className="size-2 animate-bounce rounded-full bg-gray-600"></span>
              <span className="size-2 animate-bounce rounded-full bg-gray-600 delay-150"></span>
              <span className="size-2 animate-bounce rounded-full bg-gray-600 delay-300"></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <div
        className={`sticky bottom-0 p-6 transition-all duration-300 ${
          isSidebarOpen ? 'mx-auto w-[calc(100%-26rem)]' : 'left-0 w-full'
        }`}
        style={{
          position: messages.length === 0 ? 'absolute' : 'fixed',
          bottom: messages.length === 0 ? '40%' : '0',
          transform: messages.length === 0 ? 'translateY(100%)' : 'none',
        }}
      >
        <div className="mx-auto flex max-w-2xl items-center rounded-lg border border-gray-500 bg-gray-200 p-1">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            className="flex-1 bg-transparent p-2 focus:outline-none"
            placeholder="Type a message..."
          />
          <button
            onClick={isTyping ? stopStreaming : sendMessage}
            type="button"
            title={isTyping ? 'Stop' : 'Send'}
            className="rounded-lg bg-blue-500 p-2 text-white hover:bg-blue-600"
          >
            {isTyping
              ? (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="size-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                )
              : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="size-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 12h14M12 5l7 7-7 7"
                    />
                  </svg>
                )}
          </button>
        </div>
      </div>
    </div>
  );
}

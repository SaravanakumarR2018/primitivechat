/* eslint-disable unused-imports/no-unused-vars */
'use client';

import { useEffect, useRef, useState } from 'react';

type Message = {
  sender: 'user' | 'ai';
  text: string;
  id?: string;
};

function generateUUID(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

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
  const [isNewChat, setIsNewChat] = useState(true);
  const controllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [localChatId, setLocalChatId] = useState<string | null>(null);

  // Load messages from sessionStorage when chatId changes
  useEffect(() => {
    const savedChats = sessionStorage.getItem(`chat-${chatId}`);
    if (savedChats) {
      setMessages(JSON.parse(savedChats));
      setIsNewChat(false);
    } else {
      setMessages([]);
      setIsNewChat(true);
    }
  }, [chatId]);

  // Save messages to sessionStorage whenever messages change
  useEffect(() => {
    if (messages.length > 0 || isNewChat) {
      sessionStorage.setItem(`chat-${chatId}`, JSON.stringify(messages));
      window.dispatchEvent(new Event('storage'));
      setIsNewChat(true);
    }
  }, [messages, chatId, isNewChat]);

  // Auto-scroll to the latest message
  useEffect(() => {
    if (messagesEndRef.current) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
      }, 100); // Small delay for smooth scrolling
    }
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) {
      return;
    }

    setMessages(prev => [...prev, { sender: 'user', text: input }]);
    setInput('');
    setIsTyping(true);

    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await fetch('/api/backend/sendMessage', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          ...(localChatId ? { chatId: localChatId } : {}), // <-- only include if exists
        }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Streaming failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let currentText = '';
      let newChatId: string | null = null;

      const aiMessageId = generateUUID();
      setMessages(prev => [
        ...prev,
        { id: aiMessageId, sender: 'ai', text: '' },
      ]);

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

              const token = json.choices?.[0]?.delta?.content;
              if (token) {
                currentText += token;
                setMessages(prev =>
                  prev.map(m =>
                    m.id === aiMessageId ? { ...m, text: currentText } : m,
                  ),
                );
              }

              if (!localChatId && json.chat_id && !newChatId) {
                newChatId = json.chat_id;
              }
            } catch (error) {
              // Handle JSON parsing error
              console.error('Failed to parse JSON:', error);
              console.error('Failed to parse chunk:', trimmedLine);
            }
          }
        }
      }

      if (newChatId) {
        setLocalChatId(newChatId);
      }
    } catch (err) {
      console.error('Error during stream:', err);
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
      {/* Chat Messages */}
      <div className="scrollbar-hide flex flex-1 flex-col items-center space-y-4 overflow-y-auto p-4 md:items-start">
        {/* Show "Start a new chat" when no messages */}
        {messages.length === 0 && !isTyping
          ? (
              <div className="flex size-full items-center justify-center text-center text-xl text-gray-400">
                Start a new chat
              </div>
            )
          : (
              messages.map(msg => (
                <div
                  key={msg.id}
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

                    {/* Small tail on message bubble for style */}
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

        {/* Typing Indicator (shown when bot is typing) */}
        {isTyping && (
          <div className="flex w-full sm:pl-24">
            <div className="flex space-x-1 rounded-xl bg-gray-200 px-4 py-2 shadow-md">
              <span className="size-2 animate-bounce rounded-full bg-gray-600"></span>
              <span className="size-2 animate-bounce rounded-full bg-gray-600 delay-150"></span>
              <span className="size-2 animate-bounce rounded-full bg-gray-600 delay-300"></span>
            </div>
          </div>
        )}

        {/* This div ensures the chat auto-scrolls to the latest message */}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div
        className={`sticky bottom-0 p-6 transition-all duration-300 ${
          isSidebarOpen ? 'mx-auto w-[calc(100%-26rem)]' : 'left-0 w-full'
        }`}
        style={{
          position: messages.length === 0 ? 'absolute' : 'fixed', // Use absolute for center, fixed for bottom
          bottom: messages.length === 0 ? '40%' : '0', // Center when no messages, bottom otherwise
          transform: messages.length === 0 ? 'translateY(100%)' : 'none', // Center vertically
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
            onClick={sendMessage}
            type="button"
            title="Send"
            className="rounded-lg bg-blue-500 p-2 text-white hover:bg-blue-600"
          >
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
          </button>
        </div>
      </div>
    </div>
  );
}

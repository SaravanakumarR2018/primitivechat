'use client';

import { useEffect, useRef, useState } from 'react';

type Message = {
  question: string;
  answer: string;
};

export default function Chat({ chatId, isSidebarOpen }: { chatId: string; isSidebarOpen: boolean }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Load chat history when `chatId` changes
  useEffect(() => {
    if (chatId) {
      const savedChats = sessionStorage.getItem(`chat-${chatId}`);
      setMessages(savedChats ? JSON.parse(savedChats) : []);
    }
  }, [chatId]);

  // Save messages to `sessionStorage`
  useEffect(() => {
    if (chatId && messages.length > 0) {
      sessionStorage.setItem(`chat-${chatId}`, JSON.stringify(messages));
    }
  }, [messages, chatId]);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) {
      return;
    } // Prevent empty messages

    const userMessage: Message = { question: input, answer: '...' };
    setMessages(prev => [...prev, userMessage]); // Show user message first
    setInput('');

    // Retrieve the existing chat ID from sessionStorage
    let storedChatId = sessionStorage.getItem(`chat-session-${chatId}`) || undefined;

    try {
      const response = await fetch('/api/backend/sendMessage', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(
          storedChatId
            ? { message: input, chatId: storedChatId } // Send `chatId` for ongoing chats
            : { message: input }, // Only send `message` for new chats
        ),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();

      // Store new chat_id only if it's the first message
      if (!storedChatId && data.chat_id) {
        sessionStorage.setItem('chat_id', data.chat_id);
        storedChatId = data.chat_id; // Update variable for later use
      }

      // Update the last message with the response
      setMessages(prev =>
        prev.map((msg, index) =>
          index === prev.length - 1 ? { ...msg, answer: data.answer || 'Try Again!' } : msg,
        ),
      );
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev =>
        prev.map((msg, index) =>
          index === prev.length - 1 ? { ...msg, answer: 'Try Again!' } : msg,
        ),
      );
    }
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
        {messages.length === 0
          ? (
              <div className="flex size-full items-center justify-center text-center text-xl text-gray-400">
                Start a new chat
              </div>
            )
          : (
              messages.flatMap((msg, index) => [
                // Render User's Question
                <div key={`${index}-question`} className="animate-fade-in flex w-full justify-end sm:px-24">
                  <div className="text-md relative max-w-[75%] rounded-xl rounded-br-none bg-blue-400 px-4 py-2 text-white shadow-md sm:max-w-[60%] md:max-w-[50%] lg:max-w-[40%] xl:max-w-[35%]">
                    {msg.question}
                    <span className="absolute -bottom-1 right-2 size-3 rotate-45 bg-blue-400" />
                  </div>
                </div>,

                // Render AI's Answer
                <div key={`${index}-answer`} className="animate-fade-in flex w-full justify-start sm:px-24">
                  <div className="text-md relative max-w-[75%] rounded-xl rounded-bl-none bg-gray-200 px-4 py-2 text-gray-800 shadow-md sm:max-w-[60%] md:max-w-[50%] lg:max-w-[40%] xl:max-w-[35%]">
                    {msg.answer}
                    <span className="absolute -bottom-1 left-2 size-3 rotate-45 bg-gray-200" />
                  </div>
                </div>,
              ])
            )}

        {/* This div ensures the chat auto-scrolls to the latest message */}
        <div ref={messagesEndRef} />
      </div>

      {/* Chat Input */}
      <div
        className={`transition-all duration-300 ${
          isSidebarOpen ? 'mx-auto w-[calc(100%-26rem)]' : 'left-0 w-full'
        }`}
        style={{
          position: messages.length === 0 ? 'absolute' : 'fixed', // Absolute for center, fixed for bottom
          bottom: messages.length === 0 ? '40%' : '0', // Center when no messages, bottom otherwise
          transform: messages.length === 0 ? 'translateY(100%)' : 'none', // Center vertically
        }}
      >
        <div className="mx-auto mb-10 flex max-w-2xl items-center rounded-lg border border-gray-500 bg-gray-200 p-1">
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
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

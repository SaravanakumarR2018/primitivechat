'use client';

import { useEffect, useState } from 'react';

type Message = {
  id: string;
  sender: string;
  text: string;
  timestamp: number;
};

// Utility function to generate a UUID
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

export default function Chat({ chatId, isSidebarOpen }: { chatId: string; isSidebarOpen: boolean }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isNewChat, setIsNewChat] = useState(true);

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

  useEffect(() => {
    if (messages.length > 0 && isNewChat) {
      sessionStorage.setItem(`chat-${chatId}`, JSON.stringify(messages));
      window.dispatchEvent(new Event('storage'));
      setIsNewChat(false);
    }
  }, [messages, chatId, isNewChat]);

  const sendMessage = () => {
    if (!input.trim()) {
      return;
    }

    const userMessage: Message = {
      id: generateUUID(),
      sender: 'user',
      text: input,
      timestamp: Date.now(),
    };

    const aiResponse: Message = {
      id: generateUUID(),
      sender: 'ai',
      text: 'This is a default AI response.',
      timestamp: Date.now(),
    };

    const newMessages = [...messages, userMessage, aiResponse];
    setMessages(newMessages);
    setInput('');

    // Update chat history in sessionStorage
    sessionStorage.setItem(`chat-${chatId}`, JSON.stringify(newMessages));
    window.dispatchEvent(new Event('storage'));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex h-screen flex-col text-white sm:bg-blue-200">
      {/* Chat messages */}
      <div className="flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`mx-auto mt-6 max-w-xs rounded-lg p-3 transition-all duration-300 ease-in-out ${
              msg.sender === 'user'
                ? 'bg-blue-400 text-white sm:mr-20'
                : 'bg-gray-400 text-white sm:ml-20'
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      {/* Chat input */}
      <div
        className={`mx-auto flex items-center justify-center p-4 transition-all duration-300 sm:mb-10 
    ${isSidebarOpen ? 'w-full sm:right-14 sm:min-w-[880px]' : 'right-40 w-full sm:left-48 sm:max-w-[900px]'}
  `}
        style={{
          width: `calc(100% - ${isSidebarOpen ? '20rem' : '0'})`,
        }}
      >
        <div className="fixed bottom-0 left-0 w-full bg-gray-800 p-4 sm:static sm:bg-transparent">
          <div className="mx-auto flex w-full max-w-[900px]">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              className="flex-1 rounded-md bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Type a message..."
            />
            <button
              type="button"
              title="Send Message"
              onClick={sendMessage}
              className="ml-2 flex items-center justify-center rounded-md bg-blue-500 p-3 text-white transition-transform hover:scale-110 hover:bg-blue-600"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="size-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

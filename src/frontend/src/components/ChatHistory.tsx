'use client';

import { useEffect, useState } from 'react';

export default function ChatHistory({
  onSelect,
  onNewChat,
  isSidebarOpen,
  onToggleSidebar,
}: {
  onSelect: (chatId: string) => void;
  onNewChat: () => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
}) {
  const [chats, setChats] = useState<{ id: string; preview: string }[]>([]);

  // Load chat history from sessionStorage
  const loadChats = () => {
    const savedChats = Object.keys(sessionStorage)
      .filter(key => key.startsWith('chat-'))
      .map((key) => {
        const messages = JSON.parse(sessionStorage.getItem(key) || '[]');
        const lastUserMessage = [...messages].reverse().find(msg => msg.sender === 'user');
        const lastTimestamp = messages.length ? messages[messages.length - 1].timestamp : 0;

        return {
          id: key.replace('chat-', ''),
          preview: lastUserMessage ? lastUserMessage.text.slice(0, 20) : 'New Chat',
          timestamp: lastTimestamp,
        };
      })
      .sort((a, b) => b.timestamp - a.timestamp);

    setChats(savedChats);
  };

  useEffect(() => {
    loadChats(); // Initial load
    const handleStorageChange = () => {
      loadChats(); // Load chats when sessionStorage is updated
    };
    window.addEventListener('storage', handleStorageChange);

    // Cleanup the event listener on unmount
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const handleDeleteChat = (chatId: string) => {
    sessionStorage.removeItem(`chat-${chatId}`);
    loadChats();
  };

  return (
    <>
      {/* Toggle Button (Only on Mobile) */}
      {!isSidebarOpen && (
        <button
          type="button"
          title="Open Chat History"
          onClick={onToggleSidebar}
          className="absolute left-5 top-20 z-50 rounded-lg bg-white p-2 shadow-md hover:bg-gray-300"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="size-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      )}

      {/* Chat Sidebar (Drawer on Mobile, Fixed on Desktop) */}
      <div
        className={`absolute left-0 z-40 h-screen w-80 bg-blue-50 shadow-lg transition-transform duration-300 sm:relative ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full sm:block'
        }`}
      >
        {/* Header Section */}
        <div className="flex items-center justify-between border-b bg-blue-50 px-4 py-3">
          {/* Left - Pencil Icon (New Chat) */}
          <button type="button" title="New Chat" onClick={onNewChat} className="rounded-lg p-2 hover:bg-gray-200">
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
                d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
              />
            </svg>
          </button>

          {/* Center - "Chat History" Title */}
          <h2 className="text-center text-lg font-semibold text-gray-700">Chat History</h2>

          {/* Right - Close Button (Only on Mobile) */}
          <button type="button" title="toggle" onClick={onToggleSidebar} className="rounded-lg p-2 hover:bg-gray-200">
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
          </button>
        </div>

        {/* Chat List */}
        <div className="flex-1 overflow-y-auto p-4">
          {chats.length === 0
            ? (
                <p className="text-center text-gray-500">No chat history</p>
              )
            : (
                <ul>
                  {chats.map(chat => (
                    <li
                      key={chat.id}
                      className="relative mb-2 flex items-center justify-between rounded-lg bg-gray-100 p-3 shadow-lg transition hover:bg-gray-300"
                    >
                      <button type="button" title="chat" className="flex-1 text-left text-gray-900" onClick={() => onSelect(chat.id)}>
                        {chat.preview}
                        ...
                      </button>
                      <button
                        type="button"
                        title="Delete Chat"
                        onClick={() => handleDeleteChat(chat.id)}
                        className="ml-2 text-gray-500 hover:text-red-500"
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
                            strokeWidth="2"
                            d="M10 6h4M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2M4 6h16M5 6v14a2 2 0 002 2h10a2 2 0 002-2V6H5z"
                          />
                        </svg>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
        </div>
      </div>
    </>
  );
}

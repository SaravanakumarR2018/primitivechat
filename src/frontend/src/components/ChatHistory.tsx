'use client';

import { useEffect, useState } from 'react';

export default function ChatHistory({
  onSelect,
  onNewChat,
  isSidebarOpen,
  onToggleSidebar,
  resetChat,
}: {
  onSelect: (chatId: string) => void;
  onNewChat: () => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  resetChat: () => void;
}) {
  const [chats, setChats] = useState<{ id: string; preview: string; timestamp: number }[]>([]);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    // Detect mobile screen width
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkScreenSize(); // Initial check
    window.addEventListener('resize', checkScreenSize); // Listen for screen size changes

    return () => {
      window.removeEventListener('resize', checkScreenSize);
    };
  }, []);

  useEffect(() => {
    // If on mobile, ensure sidebar is closed by default
    if (isMobile) {
      onToggleSidebar();
    }
  }, [isMobile]); // Run only when isMobile changes

  const loadChats = () => {
    const savedChats = Object.keys(sessionStorage)
      .filter(key => key.startsWith('chat-'))
      .map((key) => {
        try {
          const item = sessionStorage.getItem(key);
          if (!item) {
            return null;
          }

          // Skip if the item doesn't start with [ or { (not JSON)
          if (!(item.startsWith('[') || item.startsWith('{'))) {
            console.warn(`Skipping invalid chat data for key ${key}`);
            return null;
          }

          const messages = JSON.parse(item);

          if (!Array.isArray(messages) || messages.length === 0) {
            return null;
          }

          // Get the first question instead of looking for sender
          const firstMessage = messages[0];
          const preview = firstMessage?.question?.slice(0, 20) || 'New Chat';
          const timestamp = firstMessage?.timestamp || 0;

          return {
            id: key.replace('chat-', ''),
            preview,
            timestamp,
          };
        } catch (error) {
          console.error(`Error parsing chat data for key ${key}:`, error);
          return null;
        }
      })
      .filter(chat => chat !== null) as { id: string; preview: string; timestamp: number }[];

    const uniqueChats = Array.from(new Map(savedChats.map(chat => [chat.id, chat])).values());
    const sortedChats = uniqueChats.sort((a, b) => b.timestamp - a.timestamp);

    setChats(sortedChats);
  };

  useEffect(() => {
    loadChats();
    const handleStorageChange = () => loadChats();
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const handleDeleteChat = (chatId: string) => {
    sessionStorage.removeItem(`chat-${chatId}`);
    setChats(prevChats => prevChats.filter(chat => chat.id !== chatId));
    resetChat();
  };

  // Modified function to close the sidebar on mobile when "New Chat" is clicked
  const handleNewChat = () => {
    onNewChat();
    if (isMobile && isSidebarOpen) {
      onToggleSidebar(); // Close the sidebar only on mobile
    }
  };

  return (
    <>
      {/* Toggle Sidebar Button (Mobile) */}
      {!isSidebarOpen && (
        <button
          type="button"
          title="ToggleSidebar"
          onClick={onToggleSidebar}
          className="fixed left-2 top-20 z-50 rounded-lg bg-white p-2 shadow-md"
        >
          <svg
            className="size-7 text-gray-800 dark:text-white"
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            fill="none"
            viewBox="0 0 24 24"
          >
            <path
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="m6 10 1.99994 1.9999-1.99994 2M11 5v14m-7 0h16c.5523 0 1-.4477 1-1V6c0-.55228-.4477-1-1-1H4c-.55228 0-1 .44772-1 1v12c0 .5523.44772 1 1 1Z"
            />
          </svg>
        </button>
      )}

      {/* Toggle Sidebar Button (Mobile) */}
      {!isSidebarOpen && (
        <button
          type="button"
          title="NewChat"
          onClick={handleNewChat}
          className="fixed left-16 top-20 z-50 rounded-lg bg-white p-2 shadow-md"
        >
          <svg
            className="size-7 text-gray-800 dark:text-white"
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
            width="24"
            height="24"
            fill="none"
            viewBox="0 0 24 24"
          >
            <path
              stroke="currentColor"
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="m14.304 4.844 2.852 2.852M7 7H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-4.5m2.409-9.91a2.017 2.017 0 0 1 0 2.853l-6.844 6.844L8 14l.713-3.565 6.844-6.844a2.015 2.015 0 0 1 2.852 0Z"
            />
          </svg>
        </button>
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 top-16 z-50 mt-2 w-72 bg-white shadow-lg transition-transform duration-300 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ maxHeight: 'calc(100vh - 4rem)' }} // Prevent overflow
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b bg-gray-300 p-3">
          <button type="button" title="ToggleSidebar" onClick={onToggleSidebar} className="rounded-lg p-2 hover:bg-gray-100">
            <svg
              className="size-7 text-gray-800 dark:text-white"
              aria-hidden="true"
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="M8.99994 10 7 11.9999l1.99994 2M12 5v14M5 4h14c.5523 0 1 .44772 1 1v14c0 .5523-.4477 1-1 1H5c-.55228 0-1-.4477-1-1V5c0-.55228.44772-1 1-1Z"
              />
            </svg>
          </button>
          <h2 className="text-lg font-semibold">Chatbot</h2>
          <button type="button" title="NewChat" onClick={handleNewChat} className="rounded-lg p-2 hover:bg-gray-100">
            <svg
              className="size-7 text-gray-800 dark:text-white"
              aria-hidden="true"
              xmlns="http://www.w3.org/2000/svg"
              width="24"
              height="24"
              fill="none"
              viewBox="0 0 24 24"
            >
              <path
                stroke="currentColor"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth="2"
                d="m14.304 4.844 2.852 2.852M7 7H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-4.5m2.409-9.91a2.017 2.017 0 0 1 0 2.853l-6.844 6.844L8 14l.713-3.565 6.844-6.844a2.015 2.015 0 0 1 2.852 0Z"
              />
            </svg>
          </button>
        </div>

        {/* Chat List */}
        <div className="h-[calc(100vh-8rem)] overflow-y-auto border-t border-gray-400 bg-gray-300 p-4">
          {chats.length === 0
            ? (
                <p className="text-center text-gray-500">No chat history</p>
              )
            : (
                <ul>
                  {chats.map(chat => (
                    <li
                      key={chat.id}
                      className="mb-2 flex items-center justify-between rounded-lg bg-gray-200 p-2 hover:bg-gray-200"
                    >
                      <button
                        type="button"
                        title="Select Chat"
                        onClick={() => onSelect(chat.id)}
                        className="text-md flex-1 truncate text-left"
                      >
                        {chat.preview}
                        ...
                      </button>
                      <button
                        onClick={() => handleDeleteChat(chat.id)}
                        title="Delete Chat"
                        type="button"
                        className="text-gray-500 hover:text-red-500"
                      >
                        <svg
                          className="size-5"
                          aria-hidden="true"
                          xmlns="http://www.w3.org/2000/svg"
                          width="24"
                          height="24"
                          fill="none"
                          viewBox="0 0 24 24"
                        >
                          <path
                            stroke="currentColor"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M5 7h14m-9 3v8m4-8v8M10 3h4a1 1 0 0 1 1 1v3H9V4a1 1 0 0 1 1-1ZM6 7h12v13a1 1 0 0 1-1 1H7a1 1 0 0 1-1-1V7Z"
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

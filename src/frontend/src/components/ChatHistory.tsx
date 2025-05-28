/* eslint-disable ts/no-use-before-define */
/* eslint-disable react-hooks/exhaustive-deps */
'use client';

import { useOrganization } from '@clerk/nextjs';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useChat } from '@/context/ChatContext';
import { Ticket, ClipboardList, MessageSquare, Settings } from 'lucide-react';

interface GlobalSidebarProps {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

export default function ChatHistory({ isSidebarOpen, toggleSidebar }: GlobalSidebarProps) {
  const { newChat } = useChat();
  const {resetChat}=useChat();
  const pathname = usePathname();
  const router = useRouter();
  const [chats, setChats] = useState<{ id: string; preview: string; timestamp: number }[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const { organization } = useOrganization();

  useEffect(() => {
    if (!organization) {
      return;
    }
  }, [organization?.id]);

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
    if (isMobile && isSidebarOpen) {
      toggleSidebar(); // Close if currently open on mobile
    } else if (!isMobile && !isSidebarOpen) {
      toggleSidebar(); // Open if currently closed on desktop
    }
  }, [isMobile]);// Run only when isMobile changes

  const loadChats = () => {
    const savedChats = Object.keys(sessionStorage)
      .filter(key => key.startsWith('chat-'))
      .map((key) => {
        const messages = JSON.parse(sessionStorage.getItem(key) || '[]');

        if (messages.length === 0) {
          return null;
        }

        // Get the first user message instead of the last
        const firstUserMessage = messages.find((msg: { sender: string }) => msg.sender === 'user');
        const firstTimestamp = messages.length ? messages[0].timestamp : 0; // Get first message timestamp

        return {
          id: key.replace('chat-', ''),
          preview: firstUserMessage ? firstUserMessage.text.slice(0, 20) : 'New Chat',
          timestamp: firstTimestamp, // Use first message timestamp for sorting
        };
      })
      .filter(chat => chat !== null) as { id: string; preview: string; timestamp: number }[];

    const uniqueChats = Array.from(new Map(savedChats.map(chat => [chat.id, chat])).values());
    const sortedChats = uniqueChats.sort((a, b) => b.timestamp - a.timestamp); // Sort by first message timestamp

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
    newChat();
    if (!pathname.includes('/dashboard/chat')) router.push('/dashboard/chat');
    if (isMobile && isSidebarOpen) {
      toggleSidebar(); // Close the sidebar only on mobile
    }
  };

  const handleSelectChat = (chatId: string) => {
    router.push(`/dashboard/chat?chatId=${chatId}`);
    if (isMobile && isSidebarOpen) toggleSidebar();
  };

  return (
    <>

      {/* Sidebar */}
      <div className={`fixed inset-y-0 left-0 top-0 z-50 bg-gray-50 shadow-lg transition-transform duration-300 ${isSidebarOpen ? 'w-72' : 'hidden'}`}>
        {/* Header */}
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between p-3">
          <button type="button" title="ToggleSidebar" onClick={toggleSidebar} className="rounded-lg p-2 hover:bg-gray-100">
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

        {/* Navigation (Full only) */}
        <nav className="flex-1 p-4 space-y-6 ">
          <ul className="space-y-2">
            <li>
              <Link href="/dashboard/tickets" className={`flex items-center space-x-2 font-semibold p-2 rounded-lg transition-colors ${
    pathname === '/dashboard/tickets' ? 'bg-blue-300' : 'hover:bg-blue-100'}`}>
                <Ticket className="w-5 h-5" />
                <span>Tickets</span>
              </Link>
            </li>
            <li>
              <Link href="/dashboard/checkclerk" className={`flex items-center space-x-2 font-semibold p-2 rounded-lg transition-colors ${
    pathname === '/dashboard/checkclerk' ? 'bg-blue-300' : 'hover:bg-blue-100'}`}>
                <ClipboardList className="w-5 h-5" />
                <span>CheckClerk</span>
              </Link>
            </li>
            <li>
              <Link href="/dashboard/app-settings" className={`flex items-center space-x-2 font-semibold p-2 rounded-lg transition-colors ${
    pathname === '/dashboard/app-settings' ? 'bg-blue-300' : 'hover:bg-blue-100'}`}>
                <Settings className="w-5 h-5" />
                <span>App Settings</span>
              </Link>
            </li>
            <li>
              <Link href="/dashboard/chat" className={`flex items-center space-x-2 font-semibold p-2 rounded-lg transition-colors ${
    pathname === '/dashboard/chat' ? 'bg-blue-300' : 'hover:bg-blue-100'}`}>
                <MessageSquare className="w-5 h-5" />
                <span>Chat</span>
              </Link>
            </li>
          </ul>

        {/* Chat List */}
        <div className="overflow-y-auto pt-4">
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
                        onClick={() => handleSelectChat(chat.id)}
                        className="flex-1 truncate text-left text-base"
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
        </nav>
        </div>
      </div>
    </>
  );
}
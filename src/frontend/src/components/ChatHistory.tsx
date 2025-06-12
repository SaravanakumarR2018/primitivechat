/* eslint-disable no-console */
/* eslint-disable ts/no-use-before-define */
/* eslint-disable react-hooks/exhaustive-deps */
'use client';

import { useOrganization, useUser } from '@clerk/nextjs';
import { ClipboardList, MessageSquare, Settings, Ticket,FileText } from 'lucide-react';
import Link from 'next/link';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

import { useDashboardSidebar } from '@/features/dashboard/DashboardSidebarContext';

import { ChatHistorySkeleton } from './ui/Skeletons';

type NavLink = {
  href: string;
  label: string;
};

type ChatHistoryProps = {
  navLinks?: NavLink[];
  onSelect?: (chatId: string) => void;
  isSidebarOpen?: boolean;
  onToggleSidebar?: () => void;
  resetChat?: () => void;
  addChatToHistoryRef?: React.MutableRefObject<((chatId: string, message: string, timestamp?: number) => void) | null>;
};

const defaultNavLinks: NavLink[] = [];

export default function ChatHistory(props: ChatHistoryProps) {
  const { navLinks = defaultNavLinks } = props;
  // Use context for sidebar state and chat selection
  const {
    isSidebarOpen,
    toggleSidebar,
    setChatId,
    resetChat,
    chatId,
    addChatToHistoryRef,
  } = useDashboardSidebar();
  const [chats, setChats] = useState<{ id: string; preview: string; timestamp: number }[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const [loading, setLoading] = useState(false); // <-- Add loading state
  const [deletingChatId, setDeletingChatId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [fetchingMore, setFetchingMore] = useState(false);
  const PAGE_SIZE = 30;
  const { organization } = useOrganization();
  const { user } = useUser();
  const router = useRouter();
  const pathname = usePathname();
  const chatRefs = useRef<{ [key: string]: HTMLLIElement | null }>({});
  const [highlightVersion, setHighlightVersion] = useState(0);
  const searchParams = useSearchParams();

  useEffect(() => {
    if (!organization || !user) {
      return;
    }
    setLoading(true); // Start loading when initializing
    initializeChats().finally(() => setLoading(false));
  }, [organization?.id, user?.id]);

  useEffect(() => {
    setHighlightVersion(v => v + 1);
  }, [chatId]);
  useEffect(() => {
    setHighlightVersion(v => v + 1);
  }, [isSidebarOpen]);

  useEffect(() => {
    const chatId = searchParams.get('chat_id');
    console.log('Chat ID from URL:', chatId);
    if (chatId) {
      setChatId(chatId);
    }
  }, [searchParams]);

  // Scroll selected chat into view when sidebar opens
  useEffect(() => {
    if (isSidebarOpen && chatId && chatRefs.current[chatId]) {
      chatRefs.current[chatId]?.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
  }, [isSidebarOpen, chatId, chats.length]);

  // Infinite scroll handler
  useEffect(() => {
    if (loading || !hasMore) {
      return;
    }
    const container = document.getElementById('chat-history-scroll');
    if (!container) {
      return;
    }
    const handleScroll = () => {
      if (
        container.scrollTop + container.clientHeight >= container.scrollHeight - 40
        && !fetchingMore && hasMore
      ) {
        fetchMoreChats();
      }
    };
    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [loading, hasMore, fetchingMore, page]);

  // Fetch more chat ids/pages
  const fetchMoreChats = async () => {
    setFetchingMore(true);
    try {
      const nextPage = page + 1;
      const res = await fetch(`/api/backend/getallchatids?page=${nextPage}&page_size=${PAGE_SIZE}`);
      const data = await res.json();
      const chatIds = data.chat_ids || [];
      const more = data.hasMore !== undefined ? data.hasMore : chatIds.length === PAGE_SIZE;
      // Store has_more in sessionStorage for persistence
      if (organization?.id && user?.id) {
        sessionStorage.setItem(`${organization.id}-${user.id}-has_more`, JSON.stringify(more));
      }
      await Promise.all(
        chatIds.map(async (chatId: string) => {
          const res = await fetch(`/api/backend/getallchats?chat_id=${chatId}&page=1&page_size=60`);
          const chatData = await res.json();
          if (chatData?.messages?.length) {
            const key = `${chatId}-${organization?.id}-${user?.id}`;
            const normalizedMessages = chatData.messages.map((msg: any) => ({
              message: msg.message,
              sender_type: msg.sender_type,
              id: crypto.randomUUID(),
              timestamp: typeof msg.timestamp === 'string'
                ? new Date(msg.timestamp).getTime()
                : msg.timestamp ?? Date.now(),
            }));
            sessionStorage.setItem(key, JSON.stringify({
              chatId,
              messages: normalizedMessages,
              createdAt: Date.now(),
            }));
          }
        }),
      );
      loadChatsFromStorage();
      setPage(nextPage);
      setHasMore(more);
    } catch {
      setHasMore(false);
    } finally {
      setFetchingMore(false);
    }
  };

  const initializeChats = async () => {
    setPage(1);
    // Try to restore hasMore from sessionStorage
    let restoredHasMore = true;
    if (organization?.id && user?.id) {
      const stored = sessionStorage.getItem(`${organization.id}-${user.id}-has_more`);
      if (stored !== null) {
        try {
          restoredHasMore = JSON.parse(stored);
        } catch {}
      }
    }
    setHasMore(restoredHasMore);
    const chatKeys = Object.keys(sessionStorage).filter(key => key.includes(`-${organization?.id}-${user?.id}`));
    if (chatKeys.length > 0) {
      loadChatsFromStorage(chatKeys);
    } else {
      try {
        const res = await fetch(`/api/backend/getallchatids?page=1&page_size=${PAGE_SIZE}`);
        const data = await res.json();
        const chatIds = data.chat_ids || [];
        const more = data.hasMore !== undefined ? data.hasMore : chatIds.length === PAGE_SIZE;
        // Store has_more in sessionStorage for persistence
        if (organization?.id && user?.id) {
          sessionStorage.setItem(`${organization.id}-${user.id}-has_more`, JSON.stringify(more));
        }
        await Promise.all(
          chatIds.map(async (chatId: string) => {
            const res = await fetch(`/api/backend/getallchats?chat_id=${chatId}&page=1&page_size=60`);
            const chatData = await res.json();
            if (chatData?.messages?.length) {
              const key = `${chatId}-${organization?.id}-${user?.id}`;
              const normalizedMessages = chatData.messages.map((msg: any) => ({
                message: msg.message,
                sender_type: msg.sender_type,
                id: crypto.randomUUID(),
                timestamp: typeof msg.timestamp === 'string'
                  ? new Date(msg.timestamp).getTime()
                  : msg.timestamp ?? Date.now(),
              }));
              sessionStorage.setItem(key, JSON.stringify({
                chatId,
                messages: normalizedMessages,
                createdAt: Date.now(),
              }));
            }
          }),
        );
        loadChatsFromStorage();
        setHasMore(more);
      } catch (error) {
        setHasMore(false);
        console.error('Failed to fetch chats:', error);
      }
    }
  };

  const loadChatsFromStorage = (keys?: string[]) => {
    const storageKeys = keys || Object.keys(sessionStorage).filter(key => key.includes(`-${organization?.id}-${user?.id}`));

    const savedChats = storageKeys.map((key) => {
      const data = JSON.parse(sessionStorage.getItem(key) || '{}');
      const messages = data.messages || [];

      if (messages.length === 0) {
        return null;
      }

      const preview
  = (messages.find((m: any) => m.sender_type === 'customer')?.message?.slice(0, 20))
  || 'New Chat';

      const firstTimestamp = messages.length
        ? messages[0].timestamp || messages[0].createdAt || Date.now()
        : Date.now();

      return {
        id: data.chatId, // ✅ real chatId stored in session
        preview,
        timestamp: firstTimestamp,
      };
    }).filter((chat): chat is { id: string; preview: string; timestamp: number } => chat !== null);

    const uniqueChats = Array.from(new Map(savedChats.map(chat => [chat.id, chat])).values());
    const sortedChats = uniqueChats.sort((a, b) => {
      return b.timestamp - a.timestamp;
    });

    setChats(sortedChats);
  };
  useEffect(() => {
    // Detect mobile screen width
    const checkScreenSize = () => {
      setIsMobile(window.innerWidth < 768);
    };

    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  useEffect(() => {
    if (isMobile && isSidebarOpen) {
      toggleSidebar();
    } else if (!isMobile && !isSidebarOpen) {
      toggleSidebar();
    }
  }, [isMobile]);

  const handleDeleteChat = async (chatId: string) => {
    if (!organization || !user) {
      return;
    }
    setDeletingChatId(chatId); // Set which chat is being deleted
    try {
      const res = await fetch('/api/backend/deleteChat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chat_id: chatId }),
      });
      const data = await res.json();
      if (res.ok) {
        const keyPrefix = `${chatId}-${organization.id}-${user.id}`;
        Object.keys(sessionStorage).forEach((key) => {
          if (key.startsWith(keyPrefix)) {
            sessionStorage.removeItem(key);
          }
        });
        setChats(prevChats => prevChats.filter(chat => chat.id !== chatId));
        resetChat();
      } else {
        console.error('Failed to delete chat:', data?.error || data);
      }
    } catch (err) {
      console.error('Error deleting chat:', err);
    } finally {
      setDeletingChatId(null); // Reset after delete
    }
  };

  const handleNewChat = () => {
    resetChat();
    router.push('/dashboard/chat'); // Always navigate to chat page
    // No need to set selectedChatId, it's derived from the URL
    if (isMobile && isSidebarOpen) {
      toggleSidebar();
    }
  };

  // Add chat to history immediately after first message is sent
  const addChatToHistory = (
    chatId: string,
    message: string,
    timestamp?: number,
    updateUrl?: boolean, // <-- new param
  ) => {
    if (!organization || !user) {
      return;
    }

    const key = `${chatId}-${organization.id}-${user.id}`;
    const preview = (message?.split('\n')[0] || '').slice(0, 50);
    const now = timestamp || Date.now();

    // Check for an existing chat entry.
    const existingChatJSON = sessionStorage.getItem(key);
    if (existingChatJSON) {
      // Merge the existing chat with updated preview and timestamp.
      const existingChat = JSON.parse(existingChatJSON);
      existingChat.preview = preview;
      existingChat.updatedAt = now;
      sessionStorage.setItem(key, JSON.stringify(existingChat));
    } else {
      // Create a new chat record if none exists.
      const newChat = {
        chatId,
        preview,
        messages: [
          {
            sender_type: 'customer',
            message,
            timestamp: now,
          },
        ],
        createdAt: now,
        updatedAt: now,
      };
      sessionStorage.setItem(key, JSON.stringify(newChat));
    }

    // Update the component state so the sidebar reflects the change.
    setChats((prevChats) => {
      const exists = prevChats.some(c => c.id === chatId);
      if (exists) {
        return prevChats.map(c =>
          c.id === chatId ? { ...c, preview, timestamp: now } : c,
        );
      }
      return [{ id: chatId, preview, timestamp: now }, ...prevChats];
    });

    // Update URL with chat_id if requested (for new chat after first message)
    if (updateUrl && router) {
      router.push(`/dashboard/chat?chat_id=${chatId}`);
    }
  };

  // Expose the function to parent via ref if provided
  useEffect(() => {
    if (addChatToHistoryRef) {
      addChatToHistoryRef.current = (chatId, message, timestamp) =>
        addChatToHistory(chatId, message, timestamp, true);
    }
  }, [organization, user]);

  // Update: handle chat click to navigate to chat page with chat_id param
  const handleSelectChat = (id: string) => {
    router.push(`/dashboard/chat?chat_id=${id}`);
    setChatId(id);
    if (isMobile && isSidebarOpen) {
      toggleSidebar();
    }
  };

  return (
    <>
      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 top-16 z-50 mt-2 flex flex-col bg-white shadow-lg transition-all duration-300 ${
          isSidebarOpen ? 'w-72' : 'w-16'
        }`}
        style={{ maxHeight: 'calc(100vh - 4rem)' }}
      >
        {/* Header */}
        <div className={`flex items-center justify-between border-b bg-white p-3 transition-all duration-300 ${isSidebarOpen ? '' : 'flex-col justify-center space-y-2'}`}>
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
          {isSidebarOpen && <h2 className="ml-2 text-lg font-semibold">Chatbot</h2>}
          {isSidebarOpen && (
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
          )}
          {/* Show new chat button below toggle when sidebar is closed */}
          {!isSidebarOpen && (
            <button type="button" title="NewChat" onClick={handleNewChat} className="mt-2 rounded-lg p-2 hover:bg-gray-100">
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
        </div>

        {/* Sidebar Navigation Links (Resizable) */}
        <div
          className="max-h-[40vh] min-h-[56px] w-full min-w-0 resize-y overflow-auto overflow-x-hidden bg-white p-2"
          style={{ minHeight: 56, maxHeight: '40vh' }}
        >
          {navLinks.length > 0 && (
            <nav className="w-full min-w-0 overflow-x-hidden">
              <ul className="w-full min-w-0 space-y-2">
                {navLinks.map((link) => {
                  let Icon = null;
                  if (link.href.includes('tickets')) {
                    Icon = Ticket;
                  } else if (link.href.includes('checkclerk')) {
                    Icon = ClipboardList;
                  } else if (link.href.includes('app-settings')) {
                    Icon = Settings;
                  } else if (link.href.includes('documents')) {
                    Icon = FileText;  
                  } else if (link.href.includes('chat')) {
                    Icon = MessageSquare;
                  }
                  const isActive = pathname === link.href;
                  return (
                    <li key={link.href} className="w-full min-w-0">
                      <Link
                        href={link.href}
                        onClick={(e) => {
                          if (link.href.includes('/dashboard/chat')) {
                            e.preventDefault();
                            resetChat();
                            router.push('/dashboard/chat');
                            if (isMobile && isSidebarOpen) {
                              toggleSidebar();
                            }
                          }
                        }}
                        className="w-full min-w-0"
                        style={{ minWidth: 0 }}
                      >
                        <div
                          className={`group flex min-h-[40px] w-full min-w-0 items-center space-x-2 overflow-x-hidden rounded-lg p-2 font-semibold transition-colors
                            ${isActive ? 'bg-blue-400 shadow-md' : 'text-gray-700 hover:bg-blue-100'}
                            ${!isSidebarOpen ? 'justify-center' : ''}
                          `}
                        >
                          <span className="flex min-w-[32px] items-center justify-center">
                            {Icon && <Icon className={`size-6 ${isMobile ? 'size-2' : ''}`} />}
                          </span>
                          {isSidebarOpen && (
                            <span className="w-full truncate text-base">{link.label}</span>
                          )}
                        </div>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </nav>
          )}
        </div>

        {/* Chat List fills remaining space */}
        {isSidebarOpen && (
          <div
            id="chat-history-scroll"
            className={`relative flex-1 overflow-y-auto p-4 transition-all duration-300 ${isSidebarOpen ? '' : 'hidden'}${isSidebarOpen ? '' : ' p-1'}`}
            style={{ minHeight: 0 }}
          >
            {loading && (
              <ChatHistorySkeleton />
            )}
            {!loading && (chats.length === 0
              ? (<p className="text-center text-gray-500">No chat history</p>)
              : (
                  <ul>
                    {chats.map((chat) => {
                      console.log(
                        'chat.id:',
                        chat.id,
                        typeof chat.id,
                        'selectedChatId:',
                        chatId,
                        typeof chatId,
                        'equal:',
                        String(chat.id).trim() === String(chatId).trim(),
                      );
                      return (
                        <li
                          key={`${chat.id}-${highlightVersion}`}
                          ref={(el) => {
                            chatRefs.current[chat.id] = el;
                          }}
                          className={`mb-2 flex items-center justify-between rounded-lg transition-all duration-300 hover:bg-blue-200 ${isSidebarOpen ? 'p-2' : 'p-1'} ${chat.id.trim() === chatId?.trim() ? 'bg-blue-300' : 'bg-white'}`}
                        >
                          <button
                            type="button"
                            title="Select Chat"
                            onClick={() => handleSelectChat(chat.id)}
                            className={`flex-1 truncate text-left text-base ${isSidebarOpen ? '' : 'sr-only'}`}
                          >
                            {chat.preview}
                            ...
                          </button>
                          <button
                            onClick={() => handleDeleteChat(chat.id)}
                            title="Delete Chat"
                            type="button"
                            className={`ml-2 flex items-center justify-center text-gray-500 hover:text-red-500${deletingChatId === chat.id ? ' cursor-not-allowed opacity-60' : ''} ${isSidebarOpen ? '' : 'sr-only'}`}
                            disabled={deletingChatId === chat.id}
                          >
                            {deletingChatId === chat.id
                              ? (
                                  <svg className="size-5 animate-spin text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                                  </svg>
                                )
                              : (
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
                                )}
                          </button>
                        </li>
                      );
                    })}
                    {fetchingMore && (
                      <li className="flex justify-center py-2">
                        <svg className="size-6 animate-spin text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                        </svg>
                      </li>
                    )}
                  </ul>
                )
            )}
          </div>
        )}
      </div>
      {/* Toggle Sidebar Button (Mobile) */}
      {isMobile && !isSidebarOpen && (
        <button
          type="button"
          title="ToggleSidebar"
          onClick={toggleSidebar}
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
    </>
  );
}

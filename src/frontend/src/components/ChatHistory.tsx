'use client';

import { useOrganization } from '@clerk/nextjs';
import { useCallback, useEffect, useRef, useState } from 'react';

async function fetchChatIds(page: number = 1, pageSize: number = 15, orgId: string) {
  const res = await fetch(`/api/backend/getallchatids?page=${page}&page_size=${pageSize}&org_id=${orgId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch chat ids');
  }
  const data = await res.json();
  return {
    chatIds: data.chat_ids || [],
    hasMore: data.has_more ?? (data.chat_ids?.length === pageSize),
  };
}

async function fetchChatMessages(chatId: string, orgId: string) {
  const res = await fetch(`/api/backend/getallchats?chat_id=${chatId}&org_id=${orgId}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch messages for chat ${chatId}`);
  }
  const data = await res.json();

  return (data.messages || []).map((msg: any) => ({
    question: msg.sender_type === 'customer' ? msg.message : undefined,
    answer: msg.sender_type === 'system' ? msg.message : undefined,
    message: msg.message,
    sender_type: msg.sender_type,
    timestamp: new Date(msg.timestamp).getTime() || Date.now(),
  }));
}

type ChatHistoryProps = {
  onSelect: (chatId: string) => void;
  onNewChat: () => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  resetChat: () => void;
  currentChatId?: string;
  currentMessages?: any[];
};

export default function ChatHistory({
  onSelect,
  onNewChat,
  isSidebarOpen,
  onToggleSidebar,
  resetChat,
  currentChatId,
  currentMessages,
}: ChatHistoryProps) {
  const { organization } = useOrganization();
  const orgId = organization?.id;
  const [chats, setChats] = useState<{ id: string; preview: string; timestamp: number }[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [initialLoad, setInitialLoad] = useState(true);
  const chatListRef = useRef<HTMLDivElement>(null);

  // Check for mobile view
  useEffect(() => {
    const checkScreenSize = () => setIsMobile(window.innerWidth < 768);
    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  // Load chats from session storage
  const loadChats = useCallback(() => {
    if (!orgId) {
      setChats([]);
      return;
    }

    const savedChats = Object.keys(sessionStorage)
      .filter(key => key.startsWith(`chat-${orgId}-`))
      .map((key) => {
        try {
          const item = sessionStorage.getItem(key);
          if (!item) {
            return null;
          }

          const messages = JSON.parse(item);
          if (!Array.isArray(messages)) {
            return null;
          }

          // Find the last user message (either question or customer message)
          const lastUserMessage = [...messages].reverse().find(msg =>
            msg.question || msg.sender_type === 'customer',
          );

          const preview = lastUserMessage?.question
            || (lastUserMessage?.sender_type === 'customer' ? lastUserMessage.message : '')
            || 'New Chat';

          return {
            id: key.replace(`chat-${orgId}-`, ''),
            preview: preview.length > 20 ? `${preview.substring(0, 20)}...` : preview,
            timestamp: lastUserMessage?.timestamp || messages[messages.length - 1]?.timestamp || 0,
          };
        } catch {
          return null;
        }
      })
      .filter(Boolean) as { id: string; preview: string; timestamp: number }[];

    const sortedChats = [...new Map(savedChats.map(chat => [chat.id, chat]))].map(([_, chat]) => chat)
      .sort((a, b) => b.timestamp - a.timestamp);

    setChats(sortedChats);
  }, [orgId]);

  // Update chats when current messages change
  useEffect(() => {
    if (currentChatId && currentMessages && currentMessages.length > 0 && orgId) {
      const completeMessages = currentMessages.filter(m => m.question || m.answer);
      if (completeMessages.length > 0) {
        sessionStorage.setItem(`chat-${orgId}-${currentChatId}`, JSON.stringify(completeMessages));
        loadChats();
      }
    }
  }, [currentChatId, currentMessages, orgId, loadChats]);

  // Load more chats from API
  const loadMoreChats = useCallback(async () => {
    if (!orgId || isLoading || !hasMore) {
      return;
    }

    setIsLoading(true);
    try {
      const { chatIds, hasMore: moreAvailable } = await fetchChatIds(currentPage, 15, orgId);

      if (chatIds.length === 0) {
        setHasMore(false);
        return;
      }

      let loadedNewChats = false;
      for (const chatId of chatIds) {
        const storageKey = `chat-${orgId}-${chatId}`;
        if (!sessionStorage.getItem(storageKey)) {
          try {
            const messages = await fetchChatMessages(chatId, orgId);
            if (messages.length > 0) {
              sessionStorage.setItem(storageKey, JSON.stringify(messages));
              loadedNewChats = true;
            }
          } catch (err) {
            console.error(`Error loading chat ${chatId}:`, err);
          }
        }
      }

      if (loadedNewChats || chatIds.length > 0) {
        setCurrentPage(prev => prev + 1);
        setHasMore(moreAvailable);
        loadChats();
      } else {
        setHasMore(false);
      }
    } catch (err) {
      console.error('Error loading more chats:', err);
      setHasMore(false);
    } finally {
      setIsLoading(false);
      if (initialLoad) {
        setInitialLoad(false);
      }
    }
  }, [orgId, currentPage, isLoading, hasMore, loadChats, initialLoad]);

  // Reset and load chats when org changes
  useEffect(() => {
    if (orgId) {
      setChats([]);
      setCurrentPage(1);
      setHasMore(true);
      setInitialLoad(true);
      loadChats();
    }
  }, [orgId, loadChats]);

  // Infinite scroll handler
  useEffect(() => {
    if (!orgId) {
      return undefined;
    }

    if (initialLoad) {
      loadMoreChats();
    }

    const handleScroll = () => {
      if (!chatListRef.current || isLoading || !hasMore) {
        return;
      }
      const { scrollTop, scrollHeight, clientHeight } = chatListRef.current;
      if (scrollHeight - (scrollTop + clientHeight) < 100) {
        loadMoreChats();
      }
    };

    const chatList = chatListRef.current;
    if (chatList) {
      chatList.addEventListener('scroll', handleScroll);
      return () => chatList.removeEventListener('scroll', handleScroll);
    }

    return undefined;
  }, [orgId, loadMoreChats, isLoading, hasMore, initialLoad]);

  // Listen for chat updates from main chat component
  useEffect(() => {
    const handleChatUpdated = (e: CustomEvent) => {
      if (e.detail.orgId === orgId) {
        loadChats();
      }
    };

    window.addEventListener('chat-updated', handleChatUpdated as EventListener);
    return () => window.removeEventListener('chat-updated', handleChatUpdated as EventListener);
  }, [orgId, loadChats]);

  // Storage event listener for cross-tab sync
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key?.startsWith(`chat-${orgId}-`)) {
        loadChats();
      }
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, [orgId, loadChats]);

  const handleDeleteChat = (chatId: string) => {
    if (!orgId) {
      return;
    }

    sessionStorage.removeItem(`chat-${orgId}-${chatId}`);
    setChats(prev => prev.filter(chat => chat.id !== chatId));

    if (currentChatId === chatId) {
      resetChat();
    }
  };

  const handleNewChat = () => {
    onNewChat();
    if (isMobile) {
      onToggleSidebar();
    }
  };

  return (
    <>
      {!isSidebarOpen && (
        <div className="fixed left-2 top-20 z-50 flex gap-2">
          <button
            type="button"
            title="ToggleSidebar"
            onClick={onToggleSidebar}
            className="rounded-lg bg-white p-2 shadow-md"
          >
            <svg className="size-7 text-gray-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m6 10 2 2-2 2M11 5v14m-7 0h16c.55 0 1-.45 1-1V6c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v12c0 .55.45 1 1 1Z" />
            </svg>
          </button>
          <button
            type="button"
            title="NewChat"
            onClick={handleNewChat}
            className="rounded-lg bg-white p-2 shadow-md"
          >
            <svg className="size-7 text-gray-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m14.3 4.8 2.85 2.85M7 7H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-4.5M18.26 2.89a2.02 2.02 0 0 1 0 2.85L11.42 12.58 8.71 14l.71-3.56L16.26 3.11a2.02 2.02 0 0 1 2.85 0Z" />
            </svg>
          </button>
        </div>
      )}

      <div
        className={`fixed inset-y-0 left-0 top-16 z-50 mt-2 w-72 bg-white shadow-lg transition-transform duration-300 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ maxHeight: 'calc(100vh - 4rem)' }}
      >
        <div className="flex items-center justify-between border-b bg-gray-300 p-3">
          <button type="button" title="onToggleSidebar" onClick={onToggleSidebar} className="rounded-lg p-2 hover:bg-gray-100">
            <svg className="size-7 text-gray-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 10 7 12l2 2M12 5v14M5 4h14c.55 0 1 .45 1 1v14c0 .55-.45 1-1 1H5c-.55 0-1-.45-1-1V5c0-.55.45-1 1-1Z" />
            </svg>
          </button>
          <h2 className="text-lg font-semibold">Chat History</h2>
          <button type="button" title="handleNewChat" onClick={handleNewChat} className="rounded-lg p-2 hover:bg-gray-100">
            <svg className="size-7 text-gray-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="m14.3 4.8 2.85 2.85M7 7H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-4.5M18.26 2.89a2.02 2.02 0 0 1 0 2.85L11.42 12.58 8.71 14l.71-3.56L16.26 3.11a2.02 2.02 0 0 1 2.85 0Z" />
            </svg>
          </button>
        </div>

        <div
          ref={chatListRef}
          className="h-[calc(100vh-8rem)] overflow-y-auto border-t border-gray-400 bg-gray-300 p-4"
        >
          {!orgId
            ? (
                <p className="text-center text-gray-500">Please select an organization</p>
              )
            : initialLoad
              ? (
                  <div className="flex justify-center py-4">
                    <div className="size-8 animate-spin rounded-full border-4 border-gray-400 border-t-blue-600"></div>
                  </div>
                )
              : chats.length === 0
                ? (
                    <p className="text-center text-gray-500">No chat history</p>
                  )
                : (
                    <>
                      <ul className="space-y-2">
                        {chats.map(chat => (
                          <li
                            key={chat.id}
                            className={`flex items-center justify-between rounded-lg p-2 hover:bg-gray-200 ${
                              currentChatId === chat.id ? 'bg-gray-200' : 'bg-gray-100'
                            }`}
                          >
                            <button
                              type="button"
                              onClick={() => {
                                onSelect(chat.id);
                                if (isMobile) {
                                  onToggleSidebar();
                                }
                              }}
                              className="flex-1 truncate text-left text-sm"
                              title={chat.preview.length > 20 ? chat.preview : undefined}
                            >
                              {chat.preview}
                            </button>
                            <button
                              type="button"
                              onClick={() => handleDeleteChat(chat.id)}
                              className="text-gray-500 hover:text-red-500"
                              title="Delete chat"
                            >
                              <svg className="size-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 7h14m-9 3v8m4-8v8M10 3h4a1 1 0 0 1 1 1v3H9V4a1 1 0 0 1 1-1ZM6 7h12v13a1 1 0 0 1 1 1H7a1 1 0 0 1-1-1V7Z" />
                              </svg>
                            </button>
                          </li>
                        ))}
                      </ul>

                      {isLoading && (
                        <div className="flex justify-center py-4">
                          <div className="size-8 animate-spin rounded-full border-4 border-gray-400 border-t-blue-600"></div>
                        </div>
                      )}

                      {!hasMore && chats.length > 0 && (
                        <p className="py-2 text-center text-sm text-gray-500">No more chats to load</p>
                      )}
                    </>
                  )}
        </div>
      </div>
    </>
  );
}

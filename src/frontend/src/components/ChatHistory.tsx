/* eslint-disable no-console */
/* eslint-disable ts/no-use-before-define */
/* eslint-disable react-hooks/exhaustive-deps */
'use client';

import { useOrganization, useUser } from '@clerk/nextjs';
import { useEffect, useState } from 'react';

import { ChatHistorySkeleton } from './ui/Skeletons';

export default function ChatHistory({
  onSelect,
  onNewChat,
  isSidebarOpen,
  onToggleSidebar,
  resetChat,
  addChatToHistoryRef,
}: {
  onSelect: (chatId: string) => void;
  onNewChat: () => void;
  isSidebarOpen: boolean;
  onToggleSidebar: () => void;
  resetChat: () => void;
  addChatToHistoryRef?: React.MutableRefObject<((chatId: string, message: string, timestamp?: number) => void) | null>;
}) {
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

  useEffect(() => {
    if (!organization || !user) {
      return;
    }
    setLoading(true); // Start loading when initializing
    initializeChats().finally(() => setLoading(false));
  }, [organization?.id, user?.id]);

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
    setHasMore(true);
    const chatKeys = Object.keys(sessionStorage).filter(key => key.includes(`-${organization?.id}-${user?.id}`));
    if (chatKeys.length > 0) {
      loadChatsFromStorage(chatKeys);
    } else {
      try {
        const res = await fetch(`/api/backend/getallchatids?page=1&page_size=${PAGE_SIZE}`);
        const data = await res.json();
        const chatIds = data.chat_ids || [];
        const more = data.hasMore !== undefined ? data.hasMore : chatIds.length === PAGE_SIZE;
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
      onToggleSidebar();
    } else if (!isMobile && !isSidebarOpen) {
      onToggleSidebar();
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
    onNewChat();
    if (isMobile && isSidebarOpen) {
      onToggleSidebar();
    }
  };

  // Add chat to history immediately after first message is sent
  const addChatToHistory = (
    chatId: string,
    message: string,
    timestamp?: number,
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
      // Optionally add or update a field (like updatedAt) if you need that:
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
  };

  // Expose the function to parent via ref if provided
  useEffect(() => {
    if (addChatToHistoryRef) {
      addChatToHistoryRef.current = addChatToHistory;
    }
  }, [organization, user]);

  return (
    <>
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
        <div id="chat-history-scroll" className="relative h-[calc(100vh-8rem)] overflow-y-auto border-t border-gray-400 bg-gray-300 p-4">
          {loading && (
            <ChatHistorySkeleton />
          )}
          {!loading && (chats.length === 0
            ? (<p className="text-center text-gray-500">No chat history</p>)
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
                        className="flex-1 truncate text-left text-base"
                      >
                        {chat.preview}
                        ...
                      </button>
                      <button
                        onClick={() => handleDeleteChat(chat.id)}
                        title="Delete Chat"
                        type="button"
                        className={`ml-2 flex items-center justify-center text-gray-500 hover:text-red-500${deletingChatId === chat.id ? ' cursor-not-allowed opacity-60' : ''}`}
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
                  ))}
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
      </div>
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
    </>
  );
}

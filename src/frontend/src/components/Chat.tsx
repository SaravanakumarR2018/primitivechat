'use client';

import { useOrganization } from '@clerk/nextjs';
import { useCallback, useEffect, useRef, useState } from 'react';

type Message = {
  id: string;
  question?: string;
  answer?: string;
  message?: string;
  sender_type?: string;
  timestamp: number;
};

export default function Chat({
  chatId,
  setChatId,
  isSidebarOpen,
}: {
  chatId: string;
  setChatId: (id: string) => void;
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}) {
  const { organization } = useOrganization();
  const orgId = organization?.id;

  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingOlder, setIsLoadingOlder] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const shouldAutoScroll = useRef(false);
  const currentChatIdRef = useRef<string | null>(null);
  const currentOrgIdRef = useRef<string | null>(null);
  const [storedChatId, setStoredChatId] = useState<string | undefined>(undefined);

  const emitChatUpdateEvent = useCallback(() => {
    if (orgId && (storedChatId || chatId)) {
      const event = new CustomEvent('chat-updated', {
        detail: {
          orgId,
          chatId: storedChatId || chatId,
          lastMessage: messages[messages.length - 1]?.timestamp || Date.now(),
        },
      });
      window.dispatchEvent(event);
    }
  }, [orgId, storedChatId, chatId, messages]);

  useEffect(() => {
    if (orgId !== currentOrgIdRef.current || chatId !== currentChatIdRef.current) {
      setMessages([]);
      setInput('');
      setPage(1);
      setHasMore(true);
      currentChatIdRef.current = chatId;
      currentOrgIdRef.current = orgId || null;
      if (orgId && chatId) {
        sessionStorage.removeItem(`chat-${orgId}-${chatId}`);
      }
    }
  }, [chatId, orgId]);

  const updateSessionStorage = (allMessages: Message[]) => {
    if (!orgId || !chatId) {
      return;
    }
    sessionStorage.setItem(`chat-${orgId}-${chatId}`, JSON.stringify(allMessages));
    emitChatUpdateEvent();
  };

  const loadMessages = useCallback(async (loadType: 'initial' | 'more') => {
    const currentOrg = currentOrgIdRef.current;
    const currentChat = currentChatIdRef.current;

    if (!currentChat || !currentOrg || (loadType === 'initial' ? isLoading : isLoadingOlder) || (loadType === 'more' && !hasMore)) {
      return;
    }

    if (loadType === 'initial') {
      setIsLoading(true);
    } else {
      setIsLoadingOlder(true);
    }

    try {
      const pageToLoad = loadType === 'initial' ? 1 : page + 1;

      if (loadType === 'initial') {
        const cachedMessages = sessionStorage.getItem(`chat-${currentOrg}-${currentChat}`);
        const savedSessionId = sessionStorage.getItem(`chat-session-${currentOrg}-${currentChat}`);

        if (savedSessionId) {
          setStoredChatId(savedSessionId);
        }

        if (cachedMessages) {
          const parsedMessages = JSON.parse(cachedMessages) as Message[];
          setMessages(parsedMessages.sort((a, b) => a.timestamp - b.timestamp));
          return;
        }
      }

      const res = await fetch(`/api/backend/getallchats?chat_id=${currentChat}&page=${pageToLoad}&page_size=10&org_id=${currentOrg}`);
      const data = await res.json();
      const newMessages = data.messages || [];

      if (currentOrg === currentOrgIdRef.current && currentChat === currentChatIdRef.current) {
        const transformedMessages = newMessages.map((msg: any) => ({
          id: `${currentOrg}-${currentChat}-${msg.timestamp || Date.now()}-${msg.sender_type}`,
          question: msg.sender_type === 'customer' ? msg.message : undefined,
          answer: msg.sender_type === 'system' ? msg.message : undefined,
          message: msg.message,
          sender_type: msg.sender_type,
          timestamp: new Date(msg.timestamp).getTime() || Date.now(),
        }));

        setMessages((prev) => {
          const existingIds = new Set(prev.map(m => m.id));
          const uniqueNewMessages = transformedMessages.filter((m: Message) => !existingIds.has(m.id));
          const updatedMessages = loadType === 'initial' ? [...uniqueNewMessages] : [...uniqueNewMessages, ...prev];

          updateSessionStorage(updatedMessages.sort((a, b) => a.timestamp - b.timestamp));
          return updatedMessages.sort((a, b) => a.timestamp - b.timestamp);
        });

        setPage(pageToLoad);
        setHasMore(data.has_more ?? newMessages.length === 10);

        if (loadType === 'initial') {
          shouldAutoScroll.current = true;
        }
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      if (currentOrg === currentOrgIdRef.current && currentChat === currentChatIdRef.current) {
        if (loadType === 'initial') {
          setIsLoading(false);
        } else {
          setIsLoadingOlder(false);
        }
      }
    }
  }, [page, hasMore, isLoading, isLoadingOlder, orgId, chatId]);

  // --- NO need to create chat separately here now ---
  useEffect(() => {
    if (orgId && chatId) {
      loadMessages('initial');
    }
  }, [chatId, orgId, loadMessages]);

  useEffect(() => {
    const container = chatContainerRef.current;
    if (!container) {
      return;
    }

    const handleScroll = () => {
      if (container.scrollTop < 100 && !isLoadingOlder && hasMore && chatId === currentChatIdRef.current && orgId === currentOrgIdRef.current) {
        loadMessages('more');
      }
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [loadMessages, isLoadingOlder, hasMore, chatId, orgId]);

  useEffect(() => {
    if (shouldAutoScroll.current && messagesEndRef.current && chatId === currentChatIdRef.current && orgId === currentOrgIdRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
      shouldAutoScroll.current = false;
    }
  }, [messages, chatId, orgId]);

  const sendMessage = async () => {
    const currentOrg = currentOrgIdRef.current;
    const currentChat = currentChatIdRef.current;

    if (!input.trim() || !currentOrg || isLoading) {
      return;
    }

    const userMessage: Message = {
      id: `${currentOrg}-${currentChat || 'new'}-${Date.now()}-customer`,
      question: input,
      timestamp: Date.now(),
    };

    const tempResponse: Message = {
      id: `${currentOrg}-${currentChat || 'new'}-${Date.now() + 1}-system`,
      answer: '...',
      timestamp: Date.now() + 1,
    };

    setMessages(prev => [...prev, userMessage, tempResponse]);
    setInput('');
    setIsLoading(true);
    shouldAutoScroll.current = true;

    try {
      const bodyPayload = storedChatId
        ? { message: input, chatId: storedChatId }
        : { message: input };

      const response = await fetch('/api/backend/sendMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyPayload),
      });

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const data = await response.json();

      if (data.chat_id && (!storedChatId || data.chat_id !== storedChatId)) {
        setStoredChatId(data.chat_id);
        setChatId(data.chat_id);
        sessionStorage.setItem(`chat-session-${orgId}-${data.chat_id}`, data.chat_id);
        emitChatUpdateEvent();
      }

      setMessages((prev) => {
        const updated = prev.map(msg =>
          msg.id === tempResponse.id
            ? {
                ...msg,
                answer: data.message || data.answer || 'Try Again!',
                timestamp: Date.now(),
              }
            : msg,
        );
        updateSessionStorage(updated);
        return updated;
      });

      emitChatUpdateEvent();
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => {
        const updated = prev.map(msg =>
          msg.id === tempResponse.id
            ? {
                ...msg,
                answer: 'Failed to get response. Please try again.',
                timestamp: Date.now(),
              }
            : msg,
        );
        updateSessionStorage(updated);
        return updated;
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !isLoading) {
      e.preventDefault();
      sendMessage();
    }
  };

  const sortedMessages = [...messages].sort((a, b) => a.timestamp - b.timestamp);

  return (
    <div className="flex h-screen flex-col pb-28 pt-24 sm:pt-12">
      <div ref={chatContainerRef} className="scrollbar-hide flex flex-1 flex-col items-center space-y-4 overflow-y-auto p-4 md:items-start">
        {isLoadingOlder && (
          <div className="w-full py-2 text-center text-gray-500">
            Loading older messages...
          </div>
        )}
        {!hasMore && page > 1 && (
          <div className="w-full py-2 text-center text-gray-500">
            No more messages to load
          </div>
        )}
        {sortedMessages.length === 0 && !isLoading
          ? (
              <div className="flex size-full items-center justify-center text-center text-xl text-gray-400">
                {chatId ? 'Start a new Chat' : 'Select a chat or start a new one'}
              </div>
            )
          : (
              sortedMessages.map(msg => (
                <div key={msg.id} className="w-full">
                  {msg.question && (
                    <div className="animate-fade-in flex w-full justify-end sm:px-24">
                      <div className="text-md relative max-w-[75%] rounded-xl rounded-br-none bg-blue-400 px-4 py-2 text-white shadow-md">
                        {msg.question}
                        <span className="absolute -bottom-1 right-2 size-3 rotate-45 bg-blue-400" />
                      </div>
                    </div>
                  )}
                  {msg.answer && (
                    <div className="animate-fade-in flex w-full justify-start sm:px-24">
                      <div className="text-md relative max-w-[75%] rounded-xl rounded-bl-none bg-gray-200 px-4 py-2 text-gray-800 shadow-md">
                        {msg.answer === '...'
                          ? (
                              <div className="flex space-x-1">
                                <div className="size-2 animate-bounce rounded-full bg-gray-600 [animation-delay:-0.3s]" />
                                <div className="size-2 animate-bounce rounded-full bg-gray-600 [animation-delay:-0.15s]" />
                                <div className="size-2 animate-bounce rounded-full bg-gray-600" />
                              </div>
                            )
                          : (
                              msg.answer
                            )}
                        <span className="absolute -bottom-1 left-2 size-3 rotate-45 bg-gray-200" />
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
        <div ref={messagesEndRef} />
      </div>

      <div
        className={`transition-all duration-300 ${isSidebarOpen ? 'mx-auto w-[calc(100%-26rem)]' : 'left-0 w-full'}`}
        style={{
          position: messages.length === 0 ? 'absolute' : 'fixed',
          bottom: messages.length === 0 ? '40%' : '0',
          transform: messages.length === 0 ? 'translateY(100%)' : 'none',
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
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            type="button"
            title="Send"
            className="rounded-lg bg-blue-500 p-2 text-white hover:bg-blue-600 disabled:bg-gray-400"
            disabled={isLoading || !input.trim()}
          >
            {isLoading
              ? (
                  <div className="size-6 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                )
              : (
                  <svg xmlns="http://www.w3.org/2000/svg" className="size-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                )}
          </button>
        </div>
      </div>
    </div>
  );
}

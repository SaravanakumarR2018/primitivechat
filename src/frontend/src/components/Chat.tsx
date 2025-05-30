/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable no-console */
'use client';

import 'highlight.js/styles/github.css';

import { useOrganization, useUser } from '@clerk/nextjs';
import { useCallback, useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import remarkGfm from 'remark-gfm';

type Message = {
  sender_type: 'customer' | 'system';
  message: string;
  id?: string;
  timestamp: number; // ✅ required now for ordering
};

export default function Chat({ chatId, addChatToHistoryRef }: { chatId: string; addChatToHistoryRef?: React.MutableRefObject<((chatId: string, message: string, timestamp?: number) => void) | null> }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const { organization } = useOrganization();
  const { user } = useUser();
  const scrollCooldownRef = useRef(false);
  const scrollRestoreRef = useRef<null | { previousScrollHeight: number }>(null);
  const isAppendingRef = useRef(false);
  // Load messages from sessionStorage
  useEffect(() => {
    const loadChat = () => {
      if (!chatId || !organization?.id || !user?.id) {
        setMessages([]);
        setCurrentChatId(null);
        return;
      }

      const orgId = organization.id;
      const userId = user.id;
      const key = `${chatId}-${orgId}-${userId}`;

      const savedChat = sessionStorage.getItem(key);

      if (savedChat) {
        const parsed = JSON.parse(savedChat);
        setMessages(parsed.messages || []);
        setCurrentChatId(chatId);
      } else {
        setMessages([]);
        setCurrentChatId(null);
      }
    };

    loadChat();
  }, [chatId, organization?.id, user?.id]);

  useEffect(() => {
    if (isAppendingRef.current) {
      isAppendingRef.current = false;
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    const handleResize = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);
  const count = 0;
  // Helper to fetch messages for a page
  const fetchMessages = useCallback(async (pageToFetch: number) => {
    if (!chatId || !organization?.id || !user?.id) {
      return { messages: [], has_more: false };
    }
    const res = await fetch(`/api/backend/getallchats?chat_id=${chatId}&page=${pageToFetch}&page_size=60`);
    console.log('call number', count + 1, pageToFetch);
    const data = await res.json();
    const msgs = (data.messages || []).map((msg: any) => ({
      message: msg.message,
      sender_type: msg.sender_type,
      id: crypto.randomUUID(),

      timestamp: typeof msg.timestamp === 'string'
        ? new Date(msg.timestamp).getTime()
        : msg.timestamp ?? Date.now(),
    }));
    const has_more = data.has_more ?? (msgs.length === 60);
    console.log('hasMore:', has_more);
    return { messages: msgs, has_more: data.has_more ?? (msgs.length === 60) };
  }, [chatId, organization?.id, user?.id]);

  // Load first page on chatId change
  useEffect(() => {
    let ignore = false;
    async function loadFirstPage() {
      const orgId = organization?.id;
      const userId = user?.id;
      const key = `${chatId}-${orgId}-${userId}`;
      const savedChat = sessionStorage.getItem(key);

      if (savedChat) {
        const parsed = JSON.parse(savedChat);
        setMessages(parsed.messages || []);
        setCurrentChatId(chatId);
        setPage(1);
        setHasMore(parsed.hasMore ?? true); // ✅ use saved hasMore value

        setLoadingMore(false); // ✅ ensure this is reset
        return;
      }

      setLoadingMore(true);
      const { messages: msgs, has_more } = await fetchMessages(1);
      if (!ignore) {
        setMessages(msgs);
        setHasMore(has_more);
        setPage(1);
      }
      setLoadingMore(false);

      scrollCooldownRef.current = true;
      setTimeout(() => {
        scrollCooldownRef.current = false;
      }, 500);
    }

    loadFirstPage();

    return () => {
      ignore = true;
    };
  }, [chatId, organization?.id, user?.id]);

  // Infinite scroll: fetch more when scrolled to top
  useEffect(() => {
    const container = scrollRef.current;
    if (!container) {
      return;
    }
    const handleScroll = async () => {
      const container = scrollRef.current;
      if (!container || scrollCooldownRef.current || loadingMore || !hasMore) {
        return;
      }

      if (container.scrollTop !== 0) {
        return;
      }

      setLoadingMore(true);

      const previousScrollHeight = container.scrollHeight;
      scrollRestoreRef.current = { previousScrollHeight };

      const nextPage = page + 1;
      const { messages: newMsgs, has_more } = await fetchMessages(nextPage);

      setMessages((prev) => {
        const prevIds = new Set(prev.map(m => m.id));
        const filtered = newMsgs.filter((m: { id: string | undefined }) => !prevIds.has(m.id));
        const updated = [...filtered, ...prev];

        const orgId = organization?.id;
        const userId = user?.id;
        if (orgId && userId && chatId) {
          const key = `${chatId}-${orgId}-${userId}`;
          const saved = sessionStorage.getItem(key);
          const sessionData = saved ? JSON.parse(saved) : {};
          sessionStorage.setItem(key, JSON.stringify({
            ...sessionData,
            chatId,
            messages: updated,
            hasMore: has_more, // ✅ persist hasMore here
            updatedAt: Date.now(),
          }));
        }

        return updated;
      });

      setHasMore(has_more);
      setPage(nextPage);
      setLoadingMore(false);
    };

    container.addEventListener('scroll', handleScroll);
    return () => container.removeEventListener('scroll', handleScroll);
  }, [hasMore, loadingMore, page, fetchMessages]);

  useEffect(() => {
    const container = scrollRef.current;
    const scrollData = scrollRestoreRef.current;
    if (!container || !scrollData?.previousScrollHeight) {
      return;
    }

    // Wait for DOM paint + layout completion
    requestAnimationFrame(() => {
      setTimeout(() => {
        const newScrollHeight = container.scrollHeight;
        const scrollDifference = newScrollHeight - scrollData.previousScrollHeight;
        container.scrollTop = scrollDifference;
        scrollRestoreRef.current = null;
      }, 0);
    });
  }, [messages]);

  const startNewChat = async (firstMessage: string) => {
    if (!firstMessage.trim()) {
      return;
    }

    const timestamp = Date.now();

    const userMessage: Message = {
      sender_type: 'customer',
      message: firstMessage,
      id: crypto.randomUUID(),
      timestamp,
    };

    const aiMessage: Message = {
      sender_type: 'system',
      message: '',
      id: crypto.randomUUID(),
      timestamp: timestamp + 1,
    };

    // Store user message initially
    isAppendingRef.current = true;
    setMessages([userMessage, aiMessage]);
    setInput('');
    setIsTyping(true);

    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await fetch('/api/backend/sendMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: firstMessage, stream: true }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error('Failed to start new chat');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let newChatId = '';
      let userId = '';
      const orgId = organization?.id || '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed === 'data: [DONE]') {
            continue;
          }

          if (trimmed.startsWith('data: ')) {
            try {
              const json = JSON.parse(trimmed.slice(6));

              if (json.chat_id && !newChatId) {
                newChatId = json.chat_id;
                setCurrentChatId(newChatId);
              }
              if (json.user_id && !userId) {
                userId = json.user_id;
              }

              const content = json.choices?.[0]?.delta?.content;
              if (content) {
                aiMessage.message += content;
                setMessages(prev => [...prev.slice(0, -1), { ...aiMessage }]);
              }
            } catch (e) {
              console.error('Stream parsing error:', e);
            }
          }
        }
      }

      // ✅ Save both messages **AFTER** the AI response has streamed completely
      if (newChatId && orgId && userId) {
        const key = `${newChatId}-${orgId}-${userId}`;
        sessionStorage.setItem(
          key,
          JSON.stringify({
            chatId: newChatId,
            messages: [userMessage, aiMessage], // now with the AI response included
            hasMore: false,
            createdAt: timestamp,
          }),
        );

        // Now update ChatHistory but let addChatToHistory merge the entry.
        if (addChatToHistoryRef?.current) {
          const preview = userMessage?.message?.split('\n')[0]?.slice(0, 50);
          addChatToHistoryRef.current(newChatId, preview || '', timestamp);
        }
        window.dispatchEvent(new Event('storage'));
      }
    } catch (err) {
      if (!(err instanceof Error && err.name === 'AbortError')) {
        console.error('New chat error:', err);
        setMessages(prev => prev.slice(0, -1)); // Remove broken AI message
      }
    } finally {
      setIsTyping(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) {
      return;
    }

    if (!currentChatId || messages.length === 0) {
      return startNewChat(input); // Only if no current chat OR no messages
    }

    const timestamp = Date.now();

    const userMessage: Message = {
      sender_type: 'customer',
      message: input,
      timestamp,
      id: crypto.randomUUID(),
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInput('');
    setIsTyping(true);

    const controller = new AbortController();
    controllerRef.current = controller;

    try {
      const response = await fetch('/api/backend/sendMessage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: input,
          stream: true,
          chat_id: currentChatId,
        }),
        signal: controller.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error('Stream failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      const aiMessage: Message = {
        id: crypto.randomUUID(),
        sender_type: 'system',
        message: '',
        timestamp: timestamp + 1,
      };

      let newChatId = currentChatId;
      let userId = '';
      const orgId = organization?.id || '';

      isAppendingRef.current = true;
      setMessages(prev => [...prev, aiMessage]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed === 'data: [DONE]') {
            continue;
          }

          if (trimmed.startsWith('data: ')) {
            try {
              const json = JSON.parse(trimmed.slice(6));

              if (json.chat_id && json.chat_id !== currentChatId) {
                newChatId = json.chat_id;
                setCurrentChatId(newChatId);
              }

              if (json.user_id) {
                userId = json.user_id;
              }

              const content = json.choices?.[0]?.delta?.content;
              if (content) {
                aiMessage.message += content;
                setMessages(prev => [...prev.slice(0, -1), { ...aiMessage }]);
              }
            } catch (e) {
              console.error('Stream parse error:', e);
            }
          }
        }
      }

      // ✅ Save to sessionStorage while preserving `hasMore`
      if (newChatId && orgId && userId) {
        const key = `${newChatId}-${orgId}-${userId}`;
        const old = sessionStorage.getItem(key);
        const parsed = old ? JSON.parse(old) : {};

        sessionStorage.setItem(key, JSON.stringify({
          ...parsed,
          chatId: newChatId,
          messages: [...newMessages, aiMessage],
          updatedAt: Date.now(),
        }));

        // ✅ Trigger sidebar update manually
        window.dispatchEvent(new Event('storage'));
      }
    } catch (err) {
      if (!(err instanceof Error && err.name === 'AbortError')) {
        console.error('Send error:', err);
        setMessages(prev => prev.slice(0, -1));
      }
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
    <div className="flex h-[calc(100vh-64px)] flex-col">
      <div className="mx-auto flex size-full max-w-4xl flex-1 flex-col">
        {messages.length === 0 && !isTyping
          ? (
              <div className="flex flex-1 flex-col items-center justify-center gap-6 px-4 text-center">
                <h2 className="text-2xl font-semibold text-gray-500">
                  Hello!! What can I help with?
                </h2>
                <div className="flex w-full max-w-xl items-center rounded-full border border-gray-300 bg-gray-100 px-4 py-3 shadow-sm">
                  <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 bg-transparent text-sm focus:outline-none"
                    placeholder="Type a message to begin..."
                  />
                  <button
                    type="button"
                    onClick={sendMessage}
                    className="ml-2 rounded-full bg-blue-500 p-2 text-white hover:bg-blue-600"
                  >
                    <svg className="size-5" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                      <path d="M5 12h14M12 5l7 7-7 7" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </button>
                </div>
              </div>
            )
          : (
              <>
                <div ref={scrollRef} className="mt-20 flex-1 space-y-4 overflow-y-auto px-4 pt-4">
                  {loadingMore && (
                    <div className="flex justify-center py-2">
                      <svg className="size-6 animate-spin text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                      </svg>
                    </div>
                  )}

                  {[...messages]
                    .sort((a, b) => {
                      const t1 = (a as any).timestamp || 0;
                      const t2 = (b as any).timestamp || 0;
                      return t1 - t2;
                    })
                    .map(msg => (

                      <div key={msg.id || crypto.randomUUID()} className={`flex w-full ${msg.sender_type === 'customer' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`prose prose-sm max-w-[85vw] whitespace-pre-wrap rounded-2xl p-3 shadow-md ${
                          msg.sender_type === 'customer'
                            ? 'rounded-br-none bg-blue-400 text-white'
                            : 'bg-gray-200 text-gray-800'
                        }`}
                        >
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight]}
                          >
                            {msg.message}
                          </ReactMarkdown>
                        </div>
                      </div>
                    ))}
                  {isTyping && (
                    <div className="flex w-full">
                      <span className="size-4 animate-pulse rounded-full bg-black shadow-md" />
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                <div className="sticky bottom-0 z-10 mx-auto mb-0 flex w-full max-w-xl items-center rounded-full border border-gray-300 bg-gray-100 px-4 py-3 shadow-sm">
                  <input
                    type="text"
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    className="flex-1 bg-transparent text-sm focus:outline-none"
                    placeholder="Type a message..."
                  />
                  <button
                    type="button"
                    onClick={isTyping ? stopStreaming : sendMessage}
                    className="ml-2 rounded-full bg-blue-500 p-2 text-white hover:bg-blue-600"
                  >
                    {isTyping
                      ? (
                          <svg className="size-5" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                            <path d="M6 18L18 6M6 6l12 12" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        )
                      : (
                          <svg className="size-5" viewBox="0 0 24 24" stroke="currentColor" fill="none">
                            <path d="M5 12h14M12 5l7 7-7 7" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        )}
                  </button>
                </div>
              </>
            )}
      </div>
    </div>
  );
}

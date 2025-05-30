'use client';

import { useRef, useState } from 'react';

import Chat from '@/components/Chat';
import ChatHistory from '@/components/ChatHistory';

export default function Page() {
  const [chatId, setChatId] = useState<string>(() => Date.now().toString());
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const addChatToHistoryRef = useRef<((chatId: string, message: string, timestamp?: number) => void) | null>(null);

  const handleNewChat = () => {
    setChatId(Date.now().toString());
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  const resetChat = () => {
    setChatId(Date.now().toString());
  };

  return (
    <div className="relative flex size-full bg-gray-100">
      {' '}
      {/* Sidebar */}
      <div className="fixed left-0 top-0 z-50">
        <ChatHistory
          onSelect={setChatId}
          onNewChat={handleNewChat}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={toggleSidebar}
          resetChat={resetChat}
          addChatToHistoryRef={addChatToHistoryRef}
        />
      </div>

      {/* Chat Area */}
      <div className={`h-screen flex-1 pt-12 transition-all duration-300 ${isSidebarOpen ? 'md:ml-72' : ''}`}>
        <Chat chatId={chatId} addChatToHistoryRef={addChatToHistoryRef} />
      </div>

    </div>
  );
}

'use client';

import { useState } from 'react';

import Chat from '@/components/Chat';
import ChatHistory from '@/components/ChatHistory';

export default function Page() {
  const [chatId, setChatId] = useState<string>(() => Date.now().toString());
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

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
    <div className="relative h-screen w-full bg-gray-100">
      {/* Sidebar */}
      <div className="fixed left-0 top-0 z-50">
        <ChatHistory
          onSelect={setChatId}
          onNewChat={handleNewChat}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={toggleSidebar}
          resetChat={resetChat}
        />
      </div>

      {/* Chat Area */}
      <div
        className={`h-screen overflow-hidden pt-12 transition-all duration-300 ${
          isSidebarOpen ? 'md:ml-72' : ''
        }`}
      >
        <div className="mx-auto flex h-full max-w-4xl flex-col px-4">
          <Chat chatId={chatId} />
        </div>
      </div>
    </div>
  );
}

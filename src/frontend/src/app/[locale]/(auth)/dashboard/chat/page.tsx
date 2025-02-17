'use client';

import { useState } from 'react';

import Chat from '@/components/Chat';
import ChatHistory from '@/components/ChatHistory';

export default function Page() {
  const [chatId, setChatId] = useState<string>(() => Date.now().toString());
  const [isSidebarOpen, setIsSidebarOpen] = useState(true); // State to control sidebar visibility

  const handleNewChat = () => {
    setChatId(Date.now().toString());
  };

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  return (
    <div className="flex h-[100px]">
      {/* Sidebar */}
      <div className={`transition-all duration-300 ${isSidebarOpen ? 'w-80' : 'w-0'}`}>
        <ChatHistory
          onSelect={setChatId}
          onNewChat={handleNewChat}
          isSidebarOpen={isSidebarOpen} // Passing isSidebarOpen to ChatHistory component
          onToggleSidebar={toggleSidebar}
        />
      </div>

      {/* Chat Area - Adjust width dynamically */}
      <div className={`flex-1 transition-all duration-300 ${isSidebarOpen ? 'ml-0' : 'ml-0'}`}>
        <Chat chatId={chatId} isSidebarOpen={isSidebarOpen} />
        {' '}
        {/* Passing isSidebarOpen to Chat */}
      </div>
    </div>
  );
}

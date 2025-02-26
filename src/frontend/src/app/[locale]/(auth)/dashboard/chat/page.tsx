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

  // Function to reset the Chat component's state
  const resetChat = () => {
    setChatId(Date.now().toString()); // Reset chatId to force a re-render
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <div className={`transition-all duration-300 ${isSidebarOpen ? 'w-80' : 'w-0'}`}>
        <ChatHistory
          onSelect={setChatId}
          onNewChat={handleNewChat}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={toggleSidebar}
          resetChat={resetChat} // Pass resetChat function
        />
      </div>

      {/* Chat Area */}
      <div className={`flex-1 transition-all duration-300 ${isSidebarOpen ? 'ml-0' : 'ml-0'}`}>
        <Chat chatId={chatId} isSidebarOpen={isSidebarOpen} />
      </div>
    </div>
  );
}

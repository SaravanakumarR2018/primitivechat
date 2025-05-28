'use client';

import { useEffect, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { ChatProvider, useChat } from '@/context/ChatContext';
import { DashboardHeader } from '@/features/dashboard/DashboardHeader';
import GlobalSidebarWrapper from '@/components/GlobalSidebarWrapper';
import Link from 'next/link';
import { Ticket, ClipboardList, Settings, MessageSquare } from 'lucide-react';

export default function ChatLayout({ children }: { children: React.ReactNode }) {
  return (
    <ChatProvider>
      <DashboardClient>{children}</DashboardClient>
    </ChatProvider>
  );
}

function DashboardClient({ children }: { children: React.ReactNode }) {
  const [isSidebarOpen, setSidebarOpen] = useState(false);
  const toggleSidebar = () => setSidebarOpen((prev) => !prev);
  const [isMobile, setIsMobile] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const { newChat } = useChat();

  const handleNewChat = () => {
    if (!pathname.includes('/dashboard/chat')) {
      router.push('/dashboard/chat');
    } else {
      // if already on chat page, create a new chat
      newChat();
    }
    if (isMobile && isSidebarOpen) {
      toggleSidebar();
    }
  };

  useEffect(() => {
    const checkScreenSize = () => setIsMobile(window.innerWidth < 768);
    checkScreenSize();
    window.addEventListener('resize', checkScreenSize);
    return () => window.removeEventListener('resize', checkScreenSize);
  }, []);

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <div className="sticky top-0 z-50 w-full bg-white shadow-md">
        <div
          className={`mx-auto flex max-w-screen-xl items-center px-3 py-4 ${
            isSidebarOpen ? 'ml-72' : 'ml-0'
          }`}
        >
          {!isSidebarOpen && (
            <div className="flex items-center gap-4">
              <button
                type="button"
                title="Toggle Sidebar"
                onClick={toggleSidebar}
                className="rounded-lg bg-white p-2"
              >
                <svg className="h-6 w-6 text-gray-800" fill="none" viewBox="0 0 24 24">
                  <path
                    stroke="currentColor"
                    strokeWidth="2"
                    d="m6 10 2 2-2 2M11 5v14M4 5h16a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1Z"
                  />
                </svg>
              </button>

              <button
                type="button"
                title="New Chat"
                onClick={handleNewChat}
                className="rounded-lg bg-white p-2"
              >
                <svg className="h-6 w-6 text-gray-800" fill="none" viewBox="0 0 24 24">
                  <path
                    stroke="currentColor"
                    strokeWidth="2"
                    d="M14.3 4.8l2.85 2.85M7 7H4a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h11a1 1 0 0 0 1-1v-4.5m2.4-9.91a2 2 0 0 1 0 2.85l-6.84 6.84L8 14l.71-3.57 6.84-6.84a2 2 0 0 1 2.85 0Z"
                  />
                </svg>
              </button>
            </div>
          )}

          <DashboardHeader
            menu={[
              { href: '/dashboard', label: 'Home' },
              { href: '/dashboard/organization-profile/organization-members', label: 'Members' },
              { href: '/dashboard/organization-profile', label: 'Settings' },
            ]}
          />
        </div>
      </div>

      {/* Mini Sidebar */}
      <div className="fixed top-16 left-0 w-16 h-[652px] flex flex-col items-center gap-6 bg-white shadow-md py-4 z-40 rounded-r-md">

        <Link href="/dashboard/tickets" title="Tickets">
          <Ticket className="w-5 h-5 text-gray-700 hover:text-black" />
        </Link>
        <Link href="/dashboard/checkclerk" title="Check Clerk">
          <ClipboardList className="w-5 h-5 text-gray-700 hover:text-black" />
        </Link>
        <Link href="/dashboard/app-settings" title="App Settings">
          <Settings className="w-5 h-5 text-gray-700 hover:text-black" />
        </Link>
        <Link href="/dashboard/chat" title="Chat">
          <MessageSquare className="w-5 h-5 text-gray-700 hover:text-black" />
        </Link>
      </div>

      {/* Main Chat Content */}
      <GlobalSidebarWrapper isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar}>
        <div
          className={`transition-all duration-300 ${
            isSidebarOpen ? 'ml-0' : 'ml-20'
          } max-w-screen-xl px-2 pb-16 pt-6`}
        >
          {children}
        </div>
      </GlobalSidebarWrapper>
    </div>
  );
}
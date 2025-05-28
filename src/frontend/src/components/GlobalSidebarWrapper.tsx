'use client';

import ChatHistory from './ChatHistory';

interface SidebarWrapperProps {
  children?: React.ReactNode;
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

export default function GlobalSidebarWrapper({
  children,
  isSidebarOpen,
  toggleSidebar,
}: SidebarWrapperProps) {
  return (
    <div className="relative">
      {/* Optional Chat History or Additional Sidebar */}
      <ChatHistory isSidebarOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />

      {/* Main Content */}
      <div className={`transition-all duration-300 ${isSidebarOpen ? 'ml-72' : 'ml-0'}`}>
        {children}
      </div>
    </div>
  );
}
'use client';

import React, { createContext, useCallback, useContext, useRef, useState } from 'react';

type DashboardSidebarContextProps = {
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
  chatId: string;
  setChatId: (id: string) => void;
  resetChat: () => void;
  addChatToHistoryRef: React.MutableRefObject<((chatId: string, message: string, timestamp?: number) => void) | null>;
};

const DashboardSidebarContext = createContext<DashboardSidebarContextProps | undefined>(undefined);

export const useDashboardSidebar = () => {
  const context = useContext(DashboardSidebarContext);
  if (!context) {
    throw new Error('useDashboardSidebar must be used within DashboardSidebarProvider');
  }
  return context;
};

export const DashboardSidebarProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [chatId, setChatId] = useState(() => Date.now().toString());
  const addChatToHistoryRef = useRef<((chatId: string, message: string, timestamp?: number) => void) | null>(null);

  const toggleSidebar = useCallback(() => setIsSidebarOpen(open => !open), []);
  const resetChat = useCallback(() => setChatId(Date.now().toString()), []);

  const contextValue = React.useMemo(
    () => ({
      isSidebarOpen,
      toggleSidebar,
      chatId,
      setChatId,
      resetChat,
      addChatToHistoryRef,
    }),
    [isSidebarOpen, toggleSidebar, chatId, setChatId, resetChat, addChatToHistoryRef],
  );

  return (
    <DashboardSidebarContext.Provider value={contextValue}>
      {children}
    </DashboardSidebarContext.Provider>
  );
};

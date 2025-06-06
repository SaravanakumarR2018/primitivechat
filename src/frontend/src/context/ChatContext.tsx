'use client';
import { createContext, useContext, useState } from 'react';

interface ChatContextProps {
    chatId: string;
    newChat: () => void;
    resetChat:()=>void;
}

const ChatContext = createContext<ChatContextProps | undefined>(undefined);

export function ChatProvider({ children }: { children: React.ReactNode }) {
    const [chatId, setChatId] = useState<string>(() => Date.now().toString());
  
    const newChat = () => {
        setChatId(Date.now().toString());
    };

    const resetChat = () => {
    setChatId(Date.now().toString());
  };
  
    return (
        <ChatContext.Provider value={{ chatId, newChat, resetChat }}>
            {children}
        </ChatContext.Provider>
    );
}
  
export function useChat() {
    const context = useContext(ChatContext);
    if (!context) {
        throw new Error('useChat must be used within a ChatProvider');
    }
    return context;
}
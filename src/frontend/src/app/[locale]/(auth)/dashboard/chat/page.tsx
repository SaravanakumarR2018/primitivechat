
'use client';
import { useChat } from '@/context/ChatContext';
import Chat from '@/components/Chat';

export default function Page() {
  const { chatId } = useChat();

  return (
    <div className="h-screen flex-1 pt-12 transition-all duration-300">
        <Chat chatId={chatId} />
      </div>
  );
}

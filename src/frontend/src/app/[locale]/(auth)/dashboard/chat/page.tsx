'use client';

import Chat from '@/components/Chat';
import { useDashboardSidebar } from '@/features/dashboard/DashboardSidebarContext';

export default function Page() {
  // Use context for sidebar/chat state
  const {
    chatId,
    addChatToHistoryRef,
  } = useDashboardSidebar();

  return (
    <div className="relative flex size-full">
      {/* Chat Area */}
      <div className="flex-1 transition-all duration-300">
        <Chat chatId={chatId} addChatToHistoryRef={addChatToHistoryRef} />
      </div>
    </div>
  );
}

'use client';

export default function NewChat({ onNewChat }: { onNewChat: () => void }) {
  return (
    <button onClick={onNewChat} className="w-full rounded-md bg-green-600 py-2 text-white">
      + New Chat
    </button>
  );
}

// app/api/backend/sendmessage/route.ts
import { auth } from '@clerk/nextjs/server';
import type { NextRequest } from 'next/server';

const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

if (!CHAT_SERVICE_HOST || !CHAT_SERVICE_PORT) {
  throw new Error('CHAT_SERVICE_HOST or CHAT_SERVICE_PORT is missing from environment variables.');
}

const API_BASE_URL = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}`;

export const runtime = 'edge'; // Required for streaming

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { message, chatId } = body;

  const { getToken } = auth();
  const token = await getToken();

  if (!token) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const payload: any = {
    question: message,
    stream: true,
  };

  if (chatId) {
    payload.chat_id = chatId;
  }

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  return new Response(response.body, {
    status: response.status,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    },
  });
}

import { auth } from '@clerk/nextjs/server';
import type { NextRequest } from 'next/server';

export const runtime = 'edge'; // Required for streaming

export async function POST(req: NextRequest) {
  const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
  const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

  if (!CHAT_SERVICE_HOST || !CHAT_SERVICE_PORT) {
    throw new Error('CHAT_SERVICE_HOST or CHAT_SERVICE_PORT is missing from environment variables.');
  }

  const API_BASE_URL = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}`;
  const body = await req.json();

  const { question, chat_id } = body;

  if (!question && !chat_id) {
    return new Response(JSON.stringify({ error: 'Question or chatId is required' }), { status: 400 });
  }

  const { getToken } = auth();
  const token = await getToken();

  if (!token) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const payload: any = {
    question,
    stream: true,
  };

  if (chat_id) {
    payload.chat_id = chat_id;
  }

  const response = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  });

  return new Response(
    new ReadableStream({
      async start(controller) {
        const reader = response.body!.getReader();
        while (true) {
          const { done, value } = await reader.read();
          if (done) {
            break;
          }
          controller.enqueue(value);
        }
        controller.close();
      },
    }),
    {
      status: response.status,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    },
  );
}

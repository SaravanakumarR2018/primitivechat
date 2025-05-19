import { auth } from '@clerk/nextjs/server';
import type { NextRequest } from 'next/server';

export const runtime = 'edge';

// GET /api/backend/getLLMResponse
export async function GET() {
  const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
  const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

  if (!CHAT_SERVICE_HOST || !CHAT_SERVICE_PORT) {
    throw new Error('CHAT_SERVICE_HOST or CHAT_SERVICE_PORT is missing from environment variables.');
  }

  const API_BASE_URL = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}`;

  const { getToken } = auth();
  const token = await getToken();

  if (!token) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const response = await fetch(`${API_BASE_URL}/llm_service/get_llm_response_mode`, {
    method: 'GET',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  const data = await response.text();
  return new Response(data, {
    status: response.status,
    headers: { 'Content-Type': 'application/json' },
  });
}

// POST /api/backend/useLLMResponse
export async function POST(req: NextRequest) {
  const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
  const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

  if (!CHAT_SERVICE_HOST || !CHAT_SERVICE_PORT) {
    throw new Error('CHAT_SERVICE_HOST or CHAT_SERVICE_PORT is missing from environment variables.');
  }

  const API_BASE_URL = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}`;
  const body = await req.json();

  const { getToken } = auth();
  const token = await getToken();

  if (!token) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const response = await fetch(`${API_BASE_URL}/llm_service/use_llm_response`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });

  const data = await response.text();
  return new Response(data, {
    status: response.status,
    headers: { 'Content-Type': 'application/json' },
  });
}

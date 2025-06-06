import { auth } from '@clerk/nextjs/server';
import type { NextRequest } from 'next/server';

export const runtime = 'edge';

export async function GET(req: NextRequest) {
  const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
  const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;
  if (!CHAT_SERVICE_HOST || !CHAT_SERVICE_PORT) {
    throw new Error('CHAT_SERVICE_HOST or CHAT_SERVICE_PORT is missing from environment variables.');
  }
  const API_BASE_URL = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}`;

  // Preserve query parameters
  const { search } = new URL(req.url);
  
  const { getToken } = auth();
  const token = await getToken();
  if (!token) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  // Append search (query params) if present
  const backendUrl = `${API_BASE_URL}/files/deletionstatus${search}`;
  
  const response = await fetch(backendUrl, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });
  const data = await response.text();
  return new Response(data, {
    status: response.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
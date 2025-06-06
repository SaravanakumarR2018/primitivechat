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

  const response = await fetch(`${API_BASE_URL}/file/list${search}`, {
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


export async function DELETE(req: NextRequest) {
  const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
  const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;
  if (!CHAT_SERVICE_HOST || !CHAT_SERVICE_PORT) {
    throw new Error('CHAT_SERVICE_HOST or CHAT_SERVICE_PORT is missing from environment variables.');
  }
  const API_BASE_URL = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}`;

  const { searchParams } = new URL(req.url);
  const filename = searchParams.get('filename');
  if (!filename) {
    return new Response(JSON.stringify({ error: 'Filename is required' }), { status: 400 });
  }

  const { getToken } = auth();
  const token = await getToken();
  if (!token) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const response = await fetch(
    `${API_BASE_URL}/deletefile?filename=${encodeURIComponent(filename)}`,
    {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    }
  );
  if (response.ok) {
    return new Response(
      JSON.stringify({ message: "File deleted successfully" }),
      {
        status: 200,
        headers: { "Content-Type": "application/json" },
      }
    );
  } else {
    const errorData = await response.text();
    return new Response(errorData, {
      status: response.status,
      headers: { "Content-Type": "application/json" },
    });
  }
}

export async function POST(req: NextRequest) {
  const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
  const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;
  if (!CHAT_SERVICE_HOST || !CHAT_SERVICE_PORT) {
    throw new Error('CHAT_SERVICE_HOST or CHAT_SERVICE_PORT is missing from environment variables.');
  }
  const API_BASE_URL = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}`;

  const formData = await req.formData();

  const { getToken } = auth();
  const token = await getToken();
  if (!token) {
    return new Response(JSON.stringify({ error: 'Unauthorized' }), { status: 401 });
  }

  const response = await fetch(`${API_BASE_URL}/uploadFile`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });
  const data = await response.text();
  return new Response(data, {
    status: response.status,
    headers: { 'Content-Type': 'application/json' },
  });
}
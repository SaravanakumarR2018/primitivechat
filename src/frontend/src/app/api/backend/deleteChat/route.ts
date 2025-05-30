import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

export async function POST(request: Request) {
  try {
    const { getToken } = auth();
    const token = await getToken();
    const body = await request.json();

    if (!token) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    if (!body.chat_id) {
      return NextResponse.json({ error: 'chat_id is required' }, { status: 400 });
    }

    const res = await fetch(
      `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}/deletechat`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ chat_id: body.chat_id }),
      },
    );

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    console.error('Error deleting chat:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

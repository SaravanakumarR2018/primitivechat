import { auth } from '@clerk/nextjs/server';
import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

export async function GET(req: NextRequest) {
  const { getToken, orgId } = auth();
  const token = await getToken();
  const { searchParams } = new URL(req.url);

  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const chatId = searchParams.get('chat_id');
  const page = Number(searchParams.get('page')) || 1;
  const pageSize = Number(searchParams.get('page_size')) || 10;
  const requestOrgId = searchParams.get('org_id') || orgId;

  if (!chatId) {
    return NextResponse.json({ error: 'Missing chat_id' }, { status: 400 });
  }

  try {
    const res = await fetch(
      `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}/getallchats?chat_id=${chatId}&page=${page}&page_size=${pageSize}&org_id=${requestOrgId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      },
    );

    if (!res.ok) {
      return NextResponse.json({ error: 'Failed to fetch chat messages' }, { status: res.status });
    }

    const data = await res.json();

    return NextResponse.json({
      messages: data.messages || [],
      has_more: data.has_more ?? (data.messages?.length === pageSize),
    });
  } catch (error) {
    console.error(`Error fetching messages for chat ${chatId}:`, error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

// app/api/backend/getallchatids/route.ts
import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

export async function GET(request: Request) {
  const { getToken, orgId } = auth();
  const token = await getToken();
  const { searchParams } = new URL(request.url);

  if (!token) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  // Get pagination parameters with defaults
  const page = Number.parseInt(searchParams.get('page') || '1');
  const pageSize = Number.parseInt(searchParams.get('page_size') || '15');
  const requestOrgId = searchParams.get('org_id') || orgId;

  if (!requestOrgId) {
    return NextResponse.json({ error: 'Organization ID is required' }, { status: 400 });
  }

  try {
    const res = await fetch(
      `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}/getallchatids?page=${page}&page_size=${pageSize}&org_id=${requestOrgId}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      },
    );

    if (!res.ok) {
      return NextResponse.json({ error: 'Failed to fetch chat ids' }, { status: res.status });
    }

    const data = await res.json();

    // Ensure the response has the expected structure
    const responseData = {
      chat_ids: data.chat_ids || [],
      has_more: data.has_more !== undefined ? data.has_more : (data.chat_ids?.length === pageSize),
    };

    return NextResponse.json(responseData);
  } catch (error) {
    console.error('Error fetching chat IDs:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

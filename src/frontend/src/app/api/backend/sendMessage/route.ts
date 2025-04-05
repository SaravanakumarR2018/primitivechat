import { auth } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

type ChatRequest = {
  message: string;
  chatId?: string;
};

type ChatResponse = {
  chat_id: string;
  customer_guid: string;
  answer: string;
};

export async function POST(request: Request) {
  try {
    // Get Clerk authentication token
    const token = await auth().getToken();
    if (!token) {
      return NextResponse.json(
        { error: 'Unauthorized - Please log in' },
        { status: 401 },
      );
    }

    // Get the request body
    const { message, chatId } = (await request.json()) as ChatRequest;

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 },
      );
    }

    // Call your chat service backend
    const backendResponse = await fetch(`http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        question: message,
        chat_id: chatId,
      }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json();
      return NextResponse.json(
        { error: errorData.detail || 'Chat service request failed' },
        { status: backendResponse.status },
      );
    }

    const backendData = await backendResponse.json();

    // Transform the response to match what your frontend expects
    const responseData: ChatResponse = {
      chat_id: backendData.chat_id,
      customer_guid: backendData.customer_guid,
      answer: backendData.answer,
    };

    return NextResponse.json(responseData);
  } catch (error) {
    console.error('Error in sendMessage API route:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 },
    );
  }
}

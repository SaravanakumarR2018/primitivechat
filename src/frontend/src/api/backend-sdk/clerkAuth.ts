import { auth } from '@clerk/nextjs/server';

const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

export async function getClerkUser(): Promise<any> {
  try {
    const token = await auth().getToken();
    if (!token) {
      throw new Error('No auth token found: user is not logged in');
    }

    const response = await fetch(`http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}/checkauth`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      credentials: 'include', // Ensures cookies/session data are sent
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching user from checkauth:', error);
    return null;
  }
}

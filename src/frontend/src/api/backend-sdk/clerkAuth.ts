import { auth } from '@clerk/nextjs/server';

export async function getClerkUser(): Promise<any> {
  try {
    const token = await auth().getToken();
    console.log('token:', token);
    if (!token) {
      throw new Error('No auth token found: simple');
    }
    // const modifiedToken = token;
    // const modifiedToken1 = `${modifiedToken.slice(0, -2)}12`;
    const response = await fetch('http://localhost:8000/checkauth', {
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

/* eslint-disable no-console */
'use server';

import { auth } from '@clerk/nextjs/server';

const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

if (!CHAT_SERVICE_HOST || !CHAT_SERVICE_PORT) {
  throw new Error('CHAT_SERVICE_HOST or CHAT_SERVICE_PORT is missing from environment variables.');
}

const API_BASE_URL = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}`;

async function getAuthToken() {
  try {
    const authData = auth();
    if (!authData) {
      throw new Error('Authentication failed. No auth data available.');
    }

    const token = await authData.getToken();
    if (!token) {
      throw new Error('Failed to retrieve authentication token.');
    }

    return token;
  } catch (error) {
    console.error('Error retrieving auth token:', error);
    throw error;
  }
}

/**
 * Fetch ticket by ID
 */
export async function fetchTicketByID(ticketId: string) {
  const token = await getAuthToken();

  try {
    const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorMessage = await response.text();
      throw new Error(`Failed to fetch ticket (Status: ${response.status}) - ${errorMessage}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching ticket:', error);
    throw error;
  }
}

/**
 * Fetch tickets by customer GUID
 */
export async function fetchTicketsByCustomer(page: number, pageSize: number) {
  const token = await getAuthToken();

  try {
    const response = await fetch(
      `${API_BASE_URL}/customer/tickets?page=${page}&page_size=${pageSize}`,
      {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        cache: 'no-store',
      },
    );

    // Read response body only once
    const data = await response.json();

    if (!response.ok) {
      if (data?.detail?.includes('No tickets found')) {
        return []; // Return an empty array instead of throwing an error
      }
      console.log(data.detail);
      throw new Error(`Failed to fetch tickets: ${data.detail || 'Unknown error'}`);
    }

    return data;
  } catch (error) {
    console.error('Error fetching tickets by customer:', error);
    throw error;
  }
}
/**
 * Update full ticket details (for ticket details page)
 */
export async function updateTicketDetails(ticketId: string, formData: any) {
  const token = await getAuthToken();

  try {
    const response = await fetch(`${API_BASE_URL}/${ticketId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(formData),
    });

    if (!response.ok) {
      const errorMessage = await response.text();
      throw new Error(`Failed to update ticket details (Status: ${response.status}) - ${errorMessage}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error updating ticket details:', error);
    throw error;
  }
}

/**
 * Update ticket status or priority (for ticket list page)
 */
export async function updatePartialTicket(ticketId: string, field: 'status' | 'priority', value: string) {
  const token = await getAuthToken();

  try {
    const response = await fetch(`${API_BASE_URL}/tickets/${ticketId}`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ [field]: value }),
    });

    if (!response.ok) {
      const errorMessage = await response.text();
      throw new Error(`Failed to update ticket ${field} (Status: ${response.status}) - ${errorMessage}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error updating ticket ${field}:`, error);
    throw error;
  }
}

export async function fetchCustomFields() {
  const token = await getAuthToken();
  try {
    const response = await fetch(`${API_BASE_URL}/custom_fields}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      cache: 'no-store',
    });
    const data = await response.json();
    if (!response.ok) {
      if (data?.detail?.includes('No custom fields found')) {
        return []; // Return an empty array instead of throwing an error
      }
      throw new Error(`Failed to fetch custom fields (Status: ${response.status})`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching custom fields:', error);
    throw error;
  }
}

export async function createTicket(ticketData: any) {
  const token = await getAuthToken();

  try {
    const response = await fetch(`${API_BASE_URL}/tickets`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(ticketData),
    });

    if (!response.ok) {
      const errorMessage = await response.text();
      throw new Error(`Failed to create ticket (Status: ${response.status}) - ${errorMessage}`);
    }

    return await response.json(); // Expected response: { "ticket_id": "string", "status": "created" }
  } catch (error) {
    console.error('Error creating ticket:', error);
    throw error;
  }
}

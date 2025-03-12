import { auth } from '@clerk/nextjs/server';

const CHAT_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const CHAT_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

/**
 * Global cache for storing orgId and GUID mappings (ensures unique values)
 */
const customerCache = new Map<string, string>();

/**
 * Centralized logger function
 */
function logMessage(level: 'debug' | 'info' | 'warn' | 'error', message: string, ...args: any[]) {
  if (process.env.NODE_ENV !== 'production' || level === 'error' || level === 'debug') {
    // eslint-disable-next-line no-console
    console[level === 'debug' ? 'log' : level](`[${level.toUpperCase()}] ${message}`, ...args);
  }
}

/**
 * Fetch customer GUID for the authenticated user (Ensures API is called only once per session)
 */
export async function getCustomerGuid(): Promise<string> {
  try {
    logMessage('debug', 'Fetching Clerk auth token...');

    const authData = auth();
    const { orgId } = authData;
    const token = await authData.getToken();

    if (!orgId || !token) {
      throw new Error('Missing Clerk orgId or token. Authentication failed.');
    }

    // If orgId exists in cache, return stored GUID (avoid duplicates)
    if (customerCache.has(orgId)) {
      logMessage('debug', `Customer GUID found in cache for orgId: ${orgId}, customer GUID: ${customerCache.get(orgId)}`);
      return customerCache.get(orgId)!;
    }

    // First-time call to API
    const customerGuid = await fetchCustomerGuid(token);

    if (customerGuid && !customerCache.has(orgId)) {
      // Store in cache only if not already stored
      customerCache.set(orgId, customerGuid);
      logMessage('info', `Stored new customer GUID in cache for orgId: ${orgId}, customer GUID: ${customerGuid}`);
    }

    return customerGuid;
  } catch (error) {
    logMessage('error', 'Error fetching customer GUID', error);
    throw error; // Ensure the error propagates to the caller
  }
}

/**
 * Fetch customer GUID from backend (called only if not in cache)
 */
async function fetchCustomerGuid(token: string): Promise<string> {
  const apiUrl = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}/addcustomer`;

  try {
    logMessage('info', `Calling API (only if not in cache): ${apiUrl}`);

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    const customerGuid = data.customer_guid;

    if (!customerGuid) {
      throw new Error('No GUID returned from API');
    }

    logMessage('info', `Received customer GUID from API: ${customerGuid}`);
    return customerGuid;
  } catch (error) {
    logMessage('error', 'API request failed', error);
    throw error;
  }
}

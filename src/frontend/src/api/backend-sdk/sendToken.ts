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
function logMessage(level: 'info' | 'warn' | 'error', message: string, ...args: any[]) {
  if (process.env.NODE_ENV !== 'production' || level === 'error') {
    // eslint-disable-next-line no-console
    console[level](`[${level.toUpperCase()}] ${message}`, ...args);
  }
}

/**
 * Log the current state of customerCache
 */
function logCustomerCache() {
  logMessage('info', 'Current customerCache contents:', Array.from(customerCache.entries()));
}

/**
 * Fetch customer GUID for the authenticated user (Ensures API is called only once per session)
 */
export async function getCustomerGuid(): Promise<string | null> {
  try {
    logMessage('info', 'Fetching Clerk auth token...');

    const authData = auth();
    const { orgId } = authData;
    const token = await authData.getToken();

    if (!orgId || !token) {
      logMessage('error', 'Missing Clerk orgId or token. Authentication failed.');
      return null;
    }

    // If orgId exists in cache, return stored GUID (avoid duplicates)
    if (customerCache.has(orgId)) {
      logMessage('info', `Customer GUID found in cache for this orgId: ${orgId}`);
      logCustomerCache(); // Log the cache contents
      return customerCache.get(orgId)!;
    }

    // First-time call to API
    const customerGuid = await fetchCustomerGuid(orgId, token);

    if (customerGuid && !customerCache.has(orgId)) {
      // Store in cache only if not already stored
      customerCache.set(orgId, customerGuid);
      logMessage('info', `Stored new customer GUID in cache for this orgId: ${orgId}`);
    }

    logCustomerCache(); // Log cache after storing new entry

    return customerGuid;
  } catch (error) {
    logMessage('error', 'Error fetching customer GUID', error);
    return null;
  }
}

/**
 * Fetch customer GUID from backend (called only if not in cache)
 */
async function fetchCustomerGuid(orgId: string, token: string): Promise<string | null> {
  const apiUrl = `http://${CHAT_SERVICE_HOST}:${CHAT_SERVICE_PORT}/addcustomer`;

  try {
    logMessage('info', `Calling API (only if not in cache): ${apiUrl}`);

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ orgId }),
    });

    if (!response.ok) {
      logMessage('error', `API Error: ${response.status} ${response.statusText}`);
      return null;
    }

    const data = await response.json();
    const customerGuid = data.customer_guid;

    if (!customerGuid) {
      logMessage('error', 'No GUID returned from API');
      return null;
    }

    logMessage('info', `Received customer GUID from API: ${customerGuid}`);

    return customerGuid;
  } catch (error) {
    logMessage('error', 'API request failed', error);
    return null;
  }
}

/* eslint-disable no-console */
'use server';

import { auth } from '@clerk/nextjs/server';

// Assuming the document service uses the same host and port as the chat service.
// If this is different, these environment variables should be updated or new ones used.
const DOC_SERVICE_HOST = process.env.CHAT_SERVICE_HOST;
const DOC_SERVICE_PORT = process.env.CHAT_SERVICE_PORT;

if (!DOC_SERVICE_HOST || !DOC_SERVICE_PORT) {
  throw new Error('DOC_SERVICE_HOST or DOC_SERVICE_PORT is missing from environment variables.');
}

const API_BASE_URL = `http://${DOC_SERVICE_HOST}:${DOC_SERVICE_PORT}`;

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

export async function uploadDocument(base64String: string, fileName: string, fileType: string) {
  const token = await getAuthToken();
  const formData = new FormData();

  // Convert base64 string to a Buffer
  const buffer = Buffer.from(base64String, 'base64');

  // Create a Blob from the Buffer
  const blob = new Blob([buffer], { type: fileType });

  // Append the Blob to FormData
  formData.append('file', blob, fileName); // The backend will expect the file under the field name 'file'

  try {
    console.log(`Attempting to upload file "${fileName}" (${fileType}, from base64) to ${API_BASE_URL}/upload`);
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        // 'Content-Type' is not set here, as Fetch API with FormData handles it.
      },
      body: formData,
      cache: 'no-store', // Ensuring no caching for this request
    });

    const responseData = await response.json();

    if (!response.ok) {
      console.error('Upload failed response:', responseData);
      // Attempt to get a more specific error message from the response
      const errorMessage = responseData?.detail || responseData?.message || `Failed to upload document (Status: ${response.status})`;
      throw new Error(errorMessage);
    }

    console.log('Upload successful response:', responseData);
    return responseData; // Example: { "message": "File uploaded successfully", "file_id": "xyz123" }
  } catch (error) {
    console.error('Error uploading document:', error);
    // Ensure the error thrown is an Error object with a message
    if (error instanceof Error) {
      throw error;
    } else {
      throw new Error('An unknown error occurred during document upload.');
    }
  }
}

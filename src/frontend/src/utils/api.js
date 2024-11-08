export const fetchChatResponse = async (requestBody) => {
  try {
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody),
    });
    console.log(await response.json())
    return response;
  } catch (error) {
    console.error('Error fetching chat response:', error);
    throw error;
  }
};

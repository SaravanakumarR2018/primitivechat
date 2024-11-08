# Primitive Chat - Frontend

This is the frontend part of the Primitive Chat application, located in the `chat-bot-frontend` branch. It is built using **React** and integrates the **DeepChat** component for a chatbot interface.

## Prerequisites

- **Node.js** and **npm** installed.
- Ensure your backend server is running and accessible at `http://localhost:8000/chat`.

## How to Run Locally

### 1. Clone the Repository

Make sure to clone the specific branch `chat-bot-frontend`:

```bash
git clone -b chat-bot-frontend https://github.com/SaravanakumarR2018/primitivechat.git
cd primitivechat

2. Install Dependencies

Navigate to the frontend directory and install dependencies:

npm install

3. Start the Development Server

npm start

The frontend will be accessible at http://localhost:3000.
4. Start the Backend Server

Ensure your backend server is running locally at http://localhost:8000/chat. This is the endpoint the chatbot uses to communicate.
5. Usage

    Click on the chat icon to open the chatbot interface.
    Type your message to interact with the bot.
    The chat session ID is stored locally, allowing session persistence after refreshing the page.

Configuration

    If you need to change the backend API URL, update the url parameter in ChatBot.js:

    connect={{
      url: 'http://localhost:8000/chat',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    }}

    To customize the chat icon image, replace the file at src/assets/icons/image.png with your own image.

Additional Commands

    Build the Project:

npm run build

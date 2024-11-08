import React, { useEffect, useState, useRef } from 'react';
import { DeepChat } from 'deep-chat-react';
import { getChatIdFromLocalStorage, saveChatIdToLocalStorage } from '../../utils/localStorageHelper';
import ChatIcon from './ChatIcon';

const ChatBot = () => {
  const chatElementRef = useRef(null);
  const [isChatOpen, setChatOpen] = useState(false);
  const [chatId, setChatId] = useState(null);
  const customerId = '30b19ce2-5636-47bb-9d6f-a048ca4eaea7';
  let message_count = 1;
  console.log("1st render")
  // Flag to indicate if the chatId has been stored
  const chatIdStored = useRef(false);

  useEffect(() => {
    const storedChatId = getChatIdFromLocalStorage();
    if (storedChatId) {
      setChatId(storedChatId);
    } else {
      setChatId(''); // Set chatId as empty to avoid undefined state
    }
  }, []);

  const toggleChat = () => {
    setChatOpen(!isChatOpen);
  };

  if (chatId === null) {
    return null;
  }

  return (
    <div className="chatbot-container">
      <ChatIcon onClick={toggleChat} />
      {isChatOpen && (
        <div>
          <DeepChat
            ref={chatElementRef}
            connect={{
              url: 'http://localhost:8000/chat',
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
            }}
            requestInterceptor={(requestDetails) => {
              const messageText = requestDetails.body.messages[0]?.text;
              if (!messageText) return requestDetails;

              const requestBody = {
                question: messageText,
                customer_guid: customerId,
                ...(chatId && { chat_id: chatId }),
              };
              console.log("requestInterceptor")
              requestDetails.body = requestBody;
              console.log(`Modified Request Body (Message Count: ${message_count})`, requestDetails);
              message_count++;
              return requestDetails;
            }}
            responseInterceptor={(responseDetails) => {
              if (responseDetails && responseDetails.answer) {
                const botMessage = { role: 'ai', text: responseDetails.answer };

                // Save chat_id only on the first message
                if (!chatIdStored.current && responseDetails.chat_id) {
                  setChatId(responseDetails.chat_id); // Update chatId
                  saveChatIdToLocalStorage(responseDetails.chat_id); // Store immediately without re-rendering
                  chatIdStored.current = true; // Set flag to avoid future updates
                }
                console.log("responseInterceptor");
                console.log(responseDetails);
                return botMessage;
              }
            }}
          />
        </div>
      )}
    </div>
  );
};

export default ChatBot;

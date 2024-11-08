export const getChatIdFromLocalStorage = () => {
    return localStorage.getItem('chat_id');
  };
  
  export const saveChatIdToLocalStorage = (chatId) => {
    localStorage.setItem('chat_id', chatId);
  };
  
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  chatId: null,
  messages: [],
  isLoading: false,
};
const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    setChatId(state, action) {
      state.chatId = action.payload;
    },
    addMessage(state, action) {
      // console.log(state, action)
      state.messages.push(action.payload);
    },
    setLoading(state, action) {
      state.isLoading = action.payload;
    },
  },
});

export const { setChatId, addMessage, setLoading } = chatSlice.actions;
export default chatSlice.reducer;

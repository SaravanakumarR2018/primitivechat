// src/App.js
import React from 'react';
import { Provider } from 'react-redux';
import store from './redux/store';
import ChatBot from './components/ChatBot/ChatBot';
import "./App.css";

const App = () => {
  return (
    <Provider store={store}>
      <div className="app-container">
        <ChatBot />
      </div>
    </Provider>
  );
};

export default App;

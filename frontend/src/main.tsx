import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    const baseUrl = import.meta.env.BASE_URL as string;
    const swUrl = `${baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`}sw.js`;
    navigator.serviceWorker.register(swUrl).catch(() => {
      // Ignore registration failures to keep startup resilient on unsupported hosts.
    });
  });
}

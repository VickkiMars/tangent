import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const Notification = () => {
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    const handleNotify = (event) => {
      const { message, type = 'info', duration = 5000 } = event.detail;
      setNotification({ message, type });

      if (duration !== Infinity) {
        setTimeout(() => {
          setNotification(null);
        }, duration);
      }
    };

    window.addEventListener('notify', handleNotify);
    return () => window.removeEventListener('notify', handleNotify);
  }, []);

  const sanitizeError = (msg) => {
    if (!msg) return 'An unknown error occurred.';
    // Remove technical prefix from litellm/gemini
    let clean = msg.replace(/litellm\.BadRequestError: GeminiException BadRequestError - /, '');
    // Common error translations
    if (clean.includes('API Key not found')) return 'Configuration Error: API Key is missing or invalid. Please check your .env file.';
    if (clean.includes('rate limit')) return 'Server is busy. Please wait a moment and try again.';
    if (clean.includes('quota exceeded')) return 'API Quota exceeded. Please check your provider billing.';
    return clean;
  };

  return (
    <AnimatePresence>
      {notification && (
        <motion.div
          initial={{ opacity: 0, y: 50, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          style={{
            position: 'fixed',
            bottom: '32px',
            right: '32px',
            zIndex: 10000,
            maxWidth: '400px',
            width: '100%'
          }}
        >
          <div style={{
            padding: '16px',
            borderRadius: '16px',
            background: notification.type === 'error' ? 'rgba(30, 0, 0, 0.9)' : notification.type === 'warning' ? 'rgba(20, 12, 0, 0.9)' : 'rgba(0, 5, 20, 0.9)',
            border: `1px solid ${notification.type === 'error' ? 'rgba(239, 68, 68, 0.3)' : notification.type === 'warning' ? 'rgba(245, 158, 11, 0.3)' : 'rgba(0, 102, 255, 0.3)'}`,
            color: notification.type === 'error' ? '#EF4444' : notification.type === 'warning' ? '#F59E0B' : '#0066FF',
            backdropFilter: 'blur(12px)',
            boxShadow: '0 20px 40px rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'start',
            gap: '12px'
          }}>
            <div style={{ marginTop: '2px' }}>
              {notification.type === 'error' ? (
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              ) : notification.type === 'warning' ? (
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                </svg>
              ) : (
                <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
            <div style={{ flex: 1 }}>
              <h4 style={{ 
                margin: '0 0 4px 0', 
                fontSize: '13px', 
                fontWeight: '800', 
                textTransform: 'uppercase', 
                letterSpacing: '0.05em' 
              }}>
                {notification.type === 'error' ? 'Error' : notification.type === 'warning' ? 'Sign In Required' : 'Notification'}
              </h4>
              <p style={{ 
                margin: 0, 
                fontSize: '12px', 
                opacity: 0.9, 
                lineHeight: '1.6', 
                fontWeight: '500' 
              }}>
                {sanitizeError(notification.message)}
              </p>
            </div>
            <button 
              onClick={() => setNotification(null)}
              style={{
                background: 'none',
                border: 'none',
                color: 'inherit',
                cursor: 'pointer',
                opacity: 0.5,
                padding: '4px'
              }}
            >
              <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export const notify = (message, type = 'info', duration = 5000) => {
  window.dispatchEvent(new CustomEvent('notify', { detail: { message, type, duration } }));
};

export default Notification;

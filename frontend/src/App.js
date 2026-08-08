import React, { useState, useEffect, useRef, useCallback } from 'react';
import io from 'socket.io-client';
import { AnimatePresence, motion } from 'framer-motion';
import './App.css';

import LoginScreen from './components/LoginScreen';
import ChatInterface from './components/ChatInterface';
import LoadingScreen from './components/LoadingScreen';
import Background from './components/Background';
import { authService } from './services/authService';
import { useToast } from './components/ui/Toast';

const SOCKET_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [socket, setSocket] = useState(null);
  const [connStatus, setConnStatus] = useState('connecting');
  const socketRef = useRef(null);
  const { toast } = useToast();

  const initializeSocket = useCallback(
    (token) => {
      if (socketRef.current) socketRef.current.disconnect();

      const s = io(SOCKET_URL, {
        reconnection: true,
        reconnectionAttempts: Infinity,
        reconnectionDelay: 800,
        reconnectionDelayMax: 4000,
        transports: ['websocket', 'polling'],
      });

      s.on('connect', () => {
        setConnStatus('connected');
        s.emit('authenticate', { token });
      });
      s.on('disconnect', () => setConnStatus('disconnected'));
      s.io.on('reconnect_attempt', () => setConnStatus('reconnecting'));
      s.io.on('reconnect', () => {
        setConnStatus('connected');
        s.emit('authenticate', { token });
        toast('Reconnected to Voxa', 'success');
      });
      s.on('auth_error', (data) => {
        toast(data?.message || 'Session expired — please sign in again', 'error');
        localStorage.removeItem('access_token');
        setIsAuthenticated(false);
        setUser(null);
      });

      socketRef.current = s;
      setSocket(s);
      setIsLoading(false);
    },
    [toast]
  );

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setIsLoading(false);
      return;
    }
    authService
      .verifyToken(token)
      .then((userData) => {
        setUser(userData);
        setIsAuthenticated(true);
        initializeSocket(token);
      })
      .catch(() => {
        localStorage.removeItem('access_token');
        setIsLoading(false);
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleAuthSuccess = useCallback(
    (response, mode) => {
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      setIsAuthenticated(true);
      initializeSocket(response.access_token);
      toast(
        mode === 'register'
          ? `Welcome aboard, ${response.user.username}!`
          : `Welcome back, ${response.user.username}!`,
        'success'
      );
    },
    [initializeSocket, toast]
  );

  const handleLogin = useCallback(
    async (credentials) => {
      setIsLoading(true);
      try {
        const response = await authService.login(credentials);
        handleAuthSuccess(response, 'login');
      } catch (error) {
        setIsLoading(false);
        throw error;
      }
    },
    [handleAuthSuccess]
  );

  const handleRegister = useCallback(
    async (userData) => {
      setIsLoading(true);
      try {
        const response = await authService.register(userData);
        handleAuthSuccess(response, 'register');
      } catch (error) {
        setIsLoading(false);
        throw error;
      }
    },
    [handleAuthSuccess]
  );

  const handleLogout = useCallback(() => {
    if (socketRef.current) socketRef.current.disconnect();
    localStorage.removeItem('access_token');
    setUser(null);
    setIsAuthenticated(false);
    setSocket(null);
    socketRef.current = null;
    toast('Signed out', 'info');
  }, [toast]);

  let screen;
  if (isLoading) {
    screen = <LoadingScreen key="loading" />;
  } else if (!isAuthenticated) {
    screen = (
      <LoginScreen
        key="login"
        onLogin={handleLogin}
        onRegister={handleRegister}
      />
    );
  } else {
    screen = (
      <ChatInterface
        key="chat"
        user={user}
        socket={socket}
        connStatus={connStatus}
        onLogout={handleLogout}
      />
    );
  }

  return (
    <>
      <Background />
      <div className="App">
        <AnimatePresence mode="wait">
          <motion.div
            key={screen.key}
            style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
            initial={{ opacity: 0, scale: 0.99 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 1.01 }}
            transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          >
            {screen}
          </motion.div>
        </AnimatePresence>
      </div>
    </>
  );
}

export default App;

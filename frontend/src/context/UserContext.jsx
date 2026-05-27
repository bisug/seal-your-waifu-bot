import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { apiFetch } from '../api/client';

export const UserContext = createContext(null);

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [liteMode, setLiteMode] = useState(() => {
    const saved = localStorage.getItem('sealbot-lite-mode');
    if (saved !== null) return saved === 'true';
    
    const cores = navigator.hardwareConcurrency || 4;
    const ram = navigator.deviceMemory || 4;
    return cores <= 4 || ram <= 4;
  });

  useEffect(() => {
    if (liteMode) {
      document.body.classList.add('lite-mode');
    } else {
      document.body.classList.remove('lite-mode');
    }
    localStorage.setItem('sealbot-lite-mode', liteMode.toString());
  }, [liteMode]);

  const toggleLiteMode = useCallback(() => {
    setLiteMode(prev => !prev);
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const data = await apiFetch('/me');
      setUser(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch user:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerRefresh = useCallback(() => {
    refreshUser();
  }, [refreshUser]);

  useEffect(() => {
    refreshUser();
    window.addEventListener('user-data-refresh', triggerRefresh);
    return () => window.removeEventListener('user-data-refresh', triggerRefresh);
  }, [refreshUser, triggerRefresh]);

  return (
    <UserContext.Provider value={{ user, loading, error, liteMode, refreshUser, triggerRefresh, toggleLiteMode }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

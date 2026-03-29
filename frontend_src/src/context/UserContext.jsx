import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiFetch, secureInit } from '../api';

const UserContext = createContext();

export const useUser = () => useContext(UserContext);

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const refreshUser = async () => {
    try {
      const data = await apiFetch('/me');
      setUser(data);
    } catch (err) {
      console.error('Failed to refresh user:', err);
      setError(err.message);
    }
  };

  useEffect(() => {
    const init = async () => {
      try {
        const token = await secureInit();
        if (token) {
          await refreshUser();
        } else {
          setError('Authentication failed. Please restart the app.');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    init();
  }, []);

  const value = {
    user,
    loading,
    error,
    refreshUser,
    setUser
  };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
};

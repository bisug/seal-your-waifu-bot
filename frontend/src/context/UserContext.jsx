import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import { apiFetch } from '../api/client';

export const UserContext = createContext(null);

/**
 * @typedef {Object} UserStats
 * @property {number} level
 * @property {number} xp
 * @property {number} xp_current
 * @property {number} xp_needed
 * @property {number} zenith
 * @property {number} total_characters
 * @property {number} rank
 */

/**
 * @typedef {Object} Character
 * @property {string} id
 * @property {string} name
 * @property {string} anime
 * @property {string} rarity
 * @property {string} img_url
 * @property {number} zenith_price
 * @property {boolean} owned
 * @property {number} count
 */

/**
 * @typedef {Object} Pet
 * @property {string} name
 * @property {string} ability
 * @property {string} mood
 * @property {string} img
 * @property {number} level
 * @property {number} xp
 * @property {number} xp_needed
 */

/**
 * @typedef {Object} User
 * @property {number} id
 * @property {string} first_name
 * @property {string} username
 * @property {string} avatar
 * @property {UserStats} stats
 * @property {Character[]} characters
 * @property {Pet} current_pet
 */

export const UserProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
    <UserContext.Provider value={{ user, loading, error, refreshUser, triggerRefresh }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => useContext(UserContext);

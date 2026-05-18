import React, { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import { apiFetch } from '../api/client';

export interface UserStats {
  level: number;
  xp: number;
  xp_current: number;
  xp_needed: number;
  zenith: number;
  total_characters: number;
  rank: number;
}

export interface Character {
  id: string;
  name: string;
  anime: string;
  rarity: string;
  img_url: string;
  zenith_price: number;
  owned: boolean;
  count: number;
}

export interface Pet {
  name: string;
  ability: string;
  mood: string;
  img: string;
  level: number;
  xp: number;
  xp_needed: number;
}

export interface User {
  id: number;
  first_name: string;
  username: string;
  avatar: string;
  balance: number;
  zenith: number;
  stats: UserStats;
  characters: Character[];
  current_pet: Pet | null;
}

interface UserContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  refreshUser: () => Promise<void>;
  triggerRefresh: () => void;
}

export const UserContext = createContext<UserContextType | null>(null);

export const UserProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshUser = useCallback(async () => {
    try {
      const data = await apiFetch('/me');
      setUser(data);
      setError(null);
    } catch (err: any) {
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

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};

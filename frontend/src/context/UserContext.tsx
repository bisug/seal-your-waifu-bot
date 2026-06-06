import React, { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import { apiFetch, getErrorMessage } from '../api/client';

export interface UserStats {
  level: number;
  xp: number;
  xp_current: number;
  xp_needed: number;
  zenith: number;
  total_characters: number;
  rank: number;
  pass_type?: string;
  incubation_slots?: number;
  active_incubations?: number;
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
  stock_limit?: number;
  sold_count?: number;
  stock_remaining?: number;
  sold_out?: boolean;
}

export interface Pet {
  id: string;
  name: string;
  ability: string;
  mood: string;
  img: string;
  level: number;
  xp: number;
  xp_needed: number;
  zenith_price: number;
  req_level: number;
  rarity?: string;
  desc?: string;
  shopIndex?: number;
  hp: number;
  atk: number;
  spd: number;
  luck: number;
  affection: number;
  is_active?: boolean;
}

export interface Egg {
  id?: string | null;
  tier: string;
  name: string;
  status: string;
  is_corrupted: boolean;
  hatch_time?: string | null;
  remaining_mins?: number | null;
  base_wait_min?: number | null;
  wait_min?: number | null;
  incubation_pass_type?: string | null;
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
  eggs?: Egg[];
  pets?: Pet[];
}

interface UserContextType {
  user: User | null;
  loading: boolean;
  error: string | null;
  liteMode: boolean;
  refreshUser: () => Promise<void>;
  triggerRefresh: () => void;
  toggleLiteMode: () => void;
}

export const UserContext = createContext<UserContextType | null>(null);

export const UserProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Enforce Lite Mode permanently for all users
  const liteMode = true;

  useEffect(() => {
    document.body.classList.add('lite-mode');
  }, []);

  const toggleLiteMode = useCallback(() => {
    // No-op as requested: lite only
  }, []);

  const refreshUser = useCallback(async () => {
    try {
      const data = await apiFetch('/me');
      setUser(data);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch user:', err);
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  const triggerRefresh = useCallback(() => {
    refreshUser();
  }, [refreshUser]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  useEffect(() => {
    window.addEventListener('user-data-refresh', triggerRefresh);
    return () => window.removeEventListener('user-data-refresh', triggerRefresh);
  }, [triggerRefresh]);

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

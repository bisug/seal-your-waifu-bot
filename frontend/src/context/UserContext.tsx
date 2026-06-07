import React, { useState, useEffect, useCallback, createContext, useContext, ReactNode } from 'react';
import { apiFetch, getErrorMessage } from '../api/client';

export interface UserStats {
  level: number;
  xp: number;
  xp_current: number;
  xp_needed: number;
  streak?: number;
  points?: number;
  zenith: number;
  badges?: string[];
  total_characters: number;
  unique_characters?: number;
  total_available_characters?: number;
  collection_percent?: number;
  rank: number;
  percentile?: number;
  pass_type?: string;
  incubation_slots?: number;
  active_incubations?: number;
}

export interface Achievement {
  id: string;
  name: string;
  icon: string;
}

export interface Titles {
  current: string;
  all: string[];
}

export interface Character {
  id: string;
  name: string;
  anime: string;
  rarity: string;
  img_url: string;
  zenith_price: number;
  base_zenith_price?: number;
  staff_discount?: number;
  owned: boolean;
  count: number;
  stock_limit?: number;
  sold_count?: number;
  stock_remaining?: number;
  sold_out?: boolean;
}

export interface Pet {
  id: string;
  petid?: string;
  name: string;
  ability?: string;
  mood?: string;
  img?: string;
  img_url?: string;
  image?: string;
  photo_url?: string;
  level?: number;
  xp?: number;
  xp_needed?: number;
  zenith_price?: number;
  req_level?: number;
  rarity?: string;
  desc?: string;
  shopIndex?: number;
  hp?: number;
  atk?: number;
  spd?: number;
  luck?: number;
  affection?: number;
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
  is_sudo?: boolean;
  role?: string | null;
  role_label?: string | null;
  role_tag?: string | null;
  role_symbol?: string | null;
  is_staff?: boolean;
  can_upload?: boolean;
  can_edit_character?: boolean;
  upload_reward?: {
    balance?: number;
    zenith?: number;
  } | null;
  role_perks?: Record<string, number>;
  role_benefits?: string[];
  balance: number;
  zenith: number;
  stats: UserStats;
  achievements?: Achievement[];
  titles?: Titles;
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

const hasAuthBootstrap = () => {
  const telegramInit = Boolean(window.Telegram?.WebApp?.initData);
  if (telegramInit) return true;

  try {
    return Boolean(sessionStorage.getItem('auth_token'));
  } catch {
    return false;
  }
};

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
    if (!hasAuthBootstrap()) {
      setUser(null);
      setError(null);
      setLoading(false);
      return;
    }

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

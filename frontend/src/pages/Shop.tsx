import React from 'react';
import { useApi } from '../hooks/useApi';
import { useToast } from '../components/ui/Toast';
import { Card } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { Zap, Loader2, Sparkles, RefreshCw } from 'lucide-react';
import { formatNumber } from '../utils';
import { apiFetch } from '../api/client';
import { useUser } from '../context/UserContext';

export const Shop = ({ onCharClick, triggerRefresh }: any) => {
  const { data: shopData, loading, execute: fetchShop } = useApi('/shop/characters');

  if (loading && !shopData) return (
    <div className="grid grid-cols-3 gap-2 px-4 py-6">
       {Array.from({ length: 9 }).map((_, i) => <CardSkeleton key={i} />)}
    </div>
  );

  return (
    <div className="pb-24 pt-4">
      <header className="px-6 mb-8 flex justify-between items-end">
         <div>
            <h1 className="text-2xl font-black italic uppercase tracking-tighter text-white">Daily Boutique</h1>
            <p className="text-[9px] font-bold text-brand-accent uppercase tracking-[0.3em]">Resets in 14h 22m</p>
         </div>
         <button onClick={() => fetchShop()} className="p-2 rounded-xl bg-white/5 border border-white/10 text-slate-500 active:rotate-180 transition-transform duration-500">
            <RefreshCw size={16} />
         </button>
      </header>

      <div className="grid grid-cols-3 gap-2 px-4">
        {shopData?.map((char) => (
          <div key={char.id} className="relative group">
            <Card character={char} onClick={() => onCharClick(char)} />
          </div>
        ))}
      </div>
    </div>
  );
};

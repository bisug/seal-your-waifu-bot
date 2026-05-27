import React from 'react';
import { useApi } from '../hooks/useApi';
import { Card } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { RefreshCw } from 'lucide-react';

export const Shop = ({ onCharClick, triggerRefresh }: any) => {
  const { data: shopData, loading, execute: fetchShop } = useApi('/shop/characters');

  const handleRefresh = () => {
    fetchShop();
    if (triggerRefresh) triggerRefresh();
  };

  if (loading && !shopData) return (
    <div className="grid grid-cols-3 gap-2 px-4 py-6">
       {Array.from({ length: 9 }).map((_, i) => <CardSkeleton key={i} />)}
    </div>
  );

  return (
    <div className="pb-24 pt-4">
      <header className="px-4 mb-4 flex justify-between items-center">
         <div>
            <h1 className="text-sm font-bold uppercase tracking-wider text-white">Daily Shop</h1>
            <p className="text-[9px] font-medium text-slate-500 uppercase tracking-widest">Resets Daily</p>
         </div>
         <button onClick={handleRefresh} className="p-2 rounded-lg bg-white/5 border border-white/5 text-slate-500 active:scale-90 transition-all">
            <RefreshCw size={14} />
         </button>
      </header>

      <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2 px-4">
        {shopData?.map((char: any) => (
          <Card key={char.id} character={char} onClick={() => onCharClick(char)} />
        ))}
      </div>
    </div>
  );
};

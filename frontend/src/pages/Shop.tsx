import React from 'react';
import { useApi } from '../hooks/useApi';
import { Card } from '../components/character/Card';
import { CardSkeleton } from '../components/ui/Skeleton';
import { RefreshCw, ShoppingBag } from 'lucide-react';
import { Character } from '../context/UserContext';

interface ShopProps {
  onCharClick: (char: Character) => void;
  triggerRefresh?: () => void;
}

export const Shop = ({ onCharClick, triggerRefresh }: ShopProps) => {
  const { data: shopData, loading, execute: fetchShop } = useApi<Character[]>('/shop/characters');

  const handleRefresh = () => {
    fetchShop();
    if (triggerRefresh) triggerRefresh();
  };

  if (loading && !shopData) return (
    <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2 px-4 py-6">
       {Array.from({ length: 12 }).map((_, i) => <CardSkeleton key={i} />)}
    </div>
  );

  return (
    <div className="pb-24 pt-4">
      <header className="px-4 mb-6 flex justify-between items-end">
         <div>
            <div className="flex items-center gap-2 mb-0.5">
               <ShoppingBag size={14} className="text-brand-accent" />
               <h1 className="text-sm font-bold text-zinc-100">Daily Shop</h1>
            </div>
            <p className="text-xs font-medium text-zinc-500">Inventory resets every 24 hours</p>
         </div>
         <button
           onClick={handleRefresh}
           className="p-2 rounded-md bg-zinc-900 border border-white/5 text-zinc-400 hover:text-zinc-100 transition-colors active:bg-zinc-800"
         >
            <RefreshCw size={14} />
         </button>
      </header>

      <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 gap-2 px-4">
        {shopData?.map((char) => (
          <Card key={char.id} character={char} onClick={() => onCharClick(char)} />
        ))}
      </div>
    </div>
  );
};

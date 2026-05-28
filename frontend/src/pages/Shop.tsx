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
    <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3 px-4 py-6 max-w-5xl mx-auto">
       {Array.from({ length: 12 }).map((_, i) => <CardSkeleton key={i} />)}
    </div>
  );

  return (
    <div className="pb-20 pt-4 max-w-5xl mx-auto">
      <header className="px-4 mb-6 flex justify-between items-end border-b border-white/5 pb-4">
         <div>
            <div className="flex items-center gap-2 mb-1">
               <ShoppingBag size={18} className="text-brand-accent" />
               <h1 className="text-lg font-bold text-white tracking-tight">Daily Shop</h1>
            </div>
            <p className="text-sm font-medium text-neutral-400">Inventory resets every 24 hours</p>
         </div>
         <button
           onClick={handleRefresh}
           className="p-2.5 rounded-lg bg-brand-deep border border-white/5 text-neutral-400 hover:text-white hover:bg-white/5 transition-colors active:scale-95"
           aria-label="Refresh Shop"
         >
            <RefreshCw size={16} />
         </button>
      </header>

      <div className="grid grid-cols-3 xs:grid-cols-4 sm:grid-cols-5 md:grid-cols-6 lg:grid-cols-7 gap-3 px-4">
        {shopData?.map((char) => (
          <Card key={char.id} character={char} onClick={() => onCharClick(char)} />
        ))}
      </div>
    </div>
  );
};

import React, { useState, useEffect } from 'react';
import { ShoppingBag, Search, Dog } from 'lucide-react';
import { Shop } from './Shop';
import { Gallery } from './Gallery';
import { PetShop } from './PetShop';
import { cn } from '../utils';

interface MarketProps {
  onCharClick: (character: any) => void;
  onPetClick: (pet: any) => void;
  onNavigate?: (tabId: string) => void;
}

export const Market = ({ onCharClick, onPetClick }: MarketProps) => {
  const [activeTab, setActiveTab] = useState('shop'); // 'shop', 'gallery', 'pets'
  const [refreshKey, setRefreshKey] = useState(0);

  const triggerShopRefresh = () => setRefreshKey(prev => prev + 1);

  useEffect(() => {
    window.addEventListener('shop-data-refresh', triggerShopRefresh);
    return () => window.removeEventListener('shop-data-refresh', triggerShopRefresh);
  }, []);

  const handleTabChange = (tabId: string) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tabId);
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="sticky top-0 z-40 border-b border-white/5 px-4 pb-2 bg-brand-midnight"
           style={{ paddingTop: 'calc(1rem + env(safe-area-inset-top))' }}>
        <div className="flex p-1 bg-white/5 rounded-xl border border-white/5 max-w-sm mx-auto mb-1">
          {[
            { id: 'shop', icon: ShoppingBag, label: 'Shop' },
            { id: 'gallery', icon: Search, label: 'Catalog' },
            { id: 'pets', icon: Dog, label: 'Pets' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all ${
                activeTab === tab.id ? 'bg-brand-accent text-white' : 'text-slate-500 hover:text-white'
              }`}
            >
              <tab.icon size={12} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1">
        {activeTab === 'shop' && (
          <Shop key={`shop-${refreshKey}`} onCharClick={onCharClick} triggerRefresh={triggerShopRefresh} />
        )}
        {activeTab === 'gallery' && (
          <Gallery key={`gallery-${refreshKey}`} onCharClick={onCharClick} />
        )}
        {activeTab === 'pets' && (
          <PetShop key={`pets-${refreshKey}`} onPetClick={onPetClick} />
        )}
      </div>
    </div>
  );
};

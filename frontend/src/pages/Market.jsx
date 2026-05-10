import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShoppingBag, Search } from 'lucide-react';
import { Shop } from './Shop';
import { Gallery } from './Gallery';
import { PetShop } from './PetShop';

export const Market = ({ onCharClick, onPetClick }) => {
  const [activeTab, setActiveTab] = useState('shop'); // 'shop', 'gallery', 'pets'
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const handleRefresh = () => setRefreshKey(prev => prev + 1);
    window.addEventListener('shop-data-refresh', handleRefresh);
    return () => window.removeEventListener('shop-data-refresh', handleRefresh);
  }, []);

  const handleTabChange = (tabId) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tabId);
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Internal Sub-Nav */}
      <div className="sticky top-0 z-40 bg-brand-midnight/60 backdrop-blur-xl border-b border-white/5 px-4 pb-2" style={{ paddingTop: 'calc(1rem + env(safe-area-inset-top))' }}>
        <div className="flex p-1 bg-white/5 rounded-xl border border-white/5 max-w-sm mx-auto mb-2">
          {[
            { id: 'shop', icon: ShoppingBag, label: 'Market' },
            { id: 'gallery', icon: Search, label: 'Catalog' },
            { id: 'pets', icon: ShoppingBag, label: 'Pets' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all ${
                activeTab === tab.id ? 'bg-white text-brand-midnight shadow-lg' : 'text-slate-500 hover:text-white'
              }`}
            >
              <tab.icon size={12} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto no-scrollbar app-scroller">
        <AnimatePresence mode="wait">
          {activeTab === 'shop' && (
            <motion.div
              key={`shop-${refreshKey}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
              className=""
            >
              <Shop onCharClick={onCharClick} />
            </motion.div>
          )}
          {activeTab === 'gallery' && (
            <motion.div
              key={`gallery-${refreshKey}`}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className=""
            >
              <Gallery onCharClick={onCharClick} />
            </motion.div>
          )}
          {activeTab === 'pets' && (
            <motion.div
              key={`pets-${refreshKey}`}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className=""
            >
              <PetShop onPetClick={onPetClick} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

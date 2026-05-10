import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Users, Repeat, Heart, Trophy, Swords } from 'lucide-react';
import { Trade } from './Trade';
import { Marriage } from './Marriage';
import { Referrals } from './Referrals';
import { BattleStats } from './BattleStats';
import { Leaderboard } from './Leaderboard';
import { Quests } from './Quests';
import { Pass } from './Pass';

export const Nexus = () => {
  const [activeTab, setActiveTab] = useState('quests');

  const handleTabChange = (tabId) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tabId);
  };

  const tabs = [
    { id: 'quests', icon: Users, label: 'Tasks' },
    { id: 'pass', icon: Trophy, label: 'Pass' },
    { id: 'leaderboard', icon: Swords, label: 'Rankings' },
    { id: 'trade', icon: Repeat, label: 'Trade' },
    { id: 'marriage', icon: Heart, label: 'Marriage' },
    { id: 'referrals', icon: Users, label: 'Referrals' },
    { id: 'battle', icon: Swords, label: 'Battle' },
  ];

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Internal Sub-Nav */}
      <div className="sticky top-0 z-40 bg-brand-midnight/60 backdrop-blur-xl border-b border-white/5 px-4 pb-2" style={{ paddingTop: 'calc(1rem + env(safe-area-inset-top))' }}>
        <div className="flex p-1 bg-white/5 rounded-xl border border-white/5 mx-auto mb-2 overflow-x-auto no-scrollbar">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all whitespace-nowrap ${
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
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="p-4"
          >
            {activeTab === 'quests' && <Quests />}
            {activeTab === 'pass' && <Pass />}
            {activeTab === 'leaderboard' && <Leaderboard />}
            {activeTab === 'trade' && <Trade />}
            {activeTab === 'marriage' && <Marriage />}
            {activeTab === 'referrals' && <Referrals />}
            {activeTab === 'battle' && <BattleStats />}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

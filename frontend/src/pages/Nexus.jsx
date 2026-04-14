import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trophy, Star, LayoutGrid, Sparkles } from 'lucide-react';
import { Quests } from './Quests';
import { Pass } from './Pass';
import { Leaderboard } from './Leaderboard';

export const Nexus = () => {
  const [activeTab, setActiveTab] = useState('quests'); // 'quests', 'pass', 'leaderboard'

  const handleTabChange = (tabId) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tabId);
  };

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Internal Sub-Nav */}
      <div className="sticky top-0 z-40 bg-brand-midnight/60 backdrop-blur-xl border-b border-white/5 px-4 pb-2" style={{ paddingTop: 'calc(1rem + env(safe-area-inset-top))' }}>
        <div className="flex p-1 bg-white/5 rounded-xl border border-white/5 mx-auto mb-2 overflow-x-auto no-scrollbar">
          {[
            { id: 'quests', icon: LayoutGrid, label: 'Tasks' },
            { id: 'pass', icon: Star, label: 'Pass' },
            { id: 'leaderboard', icon: Trophy, label: 'Rankings' },
          ].map(tab => (
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

      <div className="flex-1 overflow-y-auto no-scrollbar">
        <AnimatePresence mode="wait">
          {activeTab === 'quests' && (
            <motion.div
              key="quests"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Quests />
            </motion.div>
          )}
          {activeTab === 'pass' && (
            <motion.div
              key="pass"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Pass />
            </motion.div>
          )}
          {activeTab === 'leaderboard' && (
            <motion.div
              key="leaderboard"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
            >
              <Leaderboard />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

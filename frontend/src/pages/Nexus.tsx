import React, { useState } from 'react';
import { Users, Repeat, Heart, Trophy, Swords, Zap } from 'lucide-react';
import { Trade } from './Trade';
import { Marriage } from './Marriage';
import { Referrals } from './Referrals';
import { BattleStats } from './BattleStats';
import { Leaderboard } from './Leaderboard';
import { Quests } from './Quests';
import { Pass } from './Pass';

export const Nexus = () => {
  const [activeTab, setActiveTab] = useState('quests');

  const handleTabChange = (tabId: string) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setActiveTab(tabId);
  };

  const tabs = [
    { id: 'quests', icon: Zap, label: 'Tasks' },
    { id: 'pass', icon: Trophy, label: 'Pass' },
    { id: 'leaderboard', icon: Swords, label: 'Ranks' },
    { id: 'trade', icon: Repeat, label: 'Trade' },
    { id: 'marriage', icon: Heart, label: 'Social' },
    { id: 'referrals', icon: Users, label: 'Invites' },
    { id: 'battle', icon: Swords, label: 'Stats' },
  ];

  return (
    <div className="flex-1 flex flex-col min-h-0">
      <div className="sticky top-0 z-40 border-b border-white/5 px-4 pb-2 bg-brand-midnight"
           style={{ paddingTop: 'calc(1rem + env(safe-area-inset-top))' }}>
        <div className="flex p-1 bg-white/5 rounded-xl border border-white/5 mx-auto mb-1 overflow-x-auto no-scrollbar scroll-fade-mask snap-x">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all whitespace-nowrap active:scale-95 snap-center ${
                activeTab === tab.id ? 'bg-brand-accent text-white' : 'text-slate-500 hover:text-white'
              }`}
            >
              <tab.icon size={12} />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 p-4">
        {activeTab === 'quests' && <Quests />}
        {activeTab === 'pass' && <Pass />}
        {activeTab === 'leaderboard' && <Leaderboard />}
        {activeTab === 'trade' && <Trade />}
        {activeTab === 'marriage' && <Marriage />}
        {activeTab === 'referrals' && <Referrals />}
        {activeTab === 'battle' && <BattleStats />}
      </div>
    </div>
  );
};

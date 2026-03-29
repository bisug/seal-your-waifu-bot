import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { useUser } from '../context/UserContext';
import { ProgressBar, Card } from '../components/UI';
import { Shield, Zap, Users, Trophy } from 'lucide-react';

export const Profile = ({ onCharClick }) => {
  const { user, loading } = useUser();

  // Consolidate duplicates for cleaner UI and better performance
  const consolidatedHarem = useMemo(() => {
    if (!user || !user.characters) return [];
    
    const map = new Map();
    user.characters.forEach(char => {
      const charId = char.id;
      if (map.has(charId)) {
        map.get(charId).count = (map.get(charId).count || 1) + 1;
      } else {
        map.set(charId, { ...char, count: 1 });
      }
    });
    return Array.from(map.values()).sort((a, b) => b.count - a.count);
  }, [user]);

  if (loading) return (
    <div className="flex-1 flex flex-col items-center justify-center space-y-4">
      <div className="w-12 h-12 rounded-full border-4 border-slate-800 border-t-brand-neon animate-spin neon-shadow" />
      <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest animate-pulse">Synchronizing Data</p>
    </div>
  );

  if (!user) return null;

  return (
    <div className="pb-32">
      {/* Cinematic Hero Section */}
      <section className="relative h-72 overflow-hidden flex flex-col justify-end px-6 pb-8">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-midnight/60 to-brand-midnight z-10" />
        <img 
          src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} 
          className="absolute inset-0 w-full h-full object-cover opacity-40 blur-sm scale-110"
          alt="Profile Background"
        />
        
        <div className="relative z-20 flex items-center space-x-5">
          <div className="relative">
            <div className="w-20 h-20 rounded-2xl overflow-hidden border-2 border-brand-neon neon-shadow">
              <img src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} className="w-full h-full object-cover" alt="User" />
            </div>
            <div className="absolute -bottom-2 -right-2 bg-brand-neon text-brand-midnight text-[10px] font-black px-2 py-0.5 rounded-md shadow-lg shadow-brand-neon/20">
              LVL {user.stats?.level || 1}
            </div>
          </div>
          <div className="text-left">
            <h1 className="text-2xl font-black uppercase tracking-tight leading-none mb-1">{user.first_name || 'Collector'}</h1>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-[0.2em]">@{user.username || 'unknown'}</p>
          </div>
        </div>
      </section>

      {/* Stats Dashboard */}
      <div className="px-6 -mt-4 relative z-30 grid grid-cols-3 gap-3 mb-8">
        {[
          { icon: Shield, label: 'XP', value: user.stats?.xp || 0, color: 'text-brand-neon' },
          { icon: Zap, label: 'Zenith', value: user.stats?.zenith || 0, color: 'text-brand-accent' },
          { icon: Users, label: 'Owned', value: user.stats?.total_characters || 0, color: 'text-white' },
        ].map((stat, i) => (
          <div key={i} className="glass-panel p-3 rounded-2xl border border-white/5 flex flex-col items-center">
            <stat.icon size={16} className={`${stat.color} mb-1`} />
            <span className="text-[14px] font-black">{stat.value.toLocaleString()}</span>
            <span className="text-[8px] font-bold text-slate-500 uppercase tracking-widest">{stat.label}</span>
          </div>
        ))}
      </div>

      {/* Progress Section */}
      <section className="px-6 mb-10">
        <ProgressBar 
          current={user.stats?.xp_current || 0} 
          total={user.stats?.xp_needed || 1000} 
          label="Exp Progression"
        />
      </section>

      {/* Harem Grid */}
      <section className="px-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-black uppercase tracking-widest text-slate-400">My Collection</h2>
          <div className="flex items-center space-x-1 text-[10px] font-black text-brand-neon uppercase tracking-widest bg-brand-neon/5 px-2 py-1 rounded-full border border-brand-neon/10">
            <Trophy size={12} />
            <span>Rank #{user.stats?.rank || '---'}</span>
          </div>
        </div>
        
        {consolidatedHarem.length > 0 ? (
          <div className="grid grid-cols-2 xs:grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-7 2xl:grid-cols-8 gap-3">
             {consolidatedHarem.map(char => (
               <Card 
                key={char.id} 
                character={char} 
                onClick={() => onCharClick(char)} 
               />
             ))}
          </div>
        ) : (
          <div className="glass-panel p-10 rounded-3xl border border-white/5 text-center flex flex-col items-center opacity-80">
            <Users size={40} className="text-slate-700 mb-4" />
            <p className="text-slate-500 text-xs font-medium uppercase tracking-widest italic leading-relaxed">
              Your harem is empty.<br/>Capture characters in group chats to start!
            </p>
          </div>
        )}
      </section>
    </div>
  );
};

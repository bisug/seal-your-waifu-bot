import React, { useState, memo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Medal, Loader2, Users, Star, TrendingUp } from 'lucide-react';
import { useApi } from '../components/UI';
import { Avatar } from '../components/Avatar';
import { formatNumber } from '../utils';

const LeaderboardItem = memo(({ user, index, metric, getMetricIcon }) => (
  <motion.div
    initial={{ opacity: 0, x: -10 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: (index % 10) * 0.03 }}
    className={`glass-panel p-4 rounded-2xl border flex items-center space-x-4 ${
      index === 0 ? 'border-brand-neon bg-brand-neon/5' : index === 1 ? 'border-blue-400/30' : index === 2 ? 'border-amber-400/30' : 'border-white/5'
    }`}
  >
    <div className="w-8 text-center text-brand-neon">
       {index < 3 ? <Medal className={index === 0 ? 'text-yellow-400 shadow-[0_0_10px_rgba(250,204,21,0.4)]' : index === 1 ? 'text-slate-300' : 'text-amber-600'} size={20} /> : <span className="text-[11px] text-slate-600 font-black">#{index+1}</span>}
    </div>
    
    <div className="relative">
       <Avatar src={user.avatar} className="w-10 h-10 rounded-full object-cover" alt="Avatar" />
       {index === 0 && <div className="absolute -top-1 -right-1 w-3 h-3 bg-brand-neon rounded-full animate-ping" />}
    </div>

    <div className="flex-1 text-left min-w-0">
      <p className="text-[11px] font-black truncate tracking-tight mb-0.5">{user.name}</p>
      <div className="flex items-center space-x-1 text-slate-500">
         {getMetricIcon()}
         <span className="text-[11px] truncate font-bold uppercase">{formatNumber(user.value)} {metric.toUpperCase()}</span>
      </div>
    </div>
  </motion.div>
));

export const Leaderboard = () => {
  const [metric, setMetric] = useState('harem');

  const { data: items = [], loading } = useApi(`/leaderboard?metric=${metric}&limit=50`, {
    initialData: []
  }, [metric]);

  const getMetricIcon = useCallback(() => {
    if (metric === 'level') return <TrendingUp size={14} />;
    if (metric === 'zenith') return <Star size={14} />;
    return <Users size={14} />;
  }, [metric]);

  const handleMetricSelection = (metricId) => {
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('light');
    setMetric(metricId);
  };

  return (
    <div className="pb-8 pt-6 px-4 uppercase tracking-[0.2em] font-black">
      <header className="mb-8 px-2">
        <div className="flex items-center space-x-2 text-brand-neon mb-1 text-[11px]">
          <Trophy size={16} />
          <span className="font-black uppercase tracking-[0.3em]">Global Dominance</span>
        </div>
        <h1 className="text-2xl tracking-tight font-black uppercase">Rankings</h1>
      </header>

      <div className="flex space-x-2 mb-8 overflow-x-auto no-scrollbar scroll-fade-mask">
        {[
          { id: 'harem', label: 'Collectors', icon: Users },
          { id: 'level', label: 'Tier List', icon: TrendingUp },
          { id: 'zenith', label: 'Wealth', icon: Star },
        ].map(m => (
          <button
            key={m.id}
            onClick={() => handleMetricSelection(m.id)}
            className={`px-4 py-3 rounded-2xl flex items-center space-x-2 transition-all border ${
              metric === m.id ? 'bg-white text-brand-midnight border-white shadow-xl shadow-white/5' : 'bg-white/5 text-slate-500 border-white/5'
            }`}
          >
            <m.icon size={14} />
            <span className="text-[11px] font-black whitespace-nowrap">{m.label}</span>
          </button>
        ))}
      </div>

      {loading && !items.length ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-neon" /></div>
      ) : !loading && items.length === 0 ? (
        <div className="flex flex-col items-center py-20 text-center opacity-60">
          <Trophy size={40} className="text-slate-800 mb-4" />
          <p className="text-slate-500 text-[11px] font-bold uppercase tracking-widest">No rankings yet.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((user, i) => (
            <LeaderboardItem 
              key={user.id} 
              user={user} 
              index={i} 
              metric={metric} 
              getMetricIcon={getMetricIcon} 
            />
          ))}
        </div>
      )}
    </div>
  );
};

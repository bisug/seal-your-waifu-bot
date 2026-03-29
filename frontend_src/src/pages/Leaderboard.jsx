import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { apiFetch } from '../api';
import { Trophy, Medal, Loader2, Users, Star, TrendingUp } from 'lucide-react';

export const Leaderboard = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [metric, setMetric] = useState('harem');

  const fetchLeaderboard = async () => {
    setLoading(true);
    try {
      const data = await apiFetch(`/leaderboard?metric=${metric}&limit=50`);
      setItems(data);
    } catch (err) {
      console.error('Leaderboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaderboard();
  }, [metric]);

  const getMetricIcon = () => {
    if (metric === 'level') return <TrendingUp size={14} />;
    if (metric === 'zenith') return <Star size={14} />;
    return <Users size={14} />;
  };

  return (
    <div className="pb-32 pt-6 px-4 uppercase tracking-[0.2em] font-black">
      <header className="mb-8 px-2">
        <div className="flex items-center space-x-2 text-brand-neon mb-1">
          <Trophy size={16} />
          <span className="text-[10px]">Global Dominance</span>
        </div>
        <h1 className="text-2xl tracking-tight">Rankings</h1>
      </header>

      <div className="flex space-x-2 mb-8 overflow-x-auto no-scrollbar">
        {[
          { id: 'harem', label: 'Collectors', icon: Users },
          { id: 'level', label: 'Tier List', icon: TrendingUp },
          { id: 'zenith', label: 'Wealth', icon: Star },
        ].map(m => (
          <button
            key={m.id}
            onClick={() => setMetric(m.id)}
            className={`px-4 py-3 rounded-2xl flex items-center space-x-2 transition-all border ${
              metric === m.id ? 'bg-white text-brand-midnight border-white shadow-xl shadow-white/5' : 'bg-white/5 text-slate-500 border-white/5'
            }`}
          >
            <m.icon size={14} />
            <span className="text-[10px] whitespace-nowrap">{m.label}</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Loader2 className="animate-spin text-brand-neon" /></div>
      ) : (
        <div className="space-y-3">
          {items.map((user, i) => (
            <motion.div
              key={user.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03 }}
              className={`glass-panel p-4 rounded-2xl border flex items-center space-x-4 ${
                i === 0 ? 'border-brand-neon bg-brand-neon/5' : i === 1 ? 'border-blue-400/30' : i === 2 ? 'border-amber-400/30' : 'border-white/5'
              }`}
            >
              <div className="w-8 text-center">
                 {i < 3 ? <Medal className={i === 0 ? 'text-brand-neon' : i === 1 ? 'text-slate-300' : 'text-amber-600'} size={20} /> : <span className="text-xs text-slate-600">#{i+1}</span>}
              </div>
              
              <div className="relative">
                 <img src={user.avatar || 'https://files.catbox.moe/2hsawz.jpg'} className="w-10 h-10 rounded-full border border-white/10" alt="Avatar" />
                 {i === 0 && <div className="absolute -top-1 -right-1 w-3 h-3 bg-brand-neon rounded-full animate-ping" />}
              </div>

              <div className="flex-1 text-left min-w-0">
                <p className="text-xs font-black truncate tracking-tight mb-0.5">{user.name}</p>
                <div className="flex items-center space-x-1 text-slate-500">
                   {getMetricIcon()}
                   <span className="text-[9px] truncate font-bold uppercase">{user.value.toLocaleString()} {metric.toUpperCase()}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

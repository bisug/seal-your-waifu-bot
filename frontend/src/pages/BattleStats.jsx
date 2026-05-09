import React from 'react';
import { useApi, Skeleton } from '../components/UI';
import { Swords, Trophy, Target, ShieldAlert } from 'lucide-react';

export const BattleStats = () => {
  const { data: stats, loading } = useApi('/battle/stats');

  if (loading && !stats) return <Skeleton className="h-48 rounded-3xl" />;

  const statCards = [
    { label: 'Total Battles', value: stats?.total_battles || 0, icon: Swords, color: 'text-white' },
    { label: 'Victories', value: stats?.wins || 0, icon: Trophy, color: 'text-brand-accent' },
    { label: 'Defeats', value: stats?.losses || 0, icon: ShieldAlert, color: 'text-red-500' },
    { label: 'Win Rate', value: `${stats?.win_rate?.toFixed(1) || 0}%`, icon: Target, color: 'text-brand-accent' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Battle Intelligence</h2>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {statCards.map((stat, i) => (
          <div key={i} className="glass-panel p-4 rounded-3xl border border-white/5 flex flex-col items-center text-center">
            <div className={`${stat.color} mb-2 opacity-80`}>
              <stat.icon size={20} />
            </div>
            <span className="text-lg font-black text-white tracking-tight">{stat.value}</span>
            <span className="text-[9px] font-bold text-slate-500 uppercase tracking-widest">{stat.label}</span>
          </div>
        ))}
      </div>

      <section className="mt-8">
        <h2 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-3">Recent Performance</h2>
        <div className="glass-panel p-6 rounded-3xl border border-white/5 text-center flex flex-col items-center opacity-80">
          <Swords size={40} className="text-slate-800 mb-4" />
          <p className="text-slate-500 text-[11px] font-bold uppercase tracking-widest italic leading-relaxed">
            Detailed battle logs are available in the bot.<br/>Use /battle in any group!
          </p>
        </div>
      </section>
    </div>
  );
};
